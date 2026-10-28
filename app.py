#!/usr/bin/env python3
"""Baixa vídeos do YouTube colando o link no terminal.

Uso:
    python baixar.py                 (pergunta o link)
    python baixar.py <link>          (baixa direto)

Instalação:
    pip install pytubefix            (recomendado; o pytube original costuma quebrar)
    # ou: pip install pytube

Para qualidade máxima (1080p+) instale também o ffmpeg:
    Windows: winget install ffmpeg
    Mac:     brew install ffmpeg
    Linux:   sudo apt install ffmpeg
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

# pytubefix é um fork do pytube com correções; se não estiver instalado, usa o pytube
try:
    from pytubefix import YouTube
except ImportError:
    from pytube import YouTube

PASTA_DESTINO = Path("downloads")


def mostrar_progresso(stream, chunk, bytes_restantes):
    total = stream.filesize
    pct = (total - bytes_restantes) / total * 100
    print(f"\r  {pct:5.1f}% concluído", end="", flush=True)


def nome_seguro(titulo: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", titulo).strip() or "video"


def baixar(link: str) -> None:
    PASTA_DESTINO.mkdir(exist_ok=True)
    yt = YouTube(link, on_progress_callback=mostrar_progresso)
    titulo = nome_seguro(yt.title)
    print(f"Título: {yt.title}")

    tem_ffmpeg = shutil.which("ffmpeg") is not None

    video = (
        yt.streams.filter(adaptive=True, only_video=True, file_extension="mp4")
        .order_by("resolution").desc().first()
    )
    audio = (
        yt.streams.filter(only_audio=True, file_extension="mp4")
        .order_by("abr").desc().first()
    )
    progressivo = (
        yt.streams.filter(progressive=True)
        .order_by("resolution").desc().first()
    )

    # Melhor caminho: vídeo + áudio separados, juntados pelo ffmpeg
    if video and audio and tem_ffmpeg:
        print(f"Baixando vídeo ({video.resolution})...")
        v_path = video.download(output_path=str(PASTA_DESTINO), filename=f"{titulo}_video.mp4")
        print("\nBaixando áudio...")
        a_path = audio.download(output_path=str(PASTA_DESTINO), filename=f"{titulo}_audio.m4a")
        saida = PASTA_DESTINO / f"{titulo}.mp4"
        print("\nJuntando vídeo e áudio...")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", v_path, "-i", a_path,
             "-c", "copy", str(saida)],
            check=True,
        )
        Path(v_path).unlink(missing_ok=True)
        Path(a_path).unlink(missing_ok=True)
        print(f"Pronto! Salvo em: {saida}")
        return

    # Alternativa: arquivo único (qualidade menor, mas não precisa de ffmpeg)
    if progressivo:
        if video and not tem_ffmpeg:
            print("(ffmpeg não encontrado: baixando em qualidade menor. "
                  "Instale o ffmpeg para obter a qualidade máxima.)")
        print(f"Baixando em {progressivo.resolution}...")
        caminho = progressivo.download(output_path=str(PASTA_DESTINO), filename=f"{titulo}.mp4")
        print(f"\nPronto! Salvo em: {caminho}")
        return

    print("Nenhum stream disponível. Tente: pip install -U pytubefix")


def main() -> None:
    link = sys.argv[1] if len(sys.argv) > 1 else input("Cole o link do vídeo: ").strip()
    if not link:
        print("Nenhum link informado.")
        return
    try:
        baixar(link)
    except Exception as e:
        print(f"\nErro ao baixar: {e}")


if __name__ == "__main__":
    main()