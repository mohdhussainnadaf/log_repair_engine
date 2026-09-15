import os
import subprocess
from typing import Dict, Any

def read_repo_file(filepath: str) -> str:
    """Reads content from a target file in the repository."""
    if not os.path.exists(filepath):
        return f"Error: File {filepath} not found."
    with open(filepath, "r") as f:
        return f.read()

def write_repo_file(filepath: str, content: str) -> str:
    """Writes updated source code or a patch to a target repository file."""
    try:
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully updated {filepath}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"

def run_unit_tests(test_target: str = "target_app/") -> Dict[str, Any]:
    """Runs pytest against the specified directory and returns output."""
    result = subprocess.run(
        ["pytest", test_target],
        capture_output=True,
        text=True
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0
    }
