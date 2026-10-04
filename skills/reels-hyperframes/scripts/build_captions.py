#!/usr/bin/env python3
"""Gera as legendas palavra por palavra no tempo do corte (project/captions.json).

Regras: 2–3 palavras por bloco, uma linha só (até ~15 letras), quebra nas vírgulas e pausas.
O começo/fim de cada palavra é encaixado nas pausas reais do áudio (o Whisper às vezes erra).
Destaques automáticos (revise!): número/% -> verde "g"; nome próprio/sigla -> amarelo "y";
negação (não, nunca…) -> vermelho "r". Blocos com número ou palavra única destacada ficam grandes.

Uso:
  python3 build_captions.py <pasta> [--max-words 3] [--max-chars 15]
"""

import argparse
import re

from common import detect_pauses, die, load_json, save_json, work_paths

NEG = {"não", "nao", "nunca", "nem", "jamais", "nada"}
FUNC = {"de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "que", "pra", "para", "com", "em", "no", "na",
        "nos", "nas", "um", "uma", "se", "por", "ao", "à", "the", "of", "to", "and", "in"}


def clean(t):
    t = t.strip()
    t = re.sub(r"^[\"'“”«(\[]+", "", t)
    t = re.sub(r"[\"'“”».,;:)\]]+$", "", t)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--max-words", type=int, default=3)
    ap.add_argument("--max-chars", type=int, default=15)
    a = ap.parse_args()
    p = work_paths(a.work)
    words = load_json(p["transcript"])
    clip = load_json(p["clip"])
    if not words or not clip:
        die("rode transcribe.py e make_clip.py antes.")
    D = clip["duration"]

    # palavras do corte, no tempo do corte
    cw = []
    for pi, ((a0, b0), off) in enumerate(zip(clip["pieces"], clip["offsets"])):
        pauses, _ = detect_pauses(p["original"], max(0.0, a0 - 1.0), b0 + 1.0)
        for i, w in enumerate(words):
            if w["end"] < a0 - 1 or w["start"] > b0 + 1:
                continue
            ws, we = w["start"], w["end"]
            for ps, pe in pauses:
                if ps <= ws + 0.2 and ps < we - 0.05 and pe > ws + 0.05:
                    ws, we = pe, max(we, pe + 0.12)  # a pausa cobre o começo: a palavra só começa depois dela
                elif ws < ps and pe < we - 0.08 and ps - ws > 0.2 and we - ws > 0.8:
                    ws = pe  # pausa no meio de uma palavra esticada: ela começa depois da pausa
                if ps < we - 0.05 <= pe and ps > ws + 0.08:
                    we = ps  # a pausa cobre o fim: a palavra termina antes dela
            w = dict(w, start=ws, end=we)
            dur = max(0.01, w["end"] - w["start"])
            inside = min(w["end"], b0) - max(w["start"], a0)
            if inside <= 0:
                continue
            crosses = w["start"] < a0 - 0.02 or w["end"] > b0 + 0.02
            if inside / dur < 0.5 or (crosses and dur < 0.6):
                continue  # palavra cortada na emenda: quase não se ouve
            s, e = max(w["start"], a0), min(w["end"], b0)
            if e - s > 1.0 and not re.search(r"\d", w["text"]):
                s = e - 0.45  # Whisper esticou a palavra por cima de uma pausa
            prev_raw = words[i - 1]["text"] if i > 0 else ""
            cw.append({
                "raw": w["text"],
                "text": clean(w["text"]).upper(),
                "s": round(s - a0 + off, 2),
                "e": round(e - a0 + off, 2),
                "piece": pi,
                "sentence_start": i == 0 or prev_raw.endswith((".", "?", "!")),
            })
    cw = [w for w in cw if w["text"] and 0 <= w["s"] < D]
    if not cw:
        die("nenhuma palavra caiu dentro do corte — confira os pedaços do make_clip.")

    def style(w):
        raw = clean(w["raw"])
        if re.search(r"\d", raw):
            return "g"
        if raw.lower() in NEG:
            return "r"
        if len(raw) >= 3 and raw.isupper():
            return "y"
        if raw[:1].isupper() and not w["sentence_start"] and raw.lower() not in {"eu", "i"}:
            return "y"
        return None

    groups, cur = [], []
    for w in cw:
        if cur:
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            gap = w["s"] - cur[-1]["e"]
            if (
                w["piece"] != cur[-1]["piece"]
                or len(cur) >= a.max_words
                or chars > a.max_chars
                or gap >= 0.35
                or cur[-1]["raw"].rstrip().endswith((",", ".", "?", "!", ";", ":"))
            ):
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)

    # bloco não termina em "de", "a", "que"…: a palavrinha vai para o começo do próximo
    for gi in range(len(groups) - 1):
        g, nxt = groups[gi], groups[gi + 1]
        while (
            len(g) >= 2
            and g[-1]["text"].lower() in FUNC
            and nxt[0]["piece"] == g[-1]["piece"]
            and len(nxt) <= a.max_words
            and sum(len(x["text"]) + 1 for x in nxt) + len(g[-1]["text"]) <= a.max_chars + 1
        ):
            nxt.insert(0, g.pop())

    # bloco de 1 palavra sem destaque logo depois de um bloco cheio: equilibra (ex.: "UMA TAXA" | "TÃO ALTA")
    for gi in range(1, len(groups)):
        g, prev = groups[gi], groups[gi - 1]
        if (
            len(g) == 1
            and len(prev) >= a.max_words
            and prev[-1]["piece"] == g[0]["piece"]
            and style(g[0]) is None
            and len(prev[-1]["text"]) + 1 + len(g[0]["text"]) <= a.max_chars
        ):
            g.insert(0, prev.pop())

    out = []
    for gi, g in enumerate(groups):
        s = g[0]["s"]
        e = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else min(D, g[-1]["e"] + 0.35)
        if gi == len(groups) - 1:
            e = D
        ws = []
        for w in g:
            st = style(w)
            ws.append([w["text"], w["s"], st] if st else [w["text"], w["s"]])
        has_num = any(len(x) > 2 and x[2] == "g" for x in ws)
        single_hl = len(ws) == 1 and len(ws[0]) > 2
        item = {"s": round(s, 2), "e": round(e, 2), "w": ws}
        if has_num or single_hl:
            item["big"] = True
        out.append(item)
    save_json(p["captions"], out)

    print(f"{len(out)} blocos de legenda -> {p['captions']}\n")
    for g in out:
        txt = " ".join(x[0] + ("*" if len(x) > 2 else "") for x in g["w"])
        print(f"  {g['s']:5.2f}-{g['e']:5.2f}  {txt}{'  (grande)' if g.get('big') else ''}")
    print("\n* = palavra destacada. Revise: erros do Whisper (marcas, termos técnicos), destaques e quebras.")
    print("Para um contador animado (ex.: 90%), troque a palavra por \"#NUM\" e defina \"counter\" no config.json.")


if __name__ == "__main__":
    main()
