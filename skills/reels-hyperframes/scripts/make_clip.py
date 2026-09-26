#!/usr/bin/env python3
"""Monta o corte: junta os pedaços escolhidos, reenquadra em 9:16 e prepara a voz.

Gera:
  project/assets/footage.mp4  (vídeo vertical, sem áudio)
  project/assets/voice.m4a    (voz com volume padronizado em -14 LUFS)
  project/clip.json           (pedaços, deslocamentos, duração, cor de fundo sugerida)

Uso:
  python3 make_clip.py <pasta> --pieces "445.05-450.88,453.52-462.55" --center 0.52
  (--center = centro do corte na largura do vídeo, de 0 a 1; ou --crop-x em pixels)
"""

import argparse
import math

from common import die, need, run, save_json, video_info, work_paths


def parse_pieces(s):
    out = []
    for part in s.split(","):
        a, b = part.strip().split("-")
        a, b = float(a), float(b)
        if b <= a:
            die(f"pedaço inválido: {part}")
        out.append((a, b))
    out.sort()
    return out


def sample_fill(footage, w, h):
    """Cor média dos dois cantos de cima (costuma ser a parede) — usada atrás do recorte."""
    import subprocess

    colors = []
    for x in (8, w - 88):
        res = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(footage), "-frames:v", "1",
             "-vf", f"crop=80:{int(h * 0.15)}:{x}:{int(h * 0.2)},scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True,
        )
        if len(res.stdout) >= 3:
            colors.append(tuple(res.stdout[:3]))
    if not colors:
        return "#cccccc"
    r, g, b = (sum(c[i] for c in colors) // len(colors) for i in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--pieces", required=True, help='ex.: "445.05-450.88,453.52-462.55"')
    ap.add_argument("--center", type=float, default=None, help="centro do corte (0 a 1 da largura)")
    ap.add_argument("--crop-x", type=int, default=None, help="x do corte em pixels (alternativa ao --center)")
    ap.add_argument("--size", default="720x1280", help="tamanho intermediário (o render final é 1080x1920)")
    a = ap.parse_args()
    need("ffmpeg", "Instale o FFmpeg.")
    p = work_paths(a.work)
    if not p["assets"].exists():
        die("rode setup_project.py antes.")
    pieces = parse_pieces(a.pieces)
    info = video_info(p["original"])
    W, H = info["width"], info["height"]
    ow, oh = (int(x) for x in a.size.lower().split("x"))

    # reenquadramento
    if W / H > 9 / 16 + 0.01:
        cw = int(round(H * 9 / 16 / 2) * 2)
        if a.crop_x is not None:
            x = a.crop_x
        else:
            c = 0.5 if a.center is None else a.center
            x = round(c * W - cw / 2)
        x = int(max(0, min(W - cw, x)))
        crop = f"crop={cw}:{H}:{x}:0,"
        crop_info = {"w": cw, "h": H, "x": x, "y": 0}
        scale_factor = oh / H
    elif W / H < 9 / 16 - 0.01:
        ch = int(round(W * 16 / 9 / 2) * 2)
        y = int(max(0, (H - ch) / 2))
        crop = f"crop={W}:{ch}:0:{y},"
        crop_info = {"w": W, "h": ch, "x": 0, "y": y}
        scale_factor = ow / W
    else:
        crop, crop_info, scale_factor = "", {"w": W, "h": H, "x": 0, "y": 0}, oh / H
    sharpen = ",unsharp=5:5:0.6" if scale_factor > 1.3 else ""

    t0 = max(0.0, pieces[0][0] - 1.0)
    t_end = pieces[-1][1] + 0.5
    parts, labels, offsets, total = [], [], [], 0.0
    for i, (a0, b0) in enumerate(pieces):
        s, e = a0 - t0, b0 - t0
        d = b0 - a0
        fade = min(0.02, d / 4)
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(
            f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={d - fade:.3f}:d={fade:.3f}[a{i}]"
        )
        labels.append(f"[v{i}][a{i}]")
        offsets.append(round(total, 3))
        total += d
    fc = ";".join(parts)
    fc += f";{''.join(labels)}concat=n={len(pieces)}:v=1:a=1[v][a]"
    fc += f";[v]{crop}scale={ow}:{oh}:flags=lanczos{sharpen},fps=30,format=yuv420p[vout]"
    fc += ";[a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

    footage, voice = p["assets"] / "footage.mp4", p["assets"] / "voice.m4a"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{t_end - t0:.3f}", "-i", p["original"],
         "-filter_complex", fc,
         "-map", "[vout]", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-an", footage,
         "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", voice])

    fdur = video_info(footage)["duration"]
    duration = math.floor(min(fdur, total) * 100) / 100 - 0.01
    fill = sample_fill(footage, ow, oh)
    save_json(p["clip"], {
        "pieces": [[a0, b0] for a0, b0 in pieces],
        "offsets": offsets,
        "duration": round(duration, 2),
        "fill": fill,
        "crop": crop_info,
        "source": {"width": W, "height": H},
        "size": [ow, oh],
    })
    print(f"\nCorte pronto: {duration:.2f} s em {len(pieces)} pedaço(s) · cor de fundo sugerida {fill}")
    print(f"  {footage}\n  {voice}\n  {p['clip']}")
    if duration > 16.5:
        print("  AVISO: passou de ~16 s; para Reels curto, tire uma frase ou uma pausa.")


if __name__ == "__main__":
    main()
