#!/usr/bin/env python3
"""Folha de contato de um vídeo (vários quadros numa imagem) para revisar o render.

Uso:
  python3 sheet.py <video.mp4> [--fps 2] [--from 0] [--to 0] [--cols 6] [--out folha.jpg]
"""

import argparse
import math
from pathlib import Path

from common import need, run, video_info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--fps", type=float, default=2)
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float, default=0)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--width", type=int, default=180)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    need("ffmpeg", "Instale o FFmpeg.")
    v = Path(a.video)
    dur = video_info(v)["duration"]
    t1 = a.t1 if a.t1 > a.t0 else dur
    n = max(1, int(math.ceil((t1 - a.t0) * a.fps)))
    rows = int(math.ceil(n / a.cols))
    tag = f"_{a.t0:g}-{t1:g}s" if (a.t0 > 0 or a.t1 > a.t0) else ""
    out = Path(a.out) if a.out else v.with_name(f"{v.stem}_folha{tag}.jpg")
    run(["ffmpeg", "-v", "error", "-y", "-ss", a.t0, "-t", t1 - a.t0, "-i", v,
         "-vf", f"fps={a.fps},scale={a.width}:-2,tile={a.cols}x{rows}:padding=4:color=white", "-frames:v", "1", out])
    print(f"Folha: {out}  ({n} quadros, {a.fps}/s, de {a.t0:.1f}s a {t1:.1f}s)")


if __name__ == "__main__":
    main()
