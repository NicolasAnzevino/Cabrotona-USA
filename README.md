# Cabrotona USA — actualización online v3: CPU sólidos + carrera en segundo plano

Actualización incremental sobre la edición **Online Concurrente v2**. Conserva las salas, el cronómetro global, LISTO, la largada de "Gentlemen, start your engines", las identidades de los 8 pilotos y el ranking en vivo.

## Cambios

### El juego continúa con la pestaña en segundo plano
- La simulación ya **no depende de `requestAnimationFrame`**: éste sólo dibuja. La física corre con un temporizador independiente y pasos de 1/60 s.
- Cuando la pestaña está oculta, el auto propio usa un piloto automático moderado hasta que vuelvan los controles, en lugar de frenar por la pérdida de foco.
- Si el navegador limita/suspende incluso los temporizadores, **el servidor continúa el reloj global** y mantiene avanzando el auto del piloto que no transmite durante más de 1,5 segundos. Al volver, su posición se resincroniza y un paquete viejo no puede hacer retroceder el auto.
- Si se **cierra** la pestaña, se desconecta la conexión WebSocket y se abandona la sala. Los navegadores móviles pueden suspender la red al bloquear el teléfono: no puede garantizarse funcionamiento indefinido en segundo plano.

### NPC violetas (sin NPC de otros colores)
- Con CPU apagados, no aparecen autos NPC en carrera multijugador.
- Con CPU encendidos, los autos controlados por computadora completan la parrilla hasta **20 autos incluyendo humanos**.
- Ahora todos los CPU usan el **modelo 3D original de NPC** (no el Gallop de los humanos) con **carrocería, techo, vinilos y detalles violetas**.
- Los rivales humanos conservan sus Gallop con sus colores y números de asiento.
- Se restaura la pintura NPC original al abandonar multiplayer; el modo individual no queda pintado de violeta.

### Colisiones
- Los CPU tienen **colisión contra el jugador humano**; ya no son hologramas atravesables. Hay choque frontal/trasero y roces laterales.
- Los CPU evitan superponerse unos con otros cuando circulan próximos en el mismo carril.
- Un piloto que continúa por el servidor estando inactivo también puede verse detenido detrás de un CPU.

## Actualizar GitHub y Render

1. Descomprimí este ZIP y subí los seis archivos de su raíz a **NicolasAnzevino/Cabrotona-USA**, rama `main`, **reemplazando los anteriores**: `index.html`, `multiplayer.js`, `server.py`, `requirements.txt`, `render.yaml` y `README.md`.
2. Hacé **Commit changes**. Render tiene configurado despliegue automático desde `main`.
3. Mirá **Events** en tu Web Service hasta que aparezca `Live`. Recargá la URL con Ctrl+Shift+R para evitar caché.
4. Prueba recomendada: dos dispositivos en la misma sala, CPU habilitados, contacto con un NPC violeta; luego dejar una ventana en segundo plano y comprobar que ambos siguen avanzando y que el tiempo de sala no se congela.

## Límites técnicos

- El cronómetro de sala, la preparación, la largada y la bonificación de vueltas siguen en el servidor.
- Las físicas interactivas de los humanos siguen siendo locales con posiciones por WebSocket; con latencia extrema pueden verse desajustes temporales entre dispositivos. La colisión de CPU contra cada jugador es local y se aplica en el cliente dueño de ese jugador.
- Los CPU se calculan de forma determinista usando el tiempo compartido y se separan visualmente al acercarse.
- Si la pestaña se cierra o la conexión WebSocket se corta definitivamente, el servidor libera su plaza. El servicio gratuito de Render puede suspenderse por inactividad, lo que elimina las salas en memoria.
- Se comprobaron la sintaxis JavaScript y Python, simulación en navegador sin motor WebGL, asignación de 18 CPU con dos humanos, choque del jugador con un CPU, avance en pestaña oculta y recuperación servidor tras una pausa. **No se completó una prueba end-to-end del renderizado 3D con dos navegadores reales**; conviene verificar visualmente en Render.

## Ejecución local

```bash
pip install -r requirements.txt
python server.py
```

Abrí `http://localhost:10000` desde un navegador (o desde otros dispositivos usando la IP de la computadora en la misma red).
