#!/usr/bin/env python3
"""Mostra as palavras (com tempo) e as pausas de um intervalo do vídeo original.
Serve para escolher pontos de corte exatos, sempre dentro de uma pausa.

Uso:
  python3 words.py <pasta-de-trabalho> <inicio_s> <fim_s>
"""

import sys

from common import detect_pauses, die, load_json, need, work_paths


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
    pauses, thr = detect_pauses(p["original"], a, b)
    print(f"\nPausas (bons pontos de corte; silêncio abaixo de {thr:.0f} dB):")
    for s, e in pauses:
        print(f"  {s:.2f} -> {e:.2f}  ({e - s:.2f}s)")
    if not pauses:
        print("  nenhuma pausa clara — corte entre palavras, usando o fim de uma e o começo da próxima.")
    print("\nObs.: o Whisper às vezes estica uma palavra por cima de uma pausa; confie mais nas pausas acima.")


if __name__ == "__main__":
    main()
