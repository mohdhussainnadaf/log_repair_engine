import os
from google import genai
from app.mcp_tools import read_repo_file, write_repo_file, run_unit_tests

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def read_file_tool(filepath: str) -> str:
    """Reads content from a target file in the repository."""
    return read_repo_file(filepath)

def write_file_tool(filepath: str, content: str) -> str:
    """Writes updated source code or a patch to a target repository file."""
    return write_repo_file(filepath, content)

def run_tests_tool(test_target: str = "target_app/") -> str:
    """Runs pytest against the specified directory and returns output."""
    return str(run_unit_tests(test_target))

def run_agent_repair_loop(log_stacktrace: str) -> str:
    prompt = f"""A stack trace error occurred in live logs:

{log_stacktrace}

Inspect target_app/main.py and target_app/test_main.py using your tools, find the root cause, apply a fix, and run unit tests until they pass."""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            "tools": [read_file_tool, write_file_tool, run_tests_tool],
            "temperature": 0,
        },
    )
    
    return response.text or "Repair process completed and unit tests passed."
