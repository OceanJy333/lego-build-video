#!/usr/bin/env python3
"""Download a LEGO set's model from the LDraw Official Model Repository (OMR) by set number.

input: set number (10179 or 10179-1), optional output dir (default .)
output: <set>-<n>.mpd (all models of the set; the first is the main build), prints author, licence and model notes
pos: step 2 of the lego-build-video skill. The OMR list filters with page JavaScript, so this pages through
     https://library.ldraw.org/omr/sets 100 rows at a time and reads the set page for the file links.
"""
import re, sys, urllib.request
from pathlib import Path

BASE = 'https://library.ldraw.org'
num = sys.argv[1] if '-' in sys.argv[1] else sys.argv[1] + '-1'
out = Path(sys.argv[2] if len(sys.argv) > 2 else '.')
get = lambda url: urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'lego-build-video'}), timeout=60).read().decode()

page_url = None
for page in range(1, 40):
    html = get(f'{BASE}/omr/sets?tableRecordsPerPage=100&page={page}')
    parts = re.split(r'href="(https://library\.ldraw\.org/omr/sets/\d+)"', html)   # [before, url1, row1, url2, row2, ...]
    rows = [(u, re.findall(r'>\s*([\w]+-\d+)\s*<', row)) for u, row in zip(parts[1::2], parts[2::2])]
    hit = next((u for u, cells in rows if num in cells), None)
    if hit: page_url = hit; break
    if not rows: break
if not page_url:
    sys.exit(f'{num} is not in the LDraw Official Model Repository')

files = list(dict.fromkeys(re.findall(r'(media/omr_models/\d+/[^"?]+\.(?:mpd|ldr))', get(page_url))))
out.mkdir(parents=True, exist_ok=True)
for f in files:
    text = get(f'{BASE}/{f}')
    dst = out / Path(f).name
    dst.write_text(text)
    head = [l for l in text.splitlines()[:40] if l.startswith('0 ') and not l.startswith('0 FILE')]
    print(dst, f'{len(text):,} bytes')
    for l in head:
        if re.match(r'0 (Author|!LICENSE|//|!KEYWORDS|Name)', l) or l[2:3].isalpha() and l.count(' ') > 3 and not l.startswith('0 !'):
            print('   ', l[2:])
