"""Cabrotona USA: shared multiplayer lobby and race clock, aiohttp WebSockets.

The server owns readiness, the optional CPU switch, the start instant and the
single race deadline. Positions remain client-simulated and relayed in real time.
"""
import asyncio
import json
import math
import os
import re
import secrets
import time
from pathlib import Path

from aiohttp import WSMsgType, web

ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "10000"))
ROOM_RE = re.compile(r"^cab-[a-z0-9]{3,8}$")
MAX_PLAYERS = 8
MAX_ROOMS = 200
MAX_JSON_BYTES = 4096
START_TIME = 64.0
LAP_BONUS = 48.0
INTRO_SECONDS = 4.2
COUNTDOWN_SECONDS = 3.12
MAX_LAPS = 6

rooms = {}
sessions = {}


def peer_view(peer_id, state):
    return {"id": peer_id, "slot": state["slot"], "presence": state["presence"]}


def new_session(host):
    return {"host": host, "ready": {}, "cpu": False, "phase": "lobby",
            "rid": 0, "ord": [], "introAt": 0, "countdownAt": 0,
            "raceAt": 0, "deadline": 0, "lap": {}, "bonus": 0}


def room_state(room_name):
    s = sessions[room_name]
    return {"type": "room_state", "host": s["host"], "ready": s["ready"],
            "cpu": s["cpu"], "phase": s["phase"], "rid": s["rid"],
            "ord": s["ord"], "introAt": s["introAt"],
            "countdownAt": s["countdownAt"], "raceAt": s["raceAt"],
            "deadline": s["deadline"], "bonus": s["bonus"],
            "serverNow": time.time()}


async def relay(room_name, packet, exclude=None):
    data = json.dumps(packet, separators=(",", ":"), ensure_ascii=False)
    peers = list(rooms.get(room_name, {}).items())
    if peers:
        await asyncio.gather(*(state["ws"].send_str(data) for pid, state in peers
                               if pid != exclude and not state["ws"].closed),
                             return_exceptions=True)


async def publish_state(room_name):
    if room_name in sessions:
        await relay(room_name, room_state(room_name))


def clean_presence(data):
    if not isinstance(data, dict):
        return {}
    out = {}
    if isinstance(data.get("n"), str):
        out["n"] = data["n"].strip()[:12]
    if data.get("t") in ("auto", "manual"):
        out["t"] = data["t"]
    if type(data.get("c")) is int and 0 <= data["c"] <= 2:
        out["c"] = data["c"]
    p = data.get("p", "missing")
    if p is None:
        out["p"] = None
    elif (isinstance(p, list) and len(p) == 8 and all(type(v) in (int, float)
          and math.isfinite(v) and abs(v) < 10_000_000 for v in p)):
        out["p"] = p
    return out


async def handle_command(room_name, peer_id, data):
    room = rooms[room_name]
    s = sessions[room_name]
    cmd = data.get("cmd")
    if cmd == "ready":
        if s["phase"] != "lobby" or peer_id == s["host"]:
            return
        s["ready"][peer_id] = data.get("value") is True
        await publish_state(room_name)
    elif cmd == "cpu":
        if s["phase"] != "lobby" or peer_id != s["host"]:
            return
        s["cpu"] = data.get("value") is True
        await publish_state(room_name)
    elif cmd == "start":
        if s["phase"] != "lobby" or peer_id != s["host"]:
            return
        players = [pid for pid, state in sorted(room.items(), key=lambda it: it[1]["slot"])
                   if state["presence"].get("n")]
        if len(players) < 2 or any(not s["ready"].get(pid, False)
                                   for pid in players if pid != s["host"]):
            await room[peer_id]["ws"].send_json({"type": "error_notice", "message": "Esperá a que todos estén LISTOS (mínimo 2 jugadores)."})
            return
        now = time.time()
        s.update(phase="intro", rid=s["rid"] + 1, ord=players,
                 introAt=now, countdownAt=now + INTRO_SECONDS,
                 raceAt=now + INTRO_SECONDS + COUNTDOWN_SECONDS,
                 deadline=now + INTRO_SECONDS + COUNTDOWN_SECONDS + START_TIME,
                 lap={pid: 0 for pid in players}, bonus=0)
        for pid in players:
            room[pid]["presence"]["p"] = None
        await publish_state(room_name)
    elif cmd == "lobby":
        if peer_id != s["host"] or s["phase"] == "lobby":
            return
        s.update(phase="lobby", ord=[], introAt=0, countdownAt=0,
                 raceAt=0, deadline=0, lap={}, ready={}, bonus=0)
        await publish_state(room_name)


async def websocket_handler(request):
    ws = web.WebSocketResponse(heartbeat=30, max_msg_size=MAX_JSON_BYTES, compress=False)
    await ws.prepare(request)
    room_name = None
    peer_id = None
    last_msg_times = []
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                if msg.type == WSMsgType.ERROR:
                    break
                continue
            try:
                data = json.loads(msg.data)
            except (ValueError, TypeError):
                await ws.send_json({"type": "error_notice", "message": "Mensaje inválido."})
                continue
            if not isinstance(data, dict):
                continue
            typ = data.get("type")
            if typ == "join" and room_name is None:
                name = data.get("room", "")
                if not isinstance(name, str) or not ROOM_RE.fullmatch(name):
                    await ws.send_json({"type": "error", "message": "Código de sala inválido."})
                    break
                if name not in rooms and len(rooms) >= MAX_ROOMS:
                    await ws.send_json({"type": "error", "message": "No hay salas libres."})
                    break
                if name in sessions and sessions[name]["phase"] != "lobby":
                    await ws.send_json({"type": "error", "message": "Esta sala está corriendo una carrera."})
                    break
                room = rooms.setdefault(name, {})
                if len(room) >= MAX_PLAYERS:
                    await ws.send_json({"type": "error", "message": "La sala está llena."})
                    break
                peer_id = secrets.token_hex(10)
                room_name = name
                used_slots = {state["slot"] for state in room.values()}
                slot = next(n for n in range(1, MAX_PLAYERS + 1) if n not in used_slots)
                previous = [peer_view(pid, state) for pid, state in room.items()]
                room[peer_id] = {"ws": ws, "slot": slot, "presence": {}}
                if name not in sessions:
                    sessions[name] = new_session(peer_id)
                await ws.send_json({"type": "joined", "id": peer_id,
                                    "peers": previous + [peer_view(peer_id, room[peer_id])],
                                    "state": room_state(name)})
                await relay(name, {"type": "peer_joined", "peer": peer_view(peer_id, room[peer_id])}, exclude=peer_id)
                await publish_state(name)
            elif typ == "presence" and room_name and peer_id in rooms.get(room_name, {}):
                now = time.monotonic()
                last_msg_times = [t for t in last_msg_times if now - t < 1.0]
                if len(last_msg_times) >= 40:
                    continue
                last_msg_times.append(now)
                update = clean_presence(data.get("patch"))
                if not update:
                    continue
                room = rooms[room_name]
                s = sessions[room_name]
                state = room[peer_id]
                if s["phase"] != "lobby":
                    update.pop("n", None)
                    update.pop("t", None)
                    update.pop("c", None)
                state["presence"].update(update)
                # Host flag and racing phase are owned by the server.
                state["presence"]["h"] = int(s["host"] == peer_id)
                state["presence"]["st"] = "lobby" if s["phase"] == "lobby" else "race"
                if (s["phase"] in ("intro", "race") and peer_id in s["lap"] and
                        isinstance(update.get("p"), list) and s["raceAt"] <= time.time() < s["deadline"]):
                    lap = max(0, min(MAX_LAPS, int(update["p"][5])))
                    prev = s["lap"][peer_id]
                    if lap == prev + 1:
                        s["lap"][peer_id] = lap
                        if lap < MAX_LAPS:
                            s["deadline"] += LAP_BONUS
                            s["bonus"] += 1
                            await publish_state(room_name)
                await relay(room_name, {"type": "peer_presence", "id": peer_id, "patch": update}, exclude=peer_id)
            elif typ == "command" and room_name and peer_id in rooms.get(room_name, {}):
                await handle_command(room_name, peer_id, data)
            elif typ == "ping" and room_name:
                await ws.send_json({"type": "pong"})
    finally:
        if room_name and peer_id:
            room = rooms.get(room_name)
            if room:
                room.pop(peer_id, None)
                if room:
                    s = sessions[room_name]
                    s["ready"].pop(peer_id, None)
                    if s["host"] == peer_id:
                        s["host"] = min(room, key=lambda pid: room[pid]["slot"])
                        room[s["host"]]["presence"]["h"] = 1
                    await relay(room_name, {"type": "peer_left", "id": peer_id})
                    await publish_state(room_name)
                else:
                    rooms.pop(room_name, None)
                    sessions.pop(room_name, None)
        if not ws.closed:
            await ws.close()
    return ws


async def ticker(app):
    while True:
        await asyncio.sleep(0.2)
        for name, s in list(sessions.items()):
            if s["phase"] == "intro" and time.time() >= s["raceAt"]:
                s["phase"] = "race"
                await publish_state(name)
            elif s["phase"] == "race" and time.time() >= s["deadline"]:
                s["phase"] = "timeout"
                s["timeoutAt"] = time.time()
                await publish_state(name)
            elif s["phase"] == "timeout" and time.time() >= s.get("timeoutAt", 0) + 17:
                s.update(phase="lobby", ord=[], introAt=0, countdownAt=0,
                         raceAt=0, deadline=0, lap={}, ready={}, bonus=0)
                await publish_state(name)


async def tick_context(app):
    task = asyncio.create_task(ticker(app))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def index(request):
    response = web.FileResponse(ROOT / "index.html")
    response.headers["Cache-Control"] = "no-store"
    return response


async def multiplayer_js(request):
    response = web.FileResponse(ROOT / "multiplayer.js")
    response.headers["Cache-Control"] = "no-store"
    return response


async def health(request):
    return web.json_response({"ok": True, "rooms": len(rooms),
                              "players": sum(len(r) for r in rooms.values())})


app = web.Application(client_max_size=MAX_JSON_BYTES)
app.cleanup_ctx.append(tick_context)
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_get("/multiplayer.js", multiplayer_js)
# Favicon original de Cabrotona USA convertido desde la imagen provista.
# Rutas explícitas: no exponer la carpeta del servidor como sitio estático.
for asset in ("favicon.ico", "favicon-16x16.png", "favicon-32x32.png",
              "favicon-48x48.png", "favicon-192x192.png",
              "favicon-256x256.png", "apple-touch-icon.png"):
    app.router.add_get("/" + asset, lambda request, f=asset: web.FileResponse(ROOT / f))
app.router.add_get("/health", health)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
