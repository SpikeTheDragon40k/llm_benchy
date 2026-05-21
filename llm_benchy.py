import requests
import time
import json
import csv
import sys
import threading
import psutil
try:
    from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetUtilizationRates, nvmlShutdown
    HAS_GPU_DATA = True
except ImportError:
    HAS_GPU_DATA = False

from tabulate import tabulate

OLLAMA_BASE_URL = "http://localhost:11434"

class HardwareMonitor(threading.Thread):
    """Monitor CPU, RAM, and GPU usage in a background thread."""
    def __init__(self, interval=0.5):
        super().__init__()
        self.interval = interval
        self.stopped = False
        self.cpu_usage = []
        self.ram_usage = []
        self.gpu_usage = []
        
        if HAS_GPU_DATA:
            try:
                nvmlInit()
                self.gpu_handle = nvmlDeviceGetHandleByIndex(0)
            except:
                self.gpu_handle = None
        else:
            self.gpu_handle = None

    def run(self):
        while not self.stopped:
            self.cpu_usage.append(psutil.cpu_percent())
            self.ram_usage.append(psutil.virtual_memory().percent)
            if self.gpu_handle:
                try:
                    util = nvmlDeviceGetUtilizationRates(self.gpu_handle)
                    self.gpu_usage.append(util.gpu)
                except:
                    pass
            time.sleep(self.interval)

    def stop(self):
        self.stopped = True
        if HAS_GPU_DATA:
            try:
                nvmlShutdown()
            except:
                pass

    def get_stats(self):
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        avg_ram = sum(self.ram_usage) / len(self.ram_usage) if self.ram_usage else 0
        avg_gpu = sum(self.gpu_usage) / len(self.gpu_usage) if self.gpu_usage else 0
        return round(avg_cpu, 1), round(avg_ram, 1), round(avg_gpu, 1)

def get_local_models():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        return [m["name"] for m in response.json().get("models", [])]
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        sys.exit(1)

def benchmark_model(model_name, prompt):
    print(f"\n[+] Testing: {model_name}")
    
    # Warm-up
    requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": model_name, "prompt": "hi", "stream": False})

    # Start Monitoring
    monitor = HardwareMonitor()
    monitor.start()

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 128, "temperature": 0}
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Stop Monitoring
        monitor.stop()
        monitor.join()
        avg_cpu, avg_ram, avg_gpu = monitor.get_stats()

        # Metrics
        eval_duration = data.get("eval_duration", 0) / 1e9
        eval_count = data.get("eval_count", 0)
        tps = eval_count / eval_duration if eval_duration > 0 else 0

        return {
            "Model": model_name,
            "Tokens/sec": round(tps, 2),
            "TTFT (s)": round(data.get("prompt_eval_duration", 0) / 1e9, 2),
            "Avg CPU %": avg_cpu,
            "Avg RAM %": avg_ram,
            "Avg GPU %": avg_gpu if avg_gpu > 0 else "N/A",
            "Output Tokens": eval_count
        }
    except Exception as e:
        monitor.stop()
        return {"Model": model_name, "Error": str(e)}

def save_results(results):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Save JSON
    with open(f"benchmark_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=4)
    
    # Save CSV
    keys = results[0].keys()
    with open(f"benchmark_{timestamp}.csv", "w", newline="") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
    
    print(f"\n✅ Results saved to benchmark_{timestamp}.json and .csv")

def main():
    available_models = get_local_models()
    if not available_models: return

    print("\n--- Available Ollama Models ---")
    for i, name in enumerate(available_models, 1):
        print(f"{i}. {name}")
    
    choice = input("\nEnter number(s) (e.g. 1,2) or 'all': ").strip().lower()
    selected = available_models if choice == 'all' else [available_models[int(x)-1] for x in choice.split(',')]

    prompt = input("\nEnter prompt (Enter for default): ") or "Explain quantum computing in 100 words."

    results = []
    for model in selected:
        results.append(benchmark_model(model, prompt))
    
    print("\n" + tabulate(results, headers="keys", tablefmt="fancy_grid"))
    save_results(results)

if __name__ == "__main__":
    main()