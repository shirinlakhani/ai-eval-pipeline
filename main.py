import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# =========================
# Environment Setup
# =========================

# Load environment variables from .env file (if present)
load_dotenv()

# Required API key for LLM access
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional project name for LangChain tracing / grouping
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-eval-pipeline")

# Fail fast if API key is missing (do not allow silent failure)
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

# Resolve project root directory based on this file's location (not cwd)
BASE_DIR = Path(__file__).resolve().parent

# Standard data directory for all runtime artifacts
DATA_DIR = BASE_DIR / "data"

# Directory for saving invalid JSON responses for debugging
DEBUG_DIR = DATA_DIR / "debug"

# =========================
# GitHub Fetch
# =========================

def fetch_github_code(url: str) -> str | None:
    """
    Fetch raw source code from a GitHub blob URL.

    Example supported URL:
    https://github.com/user/repo/blob/main/file.py

    Returns:
        - Raw file contents as string if successful
        - None if URL is invalid or fetch fails
    """

    # Validate GitHub blob URL format
    if "github.com" not in url or "/blob/" not in url:
        print("❌ Invalid GitHub URL. Must be a blob URL.")
        return None

    try:
        # Split URL into repo and file path parts
        base, path_part = url.split("/blob/")
        owner, repo = base.replace("https://github.com/", "").split("/")[:2]

        # Extract branch and file path
        branch, *file_parts = path_part.split("/")
        file_path = "/".join(file_parts)

        # GitHub API endpoint for raw content
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"

        # Default headers for raw content
        headers = {"Accept": "application/vnd.github.v3.raw"}

        # Optional GitHub token for private repos or rate limits
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Perform HTTP request with timeout protection
        with httpx.Client(timeout=15) as client:
            resp = client.get(api_url, headers=headers)
            resp.raise_for_status()
            return resp.text

    except Exception as e:
        # Catch and log all failures deterministically
        print(f"❌ GitHub Fetch Error: {e}")
        return None

# =========================
# LLM Output Cleaning
# =========================

def clean_llm_response(raw: str) -> str:
    """
    Normalize LLM output into parseable JSON text.

    Operations:
    - Remove Markdown code fences (```json ... ```)
    - Strip leading 'json' token if model prepends it

    This ensures deterministic JSON parsing.
    """

    cleaned = raw.strip()

    # Remove fenced Markdown blocks
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1]).strip()

    # Remove accidental leading 'json'
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    return cleaned

# =========================
# Evaluation Logic
# =========================

def run_evaluation(input_source: str | None = None):
    """
    Executes code evaluation using judge.agent.md rubric.

    Input modes:
    - GitHub blob URL → fetch and evaluate file
    - No argument → load local samples.json

    Output:
    - evaluation_report.json
    - debug files for malformed JSON
    """

    # Locate judge specification file
    judge_path = BASE_DIR / ".specify" / "agents" / "judge.agent.md"
    if not judge_path.exists():
        raise FileNotFoundError(f"Missing judge file: {judge_path}")

    # Load rubric and instructions for LLM
    judge_prompt = judge_path.read_text()

    test_cases = []

    # -------------------------
    # Input Selection
    # -------------------------

    if input_source and input_source.startswith("http"):
        # GitHub evaluation mode
        print(f"🌐 Mode: GitHub Audit -> {input_source}")
        code = fetch_github_code(input_source)

        if not code:
            print("❌ Failed to fetch code from GitHub.")
            return

        test_cases = [{"id": "github_audit", "code": code}]

    else:
        # Local samples evaluation mode
        samples_path = DATA_DIR / "test_cases" / "sample.json"
        print(f"📂 Looking for samples at: {samples_path}")

        if not samples_path.exists():
            raise FileNotFoundError(f"sample.json not found at {samples_path}")

        # Load sample test cases
        test_cases = json.loads(samples_path.read_text())

    # -------------------------
    # LLM Setup
    # -------------------------

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # Deterministic scoring behavior
        openai_api_key=OPENAI_API_KEY,
    )

    results = []

    # -------------------------
    # Run Evaluations
    # -------------------------

    for case in test_cases:
        input_id = case.get("id", "unknown")
        print(f"⚖️  Judging: {input_id}")

        # Invoke judge agent with rubric + code
        response = llm.invoke([
            SystemMessage(content=judge_prompt),
            HumanMessage(content=case["code"])
        ])

        # Normalize output for JSON parsing
        cleaned = clean_llm_response(response.content)

        try:
            # Enforce strict JSON schema compliance
            evaluation = json.loads(cleaned)
            evaluation["input_id"] = input_id
            results.append(evaluation)

        except json.JSONDecodeError:
            # Save malformed output for inspection
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            debug_file = DEBUG_DIR / f"debug_{input_id}.txt"
            debug_file.write_text(cleaned)
            print(f"❌ JSON parse failed for {input_id}. Saved to {debug_file}")

    # -------------------------
    # Save Report
    # -------------------------

    DATA_DIR.mkdir(exist_ok=True)
    report_path = DATA_DIR / "evaluation_report.json"

    report_path.write_text(json.dumps(results, indent=2))
    print(f"\n✅ Evaluation complete. Report saved to {report_path}")

# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    # Accept optional GitHub URL argument
    user_input = sys.argv[1] if len(sys.argv) > 1 else None
    run_evaluation(user_input)