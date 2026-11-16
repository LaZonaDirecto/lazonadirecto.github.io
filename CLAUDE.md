# La Zona en Directo

Web multiview de directos en español: https://lazonadirecto.github.io (GitHub Pages, rama `main`; cada push se publica en ~1 min).
El dueño es Aka Rikk. Habla en español: responde y escribe todo (código, comentarios, textos de la web) en español de España.

## Cómo funciona (versión actual)
- **Canal GTA** (desde 16-11-2026, para el lanzamiento de GTA VI el 19-11): mismo motor que el Canal La Zona pero solo con directos cuya categoría o título es GTA (`esGTA`). Si no hay nadie jugando, pone lo mejor del momento y lo dice. Enlace directo: `?canal=gta`. También hay filtro «GTA» en la rejilla.
- Modos: **Canal La Zona** (automático: pone lo más interesante y cambia solo; permanencia mínima 150 s, cambia si otro supera ×1,18 en puntos, o tras 60 s si otro tiene momento ≥ 0,5), **Elegir directo** y **Multivista** (2 o 4).
- Puntos = 0,6 × audiencia (log de espectadores, 0–1) + 0,4 × **momento** (media suavizada cada 10 s). Por debajo de 800 espectadores, ×0,6.
- Saltos sin bajones de público: el Canal La Zona solo cambia a directos con ≥ 2.000 espectadores y ≥ 30 % de los del que suena (de IlloJuan a Rubius sí, a un canal pequeño no). Los pequeños con un buen momento salen como aviso opcional.
- Antes de cada cambio automático sale la tarjeta verde 12 s: «Cambiar ya» / «Quedarme con X». Si se queda, no vuelve a proponer ese canal en 10 min y espera otros 150 s. `?demozona` lo prueba.
- Momento (0–1), siempre comparando los últimos 30 s con lo normal en ese canal (5 min): ritmo del chat 28 %, personas distintas escribiendo 17 %, reacciones (risas, NOOO, ???, emotes) 20 %, todo el chat repitiendo la misma frase 15 %, subs/bits/raids 10 %, crecimiento de espectadores en 10 min 10 %. Con chats muy pequeños se reduce (poca muestra).
- Temas: palabras que más personas distintas repiten en el último minuto (sin palabras vacías ni tacos). Salen en "Por qué estás viendo esto", en el ranking y en los avisos. Para titulares de verdad ("Xokas sobre Abascal") hace falta el motor con la API de Claude.
- Quién está en directo: SOLO decapi.me `/twitch/viewercount/<canal>` (número = en directo). No usar los eventos ONLINE/OFFLINE del reproductor de Twitch: fallan (marcaban a Auron en directo y a Rubius sin conexión).
- Chat: lectura anónima por IRC (`wss://irc-ws.chat.twitch.tv`, `justinfan…`) de los 30 directos con más gente. Si un chat se dispara, aviso abajo a la derecha.
- `?demo` en la URL saca un aviso de prueba.
- **Qué pasa ahora en cada directo** (usuario, 16-11): cada tarjeta, la fila del ranking y la barra bajo el reproductor llevan una descripción muy corta para decidir si entrar. Orden: `info[canal].resumen` de estado.json (titular del motor con transcripción + Claude) → título del directo limpio (decapi `/twitch/title/<canal>`, cada ~3 min; sin !comandos, #, @, emojis ni mayúsculas gritadas) + «En el chat: …» con los temas del chat. Funciones `limpiarTitulo`, `ahora`, `ahoraHTML` (siempre escapar el título: viene de fuera).

## Qué es
- El espectador ve 1, 2 o 4 directos a la vez (Twitch, Kick y YouTube) de streamers hispanohablantes.
- Cuando el motor detecta un momento fuerte en otro canal, sale un aviso abajo a la derecha (mini reproductor) con un titular de qué va ("Xokas sobre Abascal", "Auron jugando a Among Us") y los botones **Cambiar a este directo** / **Seguir aquí**. Nunca se cambia de directo sin que el espectador lo pida.
- Sectores para que siempre haya algo en directo a cualquier hora: Ahora, España, Latinoamérica, Esports y eventos, Noticias. La web elige qué poner según la franja horaria de España y, si no hay nadie, acaba en el Canal 24 Horas de RTVE.
- Última hora: franja roja arriba y aviso prioritario.

## Archivos
- `index.html`: toda la web (HTML + CSS + JS en un archivo, sin dependencias salvo el SDK de Twitch y Google Fonts). La lista de canales está en `CANALES` y las franjas en `franja()`.
- `estado.json`: lo que la web lee cada 20 s. Lo escribe el motor. Esquema:
  ```json
  {"actualizado":"ISO", "en_directo":["ibai","kick:westcol"],
   "info":{"ibai":{"categoria":"Just Chatting","titulo":"...","espectadores":0,"resumen":"Reacciona a la gala de los Goya"}},
   "momentos":[{"id","canal","tema","resumen","categoria","multiplicador","clip","hora"}],
   "ultima_hora":null | {"id","canal":"tv:rtve24h","titulo"}}
  ```
  La web solo usa `en_directo` si `actualizado` tiene valor.
- `motor/zona_estado.py`: se ejecuta en el Mac del dueño. Pregunta a Twitch quién está en directo, transcribe el último minuto (faster-whisper), saca el titular con la API de Claude y hace `git push` de `estado.json`. Las claves van en `motor/config_zona.json`, que está en `.gitignore`: **no se suben nunca claves al repositorio** (es público).
- Sin motor, la web ya sabe quién está en directo en Twitch (y a qué juega) preguntando a decapi.me (`/twitch/uptime/<canal>` y `/twitch/game/<canal>`) al entrar y cada 3 min. Kick todavía no.
- Ids de canal: Twitch = login (`ibai`), Kick = `kick:<canal>`, tele = `tv:<id>`.

## Reglas que no se pueden romper
- Solo reproductores oficiales (Twitch embed SDK, `player.kick.com`, YouTube embed). No tapar, recortar ni modificar el reproductor; no usar otro reproductor para vídeo de Twitch. Twitch necesita `parent` = dominio con HTTPS (no funciona en local con `file://`).
- Autoplay de Twitch solo con reproductor visible de al menos 400×300 px.
- Nada de reemitir señales (descargar y volver a emitir directos ajenos). Todo es insertar el reproductor original.
- Televisión: solo directos oficiales que se dejan insertar (RTVE 24 h en YouTube). Nada de Mediaset/Atresmedia ni programas como La isla de las tentaciones.
- Titulares de avisos neutrales; en política, sin opinar.

## Diseño (no volver a algo genérico)
- Estilo "sala de realización": fondo azul noche (#0A0F24, paneles #111833 / #18213F, borde #26305A), rojo de programa #FF2D55 = lo que suena / en directo, verde de previo #19E3A0 = aviso nuevo.
- Tipografías: Bricolage Grotesque (títulos) + Manrope (texto). Avatares con iniciales y color por canal.
- El dueño quiere una interfaz muy cuidada, llamativa, que no parezca barata. Responsive hasta móvil (muchos la verán en el móvil).

## Pendiente (por orden)
1. Motor en marcha: app de Twitch (client id/secret) y clave de la API de Claude en `motor/config_zona.json`; comprobar también directos de Kick; ejecutar `directos` cada minuto y `momento` desde el detector de picos de chat.
2. Con `en_directo` real, el arranque debe poner a la primera el directo más fuerte de la franja (ahora va probando canal a canal y tarda).
3. Clips de Twitch en el aviso (necesita autorizar una cuenta de Twitch).
4. Dominio propio y registro de la marca (cuando funcione).
