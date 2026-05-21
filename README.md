# 🚀 LLM Benchy

A lightweight Python utility to measure the performance of Large Language Models (LLMs) running locally on your machine via **Ollama**. 

This script dynamically fetches your installed models and provides a detailed breakdown of performance metrics like **Tokens Per Second (TPS)**, **Time to First Token (TTFT)**, and **Load Durations**.

## ✨ Features

- 🔍 **Dynamic Model Discovery**: Automatically lists all models currently installed on your local Ollama server.
- ⚡ **Performance Metrics**: Calculates generation speed (TPS) and system latency (TTFT).
- 🔄 **Batch Testing**: Select specific models or test your entire library in one go.
- 📝 **Custom Prompts**: Test how models handle different types of queries (logic, creative, coding).
- 📊 **Clean Output**: Displays results in a formatted table for easy comparison.

---

## 🛠️ Prerequisites

1.  **Ollama**: Ensure Ollama is installed and the background service is running. [Download Ollama here](https://ollama.com/).
2.  **Python 3.8+**: Make sure Python is installed on your laptop.
3.  **Local Models**: You must have at least one model downloaded (e.g., `ollama pull llama3`).

---

## 📥 Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/your-username/ollama-benchmark.git
   cd ollama-benchmark
   ```

2. **Install dependencies**:
   ```bash
   pip install requests tabulate
   ```

---

## 🚀 Usage

Run the script from your terminal:

```bash
python benchmark.py
```

### How it works:
1. The script scans your local Ollama library.
2. You select which models to test by entering their numbers (e.g., `1, 3`) or typing `all`.
3. You can provide a custom prompt or use the default.
4. The script performs a **warm-up run** (to ensure the model is loaded into VRAM/RAM) followed by a **timed performance run**.

---

## 📊 Metrics Explained

| Metric | Description |
| :--- | :--- |
| **Tokens/sec** | The speed of text generation. This is the most critical metric for "reading" feel. |
| **TTFT (s)** | **Time to First Token**. How long the model takes to process your prompt before it starts typing. High TTFT usually indicates high prompt-processing load. |
| **Load Time (s)** | Time taken to move the model from your disk (SSD) into your RAM/VRAM. |
| **Total Time (s)** | The total duration from hitting "Enter" to receiving the full response. |

---

## 🖥️ Example Output

```text
+--------------+--------------+------------+---------------+----------------+-----------------+
| Model        | Tokens/sec   | TTFT (s)   | Load Time (s) | Total Time (s) | Output Tokens   |
+==============+==============+============+===============+================+=================+
| llama3:8b    | 45.20        | 0.15       | 0.00          | 2.98           | 128             |
+--------------+--------------+------------+---------------+----------------+-----------------+
| phi3:mini    | 72.10        | 0.08       | 0.00          | 1.85           | 128             |
+--------------+--------------+------------+---------------+----------------+-----------------+
```

---
To implement hardware tracking, we need to add the `psutil` library (for CPU/RAM) and `pynvml` (for NVIDIA GPU). If you are on a Mac (Apple Silicon), GPU tracking is more complex, so this script focuses on CPU, RAM, and NVIDIA GPU utility.

### Updated `requirements.txt`
```text
requests>=2.31.0
tabulate>=0.9.0
psutil>=5.9.0
pynvml>=11.5.0
```

### The Enhanced Benchmark Script

```python
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
```

### New README Section for these features

Add this to your `README.md`:

---

## 📈 Hardware & Exporting

### Hardware Tracking
The script uses a background thread to sample hardware utilization every 0.5 seconds during the model's generation phase.
- **CPU %**: Total system CPU utilization.
- **RAM %**: System memory usage.
- **GPU %**: Specifically tracks **NVIDIA GPUs** via NVML. 
    *   *Note: On Apple Silicon, GPU usage is integrated into CPU/System metrics and may require specialized tools like `asitop` for detailed breakdown.*

### Exporting Results
At the end of every run, the script automatically generates two files:
1.  `benchmark_YYYYMMDD-HHMMSS.json`: Full detailed data for programmatic use.
2.  `benchmark_YYYYMMDD-HHMMSS.csv`: Spreadsheet-ready format for Excel or Google Sheets.

---

## ⚙️ Configuration
You can modify the following variables inside `benchmark.py` to suit your needs:
- `num_predict`: Change this (default 128) to test longer or shorter generation lengths.
- `temperature`: Set to `0` for deterministic results during benchmarking.

---

## 🤝 Contributing
Feel free to fork this project, open issues, or submit PRs. Possible improvements:
- [ ] Exporting results to CSV/JSON.
- [ ] Hardware usage tracking (CPU/GPU utility) during the run.
- [ ] Support for concurrent request testing.

## 📄 License
MIT License. See `LICENSE` for details.
