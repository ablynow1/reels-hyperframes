#!/usr/bin/env python3
"""Tira quadros do vídeo original para OLHAR antes de decidir.

Modos:
  overview -> 20 quadros espalhados pelo vídeo todo (tem alguém falando pra câmera? tem tela sobreposta?)
  grid   -> quadros com uma grade de 10% (achar o centro do rosto ou a região da tela para o corte 9:16)
  crop   -> quadros já cortados em 9:16 com --center (conferir o enquadramento)
  range  -> 1 quadro por segundo num intervalo (ver se há texto/tela sobreposta, gesto, corte)

Uso:
  python3 frames.py <pasta> overview
  python3 frames.py <pasta> grid  --at 30,120,300
  python3 frames.py <pasta> crop  --at 30,120,300 --center 0.52
  python3 frames.py <pasta> range --from 440 --to 465
Saída: <pasta>/source/frames_<modo>.jpg
"""

import argparse
import math

from common import die, need, run, video_info, work_paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("mode", choices=["overview", "grid", "crop", "range"])
    ap.add_argument("--at", default="")
    ap.add_argument("--center", type=float, default=0.5)
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float, default=0)
    a = ap.parse_args()
    need("ffmpeg", "Instale o FFmpeg.")
    p = work_paths(a.work)
    info = video_info(p["original"])
    W, H = info["width"], info["height"]
    out = p["source"] / f"frames_{a.mode}.jpg"

    if a.mode == "overview":
        n, cols = 20, 5
        step = info["duration"] / n
        run(["ffmpeg", "-v", "error", "-y", "-i", p["original"],
             "-vf", f"fps=1/{step:.3f},scale=256:-2,tile={cols}x{n // cols}:padding=3:color=white", "-frames:v", "1", out])
        print(f"1 quadro a cada {step:.0f} s. Confira: tem uma pessoa falando pra câmera? Se não (tela gravada, slides),"
              " siga references/screen-recording.md e avise a pessoa antes.")
    elif a.mode == "range":
        if a.t1 <= a.t0:
            die("use --from e --to (em segundos).")
        n = int(math.ceil(a.t1 - a.t0))
        cols = 5
        rows = int(math.ceil(n / cols))
        run(["ffmpeg", "-v", "error", "-y", "-ss", a.t0, "-t", a.t1 - a.t0, "-i", p["original"],
             "-vf", f"fps=1,scale=256:-2,tile={cols}x{rows}:padding=3:color=white", "-frames:v", "1", out])
    else:
        times = [float(t) for t in a.at.split(",") if t.strip()]
        if not times:
            die("use --at com tempos em segundos, ex.: --at 30,120,300")
        tiles = []
        for i, t in enumerate(times):
            f = p["source"] / f"_f{i}.png"
            if a.mode == "grid":
                vf = f"drawgrid=w=iw/10:h=ih:t=3:c=red@0.7,scale=480:-2"
            else:
                if W / H > 9 / 16:
                    cw = int(round(H * 9 / 16 / 2) * 2)
                    x = int(max(0, min(W - cw, round(a.center * W - cw / 2))))
                    vf = f"crop={cw}:{H}:{x}:0,scale=270:-2"
                else:
                    ch = int(round(W * 16 / 9 / 2) * 2)
                    y = int(max(0, (H - ch) / 2))
                    vf = f"crop={W}:{ch}:0:{y},scale=270:-2"
            run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", p["original"], "-frames:v", "1", "-vf", vf, f])
            tiles.append(f)
        inputs = []
        for f in tiles:
            inputs += ["-i", f]
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"hstack=inputs={len(tiles)}" if len(tiles) > 1 else "null", out])
        for f in tiles:
            f.unlink(missing_ok=True)
        if a.mode == "grid":
            print("Cada linha vermelha = 10% da largura. Estime o centro do rosto (ex.: 0.52) e use em --center.")
    print(f"Quadros: {out}")


if __name__ == "__main__":
    main()
