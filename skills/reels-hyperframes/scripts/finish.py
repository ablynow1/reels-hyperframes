#!/usr/bin/env python3
"""Acabamento opcional (inspirado no pdoom-video): borrão de movimento e grão de filme.

- Borrão de movimento: cada quadro final (30 fps) vira a média de 2 quadros de um render a 60 fps.
  Socos de câmera, giros 3D e entradas rápidas ganham rastro em vez de "pular". (O pdoom-video usa até
  324 subquadros por quadro; o HyperFrames vai até 60 fps, então aqui é a versão leve.)
- Grão: ruído fino que muda a cada quadro, dá textura de filme e disfarça imagem suavizada (vídeo 720p).

Uso:
  python3 hf.py <pasta> render -f 60 -q high -w 2 -o renders/reel60.mp4
  python3 finish.py <pasta> --blur --grain 5
Saída: project/renders/reel_final.mp4
"""

import argparse

from common import die, need, run, video_info, work_paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--blur", action="store_true", help="borrão de movimento (precisa de render a 60 fps)")
    ap.add_argument("--grain", type=float, default=0, help="força do grão (4 a 8 fica sutil; 0 desliga)")
    ap.add_argument("--in", dest="src", default=None, help="padrão: renders/reel60.mp4 com --blur, senão renders/reel.mp4")
    ap.add_argument("--out", default="renders/reel_final.mp4")
    a = ap.parse_args()
    need("ffmpeg", "Instale o FFmpeg.")
    p = work_paths(a.work)
    src = p["project"] / (a.src or ("renders/reel60.mp4" if a.blur else "renders/reel.mp4"))
    if not src.exists():
        die(f"não achei {src}" + (" — renderize antes com -f 60 -o renders/reel60.mp4" if a.blur else ""))
    if not a.blur and a.grain <= 0:
        die("nada a fazer: use --blur e/ou --grain")

    filters = []
    if a.blur:
        info = video_info(src)
        fps_probe = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src], capture=True).stdout.strip()
        num, den = (fps_probe.split("/") + ["1"])[:2]
        fps = float(num) / float(den or 1)
        if fps < 50:
            die(f"o vídeo está a {fps:.0f} fps; para o borrão renderize com -f 60")
        filters.append("tmix=frames=2:weights='1 1',fps=30")
    if a.grain > 0:
        filters.append(f"noise=c0s={a.grain:g}:c0f=t+u")
    filters.append("format=yuv420p")
    out = p["project"] / a.out
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", ",".join(filters),
         "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-movflags", "+faststart", "-c:a", "copy", out])
    info = video_info(out)
    print(f"Pronto: {out}  ({info['width']}x{info['height']}, {info['duration']:.2f} s)")


if __name__ == "__main__":
    main()
