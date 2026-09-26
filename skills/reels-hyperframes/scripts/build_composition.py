#!/usr/bin/env python3
"""Gera project/index.html a partir do modelo da skill + project/config.json.

- legendas: "captions" no config (lista) ou, se faltar, project/captions.json
- duração e cor de fundo: do config ou do clip.json
- efeitos sonoros: "sfx": "auto" (padrão) monta o som a partir dos efeitos; ou uma lista manual
- valida tempos e sobreposições antes de gerar

Uso:
  python3 build_composition.py <pasta-de-trabalho>
"""

import json
import re
import shutil
import sys

from common import SFX_DURATIONS, SKILL_DIR, die, find_sfx_dir, load_json, work_paths

SCENE_EFFECTS = ("glass", "frame")


def auto_sfx(cfg, D):
    E = cfg.get("effects", {})
    cam = cfg.get("camera", {})
    punches = sorted(cam.get("punches", []))
    plan = [("whoosh.mp3", 0.0, 0.3)]
    for b in (E.get("bubbles") or {}).get("items", []):
        plan.append(("pop.mp3", b["at"], 0.28))
    if E.get("bigSymbol"):
        plan.append(("whoosh-short.mp3", E["bigSymbol"]["in"] - 0.04, 0.3))
    for t in punches:
        plan.append(("impact-bass-1.mp3", t, 0.42))
    if punches and punches[-1] - 10.03 >= 0.5:
        plan.append(("riser.mp3", punches[-1] - 10.03, 0.12))
    if E.get("bigWord") and not any(abs(t - E["bigWord"]["at"]) < 0.1 for t in punches):
        plan.append(("whoosh.mp3", E["bigWord"]["at"], 0.3))
    if E.get("glass"):
        plan.append(("whoosh.mp3", E["glass"]["in"] - 0.05, 0.32))
        plan.append(("whoosh-short.mp3", E["glass"]["out"], 0.28))
    if E.get("frame"):
        for c in E["frame"].get("cards", []):
            plan.append(("pop.mp3", c["at"], 0.28))
        plan.append(("whoosh-short.mp3", E["frame"]["out"] - 0.02, 0.3))
    if E.get("ring"):
        R = E["ring"]
        end = (R.get("drawAt", R["in"] + 0.05)) + R.get("drawDur", 1.15)
        plan.append(("sparkle.mp3", end - 0.15, 0.28))
    out = []
    for f, t, v in sorted(plan, key=lambda x: x[1]):
        t = round(max(0.0, t), 2)
        if t >= D - 0.1:
            continue
        if any(o["file"] == f and abs(o["at"] - t) < 0.1 for o in out):
            continue
        out.append({"file": f, "at": t, "vol": v})
    return out


def validate(cfg, D):
    warn = []
    E = cfg.get("effects", {})

    def chk(name, t):
        if t is None:
            return
        if t < 0 or t > D:
            warn.append(f"{name} = {t} está fora do vídeo (0–{D})")

    for name, eff in E.items():
        if not eff:
            continue
        for k in ("in", "out", "at", "cardIn", "subAt", "drawAt", "alertAt", "panelOut"):
            chk(f"{name}.{k}", eff.get(k))
        for i, it in enumerate(eff.get("items", []) + eff.get("cards", [])):
            chk(f"{name}[{i}].at", it.get("at"))
        if "in" in eff and "out" in eff and eff["out"] <= eff["in"]:
            warn.append(f"{name}: out ({eff['out']}) tem que ser depois de in ({eff['in']})")
    # efeitos que mexem na cena inteira não podem se sobrepor
    ret = {"glass": 0.37, "frame": 0.3}  # tempo que a cena leva para voltar ao normal
    spans = sorted((E[k]["in"], E[k]["out"] + ret[k], k) for k in SCENE_EFFECTS if E.get(k))
    for (a0, a1, ka), (b0, b1, kb) in zip(spans, spans[1:]):
        if b0 < a1 - 0.01:
            warn.append(f"'{ka}' e '{kb}' se sobrepõem: '{kb}' tem que começar em {a1:.2f} s ou depois")
    punches = sorted(cfg.get("camera", {}).get("punches", []))
    for x, y in zip(punches, punches[1:]):
        if y - x < 1.0:
            warn.append(f"socos de câmera muito perto ({x} e {y}); deixe pelo menos 1 s")
    for t in punches:
        chk("camera.punches", t)
    caps = cfg.get("captions", [])
    for i, g in enumerate(caps):
        if g["e"] <= g["s"]:
            warn.append(f"legenda {i} termina antes de começar")
        if len(" ".join(w[0] for w in g["w"])) > (13 if g.get("big") else 16):
            warn.append(f"legenda {i} ('{' '.join(w[0] for w in g['w'])}') pode quebrar em 2 linhas; divida o bloco")
    return warn


def main():
    if len(sys.argv) != 2:
        die(__doc__)
    p = work_paths(sys.argv[1])
    cfg = load_json(p["config"])
    if cfg is None:
        die(f"não achei {p['config']} — crie o config.json (veja references/effects.md e assets/config.example.json).")
    clip = load_json(p["clip"], {})
    D = float(cfg.get("duration") or clip.get("duration") or 0)
    if D <= 0:
        die("sem duração: rode make_clip.py ou coloque \"duration\" no config.json")
    cfg["duration"] = D
    fill = cfg.get("fill") or clip.get("fill") or "#cccccc"
    if not re.match(r"^#[0-9a-fA-F]{6}$", fill):
        die(f"cor de fundo inválida: {fill}")

    caps = cfg.get("captions")
    if caps is None or isinstance(caps, str):
        caps_path = p["project"] / (caps or "captions.json")
        caps = load_json(caps_path)
        if caps is None:
            die("sem legendas: rode build_captions.py (ou coloque \"captions\" no config.json)")
    cfg["captions"] = caps

    for need_file in ("footage.mp4", "voice.m4a", "person.webm", "plate.webm"):
        if not (p["assets"] / need_file).exists():
            print(f"AVISO: falta assets/{need_file}", file=sys.stderr)

    sfx = cfg.get("sfx", "auto")
    if sfx == "auto":
        sfx = auto_sfx(cfg, D)
    sfx_dir = p["assets"] / "sfx"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    src_dir = None
    lines, kept = [], []
    for i, s in enumerate(sfx):
        f = s["file"]
        if not (sfx_dir / f).exists():
            src_dir = src_dir or find_sfx_dir(p["project"])
            if src_dir and (src_dir / f).exists():
                shutil.copy2(src_dir / f, sfx_dir / f)
            else:
                print(f"AVISO: efeito sonoro '{f}' não encontrado; pulando", file=sys.stderr)
                continue
        at = round(float(s["at"]), 2)
        dur = round(min(SFX_DURATIONS.get(f, 1.0), D - at), 2)
        if dur <= 0.05:
            continue
        sid = "sfx-" + re.sub(r"[^a-z0-9]+", "-", f.lower().rsplit(".", 1)[0]) + f"-{i}"
        lines.append(
            f'      <audio id="{sid}" src="assets/sfx/{f}" data-start="{at}" data-duration="{dur}" data-volume="{s.get("vol", 0.3)}"></audio>'
        )
        kept.append(s)

    warnings = validate(cfg, D)
    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = (
        template.replace("__DURATION__", f"{D}")
        .replace("__FILL__", fill)
        .replace("__SFX__", "\n".join(lines))
        .replace("__CONFIG__", json.dumps({k: v for k, v in cfg.items() if k != "sfx"}, ensure_ascii=False))
    )
    (p["project"] / "index.html").write_text(html, encoding="utf-8")

    E = cfg.get("effects", {})
    print(f"index.html gerado · {D:.2f} s · {len(caps)} legendas · {len(kept)} efeitos sonoros")
    print("  efeitos visuais: " + (", ".join(k for k, v in E.items() if v) or "nenhum"))
    if warnings:
        print("\nAVISOS:")
        for w in warnings:
            print("  - " + w)
    print("\nPróximo: cd project && npx hyperframes check")


if __name__ == "__main__":
    main()
