#!/usr/bin/env python3
"""Revisão automática nas trocas de efeito (ideia do `sheet --cuts` do pdoom-video).

Lê o config.json e escolhe sozinho os momentos que mais quebram: entrada e saída de cada efeito,
socos de câmera e o fim. Assim nenhuma transição fica sem ser olhada.

Além da folha normal, monta a folha "celular": os mesmos quadros com a área segura marcada —
faixas vermelhas onde a interface do Instagram cobre o vídeo (topo, base, coluna de botões) ou onde
o celular alto (iPhone 16 etc.) corta as laterais. Nenhum texto, número ou cartão pode encostar nelas.

Uso:
  python3 review.py <pasta>            -> snapshot do HyperFrames nesses tempos (antes do render)
  python3 review.py <pasta> --render   -> quadros do vídeo renderizado nesses tempos (depois do render)
Saída: project/snaps_review/contact-sheet.jpg + celular.jpg
   ou  project/renders/revisao_trocas.jpg + revisao_celular.jpg
"""

import argparse
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

from common import SAFE_ZONE, die, load_json, need, run, work_paths


def moments(cfg, D):
    E = cfg.get("effects", {})
    t = {0.25}
    items = [(n, e) for n, v in E.items() for e in (v if isinstance(v, list) else [v] if v else [])]
    for name, eff in items:
        for st in eff.get("steps", []):
            t.add(st + 0.4)
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


def safe_overlay(safe=SAFE_ZONE, w=1080, h=1920):
    """Filtro do FFmpeg que pinta de vermelho o que fica fora da área segura (references/safe-zone.md)."""
    s = safe
    red = "red@0.32"
    boxes = [
        (0, 0, w, s["top"]),  # status, Dynamic Island, cabeçalho "Reels"
        (0, s["bottom"], w, h - s["bottom"]),  # @ do perfil, legenda do post, música
        (0, s["top"], s["left"], s["bottom"] - s["top"]),  # corte lateral em celular alto
        (s["right"], s["top"], w - s["right"], s["bottom"] - s["top"]),
        (s["railX"], s["railY"], s["right"] - s["railX"], s["bottom"] - s["railY"]),  # botões
    ]
    f = [f"drawbox=x={x}:y={y}:w={bw}:h={bh}:color={red}:t=fill" for x, y, bw, bh in boxes]
    f.append(f"drawbox=x=0:y={s['capTop']}:w={w}:h=4:color=yellow@0.85:t=fill")  # topo da faixa das legendas
    return ",".join(f)


def contact_sheet(inputs, out, phone=False, cols=6):
    """Uma folha com um quadro por entrada (cada entrada = argumentos de entrada do FFmpeg)."""
    tmp = out.parent / f"_{out.stem}"
    tmp.mkdir(parents=True, exist_ok=True)
    vf = (safe_overlay() + "," if phone else "") + "scale=216:-2"
    for i, args in enumerate(inputs):
        run(["ffmpeg", "-v", "error", "-y", *args, "-frames:v", "1", "-vf", vf, tmp / f"{i:03d}.png"])
    rows = int(math.ceil(len(inputs) / cols))
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", tmp / "%03d.png",
         "-vf", f"tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", out])
    shutil.rmtree(tmp, ignore_errors=True)


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
    need("ffmpeg", "Instale o FFmpeg.")

    if not a.render:
        hf = Path(__file__).with_name("hf.py")
        snaps = p["project"] / "snaps_review"
        started = time.time() - 1
        code = subprocess.run([sys.executable, str(hf), str(p["work"]), "snapshot", "--at", ",".join(f"{x:g}" for x in ts),
                               "--no-end", "-o", "snaps_review"]).returncode
        sheets = sorted(snaps.glob("contact-sheet*.jpg"))
        # só os quadros desta rodada (a pasta pode ter quadros de revisões anteriores)
        frames = sorted(f for f in snaps.glob("frame-*.png") if f.stat().st_mtime >= started)
        if frames:
            contact_sheet([["-i", f] for f in frames], snaps / "celular.jpg", phone=True)
            sheets.append(snaps / "celular.jpg")
        print("\nFolha(s): " + "  ".join(str(x) for x in sheets) + "  (na ordem dos tempos acima)")
        if frames:
            print("celular.jpg: faixa vermelha = a interface cobre ou o celular corta; linha amarela = topo das legendas."
                  " Nada de texto, número ou cartão encostando no vermelho.")
        sys.exit(code)

    video = p["project"] / a.video
    if not video.exists():
        die(f"não achei {video}")
    inputs = [["-ss", f"{t:.3f}", "-i", video] for t in ts]
    out = p["project"] / "renders" / "revisao_trocas.jpg"
    phone = p["project"] / "renders" / "revisao_celular.jpg"
    contact_sheet(inputs, out)
    contact_sheet(inputs, phone, phone=True)
    print(f"\nFolhas: {out}\n        {phone}  (na ordem dos tempos acima, 6 por linha; vermelho = fora da área segura)")


if __name__ == "__main__":
    main()
