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
