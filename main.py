import asyncio
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from checkin import do_checkin
from config import get_config, init_db, save_config
from database import get_logs
from monitor import capture_screen, detect_qr

# ── shared state ──────────────────────────────────────────────────────────────
state: dict = {
    "running":        False,
    "paused":         False,
    "last_check":     None,
    "last_qr":        None,
    "last_qr_time":   None,
    "session_count":  0,   # 本次监控成功次数
}

ws_clients: list[WebSocket] = []
app_loop: asyncio.AbstractEventLoop | None = None


# ── WebSocket broadcast ───────────────────────────────────────────────────────
async def broadcast(data: dict):
    for ws in ws_clients[:]:
        try:
            await ws.send_json(data)
        except Exception:
            ws_clients.remove(ws)


# ── monitor thread ────────────────────────────────────────────────────────────
def monitor_loop():
    recent: dict[str, datetime] = {}
    cooldown = timedelta(minutes=5)

    while True:
        if not state["running"] or state["paused"]:
            time.sleep(0.5)
            continue

        config   = get_config()
        interval = max(1, int(config.get("scan_interval", 1)))
        keyword  = config.get("url_keyword", "")

        try:
            img      = capture_screen()
            contents = detect_qr(img)
            state["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            now = datetime.now()
            for content in contents:
                if keyword and keyword not in content:
                    continue
                if content in recent and now - recent[content] < cooldown:
                    continue

                recent[content]      = now
                state["last_qr"]     = content
                state["last_qr_time"] = now.strftime("%Y-%m-%d %H:%M:%S")

                if app_loop:
                    try:
                        future        = asyncio.run_coroutine_threadsafe(
                            do_checkin(content), app_loop
                        )
                        success, msg  = future.result(timeout=20)
                    except Exception as e:
                        success, msg  = False, str(e)

                    if success:
                        state["session_count"] += 1

                    asyncio.run_coroutine_threadsafe(
                        broadcast({"type": "checkin", "success": success,
                                   "msg": msg, "qr": content,
                                   "session_count": state["session_count"]}),
                        app_loop,
                    )

                    # 达到上限，自动停止监控
                    config       = get_config()
                    max_checkins = int(config.get("max_checkins", 2))
                    if success and state["session_count"] >= max_checkins:
                        state["running"] = False
                        asyncio.run_coroutine_threadsafe(
                            broadcast({"type": "status", **state}),
                            app_loop,
                        )
                        break  # 跳出 for 循环，while 循环继续等待下次 start

        except Exception as e:
            print(f"[monitor] {e}")

        time.sleep(interval)


# ── app setup ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_loop
    init_db()
    app_loop = asyncio.get_running_loop()
    threading.Thread(target=monitor_loop, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/status")
async def api_status():
    return state


@app.get("/api/debug-screenshot")
async def api_debug_screenshot():
    """截图保存到 debug.png，同时返回识别结果，方便排查问题"""
    import asyncio, cv2
    loop = asyncio.get_running_loop()
    img      = await loop.run_in_executor(None, capture_screen)
    contents = await loop.run_in_executor(None, detect_qr, img)
    path = "debug.png"
    cv2.imwrite(path, img)
    return {"found": contents, "screenshot_saved": path, "resolution": f"{img.shape[1]}x{img.shape[0]}"}


@app.get("/api/logs")
async def api_logs():
    return get_logs()


@app.get("/api/config")
async def api_config_get():
    return get_config()


@app.post("/api/config")
async def api_config_post(data: dict):
    save_config(data)
    return {"ok": True}


@app.get("/api/scan-now")
async def api_scan_now():
    import asyncio
    loop = asyncio.get_running_loop()
    img      = await loop.run_in_executor(None, capture_screen)
    contents = await loop.run_in_executor(None, detect_qr, img)
    return {"found": contents}


@app.post("/api/control")
async def api_control(data: dict):
    action = data.get("action")
    if action == "start":
        state["running"]       = True
        state["paused"]        = False
        state["session_count"] = 0   # 重置本次计数
    elif action == "pause":
        state["paused"]  = not state["paused"]
    elif action == "stop":
        state["running"] = False
        state["paused"]  = False
    await broadcast({"type": "status", **state})
    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        await ws.send_json({"type": "status", **state})
        while True:
            await asyncio.sleep(2)
            await ws.send_json({"type": "heartbeat",
                                "last_check": state["last_check"]})
    except (WebSocketDisconnect, Exception):
        if ws in ws_clients:
            ws_clients.remove(ws)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser, threading
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8080")).start()
    uvicorn.run(app, host="0.0.0.0", port=8080)
