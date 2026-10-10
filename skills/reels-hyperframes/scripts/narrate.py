#!/usr/bin/env python3
"""Narração com o motor de voz da Microsoft (edge-tts) — quem escolhe a voz é a pessoa.

Para vídeo sem fala (gravação de tela, produto, animação), áudio ruim, ou quando pedem uma versão
narrada. Gera a voz a partir de um roteiro e devolve o tempo exato de cada palavra: as legendas saem
sincronizadas, sem precisar refazer a voz em outro app nem ressincronizar. Precisa de internet (a voz é
gerada no serviço da Microsoft) e do pacote edge-tts (`pip3 install edge-tts`).

Uso:
  python3 narrate.py --list [--lang pt-BR] [--all]
      -> vozes do idioma (--all inclui as "Multilingual" de outros países, que também falam português,
         com o sotaque de origem)
  python3 narrate.py <pasta> --samples [--lang pt-BR] [--all] [--text "frase"] [--script roteiro.txt]
      -> uma amostra de cada voz em source/vozes/ (com a 1ª frase do roteiro, se houver) para a
         PESSOA ouvir e escolher
  python3 narrate.py <pasta> --voice pt-BR-FranciscaNeural --script roteiro.txt [--rate +10%] [--pitch +0Hz]
      -> project/assets/voice.m4a (a voz do vídeo, volume padronizado) + project/narration.json (tempo de
         cada palavra, usado pelo build_captions.py). Rode depois do make_clip.py; a voz original do corte
         fica guardada em assets/voice_original.m4a.
"""

import argparse
import asyncio
import math
import re
import shutil
from pathlib import Path

from common import die, load_json, need, run, save_json, video_info, work_paths

SAMPLE_TEXT = "Oi! Essa é a minha voz. Se você gostar, é só me escolher para narrar o seu vídeo."
GENDER = {"Male": "masculina", "Female": "feminina"}


def edge():
    try:
        import edge_tts
    except ImportError:
        die("falta o edge-tts (motor de voz da Microsoft). Instale com: pip3 install edge-tts")
    return edge_tts


def voices(lang, include_multi):
    allv = asyncio.run(edge().list_voices())
    sel = [v for v in allv if v["Locale"].lower().startswith(lang.lower())]
    if include_multi:
        sel += [v for v in allv if "Multilingual" in v["ShortName"] and v not in sel]
    if not sel:
        die(f"nenhuma voz para '{lang}'. Exemplos de idioma: pt-BR, pt-PT, en-US, es-ES")
    return sel


def describe(v, lang):
    tags = ", ".join(v.get("VoiceTag", {}).get("VoicePersonalities", []))
    other = not v["Locale"].lower().startswith(lang.lower())
    extra = f" · fala vários idiomas (sotaque de {v['Locale']})" if other else ""
    return f"{v['ShortName']:<36} voz {GENDER.get(v['Gender'], v['Gender'])}{extra}" + (f" · {tags}" if tags else "")


async def synth(text, voice, rate, pitch, mp3):
    """Gera a voz em mp3 e devolve as palavras com início/fim em segundos."""
    com = edge().Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": round(s, 3), "end": round(s + chunk["duration"] / 1e7, 3)})
    return words


def norm(s):
    return re.sub(r"[^\w]", "", s.lower())


def with_punctuation(words, script):
    """Devolve a pontuação do roteiro às palavras (a legenda quebra nas vírgulas e pontos)."""
    tokens = script.split()
    k = 0
    for w in words:
        key = norm(w["text"])
        for j in range(k, min(k + 6, len(tokens))):
            if key and norm(tokens[j]).startswith(key):
                w["raw"] = tokens[j]
                k = j + 1
                break
        else:
            w["raw"] = w["text"]
    return words


def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip(), re.S)
    return (m.group(1) if m else text.strip())[:220]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work", nargs="?")
    ap.add_argument("--list", action="store_true", help="listar as vozes do idioma")
    ap.add_argument("--samples", action="store_true", help="uma amostra de cada voz para a pessoa escolher")
    ap.add_argument("--lang", default="pt-BR")
    ap.add_argument("--all", action="store_true", help="incluir as vozes Multilingual de outros países")
    ap.add_argument("--text", default=None, help="frase das amostras")
    ap.add_argument("--voice", default=None, help="voz escolhida pela pessoa (ex.: pt-BR-FranciscaNeural)")
    ap.add_argument("--script", default=None, help="arquivo .txt com o roteiro da narração")
    ap.add_argument("--rate", default="+0%", help="velocidade, ex.: +10%% ou -5%%")
    ap.add_argument("--pitch", default="+0Hz", help="tom, ex.: +2Hz ou -2Hz")
    a = ap.parse_args()

    if a.list:
        for v in voices(a.lang, a.all):
            print("  " + describe(v, a.lang))
        print("\nOuça antes de escolher: narrate.py <pasta> --samples (a escolha é da pessoa).")
        return

    if not a.work:
        die(__doc__)
    p = work_paths(a.work)
    script = Path(a.script).read_text(encoding="utf-8").strip() if a.script else ""

    if a.samples:
        out = p["source"] / "vozes"
        out.mkdir(parents=True, exist_ok=True)
        text = a.text or (first_sentence(script) if script else SAMPLE_TEXT)
        print(f'Amostras com a frase: "{text}"\n')
        for v in voices(a.lang, a.all):
            f = out / f"{v['ShortName']}.mp3"
            asyncio.run(synth(text, v["ShortName"], a.rate, a.pitch, f))
            print(f"  {f}   ({describe(v, a.lang)})")
        print("\nMande as amostras para a pessoa ouvir. Quem escolhe a voz é ela; depois:"
              f"\n  python3 narrate.py {a.work} --voice <voz escolhida> --script roteiro.txt")
        return

    if not a.voice or not script:
        die("para narrar use --voice <voz escolhida pela pessoa> e --script roteiro.txt (ou --list / --samples)")
    need("ffmpeg", "Instale o FFmpeg.")
    clip = load_json(p["clip"])
    if clip is None or not (p["assets"] / "footage.mp4").exists():
        die("rode make_clip.py antes: a narração entra por cima do corte do vídeo.")

    raw_mp3 = p["assets"] / "narration_raw.mp3"
    words = asyncio.run(synth(script, a.voice, a.rate, a.pitch, raw_mp3))
    if not words:
        die("a Microsoft não devolveu a voz (sem internet? voz com nome errado? edge-tts desatualizado: pip3 install -U edge-tts)")
    words = with_punctuation(words, script)

    voice = p["assets"] / "voice.m4a"
    backup = p["assets"] / "voice_original.m4a"
    if voice.exists() and not clip.get("narration"):
        shutil.copy2(voice, backup)  # a voz atual ainda é a do corte (make_clip): guarda antes de trocar
    # mesmo padrão de volume do make_clip (-14 LUFS, 48 kHz) para os efeitos sonoros ficarem por baixo
    run(["ffmpeg", "-v", "error", "-y", "-i", raw_mp3, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
         "-c:a", "aac", "-b:a", "192k", voice])

    # (video_info exige faixa de vídeo; aqui é só áudio)
    res = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice], capture=True)
    speech = float(res.stdout.strip() or 0)
    footage = video_info(p["assets"] / "footage.mp4")["duration"]
    duration = math.floor(min(speech, footage) * 100) / 100 - 0.01
    clip.update({"duration": round(duration, 2), "narration": {"voice": a.voice, "file": "narration.json"}})
    save_json(p["clip"], clip)
    save_json(p["project"] / "narration.json", {
        "voice": a.voice, "rate": a.rate, "pitch": a.pitch, "duration": round(speech, 2), "text": script, "words": words,
    })

    print(f"\nNarração pronta: {a.voice} · {speech:.2f} s · {len(words)} palavras")
    print(f"  {voice}  (a voz original do corte ficou em {backup.name})")
    print(f"  {p['project'] / 'narration.json'}  (o build_captions.py usa o tempo de cada palavra)")
    if speech > footage + 0.05:
        print(f"\nAVISO: a narração tem {speech:.1f} s e o corte do vídeo {footage:.1f} s — a fala vai ser cortada no fim."
              f"\n  Refaça o make_clip.py com um trecho de {speech:.1f} s ou mais, ou encurte o roteiro.")
    elif footage - speech > 1.0:
        print(f"\nO vídeo ficou com {duration:.1f} s (o tamanho da narração; o corte tinha {footage:.1f} s).")


if __name__ == "__main__":
    main()
