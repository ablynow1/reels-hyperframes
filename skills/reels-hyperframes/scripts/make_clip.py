#!/usr/bin/env python3
"""Monta o corte: junta os pedaços escolhidos, reenquadra em 9:16 e prepara a voz.

Gera:
  project/assets/footage.mp4  (vídeo vertical, sem áudio)
  project/assets/voice.m4a    (voz com volume padronizado em -14 LUFS)
  project/clip.json           (pedaços, deslocamentos, duração, cor de fundo sugerida)

Os pedaços entram NA ORDEM em que você escreve (dá para trazer um gancho do fim para o começo).

Uso (pessoa falando):
  python3 make_clip.py <pasta> --pieces "445.05-450.88,453.52-462.55" --center 0.52
    --center = centro do corte na largura do vídeo (0 a 1); ou --crop-x em pixels

Opções: --denoise tira chiado/ruído de fundo leve da voz (antes de padronizar o volume).

Uso (gravação de tela, sem pessoa — veja references/screen-recording.md):
  python3 make_clip.py <pasta> --pieces "692.43-699.44,744.50-751.95" --crop 732,70,568,1010 --screen
    --crop x,y,largura,altura = região do vídeo original (fica fora barra de menu, notificações etc.)
    --screen = não há pessoa: cria as camadas plate/person direto (pule o remove-background)
"""

import argparse
import math
import subprocess

from common import die, need, run, save_json, video_info, work_paths


def parse_pieces(s):
    out = []
    for part in s.split(","):
        a, b = part.strip().split("-")
        a, b = float(a), float(b)
        if b <= a:
            die(f"pedaço inválido: {part}")
        out.append((a, b))
    return out


def sample_fill(footage, w, h):
    """Cor média dos dois cantos de cima (costuma ser a parede) — usada atrás do recorte."""
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
    ap.add_argument("--crop", default=None, help="região x,y,largura,altura do vídeo original")
    ap.add_argument("--screen", action="store_true", help="gravação de tela: sem pessoa para recortar")
    ap.add_argument("--size", default="720x1280", help="tamanho intermediário (o render final é 1080x1920)")
    ap.add_argument("--denoise", action="store_true", help="tira chiado/ruído de fundo leve da voz")
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
    if a.crop:
        try:
            cx, cy, cw, ch = (int(float(v)) for v in a.crop.split(","))
        except ValueError:
            die("--crop precisa de 4 números: x,y,largura,altura")
        cw, ch = min(cw, W - cx), min(ch, H - cy)
        # a região preenche a tela 9:16 (se a proporção não bater, corta o excesso no centro)
        crop = f"crop={cw}:{ch}:{cx}:{cy},scale={ow}:{oh}:force_original_aspect_ratio=increase:flags=lanczos,crop={ow}:{oh},"
        crop_info = {"w": cw, "h": ch, "x": cx, "y": cy}
        scale_factor = max(ow / cw, oh / ch)
        scale = ""
    elif W / H > 9 / 16 + 0.01:
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
        scale = f"scale={ow}:{oh}:flags=lanczos,"
    elif W / H < 9 / 16 - 0.01:
        ch = int(round(W * 16 / 9 / 2) * 2)
        y = int(max(0, (H - ch) / 2))
        crop = f"crop={W}:{ch}:0:{y},"
        crop_info = {"w": W, "h": ch, "x": 0, "y": y}
        scale_factor = ow / W
        scale = f"scale={ow}:{oh}:flags=lanczos,"
    else:
        crop, crop_info, scale_factor = "", {"w": W, "h": H, "x": 0, "y": 0}, oh / H
        scale = f"scale={ow}:{oh}:flags=lanczos,"
    sharpen = "unsharp=5:5:0.6," if scale_factor > 1.3 else ""

    t0 = max(0.0, min(x for x, _ in pieces) - 1.0)
    t_end = max(y for _, y in pieces) + 0.5
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
    fc += f";[v]{crop}{scale}{sharpen}fps=30,format=yuv420p[vout]"
    clean = "highpass=f=70,afftdn=nf=-28:tn=1," if a.denoise else ""
    fc += f";[a]{clean}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

    footage, voice = p["assets"] / "footage.mp4", p["assets"] / "voice.m4a"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{t_end - t0:.3f}", "-i", p["original"],
         "-filter_complex", fc,
         "-map", "[vout]", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-an", footage,
         "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", voice])

    fdur = video_info(footage)["duration"]
    duration = math.floor(min(fdur, total) * 100) / 100 - 0.01
    fill = sample_fill(footage, ow, oh)

    if a.screen:
        # Sem pessoa: o "fundo" é o próprio vídeo e a camada da pessoa fica transparente.
        run(["ffmpeg", "-v", "error", "-y", "-i", footage, "-c:v", "libvpx-vp9", "-crf", "18", "-b:v", "0",
             "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-an", p["assets"] / "plate.webm"])
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black@0.0:s={ow}x{oh}:r=30:d={fdur:.3f},format=yuva420p",
             "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", "-b:v", "0", "-crf", "40", "-an",
             "-metadata:s:v:0", "alpha_mode=1", p["assets"] / "person.webm"])

    save_json(p["clip"], {
        "pieces": [[a0, b0] for a0, b0 in pieces],
        "offsets": offsets,
        "duration": round(duration, 2),
        "fill": fill,
        "crop": crop_info,
        "screen": bool(a.screen),
        "source": {"width": W, "height": H},
        "size": [ow, oh],
    })
    print(f"\nCorte pronto: {duration:.2f} s em {len(pieces)} pedaço(s) · cor de fundo sugerida {fill}")
    print(f"  {footage}\n  {voice}\n  {p['clip']}")
    if a.screen:
        print("  Modo tela: plate.webm e person.webm já criados — PULE o remove-background.")
    if duration > 16.5:
        print("  AVISO: passou de ~16 s; para Reels curto, tire uma frase ou uma pausa.")


if __name__ == "__main__":
    main()
