#!/usr/bin/env python3
"""Confere se a máquina tem tudo que a skill precisa e mostra como instalar o que faltar.

Uso: python3 check_env.py
"""

import importlib.util
import platform
import re
import shutil
import subprocess

OS = platform.system()  # Darwin, Linux, Windows


def version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return ""


def hint(mac, linux, win):
    return {"Darwin": mac, "Linux": linux}.get(OS, win)


rows = []
ok_all = True

# Node 22+
node = shutil.which("node")
node_v = version(["node", "-v"]) if node else ""
m = re.match(r"v(\d+)", node_v)
node_ok = bool(m and int(m.group(1)) >= 22)
rows.append(("Node.js 22+", node_ok, node_v or "não encontrado", hint("brew install node", "https://nodejs.org (ou nvm install 22)", "winget install OpenJS.NodeJS.LTS")))

for name, cmd, h in [
    ("npm / npx", "npx", hint("vem com o Node", "vem com o Node", "vem com o Node")),
    ("FFmpeg", "ffmpeg", hint("brew install ffmpeg", "sudo apt install ffmpeg", "winget install Gyan.FFmpeg")),
    ("FFprobe", "ffprobe", "vem junto com o FFmpeg"),
    ("Python 3", "python3", hint("brew install python", "sudo apt install python3", "winget install Python.Python.3.12")),
]:
    found = shutil.which(cmd)
    v = version([cmd, "-version"] if cmd.startswith("ff") else [cmd, "--version"]) if found else ""
    rows.append((name, bool(found), v[:60] or "não encontrado", h))

# yt-dlp (só se o vídeo vier de link)
ytdlp = shutil.which("yt-dlp")
rows.append(("yt-dlp (links do YouTube)", bool(ytdlp), version(["yt-dlp", "--version"]) if ytdlp else "não encontrado", hint("brew install yt-dlp", "pipx install yt-dlp", "winget install yt-dlp.yt-dlp")))

# Transcrição: pelo menos um motor
engines = []
if importlib.util.find_spec("mlx_whisper"):
    engines.append("mlx_whisper")
if importlib.util.find_spec("faster_whisper"):
    engines.append("faster_whisper")
if shutil.which("whisper-cli"):
    engines.append("whisper-cpp")
rows.append((
    "Transcrição (algum motor)",
    bool(engines),
    ", ".join(engines) or "nenhum",
    hint(
        "Mac com chip Apple: pip3 install mlx-whisper  (ou brew install whisper-cpp)",
        "pip3 install faster-whisper  (ou compile o whisper.cpp)",
        "pip install faster-whisper",
    ),
))

print("\nChecagem do ambiente da skill reels-hyperframes\n")
for name, ok, detail, how in rows:
    required = name not in ("yt-dlp (links do YouTube)",)
    mark = "OK " if ok else ("FALTA" if required else "opcional")
    print(f"  [{mark:^8}] {name:<28} {detail}")
    if not ok:
        print(f"             instalar: {how}")
        if required:
            ok_all = False

try:
    import os

    if OS == "Darwin":
        mem = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip()) / 1024**3
    elif OS == "Linux":
        mem = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    else:
        mem = 0
    if mem:
        print(f"\n  Memória RAM: {mem:.0f} GB" + ("  (pouca: renderize com -w 1 ou -w 2)" if mem < 12 else ""))
except Exception:
    pass

print("\nTudo certo." if ok_all else "\nFalta instalar o que está marcado como FALTA antes de seguir.")
raise SystemExit(0 if ok_all else 1)
