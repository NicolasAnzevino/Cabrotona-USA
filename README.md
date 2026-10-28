# Cabrotona USA Online v3 — FPS/restauración del primer plano

Esta versión **quita completamente** el cambio de segundo plano de la v3 anterior que provocaba lag.
La física vuelve a actualizarse exclusivamente con el bucle habitual `requestAnimationFrame`, como en Online Concurrente v2. No hay un segundo timer de simulación, ni autopiloto por pestaña oculta, ni progreso ficticio desde el servidor.

## Se conservan las correcciones de los CPU
- CPU opcionales violetas usando la **carrocería NPC original** y las texturas violetas, no Gallop ni rivales NPC multicolor.
- Al activar CPU, completan hasta 20 autos sumando los jugadores reales; no cuentan en la clasificación.
- Los CPU chocan con el auto propio: no pueden atravesarse. Los CPU cercanos se separan entre sí.
- Al salir de multijugador, los autos NPC originales restauran sus colores.
- Siguen el reloj global compartido, sistema LISTO, largada sincronizada y ranking transparente del Online Concurrente v2.

## Importante sobre pestañas en segundo plano
Con el retroceso solicitado, la **simulación local se ralentiza o pausa cuando el navegador suspende la pestaña**, como antes. El reloj global del servidor y la partida de los demás jugadores que tengan el juego activo continúan.

## Publicar

1. Extraer el ZIP y subir los seis archivos de la raíz al repositorio `NicolasAnzevino/Cabrotona-USA` rama `main`, reemplazando los anteriores.
2. Hacer un commit. Render desplegará automáticamente el cambio.
3. Comprobar que aparezca `Live` en Events y recargar la página sin caché.

## Ejecución local

```bash
pip install -r requirements.txt
python server.py
```

La prueba del juego 3D en dos dispositivos reales requiere comprobarse en Render tras publicar.


## Nuevo: ícono de pestaña Cabrotona USA
- Se incorporó la imagen proporcionada como favicon de navegador (`favicon.ico`) y versiones PNG de 16, 32, 48, 192 y 256 píxeles.
- `apple-touch-icon.png` para acceso directo en iPhone/iPad.
- El servidor expone rutas específicas para los íconos. Se reemplazó el viejo favicon incrustado en el HTML.
- No se modificaron la física, los CPU, el multijugador ni la gestión del segundo plano.
- Para publicar: subir **todos los archivos** del ZIP a la raíz de la rama `main`, hacer commit y esperar a que Render termine el despliegue. Si aparece el ícono anterior, recargar sin caché o cerrar y reabrir la pestaña.


## Actualización del favicon (imagen nueva del auto 41)
Se reemplazaron únicamente las imágenes de favicon por la nueva imagen proporcionada, en tamaños 16, 32, 48, 192 y 256, además del `.ico` y `apple-touch-icon`. Se actualizó la versión de caché de las referencias en `index.html` a `v=5`. El motor, multijugador, NPC, física y servidor no fueron modificados.


## Online v4 — selección FREE e inicio pulido

- El HUD del modo FREE sube el velocímetro 43 puntos de coordenadas internas (de y=198 a y=155); Arcade/Online mantienen el medidor donde estaba.
- Selección de auto en FREE: 15 segundos en lugar de 20 (Arcade no cambia).
- En la etiqueta superior de la tarjeta FREE, BEGINNER para automático y PROFESSIONAL para manual, al igual que Arcade.
- El auto amarillo del modo FREE vuelve exactamente al aspecto de la versión anterior a v4, sin las franjas y los filetes añadidos en v4.
- Se retiró el menú HTML antiguo «Automática / Manual / Largar» que aparecía brevemente antes de cargar el motor 3D. El menú real dentro del juego se mantiene.
- Se eliminó el logo CABROTONA USA de la esquina superior izquierda, sin restaurar el antiguo título de texto. Se conserva el favicon de la pestaña.

**Publicación:** subí el contenido del ZIP a la raíz del repositorio, reemplazando los archivos anteriores; si todavía está `cabrotona-logo.png` en GitHub podés borrarlo, porque ya no se utiliza. Hacé commit en `main` para desplegar en Render. Las lógicas de multijugador, CPU y físicas no se modificaron en esta actualización.
