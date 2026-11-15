#!/usr/bin/env python3
"""
Motor de La Zona en Directo.

Actualiza estado.json (lo que lee la web) y lo publica en GitHub Pages.

  python zona_estado.py directos
      Pregunta a Twitch quién está en directo y lo guarda en "en_directo".

  python zona_estado.py momento <canal> <multiplicador> [--audio ultimo_minuto.wav | --texto "transcripción"] [--clip SLUG]
      Crea un aviso con titular de qué va ("Xokas sobre Abascal"):
        1) categoría y título del directo (Twitch)
        2) transcripción del último minuto (faster-whisper, si se pasa --audio)
        3) titular + frase con la API de Claude

  python zona_estado.py ultima_hora "Titular" [--canal tv:rtve24h]
  python zona_estado.py ultima_hora --quitar

Configuración en config_zona.json (junto a este archivo):
  {
    "twitch_client_id": "...", "twitch_client_secret": "...",
    "anthropic_api_key": "...",
    "repo": "/ruta/al/clon/del/repo/de/la/web",
    "canales": ["ibai", "rubius", ...]
  }
"""
import json, os, sys, time, subprocess, argparse, datetime, urllib.request, urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(AQUI, "config_zona.json"), encoding="utf-8"))
REPO = CFG["repo"]
ESTADO = os.path.join(REPO, "estado.json")
NOMBRES = CFG.get("nombres", {})          # {"elxokas": "Xokas", ...} para los titulares
MAX_MOMENTOS = 30
MAX_EDAD_MIN = 60
MODELO = CFG.get("modelo", "claude-haiku-5-5")


# ---------------- Twitch ----------------
_token = {"v": None, "exp": 0}

def twitch_token():
    if _token["v"] and time.time() < _token["exp"] - 60:
        return _token["v"]
    data = urllib.parse.urlencode({
        "client_id": CFG["twitch_client_id"],
        "client_secret": CFG["twitch_client_secret"],
        "grant_type": "client_credentials"}).encode()
    r = json.load(urllib.request.urlopen("https://id.twitch.tv/oauth2/token", data, timeout=15))
    _token.update(v=r["access_token"], exp=time.time() + r["expires_in"])
    return _token["v"]

def helix(ruta, params):
    q = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(f"https://api.twitch.tv/helix/{ruta}?{q}", headers={
        "Client-Id": CFG["twitch_client_id"], "Authorization": "Bearer " + twitch_token()})
    return json.load(urllib.request.urlopen(req, timeout=15))["data"]

def en_directo(canales):
    vivos = {}
    for i in range(0, len(canales), 100):
        for s in helix("streams", {"user_login": canales[i:i + 100], "first": 100}):
            vivos[s["user_login"].lower()] = {"categoria": s.get("game_name", ""), "titulo": s.get("title", ""),
                                              "espectadores": s.get("viewer_count", 0)}
    return vivos


# ---------------- Transcripción ----------------
def transcribir(audio):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("⚠️ faster-whisper no instalado: el aviso se hará solo con categoría y título")
        return ""
    modelo = WhisperModel(CFG.get("whisper", "small"), device="auto", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language="es", vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


# ---------------- Titular con Claude ----------------
def titular(nombre, categoria, titulo_directo, texto):
    if not CFG.get("anthropic_api_key"):
        return None
    prompt = (
        "Eres el editor de avisos de una web que enseña directos de streamers españoles. "
        "Con estos datos escribe un aviso para que el espectador sepa de qué va este momento.\n"
        f"Streamer: {nombre}\nCategoría: {categoria}\nTítulo del directo: {titulo_directo}\n"
        f"Transcripción del último minuto: {texto[:4000] or '(sin transcripción)'}\n\n"
        "Responde solo con JSON: {\"tema\": \"<nombre> sobre <tema> | <nombre> jugando a <juego> (máx. 6 palabras)\", "
        "\"resumen\": \"una frase neutral de máx. 12 palabras\"}. "
        "Si es política o actualidad, neutral y sin opinar. Nada inventado: si no sabes el tema, usa el juego o la categoría."
    )
    body = json.dumps({"model": MODELO, "max_tokens": 150,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, headers={
        "x-api-key": CFG["anthropic_api_key"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=30))
        txt = r["content"][0]["text"]
        return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    except Exception as e:
        print("⚠️ No se pudo generar el titular:", e)
        return None


# ---------------- estado.json + publicar ----------------
def leer():
    try:
        return json.load(open(ESTADO, encoding="utf-8"))
    except Exception:
        return {"en_directo": [], "momentos": [], "ultima_hora": None}

def guardar(e, mensaje):
    ahora = datetime.datetime.now().astimezone()
    e["actualizado"] = ahora.isoformat(timespec="seconds")
    limite = ahora - datetime.timedelta(minutes=MAX_EDAD_MIN)
    e["momentos"] = [m for m in e.get("momentos", [])
                     if datetime.datetime.fromisoformat(m["hora"]) > limite][-MAX_MOMENTOS:]
    tmp = ESTADO + ".tmp"
    json.dump(e, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, ESTADO)
    publicar(mensaje)

def publicar(mensaje):
    def git(*a):
        return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
    git("add", "estado.json")
    if git("diff", "--cached", "--quiet").returncode == 0:
        return
    git("commit", "-m", mensaje)
    r = git("push")
    if r.returncode != 0:
        git("pull", "--rebase")
        r = git("push")
    print("✅ publicado" if r.returncode == 0 else "❌ push falló: " + r.stderr[-300:])


# ---------------- Comandos ----------------
def cmd_directos(_):
    vivos = en_directo(CFG["canales"])
    e = leer()
    e["en_directo"] = sorted(vivos)
    e["info"] = vivos
    guardar(e, f"directos: {len(vivos)}")
    print("En directo:", ", ".join(sorted(vivos)) or "nadie")

def cmd_momento(a):
    canal = a.canal.lower()
    nombre = NOMBRES.get(canal, canal)
    info = {}
    try:
        info = en_directo([canal]).get(canal, {})
    except Exception as ex:
        print("⚠️ Twitch:", ex)
    texto = a.texto or (transcribir(a.audio) if a.audio else "")
    t = titular(nombre, info.get("categoria", ""), info.get("titulo", ""), texto) or {}
    cat = info.get("categoria", "")
    tema = t.get("tema") or (f"{nombre} jugando a {cat}" if cat and cat != "Just Chatting" else f"{nombre} en directo")
    m = {"id": f"{canal}-{int(time.time())}", "canal": canal, "tema": tema,
         "resumen": t.get("resumen", info.get("titulo", "")), "categoria": cat,
         "multiplicador": a.multiplicador, "clip": a.clip or "",
         "hora": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    e = leer()
    e.setdefault("momentos", []).append(m)
    guardar(e, f"momento: {tema}")
    print("🔥", tema, "-", m["resumen"])

def cmd_ultima_hora(a):
    e = leer()
    if a.quitar:
        e["ultima_hora"] = None
        guardar(e, "última hora: quitada")
        return
    e["ultima_hora"] = {"id": f"uh-{int(time.time())}", "canal": a.canal, "tema": "ÚLTIMA HORA",
                        "titulo": a.titulo, "resumen": a.titulo,
                        "hora": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    guardar(e, "última hora: " + a.titulo)

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
sub.add_parser("directos").set_defaults(f=cmd_directos)
pm = sub.add_parser("momento"); pm.set_defaults(f=cmd_momento)
pm.add_argument("canal"); pm.add_argument("multiplicador", type=float)
pm.add_argument("--audio"); pm.add_argument("--texto"); pm.add_argument("--clip")
pu = sub.add_parser("ultima_hora"); pu.set_defaults(f=cmd_ultima_hora)
pu.add_argument("titulo", nargs="?", default=""); pu.add_argument("--canal", default="tv:rtve24h")
pu.add_argument("--quitar", action="store_true")

if __name__ == "__main__":
    a = p.parse_args()
    a.f(a)
