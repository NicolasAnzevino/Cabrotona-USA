# Cabrotona USA (11) — multijugador online

Esta edición está basada en **Cabrotona USA (11).html** y mantiene la pista, el menú original, las cámaras, la física, los autos y la música del proyecto. Habilita su opción original **MULTIPLAYER** utilizando un servidor Python y WebSockets, sin depender de Claude Artifacts.

## Qué incluye

- Juego 3D original en `index.html` con multijugador habilitado.
- Crear sala y entrar con un código de 5 caracteres.
- Hasta **8 jugadores por sala**, con autos visibles, posición, velocidad y transmisión individual sincronizadas en red.
- Anfitrión que inicia la carrera; salida de lobby, abandono y detección de desconexión.
- Modos ARCADE y FREE para jugar en solitario preservados.

## Subir a Render

1. Descomprimí el ZIP y subí el **contenido de la carpeta** a un repositorio de GitHub, con `index.html`, `server.py`, `multiplayer.js`, `requirements.txt` y `render.yaml` en la **raíz**.
2. En Render, creá un **Web Service** desde el repositorio GitHub (o creá un Blueprint usando `render.yaml`).
3. Configuración: **Python**, plan **Free**, construcción `pip install -r requirements.txt`, inicio `python server.py`. Ruta de comprobación `/health`.
4. Una vez que figure activo, abrí la **misma URL pública** del servicio en dos dispositivos.
5. Para jugar: Enter o clic para abrir el menú → **MULTIPLAYER** → nombre → **Crear sala**. El segundo jugador abre la misma URL, elige **Unirme** e ingresa el código mostrado en el lobby. El anfitrión pulsa **START** o Enter.

**Importante:** el ZIP no es por sí mismo un sitio alojado. Tampoco alcanza con abrir `index.html` desde el explorador de archivos: el juego multijugador necesita que el servidor WebSocket esté en funcionamiento. Si necesitás solo el juego local, los modos de un jugador siguen disponibles cuando el navegador carga sus recursos.

## Ejecutar en tu computadora

Python 3.10+:

```bash
pip install -r requirements.txt
python server.py
```

Visitá `http://localhost:10000` desde dos pestañas. Podés abrir `/health` para verificar el servidor.

## Límites y alcance

El servidor mantiene las salas y sus posiciones en memoria (se pierden al reiniciar). Usa un proceso y una instancia de Render; no escales a varias instancias sin agregar un backend compartido. El multijugador sincroniza las posiciones de los clientes; la física y los choques se calculan localmente, por lo que puede haber diferencias entre pantallas con latencia elevada y **no es un sistema de arbitraje competitivo**. Los modelos 3D de Three.js y las fuentes externas requieren conexión a Internet. En el plan Free de Render el servicio puede suspenderse por inactividad, provocando demora al reactivarse o desconexiones.

## Archivos

- `index.html`: juego actualizado, basado en el archivo del usuario.
- `multiplayer.js`: adaptador WebSocket (salas, participantes y presencia).
- `server.py`: servidor HTTP + WebSocket.
- `requirements.txt`: dependencia Python.
- `render.yaml`: plantilla para Render.
