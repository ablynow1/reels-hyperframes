#!/usr/bin/env python3
"""Baixa o vídeo (link do YouTube etc.) ou copia um arquivo local para <pasta>/source/original.mp4.

Uso:
  python3 fetch_video.py <link-ou-arquivo> <pasta-de-trabalho>
"""

import shutil
import sys
from pathlib import Path

from common import die, need, run, video_info, work_paths


def main():
    if len(sys.argv) != 3:
        die(__doc__)
    src, work = sys.argv[1], sys.argv[2]
    p = work_paths(work)
    p["source"].mkdir(parents=True, exist_ok=True)
    out = p["original"]
    if out.exists():
        print(f"Já existe: {out} (apague para baixar de novo)")
    elif src.startswith(("http://", "https://")):
        need("yt-dlp", "Instale o yt-dlp (macOS: brew install yt-dlp).")
        res = run(
            [
                "yt-dlp",
                "--no-warnings",
                "--no-progress",
                "--no-playlist",
                "-f",
                "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b",
                "--merge-output-format",
                "mp4",
                "-o",
                str(p["source"] / "original.%(ext)s"),
                src,
            ],
            check=False,
        )
        if res.returncode != 0 or not out.exists():
            die(
                "o yt-dlp não conseguiu baixar. Se deu 'HTTP Error 403', atualize o yt-dlp "
                "(brew upgrade yt-dlp  ou  yt-dlp -U) e tente de novo. Se continuar, peça o arquivo do vídeo."
            )
        run(["yt-dlp", "--no-warnings", "--skip-download", "--print", "%(title)s | %(channel)s | %(duration)ss", src], check=False)
    else:
        f = Path(src).expanduser()
        if not f.exists():
            die(f"arquivo não encontrado: {f}")
        if f.suffix.lower() == ".mp4":
            shutil.copy2(f, out)
        else:
            need("ffmpeg", "Instale o FFmpeg.")
            run(["ffmpeg", "-v", "error", "-y", "-i", f, "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", out])
    info = video_info(out)
    print(f"\nVídeo: {out}\n  {info['width']}x{info['height']} · {info['duration']:.1f} s · áudio: {'sim' if info['has_audio'] else 'NÃO'}")
    if not info["has_audio"]:
        die("o vídeo não tem áudio — a skill precisa da fala para escolher o trecho e legendar.")


if __name__ == "__main__":
    main()
