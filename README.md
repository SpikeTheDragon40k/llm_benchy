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
