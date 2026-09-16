import asyncio
import json
import websockets

async def stream_dummy_errors():
    uri = "ws://localhost:8000/ws/logs"
    print(f"Connecting to log stream at {uri}...")
    
    async with websockets.connect(uri) as ws:
        # Simulate normal log
        await ws.send(json.dumps({"level": "INFO", "message": "System running normally."}))
        res = await ws.receive()
        print(f"Received: {res}")

        # Simulate exception trigger
        payload = {
            "level": "ERROR",
            "message": "ZeroDivisionError encountered during execution",
            "stack_trace": "ZeroDivisionError: division by zero in app/test_target.py line 6",
            "source_file": "app/test_target.py"
        }
        print("\n[!] Emitting ERROR stack trace to trigger Claude MCP Agent...")
        await ws.send(json.dumps(payload))
        
        while True:
            response = await ws.receive()
            print(f"[Agent Response]: {response}")
            data = json.loads(response)
            if data.get("event") == "REPAIR_FINISHED":
                print("\n[✔] Repair loop completed!")
                break

if __name__ == "__main__":
    asyncio.run(stream_dummy_errors())
