#!/usr/bin/env python3
"""
tmdb_ids_to_html.py
Scarica lista da https://vixsrc.to/api/list/movie/?lang=It,
risolve tmdb_id -> titolo e genera movies.html con link + iframe miniplayer
"""

import requests
from bs4 import BeautifulSoup
import time
import html

SRC_URL = "https://vixsrc.to/api/list/movie/?lang=It"
TMDB_URL_TEMPLATE = "https://www.themoviedb.org/movie/{}"
VIX_PLAYER_TEMPLATE = "https://vixsrc.to/movie/{}/?"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; script/1.0; +https://example.org)"
}
OUTPUT_HTML = "movies.html"

def get_id_list():
    resp = requests.get(SRC_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    ids = []
    # prova varie possibili strutture
    items = data.get("results") if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
    for item in items:
        for key in ("tmdb_id", "tmdbId", "id"):
            if key in item and item[key]:
                ids.append(str(item[key]))
                break
    return ids

def get_title_from_tmdb(tmdb_id):
    url = TMDB_URL_TEMPLATE.format(tmdb_id)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # cerca titolo principale (fallback a <title>)
    h2 = soup.find("h2")
    if h2 and h2.text.strip():
        return h2.text.strip()
    if soup.title and soup.title.text:
        return soup.title.text.split(" - ")[0].strip()
    return None

def build_html(entries):
    head = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Movie miniplayers</title>
<style>
body{font-family: Arial, Helvetica, sans-serif; margin:20px}
.movie{margin-bottom:24px}
.title{font-weight:600; margin-bottom:6px}
iframe{border:1px solid #ccc; width:560px; height:315px}
.small{font-size:0.9em; color:#555}
</style>
</head>
<body>
<h1>Movie miniplayers</h1>
<div class="list">
"""
    items_html = []
    for tmdb_id, title in entries:
        safe_title = html.escape(title if title else f"(titolo non trovato per {tmdb_id})")
        vix_url = VIX_PLAYER_TEMPLATE.format(tmdb_id)
        item = f'''
<div class="movie">
  <div class="title">{safe_title} <span class="small">({tmdb_id})</span></div>
  <div class="small"><a href="{html.escape(vix_url)}" target="_blank">Apri su vixsrc.to</a></div>
  <div class="player"><iframe src="{html.escape(vix_url)}" loading="lazy" allowfullscreen></iframe></div>
</div>
'''
        items_html.append(item)
    tail = """
</div>
</body>
</html>
"""
    return head + "\n".join(items_html) + tail

def main():
    try:
        ids = get_id_list()
    except Exception as e:
        print("Errore scaricando la lista:", e)
        return

    if not ids:
        print("Nessun id trovato.")
        return

    entries = []
    for tmdb_id in sorted(set(ids), key=int):
        try:
            title = get_title_from_tmdb(tmdb_id)
        except Exception as e:
            print(f"{tmdb_id} -> ERRORE: {e}")
            title = None
        print(f"{tmdb_id} -> {title or 'titolo non trovato'}")
        entries.append((tmdb_id, title or ""))
        time.sleep(DELAY)

    html_content = build_html(entries)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Pagina generata: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()