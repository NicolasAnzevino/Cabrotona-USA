/* Same-origin WebSocket rooms compatible with the original Cabrotona USA game. */
(() => {
  'use strict';
  const wsURL = () => (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';

  async function join(roomName) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsURL());
      let lastSnapshotTick = -1;
      let ownPose = null;
      const everyone = new Map();
      const listeners = new Set();
      const lostListeners = new Set();
      let selfId = '';
      let established = false;
      let intentionalClose = false;
      let completed = false;
      let session = null;
      let syncInterval = null;
      const clock = { valid: false, offset: 0, rtt: 0, jitter: 0, samples: [] };
      let roughOffset = 0;
      const liveRank = { rid: 0, seq: 0, order: [], queued: [] };
      const resetRank = state => {
        liveRank.rid = Number(state?.rid) || 0;
        liveRank.seq = Number(state?.rankSeq) || 0;
        liveRank.order = Array.isArray(state?.rankOrder) && state.rankOrder.length
          ? state.rankOrder.slice() : (Array.isArray(state?.ord) ? state.ord.slice() : []);
        liveRank.queued = [];
      };
      const rankAtServerTime = () => {
        const now = Date.now() / 1000 + (clock.valid ? clock.offset : roughOffset);
        while (liveRank.queued.length && liveRank.queued[0].applyAt <= now) {
          const next = liveRank.queued.shift();
          liveRank.seq = next.seq;
          liveRank.order = next.order;
        }
        return { rid: liveRank.rid, seq: liveRank.seq, order: liveRank.order.slice() };
      };
      const pingClock = () => {
        if (ws.readyState === WebSocket.OPEN && established) send({ type: 'time_ping', t0: Date.now() / 1000 });
      };
      const notify = () => { for (const fn of listeners) { try { fn(); } catch (err) { console.warn(err); } } };
      const send = packet => {
        if (ws.readyState !== WebSocket.OPEN) throw new Error('Sin conexión con el servidor');
        ws.send(JSON.stringify(packet));
      };
      const addOrChange = (id, presence, replace = false, slot = null) => {
        if (typeof id !== 'string') return;
        let peer = everyone.get(id);
        if (!peer) {
          peer = { peer: id, slot: null, kind: 'viewer', sameTab: id === selfId, isMe: id === selfId, presence: {}, updatedAt: Date.now(), samples: [], lastSeq: -1 };
          everyone.set(id, peer);
        }
        peer.sameTab = peer.isMe = id === selfId;
        if (Number.isInteger(slot) && slot >= 1 && slot <= 8) peer.slot = slot;
        peer.presence = replace ? { ...(presence || {}) } : { ...peer.presence, ...(presence || {}) };
        peer.updatedAt = Date.now();
      };
      const api = {
        peers: () => Array.from(everyone.values()),
        state: () => session,
        ranking: rankAtServerTime,
        authoritative: () => ownPose,
        input: input => {
          if (!established || ws.readyState !== WebSocket.OPEN) return;
          // El servidor únicamente admite controles: nunca aceptará posiciones declaradas por el cliente.
          send({ type: 'input', ...input });
        },
        clock: () => ({ valid: clock.valid, offset: clock.offset, rtt: clock.rtt, jitter: clock.jitter }),
        command: (cmd, value) => send({ type: "command", cmd, value }),
        onPeers: (fn, onLost) => {
          if (typeof fn === 'function') listeners.add(fn);
          if (typeof onLost === 'function') lostListeners.add(onLost);
          if (typeof fn === 'function') fn();
          return () => { listeners.delete(fn); lostListeners.delete(onLost); };
        },
        presence: async patch => {
          if (!established) throw new Error('La sala no está conectada');
          addOrChange(selfId, patch || {});
          send({ type: 'presence', patch });
          notify();
        },
        leave: async () => {
          intentionalClose = true;
          established = false;
          if (syncInterval !== null) { clearInterval(syncInterval); syncInterval = null; }
          ownPose = null;
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) ws.close(1000, 'Salida de sala');
        }
      };

      ws.addEventListener('open', () => {
        try { send({ type: 'join', room: roomName, protocol: 32 }); }
        catch (err) { if (!completed) { completed = true; reject(err); } }
      });
      ws.addEventListener('message', event => {
        let message;
        try { message = JSON.parse(event.data); } catch (_) { return; }
        if (message.type === 'error') {
          if (!completed) { completed = true; reject(new Error(message.message || 'Error en la sala')); }
          intentionalClose = true;
          ws.close();
          return;
        }
        if (message.type === 'joined') {
          selfId = message.id;
          everyone.clear();
          for (const peer of message.peers || []) addOrChange(peer.id, peer.presence, true, peer.slot);
          established = true;
          if (message.state) {
            session = message.state;
            roughOffset = Number(session.serverNow) - Date.now() / 1000 || 0;
            resetRank(session);
          }
          pingClock();
          if (syncInterval === null) syncInterval = setInterval(pingClock, 3000);
          if (!completed) { completed = true; resolve(api); }
          notify();
        } else if (message.type === 'room_state') {
          const newRace = !session || message.rid !== session.rid;
          session = message;
          if (newRace || message.phase === 'lobby') {
            resetRank(message);
            lastSnapshotTick = -1;
            ownPose = null;
            for (const peer of everyone.values()) { peer.samples.length = 0; peer.lastSeq = -1; }
          }
          notify();
        } else if (message.type === 'race_snapshot') {
          if (!session || message.rid !== session.rid ||
              !Number.isInteger(message.tick) || message.tick <= lastSnapshotTick ||
              !Number.isFinite(message.serverNow) || !message.cars ||
              typeof message.cars !== 'object') return;
          lastSnapshotTick = message.tick;
          for (const [id, pose] of Object.entries(message.cars)) {
            if (!Array.isArray(pose) || pose.length < 12 || !pose.slice(0, 9).every(Number.isFinite)) continue;
            if (id === selfId) {
              ownPose = { p: pose.slice(), tick: message.tick, serverNow: message.serverNow };
            } else {
              // Todos ven las MISMAS posiciones del servidor. El retraso visual
              // es solo interpolación; no hay múltiples físicas independientes.
              const peer = everyone.get(id);
              if (!peer) continue;
              peer.presence.p = pose.slice(0, 8);
              peer.updatedAt = Date.now();
              peer.samples.push({ t: message.serverNow, p: pose.slice(0, 8) });
              if (peer.samples.length > 16) peer.samples.splice(0, peer.samples.length - 16);
            }
          }
          // Las posiciones se leen durante el loop de render para evitar
          // recalcular menús/estado de lobby 30 veces por segundo.
        } else if (message.type === 'race_standings') {
          if (!session || message.rid !== session.rid || !Array.isArray(message.order) ||
              !Number.isInteger(message.seq) || !Number.isFinite(message.applyAt)) return;
          const highest = liveRank.queued.length
            ? liveRank.queued[liveRank.queued.length - 1].seq : liveRank.seq;
          if (message.seq <= highest) return;
          liveRank.queued.push({ seq: message.seq, order: message.order.slice(), applyAt: message.applyAt });
          notify();
        } else if (message.type === 'error_notice') {
          session = { ...(session || {}), notice: message.message };
          notify();
        } else if (message.type === 'peer_joined') {
          addOrChange(message.peer.id, message.peer.presence, true, message.peer.slot);
          notify();
        } else if (message.type === 'peer_left') {
          everyone.delete(message.id);
          notify();
        } else if (message.type === 'peer_presence') {
          const patch = message.patch || {};
          const seq = message.seq;
          let peer = everyone.get(message.id);
          if (peer && Array.isArray(patch.p) && Number.isInteger(seq) && seq <= peer.lastSeq) return;
          addOrChange(message.id, patch);
          peer = everyone.get(message.id);
          if (peer && Array.isArray(patch.p) && patch.p.length === 8 &&
              Number.isFinite(message.serverNow)) {
            peer.lastSeq = Number.isInteger(seq) ? seq : peer.lastSeq + 1;
            peer.samples.push({ t: message.serverNow, p: patch.p.slice() });
            if (peer.samples.length > 16) peer.samples.splice(0, peer.samples.length - 16);
          } else if (peer && patch.p === null) {
            peer.samples.length = 0;
          }
          notify();
        } else if (message.type === 'time_pong') {
          const received = Date.now() / 1000;
          const sent = Number(message.t0), server = Number(message.serverNow);
          const rtt = received - sent;
          if (Number.isFinite(sent) && Number.isFinite(server) && rtt >= 0 && rtt < 2) {
            const sample = { rtt, offset: server - (sent + received) / 2 };
            clock.samples.push(sample);
            if (clock.samples.length > 12) clock.samples.shift();
            const best = clock.samples.reduce((a, b) => b.rtt < a.rtt ? b : a);
            // Las muestras de menor RTT sufren menos sesgo por retardo de red.
            clock.offset = clock.valid ? clock.offset * 0.7 + best.offset * 0.3 : best.offset;
            clock.rtt = clock.valid ? clock.rtt * 0.7 + rtt * 0.3 : rtt;
            clock.jitter = Math.max(0, Math.abs(rtt - clock.rtt));
            clock.valid = true;
            notify();
          }
        }
      });
      ws.addEventListener('error', () => {
        if (!completed) { completed = true; reject(new Error('No se pudo abrir la conexión multijugador')); }
      });
      ws.addEventListener('close', () => {
        established = false;
        if (syncInterval !== null) { clearInterval(syncInterval); syncInterval = null; }
        if (!completed) { completed = true; reject(new Error('El servidor cerró la conexión')); }
        if (!intentionalClose) for (const fn of lostListeners) { try { fn(); } catch (err) { console.warn(err); } }
      });
    });
  }
  window.CabRoom = { join };
})();
