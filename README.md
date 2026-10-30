# CABROTONA USA — V12 (ONLINE RESULTS)

Este paquete parte del `index.html` proporcionado por el usuario el 30 de octubre de 2026.

## Cambios de multijugador
- Menú SESSION DATA: COURSE / BEGINNER (4 LAPS), NON PLAYER CARS / YES-NO, GAME TYPE / TYPE A. Eliminadas las opciones TRANSMISSION y LAPS del panel y los controles de transmisión del lobby.
- La pista BEGINNER en multijugador dura 4 vueltas. La carrera individual Arcade sigue en 4 vueltas.
- El servidor registra al primer corredor que alcanza la sexta vuelta y establece el final de la carrera 2.0 segundos después. El ganador queda en primer lugar; los demás se ordenan por llegada (si cruzan dentro del margen) o distancia recorrida. Todos reciben la misma clasificación.
- Cada jugador ve una secuencia final según su puesto: toma lateral para el ganador, derrape/alejamiento para el segundo, choque para el tercero y vuelco para cuarto en adelante. El reloj de carrera deja de actualizarse al terminar, pero la simulación continúa hasta la pantalla de RESULTS (se congela durante esa pantalla).
- CPU violeta 00, controles del host, READY y el multijugador permanecen.

## Instalación
Subir los archivos de este ZIP a la raíz del repositorio GitHub y hacer commit en `main`. Render puede redesplegar automáticamente si está configurado. No se ha publicado remotamente.

## Pruebas
Comprobada sintaxis del JavaScript con `node --check`, compilación del servidor Python y conexión real de 2 sockets con 4 vueltas, ganador y clasificación compartida. La revisión visual 3D real quedó pendiente: el navegador automatizado del entorno impidió abrir la URL local.


### v13 — Multiplayer
- TRANSMISSION: cada jugador puede alternar AT/MT desde su fila, boton inferior o tecla T.
- Eliminado solamente el titulo SESSION DATA (se conservan COURSE, NON PLAYER CARS, GAME TYPE).
- BEGINNER 4 LAPS tanto Arcade como Multiplayer.
- Una cinematografica de RESULTS para todos, ganen o se agote el reloj global; el servidor fija el puesto.
- El ganador queda con un plano lateral grande del auto similar a Daytona USA.

## v14 · Endings adaptados del video de referencia

- Desde que termina la carrera aparece RESULTS, y el reloj de la carrera queda fijado.
- Cámara tipo TV a un costado de pista: el auto se acerca desde lejos en movimiento.
- 1.º: acercamiento y plano lateral grande, el auto posa sin movimientos extraños.
- 2.º: derrape y alejamiento; 3.º: golpe y queda detenido; 4.º+: múltiples vueltas de campana.
- GAME OVER entra con la animación de letras mientras la escena 3D sigue funcionando.
- 4 vueltas en BEGINNER multijugador, AT/MT y cierre compartido a los 2 s sin cambios.

Este código recrea el montaje en el motor 3D y no reproduce ni incorpora el video como asset.

### Versión v15: endings y NPC
- Cinematográficas revisadas contra el video de referencia: planos generales, perfil cercano, derrape, choque y vuelco real del modelo 3D. RESULTS aparece desde el principio.
- Final online por reloj: acepta la clasificación del servidor y activa un cierre local provisional si el paquete de resultados tarda más de 1,3 segundos. La clasificación del servidor tiene prioridad al llegar.
- Corregido el repintado de texturas de NPC al volver a Arcade/intro tras Multiplayer; no se reutilizan las texturas violetas/00.
- Se conservan las 4 vueltas en BEGINNER, el selector AT/MT, el sistema LISTO y los CPU violetas.
