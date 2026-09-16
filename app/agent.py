import os
import time
import pathlib
import subprocess
import logging
import json
from typing import Dict, Any
from anthropic import Anthropic
from fastmcp import FastMCP

# Enterprise JSON Logger Setup
logger = logging.getLogger("agentic_repair")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log_event(event_type: str, data: dict):
    payload = {"timestamp": time.time(), "event": event_type, **data}
    logger.info(json.dumps(payload))

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
mcp = FastMCP("LogRepairTools")

# Security Boundary: Restrict agent operations strictly to allowed workspace roots
ALLOWED_ROOT = pathlib.Path(os.getcwd()).resolve()

def _validate_path(file_path: str) -> pathlib.Path:
    """Security sandbox preventing directory traversal outside repository workspace."""
    target_path = (ALLOWED_ROOT / file_path).resolve()
    if not str(target_path).startswith(str(ALLOWED_ROOT)):
        raise PermissionError(f"Access denied: Target path '{file_path}' lies outside workspace root.")
    return target_path

@mcp.tool()
def read_file(file_path: str) -> str:
    """Safely reads content of a repository file."""
    try:
        path = _validate_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"File Read Error: {str(e)}"

@mcp.tool()
def apply_patch(file_path: str, new_content: str) -> str:
    """Safely updates target source code file."""
    try:
        path = _validate_path(file_path)
        path.write_text(new_content, encoding="utf-8")
        log_event("PATCH_APPLIED", {"file": file_path})
        return f"Successfully updated '{file_path}'."
    except Exception as e:
        return f"Patch Application Error: {str(e)}"

@mcp.tool()
def run_unit_tests(test_target: str = "app/test_target.py") -> str:
    """Executes pytest suite and returns stdout/stderr with execution codes."""
    try:
        path = _validate_path(test_target)
        result = subprocess.run(
            ["pytest", str(path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        return json.dumps({
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"exit_code": -1, "stdout": "", "stderr": "Test execution timed out (30s limit).", "passed": False})
    except Exception as e:
        return json.dumps({"exit_code": -1, "stdout": "", "stderr": str(e), "passed": False})

# Anthropic Function Tool Schemas
TOOLS_SCHEMA = [
    {
        "name": "read_file",
        "description": "Reads source code from workspace file.",
        "input_schema": {
            "type": "object",
            "properties": {"file_path": {"type": "string"}},
            "required": ["file_path"],
        },
    },
    {
        "name": "apply_patch",
        "description": "Applies corrected source code implementation to workspace file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "new_content": {"type": "string"},
            },
            "required": ["file_path", "new_content"],
        },
    },
    {
        "name": "run_unit_tests",
        "description": "Runs pytest verification suite against target test file.",
        "input_schema": {
            "type": "object",
            "properties": {"test_target": {"type": "string"}},
            "required": [],
        },
    },
]

def run_repair_agent(error_traceback: str, file_path: str = "app/test_target.py") -> Dict[str, Any]:
    """Autonomous ReAct loop with timing, logging, and multi-step verification."""
    start_time = time.time()
    log_event("REPAIR_STARTED", {"target_file": file_path})

    system_prompt = (
        "You are an Autonomous Site Reliability Engineer (SRE). "
        "Your objective: Analyze runtime stack traces, inspect relevant code files via read_file, "
        "apply targeted patches using apply_patch, and run unit tests via run_unit_tests. "
        "Do NOT report complete until run_unit_tests returns passed: true."
    )
    
    messages = [{
        "role": "user",
        "content": f"Production Alert! Exception caught:\n\n```\n{error_traceback}\n```\nTarget File: {file_path}"
    }]

    for step in range(1, 6):
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=TOOLS_SCHEMA,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                elapsed = time.time() - start_time
                text_content = "\n".join([b.text for b in response.content if hasattr(b, "text")])
                log_event("REPAIR_SUCCESS", {"duration_sec": round(elapsed, 2), "steps": step})
                return {
                    "status": "SUCCESS",
                    "duration_seconds": round(elapsed, 2),
                    "steps_taken": step,
                    "resolution": text_content
                }

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        t_name = block.name
                        t_input = block.input
                        t_id = block.id

                        log_event("TOOL_EXECUTION", {"step": step, "tool": t_name, "args": t_input})

                        if t_name == "read_file":
                            output = read_file(t_input["file_path"])
                        elif t_name == "apply_patch":
                            output = apply_patch(t_input["file_path"], t_input["new_content"])
                        elif t_name == "run_unit_tests":
                            output = run_unit_tests(t_input.get("test_target", file_path))
                        else:
                            output = f"Unknown tool: {t_name}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": t_id,
                            "content": output,
                        })

                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            log_event("REPAIR_ERROR", {"step": step, "error": str(e)})
            return {"status": "ERROR", "error": str(e)}

    log_event("REPAIR_FAILED", {"reason": "Max iterations reached"})
    return {"status": "FAILED", "reason": "Exceeded maximum autonomous repair attempts."}
