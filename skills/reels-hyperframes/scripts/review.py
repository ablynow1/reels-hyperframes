#!/usr/bin/env python3
"""Revisão automática nas trocas de efeito (ideia do `sheet --cuts` do pdoom-video).

Lê o config.json e escolhe sozinho os momentos que mais quebram: entrada e saída de cada efeito,
socos de câmera e o fim. Assim nenhuma transição fica sem ser olhada.

Uso:
  python3 review.py <pasta>            -> snapshot do HyperFrames nesses tempos (antes do render)
  python3 review.py <pasta> --render   -> quadros do vídeo renderizado nesses tempos (depois do render)
Saída: project/snaps_review/contact-sheet.jpg  ou  project/renders/revisao_trocas.jpg
"""

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

from common import die, load_json, need, run, work_paths


def moments(cfg, D):
    E = cfg.get("effects", {})
    t = {0.25}
    for name, eff in E.items():
        if not eff:
            continue
        if "in" in eff:
            t |= {eff["in"] + 0.15, eff["in"] + 0.6}
        if "out" in eff:
            t |= {eff["out"] - 0.1, eff["out"] + 0.25}
        if "at" in eff:
            t |= {eff["at"] + 0.1}
        for it in eff.get("items", []) + eff.get("cards", []):
            t.add(it["at"] + 0.35)
        if name == "ring":
            t.add((eff.get("drawAt", eff["in"]) + eff.get("drawDur", 1.15)))
    for p in cfg.get("camera", {}).get("punches", []):
        t.add(p + 0.08)
    t.add(D - 0.1)
    out = []
    for x in sorted(round(x, 2) for x in t if 0 <= x < D):
        if not out or x - out[-1] >= 0.15:  # tempos quase iguais mostram o mesmo quadro
            out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--render", action="store_true", help="usar o vídeo renderizado")
    ap.add_argument("--video", default="renders/reel.mp4")
    a = ap.parse_args()
    p = work_paths(a.work)
    cfg = load_json(p["config"])
    if not cfg:
        die("sem config.json")
    D = float(cfg.get("duration") or load_json(p["clip"], {}).get("duration") or 0)
    ts = moments(cfg, D)
    print(f"{len(ts)} momentos: " + ", ".join(f"{x:g}" for x in ts))

    if not a.render:
        hf = Path(__file__).with_name("hf.py")
        code = subprocess.run([sys.executable, str(hf), str(p["work"]), "snapshot", "--at", ",".join(f"{x:g}" for x in ts),
                               "--no-end", "-o", "snaps_review"]).returncode
        print(f"\nFolha: {p['project'] / 'snaps_review' / 'contact-sheet.jpg'}  (na ordem dos tempos acima)")
        sys.exit(code)

    need("ffmpeg", "Instale o FFmpeg.")
    video = p["project"] / a.video
    if not video.exists():
        die(f"não achei {video}")
    tmp = p["project"] / "renders" / "_rev"
    tmp.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, t in enumerate(ts):
        f = tmp / f"{i:03d}.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", "scale=216:-2", f])
        frames.append(f)
    cols = 6
    rows = int(math.ceil(len(frames) / cols))
    out = p["project"] / "renders" / "revisao_trocas.jpg"
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", tmp / "%03d.png",
         "-vf", f"tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", out])
    for f in frames:
        os.remove(f)
    tmp.rmdir()
    print(f"\nFolha: {out}  (na ordem dos tempos acima, {cols} por linha)")


if __name__ == "__main__":
    main()
