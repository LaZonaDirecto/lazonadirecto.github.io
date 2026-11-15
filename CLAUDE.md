# La Zona en Directo

Web multiview de directos en español: https://lazonadirecto.github.io (GitHub Pages, rama `main`; cada push se publica en ~1 min).
El dueño es Aka Rikk. Habla en español: responde y escribe todo (código, comentarios, textos de la web) en español de España.

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
   "info":{"ibai":{"categoria":"Just Chatting","titulo":"...","espectadores":0}},
   "momentos":[{"id","canal","tema","resumen","categoria","multiplicador","clip","hora"}],
   "ultima_hora":null | {"id","canal":"tv:rtve24h","titulo"}}
  ```
  La web solo usa `en_directo` si `actualizado` tiene valor.
- `motor/zona_estado.py`: se ejecuta en el Mac del dueño. Pregunta a Twitch quién está en directo, transcribe el último minuto (faster-whisper), saca el titular con la API de Claude y hace `git push` de `estado.json`. Las claves van en `motor/config_zona.json`, que está en `.gitignore`: **no se suben nunca claves al repositorio** (es público).
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
