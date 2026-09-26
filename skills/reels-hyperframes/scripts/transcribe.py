#!/usr/bin/env python3
"""Transcreve o vídeo inteiro com tempo de cada palavra.

Gera <pasta>/source/transcript.json (lista de palavras {text,start,end})
e <pasta>/source/transcript.txt (frases com tempo, para ler e escolher o trecho).

Motores, na ordem em que são tentados (--engine auto):
  mlx      -> mlx_whisper (Mac com chip Apple; rápido)
  faster   -> faster_whisper (qualquer sistema; pip install faster-whisper)
  hf       -> npx hyperframes transcribe (usa whisper.cpp; precisa do whisper-cli)

Uso:
  python3 transcribe.py <pasta-de-trabalho> [--lang pt] [--engine auto|mlx|faster|hf] [--model ...]
"""

import argparse
import importlib.util
import json
import shutil
import sys

from common import HF, die, need, run, save_json, work_paths


def extract_audio(p):
    if not p["audio"].exists():
        need("ffmpeg", "Instale o FFmpeg.")
        run(["ffmpeg", "-v", "error", "-y", "-i", p["original"], "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", p["audio"]])


def with_mlx(p, lang, model):
    import mlx_whisper

    repo = model or "mlx-community/whisper-large-v3-turbo"
    print(f"Transcrevendo com mlx_whisper ({repo})… pode levar alguns minutos.", file=sys.stderr)
    r = mlx_whisper.transcribe(str(p["audio"]), path_or_hf_repo=repo, language=lang, word_timestamps=True, verbose=False)
    words = []
    for s in r.get("segments", []):
        for w in s.get("words", []):
            t = w["word"].strip()
            if t:
                words.append({"text": t, "start": round(w["start"], 3), "end": round(w["end"], 3)})
    return words


def with_faster(p, lang, model):
    from faster_whisper import WhisperModel

    name = model or "small"
    print(f"Transcrevendo com faster-whisper ({name})… pode levar alguns minutos.", file=sys.stderr)
    m = WhisperModel(name, device="auto", compute_type="auto")
    segments, _ = m.transcribe(str(p["audio"]), language=lang, word_timestamps=True, vad_filter=False)
    words = []
    for s in segments:
        for w in s.words or []:
            t = w.word.strip()
            if t:
                words.append({"text": t, "start": round(w.start, 3), "end": round(w.end, 3)})
    return words


def with_hf(p, lang, model):
    name = model or "small"  # nunca usar modelo ".en" para fala que não é em inglês: ele traduz
    out = p["source"] / "transcript.json"
    run(HF + ["transcribe", str(p["audio"]), "--model", name, "--language", lang, "-d", str(p["source"])])
    data = json.loads(out.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("words", [])
    return [{"text": w["text"].strip(), "start": float(w["start"]), "end": float(w["end"])} for w in items if w.get("text", "").strip()]


def write_txt(words, path):
    lines, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 9
        if gap >= 0.5 or len(cur) >= 14 or w["text"].endswith((".", "?", "!")):
            lines.append(f"[{cur[0]['start']:7.2f} - {cur[-1]['end']:7.2f}] " + " ".join(x["text"] for x in cur))
            cur = []
    if cur:
        lines.append(f"[{cur[0]['start']:7.2f} - {cur[-1]['end']:7.2f}] " + " ".join(x["text"] for x in cur))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--engine", default="auto", choices=["auto", "mlx", "faster", "hf"])
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    p = work_paths(a.work)
    if not p["original"].exists():
        die(f"não achei {p['original']} — rode fetch_video.py antes.")
    extract_audio(p)

    order = [a.engine] if a.engine != "auto" else ["mlx", "faster", "hf"]
    words, used = None, None
    for eng in order:
        if eng == "mlx" and importlib.util.find_spec("mlx_whisper"):
            words, used = with_mlx(p, a.lang, a.model), "mlx_whisper"
        elif eng == "faster" and importlib.util.find_spec("faster_whisper"):
            words, used = with_faster(p, a.lang, a.model), "faster-whisper"
        elif eng == "hf" and shutil.which("whisper-cli"):
            words, used = with_hf(p, a.lang, a.model), "hyperframes/whisper.cpp"
        if words:
            break
    if not words:
        die(
            "nenhum motor de transcrição disponível. Instale um: "
            "Mac com chip Apple -> pip3 install mlx-whisper; outros -> pip3 install faster-whisper; "
            "ou instale o whisper.cpp (brew install whisper-cpp)."
        )
    save_json(p["transcript"], words)
    write_txt(words, p["transcript_txt"])
    print(f"\nOK ({used}): {len(words)} palavras")
    print(f"  {p['transcript']}\n  {p['transcript_txt']}  <- leia este para escolher o trecho")


if __name__ == "__main__":
    main()
