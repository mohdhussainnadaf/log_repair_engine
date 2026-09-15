from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from typing import List
from app.agent import run_agent_repair_loop

app = FastAPI(title="AI Agentic Log Observability Engine")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("app/index.html", "r") as f:
        return f.read()

@app.websocket("/ws/logs")
async def log_stream_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"type": "log", "content": data})
            if "Traceback" in data or "ERROR" in data:
                await manager.broadcast({"type": "agent_status", "status": "Repairing"})
                asyncio.create_task(trigger_repair_process(data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def trigger_repair_process(stacktrace: str):
    await manager.broadcast({"type": "agent_output", "content": "=== AI Repair Agent Triggered ==="})
    result = await asyncio.to_thread(run_agent_repair_loop, stacktrace)
    await manager.broadcast({"type": "agent_output", "content": result})
    await manager.broadcast({"type": "agent_status", "status": "Idle"})
