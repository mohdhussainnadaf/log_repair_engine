import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from pydantic import BaseModel, Field
from app.agent import run_repair_agent

logger = logging.getLogger("observability_server")

app = FastAPI(
    title="AI Agentic Log Repair & Observability Engine",
    version="2.0.0",
    description="High-throughput WebSocket observability engine driving autonomous Claude FastMCP code repairs."
)

class LogIngestPayload(BaseModel):
    level: str = Field(..., example="ERROR")
    message: str = Field(..., example="ZeroDivisionError detected in calculation pipeline")
    stack_trace: str = Field(..., example="ZeroDivisionError: division by zero in app/test_target.py line 7")
    source_file: str = Field(default="app/test_target.py")

@app.websocket("/ws/logs")
async def websocket_log_ingest(websocket: WebSocket):
    """Real-time log stream processing with background repair dispatch."""
    await websocket.accept()
    logger.info("Observability socket connection opened.")
    
    try:
        while True:
            data = await websocket.receive_json()
            level = str(data.get("level", "INFO")).upper()
            stack_trace = data.get("stack_trace", "")
            source_file = data.get("source_file", "app/test_target.py")

            if level in ["ERROR", "CRITICAL"] and stack_trace:
                await websocket.send_json({
                    "event": "REPAIR_DISPATCHED",
                    "status": "Targeting error with Autonomous Claude Agent...",
                    "file": source_file
                })

                # Offload heavy multi-turn agent execution to threadpool
                result = await asyncio.to_thread(run_repair_agent, stack_trace, source_file)

                await websocket.send_json({
                    "event": "REPAIR_FINISHED",
                    "payload": result
                })
            else:
                await websocket.send_json({"event": "LOG_PROCESSED", "status": "ACK"})

    except WebSocketDisconnect:
        logger.info("Observability socket connection closed.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

@app.post("/v1/trigger_repair", status_code=status.HTTP_202_ACCEPTED)
async def trigger_repair_http(payload: LogIngestPayload, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Asynchronous HTTP fallback trigger for CI/CD pipelines and alerting webhooks."""
    background_tasks.add_task(run_repair_agent, payload.stack_trace, payload.source_file)
    return {
        "status": "QUEUED",
        "message": "Autonomous repair agent dispatched in background task.",
        "target_file": payload.source_file
    }
