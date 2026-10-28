# Cabrotona USA — multijugador con 8 colores y ranking en vivo

Versión actualizada a partir de **Cabrotona USA (11)**, manteniendo el contenido original (modos individuales, física, audio, cámaras y pista). Los cambios de esta versión se aplican **solo al multijugador**.

## Autos por participante

1P: rojo / nº 1 · 2P: azul / nº 2 · 3P: amarillo / nº 3 · 4P: verde / nº 4 · 5P: negro / nº 5 · 6P: rosa / nº 6 · 7P: celeste / nº 7 · 8P: naranja / nº 8.

Los números son **asientos de sala asignados por el servidor**, no posiciones de carrera. Si un piloto abandona, el asiento queda disponible para el próximo piloto; los demás mantienen su número. Todos los rivales se dibujan con el **modelo Gallop completo**, igual que el auto controlado localmente, con color y número que les corresponden en carrocería/techo. Se muestra el color y número en el lobby y en el radar.

En carrera, el panel izquierdo reemplaza los tiempos de vueltas por **POSICIONES EN VIVO**, con orden por progreso en la pista y formato `2P: Nico`, `1P: Agustin`, etc. Se recalcula cada cuadro a partir de las posiciones WebSocket. El contador y los tiempos del modo individual siguen como estaban.

## Actualizar el repositorio existente

1. Descomprimí este ZIP.
2. En tu repositorio `NicolasAnzevino/Cabrotona-USA`, **reemplazá** los archivos de la raíz por `index.html`, `multiplayer.js`, `server.py`, `requirements.txt` y `render.yaml` del ZIP; guardá los cambios con **Commit changes**. No subas el ZIP sin descomprimir.
3. En tu servicio `cabrotona-usa-multijugador` de Render, si la publicación automática está activa, el commit dispara un nuevo despliegue. Revisá **Events** o **Logs** hasta ver **Live**.
4. Abrí `https://cabrotona-usa-multijugador.onrender.com` en dos dispositivos, creá una sala e invitá al otro participante con el código. Cada participante debe abrir la misma versión actualizada.

## Ejecutar localmente

```bash
pip install -r requirements.txt
python server.py
```

Abrí `http://localhost:10000`. Para salud del servicio: `/health`. El multijugador necesita conexión WebSocket, por lo que no sirve abrir el HTML como archivo local sin el servidor.

## Alcance

La sala admite máximo 8 pilotos por proceso y mantiene los datos en memoria. Los coches remotos se interpolan con datos del servidor; la física es cliente a cliente (no hay árbitro de colisiones ni precisión competitiva garantizada). Render Free puede entrar en suspensión por inactividad. La carga de Three.js desde CDN y las fuentes necesitan acceso a Internet.
