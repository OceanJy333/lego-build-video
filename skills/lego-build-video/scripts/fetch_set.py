#!/usr/bin/env python3
"""Find a LEGO set in the LDraw Official Model Repository (OMR) by number or name, and download its model.

input: a set number (10179 or 10179-1) or English name words ("millennium falcon"), optional output dir (default .)
output: by number: <set>-<n>.mpd (all models of the set; the first is the main build), prints author, licence and notes.
        by name: prints the matching sets (number, name, theme, year) and downloads nothing.
pos: step 2 of the lego-build-video skill. The OMR list filters with page JavaScript, so this pages through
     https://library.ldraw.org/omr/sets 100 rows at a time and reads the set page for the file links.
"""
import html, re, sys, unicodedata, urllib.request
from pathlib import Path

BASE = 'https://library.ldraw.org'
query = sys.argv[1].strip()
out = Path(sys.argv[2] if len(sys.argv) > 2 else '.')
get = lambda url: urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'lego-build-video'}), timeout=60).read().decode()
by_number = re.fullmatch(r'\d+(-\d+)?', query)
num = query if not by_number or '-' in query else query + '-1'

def sets():
    """Yield (set page url, [number, name, theme, year]) for every set in the OMR."""
    for page in range(1, 40):
        parts = re.split(r'href="(https://library\.ldraw\.org/omr/sets/\d+)"', get(f'{BASE}/omr/sets?tableRecordsPerPage=100&page={page}'))
        rows = {}
        for u, cell in zip(parts[1::2], parts[2::2]):   # one link per table cell
            m = re.search(r'>([^<>]*\S[^<>]*)<', cell)
            if m: rows.setdefault(u, []).append(html.unescape(m.group(1).strip()))
        if not rows: return
        yield from rows.items()

if not by_number:
    plain = lambda t: unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()   # Sián → sian
    words = plain(query).split()
    hits = [c for _, c in sets() if all(w in plain(' '.join(c)) for w in words)]
    for c in hits: print('  '.join(c))
    sys.exit(0 if hits else f'No set in the LDraw Official Model Repository matches "{query}"')

page_url = next((u for u, c in sets() if num in c), None)
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
