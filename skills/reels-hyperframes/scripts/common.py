"""Funções compartilhadas pelos scripts da skill reels-hyperframes."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
HF_VERSION = "0.8.78"  # versão do HyperFrames testada com esta skill
HF = ["npx", "-y", f"hyperframes@{HF_VERSION}"]
# Variáveis que deixam o HyperFrames quieto: sem telemetria, sem checar atualização, sem instalar
# skills globais no Claude Code. (A chave do Gemini é removida no hf.py para o snapshot não enviar quadros.)
HF_ENV = {
    "HYPERFRAMES_NO_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
    "HYPERFRAMES_NO_UPDATE_CHECK": "1",
    "HYPERFRAMES_SKIP_SKILLS": "1",
}

# Duração (s) de cada efeito sonoro que vem dentro do pacote do HyperFrames
SFX_DURATIONS = {
    "whoosh.mp3": 0.57,
    "whoosh-short.mp3": 0.57,
    "whoosh-cinematic.mp3": 5.54,
    "pop.mp3": 0.72,
    "impact-bass-1.mp3": 2.12,
    "impact-bass-2.mp3": 2.59,
    "sparkle.mp3": 1.8,
    "riser.mp3": 10.03,
    "chime.mp3": 2.5,
    "ping.mp3": 1.32,
    "click.mp3": 0.37,
    "click-soft.mp3": 0.37,
    "notification.mp3": 2.46,
    "glitch-1.mp3": 2.64,
    "glitch-2.mp3": 3.5,
    "glitch-3.mp3": 3.1,
    "error.mp3": 1.62,
    "typing.mp3": 1.5,
    "key-press.mp3": 0.4,
}
DEFAULT_SFX = ["whoosh.mp3", "whoosh-short.mp3", "pop.mp3", "impact-bass-1.mp3", "sparkle.mp3", "riser.mp3"]

# Área segura da tela 1080x1920 (references/safe-zone.md). Fora dela a interface do Instagram/TikTok/
# Shorts cobre o vídeo, ou o celular corta: em tela alta (iPhone 16, Android 20:9) o Instagram dá zoom
# para preencher a altura e perde ~100 px de cada lado. O template encaixa tudo aqui dentro sozinho.
SAFE_ZONE = {
    "top": 300,  # barra de status, Dynamic Island e cabeçalho "Reels" (o feed 4:5 também corta 285 px)
    "bottom": 1440,  # @ do perfil, legenda do post, música e barra de navegação
    "left": 120,  # corte lateral em celular alto
    "right": 960,
    "railX": 860,  # coluna de botões (curtir, comentar, compartilhar, áudio) à direita...
    "railY": 900,  # ...da metade da tela para baixo
    "capTop": 1170,  # topo da faixa das legendas (os outros textos ficam acima dela)
}


def die(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, cwd=None, env=None, check=True, capture=False):
    """Roda um comando mostrando o que está rodando."""
    shown = " ".join(str(c) for c in cmd)
    print(f"$ {shown}", file=sys.stderr)
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    res = subprocess.run(
        [str(c) for c in cmd],
        cwd=cwd,
        env=full_env,
        text=True,
        capture_output=capture,
    )
    if check and res.returncode != 0:
        if capture:
            sys.stderr.write((res.stdout or "") + (res.stderr or ""))
        die(f"comando falhou ({res.returncode}): {shown}")
    return res


def need(binary, hint):
    if not shutil.which(binary):
        die(f"'{binary}' não encontrado. {hint}")


def work_paths(work):
    work = Path(work).expanduser().resolve()
    return {
        "work": work,
        "source": work / "source",
        "original": work / "source" / "original.mp4",
        "audio": work / "source" / "audio16k.wav",
        "transcript": work / "source" / "transcript.json",
        "transcript_txt": work / "source" / "transcript.txt",
        "project": work / "project",
        "assets": work / "project" / "assets",
        "clip": work / "project" / "clip.json",
        "captions": work / "project" / "captions.json",
        "config": work / "project" / "config.json",
    }


def ffprobe_json(path):
    need("ffprobe", "Instale o FFmpeg (ele traz o ffprobe).")
    res = run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", path],
        capture=True,
    )
    return json.loads(res.stdout)


def video_info(path):
    info = ffprobe_json(path)
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if not v:
        die(f"sem faixa de vídeo em {path}")
    return {
        "width": int(v["width"]),
        "height": int(v["height"]),
        "duration": float(info["format"]["duration"]),
        "has_audio": any(s.get("codec_type") == "audio" for s in info.get("streams", [])),
    }


def find_sfx_dir(project=None):
    """Acha a pasta de efeitos sonoros que vem dentro do pacote npm do HyperFrames."""
    rel = Path("node_modules/hyperframes/dist/skills/media-use/audio/assets/sfx")
    candidates = []
    if project:
        candidates.append(Path(project) / rel)
    npm_cache = Path.home() / ".npm" / "_npx"
    if npm_cache.exists():
        candidates += sorted(npm_cache.glob("*/" + str(rel)), key=lambda p: p.stat().st_mtime, reverse=True)
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidates += list((Path(local_app) / "npm-cache" / "_npx").glob("*/" + str(rel)))
    for c in candidates:
        if (c / "whoosh.mp3").exists():
            return c
    return None


def detect_pauses(media, start, end, min_dur=0.12):
    """Pausas no áudio entre start e end (s, tempo do arquivo). O limite de silêncio sai do próprio áudio:
    fica entre o ruído de fundo (10% mais baixos) e a fala (10% mais altos), então funciona com voz alta,
    baixa ou com chiado. Devolve (pausas, limite_db)."""
    import re as _re

    dur = max(0.1, end - start)
    stats = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(media), "-vn",
         "-af", "aresample=16000,asetnsamples=n=800:p=0,astats=metadata=1:reset=1,"
                "ametadata=print:key=lavfi.astats.Overall.RMS_level", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    levels = sorted(-90.0 if "inf" in x else float(x) for x in _re.findall(r"RMS_level=(-?inf|-?[0-9.]+)", stats))
    if len(levels) >= 10:
        noise, speech = levels[int(len(levels) * 0.1)], levels[int(len(levels) * 0.9)]
        thr = noise + 0.35 * (speech - noise)
    else:
        thr = -32.0
    thr = max(-65.0, min(-20.0, round(thr)))
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(media), "-vn",
         "-af", f"silencedetect=noise={thr}dB:d={min_dur}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) + start for x in _re.findall(r"silence_start: (-?[0-9.]+)", res)]
    ends = [float(x) + start for x in _re.findall(r"silence_end: (-?[0-9.]+)", res)]
    if len(ends) < len(starts):
        ends.append(end)
    return [(max(start, a), b) for a, b in zip(starts, ends)], thr


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
