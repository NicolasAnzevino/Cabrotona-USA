"""Cabrotona USA multiplayer relay: same-origin HTTP + WebSocket rooms.

Run locally: pip install -r requirements.txt && python server.py
No accounts, database, or external realtime provider required.
Rooms and positions only exist while the server is running.
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

# Each room contains {peer_id: {"ws": WebSocketResponse, "presence": dict}}.
rooms = {}


def peer_view(peer_id, state):
    return {"id": peer_id, "slot": state["slot"], "presence": state["presence"]}


async def relay(room_name, packet, exclude=None):
    """Send a room event to the other peers, tolerating disconnects."""
    data = json.dumps(packet, separators=(",", ":"), ensure_ascii=False)
    peers = list(rooms.get(room_name, {}).items())
    if not peers:
        return
    await asyncio.gather(
        *(state["ws"].send_str(data) for pid, state in peers if pid != exclude and not state["ws"].closed),
        return_exceptions=True,
    )


def clean_presence(data, peer_ids):
    """Whitelist the small set of values used by the original game."""
    if not isinstance(data, dict):
        return {}
    out = {}
    if "n" in data and isinstance(data["n"], str):
        out["n"] = data["n"].strip()[:12]
    if "t" in data and data["t"] in ("auto", "manual"):
        out["t"] = data["t"]
    if "h" in data:
        out["h"] = 1 if data["h"] else 0
    if "j" in data and isinstance(data["j"], (int, float)) and math.isfinite(data["j"]):
        out["j"] = int(data["j"])
    if "st" in data and data["st"] in ("lobby", "race"):
        out["st"] = data["st"]
    if "c" in data and type(data["c"]) is int and 0 <= data["c"] <= 2:
        out["c"] = data["c"]
    if "rid" in data and type(data["rid"]) is int and 0 <= data["rid"] <= 1_000_000:
        out["rid"] = data["rid"]
    if "ord" in data and isinstance(data["ord"], list) and len(data["ord"]) <= MAX_PLAYERS:
        if all(isinstance(x, str) and x in peer_ids for x in data["ord"]):
            out["ord"] = list(dict.fromkeys(data["ord"]))
    if "p" in data:
        p = data["p"]
        if p is None:
            out["p"] = None
        elif (isinstance(p, list) and len(p) == 8 and
              all(type(v) in (int, float) and math.isfinite(v) and abs(v) < 10_000_000 for v in p)):
            out["p"] = p
    if "fin" in data and data["fin"] is None:
        out["fin"] = None
    return out


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
                await ws.send_json({"type": "error", "message": "Mensaje inválido."})
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
                room = rooms.setdefault(name, {})
                if len(room) >= MAX_PLAYERS:
                    await ws.send_json({"type": "error", "message": "La sala está llena."})
                    break
                peer_id = secrets.token_hex(10)
                room_name = name
                previous = [peer_view(pid, state) for pid, state in room.items()]
                used_slots = {state["slot"] for state in room.values()}
                slot = next(n for n in range(1, MAX_PLAYERS + 1) if n not in used_slots)
                room[peer_id] = {"ws": ws, "slot": slot, "presence": {}}
                await ws.send_json({"type": "joined", "id": peer_id,
                                    "peers": previous + [peer_view(peer_id, room[peer_id])]})
                await relay(room_name, {"type": "peer_joined", "peer": peer_view(peer_id, room[peer_id])}, exclude=peer_id)
            elif typ == "presence" and room_name and peer_id in rooms.get(room_name, {}):
                now = time.monotonic()
                last_msg_times = [t for t in last_msg_times if now - t < 1.0]
                if len(last_msg_times) >= 40:
                    continue  # 22 updates/second in game; ignore excessive traffic.
                last_msg_times.append(now)
                update = clean_presence(data.get("patch"), rooms[room_name].keys())
                if not update:
                    continue
                state = rooms[room_name][peer_id]
                state["presence"].update(update)
                await relay(room_name, {"type": "peer_presence", "id": peer_id, "patch": update}, exclude=peer_id)
            elif typ == "ping" and room_name:
                await ws.send_json({"type": "pong"})
    finally:
        if room_name and peer_id:
            room = rooms.get(room_name)
            if room:
                room.pop(peer_id, None)
                if room:
                    # Aiohttp puede cancelar la tarea HTTP al desconectar un
                    # WebSocket; enviamos el aviso desde una tarea independiente.
                    asyncio.create_task(relay(room_name, {"type": "peer_left", "id": peer_id}))
                else:
                    rooms.pop(room_name, None)
        if not ws.closed:
            await ws.close()
    return ws


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
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_get("/multiplayer.js", multiplayer_js)
app.router.add_get("/health", health)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    print(f"Cabrotona USA listo en http://localhost:{PORT}", flush=True)
    web.run_app(app, host="0.0.0.0", port=PORT)
