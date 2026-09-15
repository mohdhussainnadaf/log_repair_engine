# 🛠️ AI Agentic Log Repair & Observability Engine

An autonomous developer utility and Site Reliability Engineering (SRE) tool that monitors live application logs, identifies stack trace errors in real time, and leverages an LLM agent (Claude 3.5 Sonnet) via the Model Context Protocol (MCP) to execute automated code repairs and run unit verification suites.

---

## 🏗️ Architecture & Core Components

* **FastAPI & WebSockets**: Low-latency log ingestion stream that flags ERROR and CRITICAL stack traces.
* **FastMCP Tooling**: Exposes safe, structured system tools to inspect project files, write code fixes, and run test runners.
* **Anthropic Claude 3.5 Sonnet**: Multi-turn ReAct reasoning agent that diagnoses root causes and reduces MTTR (Mean-Time-To-Resolution).
* **Pytest Verification**: Automatically confirms that code patches pass unit tests without introducing regressions.

---

## 🚀 Quickstart

### Prerequisites
* Python 3.11+
* Anthropic API Key (`export ANTHROPIC_API_KEY="your-key"`)

### Installation & Execution

1. **Install Dependencies**:
   pip install -r requirements.txt

2. **Launch Server**:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

3. **Trigger Autonomous Repair Test**:
   curl -X POST "http://localhost:8000/v1/trigger_repair" \
     -H "Content-Type: application/json" \
     -d '{"level": "ERROR", "message": "ZeroDivisionError in metrics calculation", "stack_trace": "ZeroDivisionError: division by zero in app/test_target.py", "source_file": "app/test_target.py"}'
