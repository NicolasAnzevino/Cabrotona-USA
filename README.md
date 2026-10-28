# Cabrotona USA — multijugador sincronizado

Versión preparada para Render. Conserva los modos individuales, el motor 3D y los colores/números de los ocho jugadores, e incluye estos cambios exclusivos para **Multiplayer**:

- Clasificación transparente, sin título ni panel: cuadrado del color del piloto, posición actual y apodo.
- Un **único cronómetro de sala** dirigido por el servidor, con inicio simultáneo y +48 segundos para **todos** cuando un piloto completa una vuelta (hasta la sexta vuelta).
- El anfitrión solo puede largar con un mínimo de dos jugadores y **todos los invitados en LISTO**. Los invitados pueden activar/cancelar LISTO.
- Antes de la largada se muestra a todos la pantalla original **«Gentlemen, start your engines»**, y después la cuenta regresiva compartida.
- Opción **Non-player cars** en el lobby, apagada por defecto y configurable solo por el anfitrión. Cuando está activada, se muestran autos **violetas** hasta llegar a **20 autos totales** (jugadores + CPU). Los CPU no cuentan en posiciones ni puestos finales, y no chocan con jugadores (son tráfico visual sincronizado).
- Colores de jugadores fijos: rojo, azul, amarillo, verde, negro, rosa, celeste y naranja (1P–8P).

## Cómo actualizar GitHub/Render

1. Subí los archivos de **este ZIP** a la raíz del repositorio [Cabrotona-USA](https://github.com/NicolasAnzevino/Cabrotona-USA), sobrescribiendo los anteriores: `index.html`, `multiplayer.js`, `server.py`, `requirements.txt`, `render.yaml` y `README.md`.
2. Confirmá los cambios en la rama `main` (**Commit changes**).
3. Render despliega automáticamente desde esa rama si el servicio tiene Auto Deploy habilitado. Mirá `Events` y esperá el estado `Live`.
4. Para intentar cambiar la URL de `cabrotona-usa-multijugador.onrender.com` a **`cabrotona-usa.onrender.com`**, abrí el **servicio existente** en Render y buscá en **Settings → General → Name** la opción de cambiar el nombre a `cabrotona-usa`. Comprobá la nueva URL que muestre Render y que esté disponible. **No crees otro servicio ni borres el anterior** solo para actualizar el código. Cambiar `name` en `render.yaml` no renombra por sí solo un servicio creado anteriormente desde el panel.

### Arquitectura y límites

- Un proceso `aiohttp` sirve `/` y `/multiplayer.js`, acepta WebSocket en `/ws` y expone `/health`.
- El servidor valida quién es el anfitrión, quién está listo, los CPU opcionales, el inicio de la carrera, el tiempo único y los bonos por vuelta; emite el estado a todos los clientes.
- Los movimientos y la física del auto de cada humano se calculan en su navegador y se transmiten aproximadamente 22 veces/segundo para que los demás los vean. **No hay físicas de colisión deterministas/autoritativas del lado del servidor**, por lo que los contactos entre autos humanos aún pueden presentar diferencias entre dispositivos bajo mucha latencia. Los CPU siguen una trayectoria visual determinista a partir del reloj compartido.
- Para no exceder las ocho conexiones humanas por sala, las salas admiten como máximo **8 participantes**. Los cupos CPU solo se activan al empezar la carrera.
- Las salas viven en memoria del proceso; si Render reinicia o suspende el servicio, las salas activas se pierden. Un plan gratuito puede suspenderse por inactividad.
- Los jugadores que intentan ingresar después de iniciarse la carrera reciben un aviso de que la sala está jugando.

## Ejecutar localmente

```bash
pip install -r requirements.txt
python server.py
```

Luego abrí http://localhost:10000 en dos pestañas o dispositivos de la misma red (usando la IP del host).
