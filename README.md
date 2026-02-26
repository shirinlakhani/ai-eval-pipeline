# AI Evaluation Pipeline (`ai-eval-pipeline`)

**Agentic AI code evaluation system using LLM judges, tool-based code ingestion, and deterministic JSON scoring.**

---

## Overview

`ai-eval-pipeline` is a **production-ready framework** to evaluate Python code (or any textual code files) using a **strict 100-point rubric** via a **LangChain LLM agent**. It supports:

* **GitHub Code Audits**: Fetch and evaluate code directly from public or private GitHub repositories.
* **Local Test Cases**: Run deterministic evaluations on JSON-defined samples.
* **Structured JSON Scoring**: Enforces a strict schema with category-wise scoring and detailed justifications.
* **Debug Logging**: Malformed LLM outputs are saved for inspection.
* **Agentic & Deterministic**: Uses a judge agent file (`judge.agent.md`) to enforce consistent evaluation.

This project demonstrates **LangChain LLM integration**, **tool-based ingestion**, and **deterministic scoring**, making it suitable for **technical hiring, automated code review, and AI-assisted quality checks**.

---

## Features

* **Strict 100-point rubric** with categories: correctness, safety, readability, maintainability, performance, documentation.
* **GitHub Integration**: Evaluate code from a GitHub blob URL.
* **Local Evaluation**: Evaluate sample test cases from `data/test_cases/sample.json`.
* **Debug Handling**: Stores invalid JSON outputs in `data/debug/`.
* **Deterministic LLM Evaluation**: Uses `gpt-4o-mini` with zero temperature for reproducible results.
* **Environment Safe**: Reads API keys from `.env`.

---

## Getting Started

### Requirements

* Python 3.11+
* `pip install -r requirements.txt`
* `OPENAI_API_KEY` set in `.env`
* Optional: `GITHUB_TOKEN` for private repo access

### Directory Structure

```
ai-eval-pipeline/
├─ .specify/agents/judge.agent.md  # LLM judge rules and rubric
├─ data/
│  ├─ test_cases/sample.json       # Sample code evaluation test cases
│  └─ debug/                       # Malformed LLM JSON outputs
├─ main.py                         # Entry point to run evaluation
├─ pyproject.toml
└─ README.md
```

---

## Usage

### Evaluate a GitHub File

```bash
python main.py "https://github.com/<user>/<repo>/blob/main/<file>.py"
```

### Evaluate Local Test Cases

```bash
python main.py
```

* Generates `data/evaluation_report.json` with structured results.
* Saves any malformed LLM responses to `data/debug/`.

---

## JSON Output Format

```json
{
  "input_id": "github_audit",
  "total_score": 75,
  "verdict": "fail",
  "category_scores": {
    "correctness": 25,
    "safety": 10,
    "readability": 10,
    "maintainability": 10,
    "performance": 8,
    "documentation": 12
  },
  "justification": "Detailed reasoning for score deductions",
  "critical_issues": ["List of critical problems"],
  "suggested_improvements": ["Actionable improvement steps"]
}
```

---

## Recommended Git Ignore

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
build/
dist/
*.egg-info/
.env
.DS_Store
data/evaluation_report.json
data/debug/
```

---

## Contributions

* Ensure all code changes maintain **deterministic evaluation behavior**.
* Update `judge.agent.md` to refine scoring rubric or evaluation rules.
* Avoid committing generated debug files or evaluation reports.

---

## License

MIT License — free to use for personal, academic, or commercial projects.
