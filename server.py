"""Cabrotona USA: shared multiplayer lobby and race clock, aiohttp WebSockets.

The server owns readiness, the optional CPU switch, the start instant and the
single race deadline. v32: input-driven authoritative car positions, contacts, and race results.
"""
import asyncio
import base64
import array
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
MAX_LAPS = 4   # BEGINNER multiplayer: cuatro vueltas, igual que Arcade
FINISH_GRACE = 2.0
PROTOCOL = 32
SIM_DT = 1.0 / 60.0
SNAPSHOT_DT = 1.0 / 30.0  # 30 posiciones compartidas por segundo; física a 60 Hz
CAR_L, CAR_W, WALL = 4.9, 2.1, 16.6
MAXV, ACC, BRAKE, PACE = 83.3, 19.0, 36.0, 34.0
GA = (2.2, 1.5, 1.15, 0.95)
GM = (26.0, 47.0, 65.0, 83.3)
TRACK_LENGTH = 3099.201184824959
TRACK_DS = 3.9989692707418825
TRACK_N = 775
CURVE_K = array.array("f")
CURVE_K.frombytes(base64.b64decode(
    "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"))
CURVE_B = array.array("f")
CURVE_B.frombytes(base64.b64decode(
    "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"))

rooms = {}
sessions = {}


def peer_view(peer_id, state):
    return {"id": peer_id, "slot": state["slot"], "presence": state["presence"]}


def new_session(host):
    return {"host": host, "ready": {}, "cpu": False, "phase": "lobby",
            "rid": 0, "ord": [], "introAt": 0, "countdownAt": 0,
            "raceAt": 0, "deadline": 0, "lap": {}, "bonus": 0,
            "winner": None, "finishAt": 0.0, "results": {},
            "finish_order": [], "last_progress": {}, "resultsAt": 0.0,
            "progress_seen": {}, "progress_speed": {},
            "rank_order": [], "rank_seq": 0,
            "sim": {}, "controls": {}, "sim_tick": 0,
            "last_sim": 0.0, "last_snap": 0.0, "transmissions": {}}


def room_state(room_name):
    s = sessions[room_name]
    return {"type": "room_state", "host": s["host"], "ready": s["ready"],
            "cpu": s["cpu"], "phase": s["phase"], "rid": s["rid"],
            "ord": s["ord"], "introAt": s["introAt"],
            "countdownAt": s["countdownAt"], "raceAt": s["raceAt"],
            "deadline": s["deadline"], "bonus": s["bonus"],
            "winner": s["winner"], "finishAt": s["finishAt"],
            "resultsAt": s["resultsAt"], "results": s["results"],
            "rankOrder": s["rank_order"], "rankSeq": s["rank_seq"],
            "serverNow": time.time(), "protocol": PROTOCOL}


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


def live_ranking(room_name, now_mono=None):
    """La carrera usa exclusivamente posiciones calculadas por el servidor."""
    s = sessions[room_name]
    active = rooms.get(room_name, {})
    previous = [pid for pid in s["rank_order"] if pid in active]
    previous += [pid for pid in s["ord"] if pid in active and pid not in previous]
    arrived = [pid for pid in s["finish_order"] if pid in previous]
    pending = [pid for pid in previous if pid not in arrived]
    sim = s["sim"]
    for i in range(1, len(pending)):
        j = i
        while j > 0 and (pending[j] in sim and pending[j - 1] in sim and
                         sim[pending[j]]["dist"] > sim[pending[j - 1]]["dist"] + 0.40):
            pending[j], pending[j - 1] = pending[j - 1], pending[j]
            j -= 1
    return arrived + pending


async def publish_live_ranking(room_name):
    s = sessions.get(room_name)
    if not s or s["phase"] != "race":
        return
    order = live_ranking(room_name)
    if order == s["rank_order"]:
        return
    s["rank_order"] = order
    s["rank_seq"] += 1
    # Todos aplican el MISMO cambio a una hora futura del servidor.
    # 300 ms cubren el tránsito habitual de la conexión; con ping mayor
    # puede existir un retardo residual, pero nunca rankings locales distintos.
    await relay(room_name, {"type": "race_standings", "rid": s["rid"],
                           "seq": s["rank_seq"], "order": order,
                           "applyAt": time.time() + 0.30})



def clamp(v, a, b):
    return max(a, min(b, v))


def curve_at(dist):
    f = (dist % TRACK_LENGTH) / TRACK_DS
    i = int(f) % TRACK_N
    j = (i + 1) % TRACK_N
    t = f - int(f)
    k = CURVE_K[i] * (1 - t) + CURVE_K[j] * t
    b = CURVE_B[i] * (1 - t) + CURVE_B[j] * t
    return k, b


def grid(k):
    right = k % 2
    return {"dist": 24 - (k // 2) * 18 + (6 if right else 0),
            "d": 3.75 if right else -10.9}


def start_sim(s):
    cpu_count = max(0, 20 - len(s["ord"])) if s["cpu"] else 0
    s["sim"] = {}
    s["controls"] = {}
    s["sim_tick"] = 0
    s["last_sim"] = time.monotonic()
    s["last_snap"] = 0.0
    for index, pid in enumerate(s["ord"]):
        g = grid(index + cpu_count)
        s["sim"][pid] = {"dist": float(g["dist"]), "d": float(g["d"]),
                         "v": PACE, "psi": 0.0, "phi": 0.0, "steer": 0.0,
                         "gear": 1, "shift": 0.0, "lap": 0, "finished": False,
                         "hit": 0, "hit_side": 0, "hit_cd": 0.0, "ack": 0,
                         "wall_cd": 0.0, "wall_seq": 0, "wall_mask": 0}
        s["controls"][pid] = {"gas": False, "brake": False, "steer": 0.0,
                              "gear": 1, "seq": 0, "received": 0.0}
        s["last_progress"][pid] = g["dist"]


def cpu_poses(s, elapsed):
    """Misma trayectoria determinista que los CPU violetas del cliente."""
    if not s["cpu"]:
        return []
    result = []
    for i in range(max(0, 20 - len(s["ord"]))):
        g = grid(i)
        speed = 42.0 + (i % 8) * 2.2
        d = clamp(g["d"] + math.sin(elapsed * 0.34 + i * 1.7) * .8, -11.5, 11.5)
        result.append((g["dist"] + speed * elapsed, d, speed))
    return result


def resolve_contact(a, b, dt, b_is_cpu=False):
    """Una sola decisión compartida para cada contacto; sin mover rivales en cada navegador."""
    gap = b["dist"] - a["dist"]
    # Misma posición física de pista, incluso cuando difieren una vuelta.
    gap -= round(gap / TRACK_LENGTH) * TRACK_LENGTH
    dx = abs(gap)
    lat = b["d"] - a["d"]
    dy = abs(lat)
    if dx >= CAR_L or dy >= CAR_W:
        return
    if (CAR_L - dx) / CAR_L <= (CAR_W - dy) / CAR_W:
        penetration = CAR_L + .04 - dx
        if gap >= 0:
            a["dist"] -= penetration if b_is_cpu else penetration * .5
            if not b_is_cpu:
                b["dist"] += penetration * .5
            va, vb = a["v"], b["v"]
            if va > vb:
                a["v"] = max(0.0, va - (va - vb) * .52)
                if not b_is_cpu:
                    b["v"] = min(MAXV * 1.12, vb + (va - vb) * .27)
            a["hit_side"] = 1
            if not b_is_cpu:
                b["hit_side"] = -1
        else:
            if b_is_cpu:
                a["dist"] += penetration
            else:
                b["dist"] -= penetration * .5
                a["dist"] += penetration * .5
            va, vb = a["v"], b["v"]
            if vb > va:
                if not b_is_cpu:
                    b["v"] = max(0.0, vb - (vb - va) * .52)
                a["v"] = min(MAXV * 1.12, va + (vb - va) * .27)
            a["hit_side"] = -1
            if not b_is_cpu:
                b["hit_side"] = 1
    else:
        sign = 1 if lat >= 0 else -1
        displacement = CAR_W + .04 - dy
        if b_is_cpu:
            a["d"] = clamp(a["d"] - sign * displacement, -WALL + CAR_W / 2, WALL - CAR_W / 2)
        else:
            a["d"] -= sign * displacement * .5
            b["d"] += sign * displacement * .5
        a["v"] *= 1 - min(.13, dt * 3)
        if not b_is_cpu:
            b["v"] *= 1 - min(.13, dt * 3)
        a["hit_side"] = 2
        if not b_is_cpu:
            b["hit_side"] = 2
    for st in ([a] if b_is_cpu else [a, b]):
        limit = WALL - CAR_W / 2
        if abs(st["d"]) > limit:
            sign = 1 if st["d"] > 0 else -1
            # Contact with the physical barrier, following the shove from a car.
            penetration_speed = (abs(st["d"]) - limit) / max(dt, .001)
            mark_wall_impact(st, sign, penetration_speed)
        st["d"] = clamp(st["d"], -limit, limit)
        if st["hit_cd"] <= 0:
            st["hit"] += 1
            st["hit_cd"] = 0.32


def wall_front_mask(sign, phi):
    """Same front-corner choice as wallCorner() on the client (bit 1=FL, 2=FR)."""
    si, co = math.sin(phi), math.cos(phi)
    lat = {"fr": .95 * co + 2.45 * si, "fl": -.95 * co + 2.45 * si,
           "rr": .95 * co - 2.45 * si, "rl": -.95 * co - 2.45 * si}
    rank = lambda corner: lat[corner] * sign + (.08 if corner[0] == "f" else 0.)
    best = max(lat, key=rank)
    mask = (1 if best == "fl" else 2 if best == "fr" else 0)
    other = best[0] + ("l" if best[1] == "r" else "r")
    if rank(other) >= rank(best) - .25:
        mask |= (1 if other == "fl" else 2 if other == "fr" else 0)
    return mask


def mark_wall_impact(st, sign, into):
    """Wall-only hood signal; car-contact hit counters never call this."""
    if into <= 3.2 or st["wall_cd"] > 0:
        return
    st["wall_cd"] = .5
    st["wall_mask"] = wall_front_mask(sign, st["phi"])
    st["wall_seq"] += 1


def simulate_car(st, ctrl, trans, dt, now):
    k, b = curve_at(st["dist"])
    st["hit_cd"] = max(0., st["hit_cd"] - dt)
    st["wall_cd"] = max(0., st["wall_cd"] - dt)
    age = now - ctrl["received"]
    gas = ctrl["gas"] if age <= 0.30 else False
    brake = ctrl["brake"] if age <= 0.30 else False
    steer_in = ctrl["steer"] if age <= 0.30 else 0.0
    rate = 3.4 if abs(steer_in) > abs(st["steer"]) and steer_in * st["steer"] >= 0 else 9.0
    st["steer"] += clamp(steer_in - st["steer"], -rate * dt, rate * dt)
    v, gear = st["v"], st["gear"]
    if trans == "auto":
        mx = GM[gear]
        if gear < 3 and v / mx > .93:
            gear += 1
            st["shift"] = .2
        elif gear > 0 and v / GM[gear - 1] < .62:
            gear -= 1
    else:
        gear = int(ctrl["gear"])
        if gear < 3 and v > GM[gear]:
            v = max(GM[gear], v - 34 * dt)
    st["gear"] = gear
    rpm = v / GM[gear]
    if st["shift"] > 0:
        st["shift"] -= dt
    slipping = brake and v > 27 and abs(st["steer"]) > .20
    if gas:
        power = .55 + rpm * 1.5 if rpm < .3 else (1.0 if rpm < .88 else max(0., (1 - rpm) / .12))
        if trans == "manual" and rpm < .5:
            floor = (.55, .3, .12, .05)[gear]
            power = floor + (1 - floor) * (rpm / .5) ** 1.5
        acc = ACC * GA[gear] * power * (.15 if st["shift"] > 0 else 1.)
        if rpm >= 1 and gear < 3:
            acc = 0.
        if gear < 3 and rpm > 1:
            acc -= ACC * .8
    else:
        acc = -ACC * .35
    if brake:
        acc = -BRAKE
    cap = 28 + 9.5 * abs(math.sin(b))
    if brake:
        cap *= .65 if slipping else .78
    if gas and gear < 2 and v > 12:
        cap *= .85
    max_turn = cap / max(v, 12.)
    omega = st["steer"] * max_turn * .98 + (1 - abs(st["steer"])) * (-1.7 if slipping else -3.2) * (st["phi"] - st["psi"])
    if v > 35:
        if brake:
            omega += st["steer"] * .45 * min(1., v / 60.)
        elif not gas:
            omega += st["steer"] * .24
    slip = st["phi"] - st["psi"]
    grip = clamp((2.6 if slipping else 7.) * slip, -max_turn, max_turn)
    u = v * math.cos(st["psi"])
    st["phi"] += (omega + k * u) * dt
    st["psi"] += (grip + k * u) * dt
    delta = st["phi"] - st["psi"]
    if abs(delta) > .78:
        st["phi"] = st["psi"] + math.copysign(.78, delta)
    acc -= abs(math.sin(st["phi"] - st["psi"])) * v * 1.3
    st["v"] = clamp(v + acc * dt, 0., MAXV * 1.12)
    st["dist"] += st["v"] * math.cos(st["psi"]) * dt / max(.3, 1 + k * st["d"])
    st["d"] += st["v"] * math.sin(st["psi"]) * dt
    wall = WALL - CAR_W / 2
    if abs(st["d"]) > wall:
        sign = 1 if st["d"] > 0 else -1
        into = max(0., st["v"] * math.sin(st["psi"]) * sign)
        st["d"] = sign * wall
        if into > 0:
            mark_wall_impact(st, sign, into)
            st["v"] = max(0., st["v"] - into * .55 - st["v"] * .03)
            st["psi"] *= -.15
            st["phi"] = st["psi"] + (st["phi"] - st["psi"]) * .4
            st["steer"] *= .5
        else:
            st["v"] *= 1 - .8 * dt
    st["dist"] = max(0., st["dist"])


def advance_sim(s, dt, now_mono):
    if s["phase"] != "race":
        return False
    for pid in s["ord"]:
        st = s["sim"].get(pid)
        ctrl = s["controls"].get(pid)
        if st is None or ctrl is None or st["finished"]:
            continue
        trans = s["transmissions"].get(pid, "auto")
        simulate_car(st, ctrl, trans, dt, now_mono)
    active = [s["sim"][pid] for pid in s["ord"] if pid in s["sim"] and not s["sim"][pid]["finished"]]
    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            resolve_contact(active[i], active[j], dt)
    elapsed = max(0, time.time() - s["raceAt"])
    for st in active:
        for dist, d, v in cpu_poses(s, elapsed):
            resolve_contact(st, {"dist": dist, "d": d, "v": v}, dt, True)
    # SOLO el servidor declara vueltas, metas y orden de llegada.
    altered = False
    for pid in s["ord"]:
        st = s["sim"].get(pid)
        if st is None:
            continue
        s["last_progress"][pid] = st["dist"]
        lap = min(MAX_LAPS, max(0, int(st["dist"] / TRACK_LENGTH)))
        if lap > st["lap"]:
            st["lap"] = lap
            s["lap"][pid] = lap
            if lap < MAX_LAPS and not s["winner"]:
                s["deadline"] += LAP_BONUS
                s["bonus"] += 1
                altered = True
            if lap >= MAX_LAPS and pid not in s["finish_order"]:
                st["finished"] = True
                s["finish_order"].append(pid)
                if s["winner"] is None:
                    s["winner"] = pid
                    s["finishAt"] = time.time() + FINISH_GRACE
                altered = True
    s["sim_tick"] += 1
    return altered


def sim_snapshot(s):
    def q(x):
        return round(x, 3)
    return {"type": "race_snapshot", "rid": s["rid"], "tick": s["sim_tick"],
            "serverNow": time.time(), "cars": {
                pid: [q(st["dist"]), q(st["d"]), q(st["v"]), q(st["psi"]),
                      q(st["phi"]), st["lap"], int(st["finished"]), 0,
                      st["gear"], st["ack"], st["hit"], st["hit_side"],
                       st["wall_seq"], st["wall_mask"]]
                for pid, st in s["sim"].items()}}


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
                 lap={pid: 0 for pid in players}, bonus=0, winner=None,
                 finishAt=0.0, results={}, finish_order=[], last_progress={}, resultsAt=0.0,
                 progress_seen={}, progress_speed={}, rank_order=players[:], rank_seq=0,
                 sim={}, controls={}, sim_tick=0, last_sim=0.0, last_snap=0.0,
                 transmissions={pid: room[pid]["presence"].get("t", "auto") for pid in players})
        for pid in players:
            room[pid]["presence"]["p"] = None
        await publish_state(room_name)
    elif cmd == "lobby":
        if peer_id != s["host"] or s["phase"] == "lobby":
            return
        s.update(phase="lobby", ord=[], introAt=0, countdownAt=0,
                 raceAt=0, deadline=0, lap={}, ready={}, bonus=0, winner=None,
                 finishAt=0.0, results={}, finish_order=[], last_progress={}, resultsAt=0.0,
                 progress_seen={}, progress_speed={}, rank_order=[], rank_seq=0,
                 sim={}, controls={}, sim_tick=0, last_sim=0.0, last_snap=0.0, transmissions={})
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
                if data.get("protocol") != PROTOCOL:
                    await ws.send_json({"type": "error", "message": "La sala usa Cabrotona USA v32. Recargá el juego."})
                    break
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
                room[peer_id] = {"ws": ws, "slot": slot, "presence": {}, "seq": 0}
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
                # Las posiciones de clientes NO son autoridad en v32.
                update.pop("p", None)
                state["presence"].update(update)
                # Host flag and racing phase are owned by the server.
                state["presence"]["h"] = int(s["host"] == peer_id)
                state["presence"]["st"] = "lobby" if s["phase"] == "lobby" else "race"
                if update:
                    await relay(room_name, {"type": "peer_presence", "id": peer_id,
                                            "patch": update}, exclude=peer_id)
            elif typ == "input" and room_name and peer_id in rooms.get(room_name, {}):
                s = sessions[room_name]
                if s["phase"] != "race" or data.get("rid") != s["rid"]:
                    continue
                ctrl = s["controls"].get(peer_id)
                if not ctrl:
                    continue
                seq = data.get("seq")
                steer = data.get("steer")
                gear = data.get("gear")
                if (type(seq) is not int or seq <= ctrl["seq"] or
                        type(steer) not in (int, float) or not math.isfinite(steer) or
                        type(gear) is not int):
                    continue
                # Ventana móvil de 1 segundo: sin limpieza el jugador
                # dejaría de responder para siempre después del mensaje 40.
                t_input = time.monotonic()
                last_msg_times = [t for t in last_msg_times if t_input - t < 1.0]
                if len(last_msg_times) >= 40:
                    continue
                last_msg_times.append(t_input)
                ctrl.update(seq=seq, gas=data.get("gas") is True, brake=data.get("brake") is True,
                            steer=clamp(steer, -1, 1), gear=int(clamp(gear, 0, 3)),
                            received=time.monotonic())
                s["sim"][peer_id]["ack"] = seq
            elif typ == "command" and room_name and peer_id in rooms.get(room_name, {}):
                await handle_command(room_name, peer_id, data)
            elif typ == "time_ping" and room_name and peer_id:
                t0 = data.get("t0")
                if type(t0) in (int, float) and math.isfinite(t0):
                    await ws.send_json({"type": "time_pong", "t0": t0,
                                        "serverNow": time.time()})
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


def calculate_results(s):
    """Freeze completed order + distance order at winner+2s or time limit."""
    ordered = [pid for pid in s["finish_order"] if pid in s["ord"]]
    remaining = [pid for pid in s["ord"] if pid not in ordered]
    remaining.sort(key=lambda pid: (-s["last_progress"].get(pid, 0), s["ord"].index(pid)))
    return {pid: i + 1 for i, pid in enumerate(ordered + remaining)}


async def ticker(app):
    while True:
        await asyncio.sleep(SIM_DT)
        t_wall, t_mono = time.time(), time.monotonic()
        for name, s in list(sessions.items()):
            if s["phase"] == "intro" and t_wall >= s["raceAt"]:
                s["phase"] = "race"
                start_sim(s)
                await publish_state(name)
            if s["phase"] == "race":
                elapsed = clamp(t_mono - s["last_sim"], 0., .10)
                steps = min(6, int(elapsed / SIM_DT))
                if steps:
                    for _ in range(steps):
                        altered = advance_sim(s, SIM_DT, t_mono)
                        if altered:
                            await publish_state(name)
                    s["last_sim"] += steps * SIM_DT
                if t_mono - s["last_snap"] >= SNAPSHOT_DT:
                    s["last_snap"] = t_mono
                    await relay(name, sim_snapshot(s))
                await publish_live_ranking(name)
                if (s["winner"] and t_wall >= s["finishAt"]) or (not s["winner"] and t_wall >= s["deadline"]):
                    s["phase"] = "results"
                    if not s["winner"]:
                        s["finishAt"] = s["deadline"]
                    s["results"] = calculate_results(s)
                    s["resultsAt"] = time.time()
                    await publish_state(name)
            elif s["phase"] == "results" and t_wall >= s.get("resultsAt", 0) + 17:
                s.update(phase="lobby", ord=[], introAt=0, countdownAt=0,
                         raceAt=0, deadline=0, lap={}, ready={}, bonus=0, winner=None,
                         finishAt=0.0, results={}, finish_order=[], last_progress={}, resultsAt=0.0,
                         progress_seen={}, progress_speed={}, rank_order=[], rank_seq=0,
                         sim={}, controls={}, transmissions={}, sim_tick=0, last_sim=0.0, last_snap=0.0)
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
