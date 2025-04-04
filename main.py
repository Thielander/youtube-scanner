#!/usr/bin/env python3
# coding: utf-8
# source venv/bin/activate
# YouTube ID Scanner (async Version mit tqdm & CSV)
# (c) 2025 by Alexander Thiele
# License: GPL-2.0-or-later
# Ja ich weiß es gibt Trillionen Kombinationen -> Spaßprojekt

import asyncio
import aiohttp
import csv
import time
import random
import sys
import os
from pathlib import Path
from itertools import product
from tqdm.asyncio import tqdm

SIGNS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
YOUTUBE_URL = "https://www.youtube.com/watch?v="
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
LAST_FILE = BASE_DIR / "lastyt"
CSV_FILE = BASE_DIR / "ytfound.csv"
MAX_CONCURRENT_REQUESTS = 10


def id_from_index(indices):
    return ''.join(SIGNS[i] for i in indices)


async def fetch_title(session, video_id, semaphore):
    url = YOUTUBE_URL + video_id
    async with semaphore:
        try:
            async with session.get(url) as resp:
                text = await resp.text()
                if "<title>" in text:
                    title = text.split("<title>")[1].split("</title>")[0].strip()
                    if title and title != "- YouTube":
                        return title
        except Exception as e:
            print(f"Fehler bei {video_id}: {e}")
    return None


async def scan_youtube_ids_async(start_indices, sleep_mode=False):
    ranges = [range(start_indices[i], 62) for i in range(11)]
    combos = list(product(*ranges))
    found_rows = []
    total_checked = 0
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        tasks = []
        for combo in combos:
            yt_id = id_from_index(combo)
            task = asyncio.create_task(fetch_title(session, yt_id, semaphore))
            tasks.append((yt_id, combo, task))

        for yt_id, combo, task in tqdm(tasks, desc="🔍 Scanne YouTube-IDs", unit="ID"):
            title = await task
            total_checked += 1
            print(f"ID: {yt_id}")
            if title:
                print(f"🎥  {yt_id} → {title}")
                found_rows.append([yt_id, title, YOUTUBE_URL + yt_id])
            else:
                print(f"❌  {yt_id} → ungültig")

            with LAST_FILE.open("w") as f:
                f.write(":".join(map(str, combo)))

            if sleep_mode:
                await asyncio.sleep(random.uniform(1, 2))

    if found_rows:
        with CSV_FILE.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Video ID", "Titel", "URL"])
            writer.writerows(found_rows)
        print(f"\n✅ {len(found_rows)} Videos gefunden und in {CSV_FILE.name} gespeichert.")
    else:
        if CSV_FILE.exists():
            CSV_FILE.unlink()
        print("\n❌ Keine gültigen Videos gefunden.")

    print(f"\n📊 Gesamt gescannte IDs: {total_checked}")



def load_last_indices():
    if LAST_FILE.exists():
        with LAST_FILE.open() as f:
            return list(map(int, f.read().strip().split(":")))
    return [0] * 11


def convert_id(ytid):
    return ":".join(str(SIGNS.index(char)) for char in ytid)


def main():
    try:
        if len(sys.argv) < 2:
            print("Verwendung: scan | convert [id] | reset | test [id]")
            return

        command = sys.argv[1]

        if command == "convert" and len(sys.argv) == 3:
            print(convert_id(sys.argv[2]))

        elif command == "test" and len(sys.argv) == 3:
            import requests
            url = YOUTUBE_URL + sys.argv[2]
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if "<title>" in r.text:
                    title = r.text.split("<title>")[1].split("</title>")[0].strip()
                    print(f"Titel: {title}" if title != "- YouTube" else "Kein gültiger Titel gefunden.")
                else:
                    print("Kein Titel gefunden.")
            except Exception as e:
                print(f"Fehler beim Abrufen: {e}")

        elif command == "reset":
            with LAST_FILE.open("w") as f:
                f.write("0:0:0:0:0:0:0:0:0:0:0")
            print("Zähler zurückgesetzt.")

        elif command == "scan":
            sleep_mode = len(sys.argv) > 2 and sys.argv[2] == "sleep"
            start_indices = load_last_indices()
            asyncio.run(scan_youtube_ids_async(start_indices, sleep_mode=sleep_mode))

        else:
            print("Unbekannter Befehl.")
    except KeyboardInterrupt:
        print("\n🛑 Scan wurde durch Benutzer abgebrochen.")
        sys.exit(0)


if __name__ == "__main__":
    main()
