#!/usr/bin/env python3
"""Gera project/index.html a partir do modelo da skill + project/config.json.

- legendas: "captions" no config (lista) ou, se faltar, project/captions.json
- duração e cor de fundo: do config ou do clip.json
- efeitos sonoros: "sfx": "auto" (padrão) monta o som a partir dos efeitos; ou uma lista manual
- valida tempos e sobreposições antes de gerar
- área segura (common.SAFE_ZONE): o modelo encaixa textos e cartões sozinho; aqui só avisa o que vai mexer

Uso:
  python3 build_composition.py <pasta-de-trabalho>
"""

import json
import re
import shutil
import sys

from common import SAFE_ZONE, SFX_DURATIONS, SKILL_DIR, die, find_sfx_dir, load_json, work_paths

SCENE_EFFECTS = ("glass", "frame")


def arr(v):
    return v if isinstance(v, list) else ([v] if v else [])


def auto_sfx(cfg, D):
    E = cfg.get("effects", {})
    cam = cfg.get("camera", {})
    punches = sorted(cam.get("punches", []))
    plan = [("whoosh.mp3", 0.0, 0.3)]
    for b in (E.get("bubbles") or {}).get("items", []):
        plan.append(("pop.mp3", b["at"], 0.28))
    for S in arr(E.get("bigSymbol")):
        plan.append(("whoosh-short.mp3", S["in"] - 0.04, 0.3))
    for t in punches:
        plan.append(("impact-bass-1.mp3", t, 0.42))
    if punches and punches[-1] - 10.03 >= 0.5:
        plan.append(("riser.mp3", punches[-1] - 10.03, 0.12))
    for W in arr(E.get("bigWord")):
        if not any(abs(t - W["at"]) < 0.1 for t in punches):
            plan.append(("whoosh.mp3", W["at"], 0.3))
    for G in arr(E.get("diagram")):
        plan.append(("whoosh.mp3", G["in"], 0.3))
        for t in G.get("steps", [])[1:]:
            plan.append(("pop.mp3", t, 0.22))
    for T in arr(E.get("table")):
        plan.append(("whoosh.mp3", T["in"], 0.3))
        n = len(T.get("rows", []))
        for k in range(n):
            t = T["rowTimes"][k] if T.get("rowTimes") and k < len(T["rowTimes"]) else T.get("rowStart", T["in"] + 0.4) + k * T.get("rowStep", 0.35)
            plan.append(("click-soft.mp3", t, 0.3))
        if T.get("flashAt") is not None:
            plan.append(("sparkle.mp3", T["flashAt"], 0.28))
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

    for name, effs in E.items():
        for j, eff in enumerate(arr(effs)):
            tag = name if not isinstance(effs, list) else f"{name}[{j}]"
            for k in ("in", "out", "at", "cardIn", "subAt", "drawAt", "alertAt", "panelOut", "flashAt", "rowStart"):
                chk(f"{tag}.{k}", eff.get(k))
            for i, it in enumerate(eff.get("items", []) + eff.get("cards", [])):
                chk(f"{tag}[{i}].at", it.get("at"))
            for t in eff.get("steps", []) + eff.get("rowTimes", []):
                chk(f"{tag}.tempo", t)
            if "in" in eff and "out" in eff and eff["out"] <= eff["in"]:
                warn.append(f"{tag}: out ({eff['out']}) tem que ser depois de in ({eff['in']})")
    for k in SCENE_EFFECTS + ("bubbles", "ring"):
        if isinstance(E.get(k), list):
            warn.append(f"'{k}' só pode aparecer uma vez (use um objeto, não uma lista)")
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
        if len(" ".join(w[0] for w in g["w"])) > (12 if g.get("big") else 15):
            warn.append(f"legenda {i} ('{' '.join(w[0] for w in g['w'])}') é longa: pode sair com fonte menor; divida o bloco")
    return warn


def word_in_front(W, safe):
    """bigWord na frente: pedido no config, ou "por trás" acima da área segura (o modelo converte)."""
    top = W.get("top")
    return bool(W.get("front")) or (W.get("front") is None and isinstance(top, (int, float)) and top < safe["top"])


def safe_notes(cfg):
    """O que o modelo vai mexer para caber na área segura (o encaixe é automático; isto só avisa)."""
    S = cfg["safe"]
    E = cfg.get("effects", {})
    notes = []

    def low(v, lim):
        return isinstance(v, (int, float)) and v < lim

    for b in (E.get("bubbles") or {}).get("items", []):
        if low(b.get("left"), S["left"]) or low(b.get("top"), S["top"]):
            notes.append(f"balão '{b.get('text', '')}' (left {b.get('left')}, top {b.get('top')}) vai para dentro da área segura;"
                         " confira se não ficou escondido atrás da cabeça")
    for s in arr(E.get("bigSymbol")):
        if low(s.get("left"), S["left"]) or low(s.get("top"), S["top"]) or s.get("size", 980) * 1.1 > S["bottom"] - S["top"]:
            notes.append(f"bigSymbol '{s.get('text', '')}' vai encolher/entrar na área segura (x ≥ {S['left']}, y ≥ {S['top']})")
    for w in arr(E.get("bigWord")):
        if not w.get("front") and word_in_front(w, S):
            notes.append(f"bigWord '{w.get('text', '')}' (top {w.get('top')}): acima da cabeça não cabe na área segura —"
                         " vai na frente da pessoa, logo acima das legendas (como \"front\": true)")
    F = E.get("frame")
    if F:
        if low(F.get("headlineTop"), S["top"]) or low(F.get("panelX"), S["left"]) or low(F.get("y"), S["top"]) or (
            F.get("x", 0) + F.get("w", 500) > S["right"]
        ):
            notes.append(f"frame: manchete desce para y {S['top']}, moldura fica entre x {S['left']} e {S['right']} e os cartões"
                         " entre a margem e a moldura")
    R = E.get("ring")
    if R and (R.get("r", 340) > 350 or R.get("cy", 620) - R.get("r", 340) < S["top"] - 30):
        notes.append(f"ring: o anel encolhe/desce para caber inteiro (raio até ~345, topo em y ≥ {S['top']})")
    for name in ("diagram", "table"):
        for j, P in enumerate(arr(E.get(name))):
            if low(P.get("top"), S["top"]):
                notes.append(f"{name}[{j}]: painel desce para y {S['top']} (e encolhe se não couber acima das legendas)")
    return notes


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
    cfg["safe"] = {**SAFE_ZONE, **(cfg.get("safe") or {})}
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

    for need_file in ("footage.mp4", "voice.m4a", "person.webm") + (("plate.webm",) if cfg.get("effects", {}).get("glass") else ()):  # noqa: E501
        if not (p["assets"] / need_file).exists():
            print(f"AVISO: falta assets/{need_file}", file=sys.stderr)

    for G in arr(cfg.get("effects", {}).get("diagram")):
        if G.get("svg"):
            f = p["assets"] / G["svg"]
            if not f.exists():
                die(f"ilustração não encontrada: assets/{G['svg']}")
            G["svgMarkup"] = re.sub(r"<\?xml[^>]*>", "", f.read_text(encoding="utf-8"))

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

    # fundo com o buraco da pessoa só entra durante as camadas de vidro (economiza disco e tempo no render)
    plate = ""
    G = cfg.get("effects", {}).get("glass")
    if G:
        st = round(max(0.0, G["in"] - 0.1), 2)
        du = round(min(D - st, G["out"] - st + 0.5), 2)
        plate = (
            '            <div id="plateWrap" class="clipwrap">\n'
            f'              <video id="plate" class="clip vid" src="assets/plate.webm" data-start="{st}" data-duration="{du}"'
            f' data-media-start="{st}" data-track-index="4" muted playsinline></video>\n'
            "            </div>"
        )
    # trechos em que a pessoa recortada precisa estar por cima (algo passa por trás dela); fora deles o
    # vídeo original já mostra a pessoa igualzinha — isso corta pela metade (ou mais) o disco do render
    E = cfg.get("effects", {})
    wins = []
    def need(a, b):
        wins.append([max(0.0, a - 0.3), min(D, b + 0.45)])
    B = E.get("bubbles")
    if B and B.get("items") and not B.get("front"):
        need(min(i["at"] for i in B["items"]), B["out"] + 0.3)
    for S in arr(E.get("bigSymbol")):
        if not S.get("front"):
            need(S["in"], S["out"] + 0.3)
    for W in arr(E.get("bigWord")):
        if not word_in_front(W, cfg["safe"]):
            need(W["at"], W["out"] + 0.25)
    if E.get("ring"):
        need(E["ring"]["in"], E["ring"].get("out", D) + 0.3)
    if E.get("glass"):
        need(E["glass"]["in"], E["glass"]["out"] + 0.4)
    # (na moldura a cena inteira encolhe junto — o vídeo original já basta, não precisa do recorte)
    wins.sort()
    merged = []
    for a, b in wins:
        if merged and a - merged[-1][1] < 0.6:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    person = "\n".join(
        f'            <video id="person{k}" class="clip vid" src="assets/person.webm" data-start="{a:.2f}" data-duration="{b - a:.2f}"'
        f' data-media-start="{a:.2f}" data-track-index="{5 + k}" muted playsinline></video>'
        for k, (a, b) in enumerate(merged)
    )
    warnings = validate(cfg, D)
    notes = safe_notes(cfg)
    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    # "<" escapado: um SVG embutido com "</script>" ou "<!--" não pode fechar o <script> do modelo
    config_js = json.dumps({k: v for k, v in cfg.items() if k != "sfx"}, ensure_ascii=False).replace("<", "\\u003c")
    html = (
        template.replace("__DURATION__", f"{D}")
        .replace("__FILL__", fill)
        .replace("__SFX__", "\n".join(lines))
        .replace("__PLATE__", plate)
        .replace("__PERSON__", person)
        .replace("__CONFIG__", config_js)
    )
    (p["project"] / "index.html").write_text(html, encoding="utf-8")

    E = cfg.get("effects", {})
    print(f"index.html gerado · {D:.2f} s · {len(caps)} legendas · {len(kept)} efeitos sonoros")
    print("  pessoa recortada em: " + (", ".join(f"{a:.1f}–{b:.1f}s" for a, b in merged) or "nenhum trecho")
          + f" ({sum(b - a for a, b in merged):.1f} s de {D:.0f} s)")
    print("  efeitos visuais: " + (", ".join(f"{k}×{len(arr(v))}" if isinstance(v, list) else k for k, v in E.items() if v) or "nenhum"))
    if warnings:
        print("\nAVISOS:")
        for w in warnings:
            print("  - " + w)
    if notes:
        print("\nÁREA SEGURA (o modelo ajusta sozinho; confira em snaps_review/celular.jpg depois do review.py):")
        for n in notes:
            print("  - " + n)
    print(f"\nPróximo: python3 {SKILL_DIR}/scripts/hf.py <pasta-de-trabalho> check")


if __name__ == "__main__":
    main()
