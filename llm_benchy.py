import requests
import time
import json
import sys
from tabulate import tabulate  # pip install tabulate

OLLAMA_BASE_URL = "http://localhost:11434"

def get_local_models():
    """Fetch the list of models currently installed in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        return [m["name"] for m in models]
    except Exception as e:
        print(f"Error: Could not connect to Ollama. Is it running? ({e})")
        sys.exit(1)

def benchmark_model(model_name, prompt):
    print(f"\n[+] Testing: {model_name}")
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 128,  # Fixed output length for fair comparison
            "temperature": 0
        }
    }

    try:
        # 1. Warm-up (Ensures model is in VRAM/RAM)
        print(f"    - Warming up model...")
        requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": model_name, "prompt": "hi", "stream": False})

        # 2. Performance Run
        print(f"    - Running performance test...")
        start_time = time.time()
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()

        # Metrics conversion (Nanoseconds to Seconds)
        total_duration = data.get("total_duration", 0) / 1e9
        load_duration = data.get("load_duration", 0) / 1e9
        prompt_eval_duration = data.get("prompt_eval_duration", 0) / 1e9
        eval_duration = data.get("eval_duration", 0) / 1e9
        eval_count = data.get("eval_count", 0)

        # Performance Calculations
        tps = eval_count / eval_duration if eval_duration > 0 else 0
        ttft = prompt_eval_duration # Time to first token proxy

        return {
            "Model": model_name,
            "Tokens/sec": f"{tps:.2f}",
            "TTFT (s)": f"{ttft:.2f}",
            "Load Time (s)": f"{load_duration:.2f}",
            "Total Time (s)": f"{total_duration:.2f}",
            "Output Tokens": eval_count
        }

    except Exception as e:
        return {"Model": model_name, "Error": str(e)}

def main():
    # 1. Get dynamic list of models
    available_models = get_local_models()
    
    if not available_models:
        print("No models found. Use 'ollama pull <model>' to download one.")
        return

    print("\n--- Available Ollama Models ---")
    for i, name in enumerate(available_models, 1):
        print(f"{i}. {name}")
    
    # 2. User Input
    choice = input("\nEnter the number(s) to test (e.g., 1,3) or 'all': ").strip().lower()
    
    selected_models = []
    if choice == 'all':
        selected_models = available_models
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_models = [available_models[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid selection. Exiting.")
            return

    # 3. Prompt Configuration
    prompt = input("\nEnter test prompt (Press Enter for default: 'Write a short story about a robot'): ")
    if not prompt:
        prompt = "Write a short story about a robot."

    # 4. Run Benchmarks
    results = []
    for model in selected_models:
        res = benchmark_model(model, prompt)
        results.append(res)
    
    # 5. Show Results
    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    print(tabulate(results, headers="keys", tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
