#!/usr/bin/env python3
"""Mostra as palavras (com tempo) e as pausas de um intervalo do vídeo original.
Serve para escolher pontos de corte exatos, sempre dentro de uma pausa.

Uso:
  python3 words.py <pasta-de-trabalho> <inicio_s> <fim_s>
"""

import re
import subprocess
import sys

from common import die, load_json, need, work_paths


def main():
    if len(sys.argv) != 4:
        die(__doc__)
    p = work_paths(sys.argv[1])
    a, b = float(sys.argv[2]), float(sys.argv[3])
    words = load_json(p["transcript"])
    if not words:
        die("rode transcribe.py antes.")
    print(f"Palavras entre {a:.2f}s e {b:.2f}s:")
    line = []
    for w in words:
        if a <= w["start"] <= b:
            line.append(f"{w['text']}[{w['start']:.2f}-{w['end']:.2f}]")
            if w["text"].endswith((".", "?", "!", ",")) or len(line) >= 8:
                print("  " + " ".join(line))
                line = []
    if line:
        print("  " + " ".join(line))

    need("ffmpeg", "Instale o FFmpeg.")
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", str(a), "-t", str(b - a), "-i", str(p["original"]), "-vn", "-af", "silencedetect=noise=-32dB:d=0.12", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    starts = [float(x) + a for x in re.findall(r"silence_start: ([0-9.]+)", res.stderr)]
    ends = [float(x) + a for x in re.findall(r"silence_end: ([0-9.]+)", res.stderr)]
    print("\nPausas (bons pontos de corte):")
    for s, e in zip(starts, ends):
        print(f"  {s:.2f} -> {e:.2f}  ({e - s:.2f}s)")
    if not starts:
        print("  nenhuma pausa clara — corte entre palavras, usando o fim de uma e o começo da próxima.")
    print("\nObs.: o Whisper às vezes estica uma palavra por cima de uma pausa; confie mais nas pausas acima.")


if __name__ == "__main__":
    main()
