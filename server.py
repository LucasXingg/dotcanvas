from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
import asyncio

app = FastAPI()
app.mount("/ui", StaticFiles(directory="pages", html=True), name="pages")

running = False

async def daemon_task():
    global running
    while running:
        # Your daemon logic goes here
        print("Daemon working...")
        await asyncio.sleep(5)

@app.post("/start")
async def start_daemon(background_tasks: BackgroundTasks):
    global running
    if not running:
        running = True
        background_tasks.add_task(daemon_task)
    return {"status": "started"}

@app.post("/stop")
async def stop_daemon():
    global running
    running = False
    return {"status": "stopped"}

@app.get("/status")
def get_status():
    return {"running": running}

