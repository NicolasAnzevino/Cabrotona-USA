/* Same-origin WebSocket rooms compatible with the original Cabrotona USA game. */
(() => {
  'use strict';
  const wsURL = () => (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';

  async function join(roomName) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsURL());
      const everyone = new Map();
      const listeners = new Set();
      const lostListeners = new Set();
      let selfId = '';
      let established = false;
      let intentionalClose = false;
      let completed = false;
      const notify = () => { for (const fn of listeners) { try { fn(); } catch (err) { console.warn(err); } } };
      const send = packet => {
        if (ws.readyState !== WebSocket.OPEN) throw new Error('Sin conexión con el servidor');
        ws.send(JSON.stringify(packet));
      };
      const addOrChange = (id, presence, replace = false) => {
        if (typeof id !== 'string') return;
        let peer = everyone.get(id);
        if (!peer) {
          peer = { peer: id, kind: 'viewer', sameTab: id === selfId, isMe: id === selfId, presence: {}, updatedAt: Date.now() };
          everyone.set(id, peer);
        }
        peer.sameTab = peer.isMe = id === selfId;
        peer.presence = replace ? { ...(presence || {}) } : { ...peer.presence, ...(presence || {}) };
        peer.updatedAt = Date.now();
      };
      const api = {
        peers: () => Array.from(everyone.values()),
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
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) ws.close(1000, 'Salida de sala');
        }
      };

      ws.addEventListener('open', () => {
        try { send({ type: 'join', room: roomName }); }
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
          for (const peer of message.peers || []) addOrChange(peer.id, peer.presence, true);
          established = true;
          if (!completed) { completed = true; resolve(api); }
          notify();
        } else if (message.type === 'peer_joined') {
          addOrChange(message.peer.id, message.peer.presence, true);
          notify();
        } else if (message.type === 'peer_left') {
          everyone.delete(message.id);
          notify();
        } else if (message.type === 'peer_presence') {
          addOrChange(message.id, message.patch);
          notify();
        }
      });
      ws.addEventListener('error', () => {
        if (!completed) { completed = true; reject(new Error('No se pudo abrir la conexión multijugador')); }
      });
      ws.addEventListener('close', () => {
        established = false;
        if (!completed) { completed = true; reject(new Error('El servidor cerró la conexión')); }
        if (!intentionalClose) for (const fn of lostListeners) { try { fn(); } catch (err) { console.warn(err); } }
      });
    });
  }
  window.CabRoom = { join };
})();
