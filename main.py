#!/usr/bin/env python3
# coding: utf-8
# source venv/bin/activate
# YouTube ID Scanner
# (c) 2025 by Alexander Thiele
# License: GPL-2.0-or-later

import requests
import time
import random
from pathlib import Path
import os


SIGNS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
YOUTUBE_URL = "https://www.youtube.com/watch?v="
# Basispfad: Ordner, in dem das Skript liegt
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

LAST_FILE = BASE_DIR / "lastyt"
CACHE_FILE = BASE_DIR / "ytscache"
FOUND_FILE = BASE_DIR / "ytfound.txt"


def get_video_title(video_id):
    try:
        url = YOUTUBE_URL + video_id
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if "<title>" in response.text:
            title = response.text.split("<title>")[1].split("</title>")[0].strip()
            if title != "- YouTube":  # <- hier ist der wichtige Check
                return title
    except Exception as e:
        print(f"Fehler beim Abrufen: {e}")
    return None


def id_from_index(indices):
    return ''.join(SIGNS[i] for i in indices)

def scan_youtube_ids(start_indices, sleep_mode=False):
    from itertools import product

    ranges = [range(start_indices[i], 62) for i in range(11)]
    found_anything = False  # ← Flag setzen

    for combo in product(*ranges):
        yt_id = id_from_index(combo)
        title = get_video_title(yt_id)

        if title:
            print(f"🎥  {yt_id} → {title}")
            if not found_anything:
                found_anything = True  # erstes Ergebnis gefunden → Datei darf jetzt erstellt werden

            with FOUND_FILE.open("a") as f:
                f.write(f"URL: {YOUTUBE_URL}{yt_id}\n")
                f.write(f"Titel: {title}\n")
                f.write("_____________________________________\n")
        else:
            print(f"❌  {yt_id} → ungültig")

        with LAST_FILE.open("w") as f:
            f.write(":".join(map(str, combo)))

        if sleep_mode:
            time.sleep(random.randint(1, 4))

    if not found_anything and FOUND_FILE.exists():
        FOUND_FILE.unlink()  # Falls Datei existiert, aber leer blieb → löschen


def load_last_indices():
    if LAST_FILE.exists():
        with LAST_FILE.open() as f:
            return list(map(int, f.read().strip().split(":")))
    return [0] * 11

def convert_id(ytid):
    return ":".join(str(SIGNS.index(char)) for char in ytid)

def main():
    import sys

    try:
        if len(sys.argv) < 2:
            print("Verwendung: scan | convert [id] | reset | test [id]")
            return

        command = sys.argv[1]

        if command == "convert" and len(sys.argv) == 3:
            print(convert_id(sys.argv[2]))

        elif command == "test" and len(sys.argv) == 3:
            title = get_video_title(sys.argv[2])
            print(f"Titel: {title}" if title else "Kein Titel gefunden.")

        elif command == "reset":
            with LAST_FILE.open("w") as f:
                f.write("0:0:0:0:0:0:0:0:0:0:0")
            print("Zähler zurückgesetzt.")

        elif command == "scan":
            sleep_mode = len(sys.argv) > 2 and sys.argv[2] == "sleep"
            start_indices = load_last_indices()
            scan_youtube_ids(start_indices, sleep_mode=sleep_mode)

        else:
            print("Unbekannter Befehl.")
    except KeyboardInterrupt:
        print("\n🛑 Scan wurde durch Benutzer abgebrochen.")
        sys.exit(0)

if __name__ == "__main__":
    main()
