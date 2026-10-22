#!/usr/bin/env python3
"""v3.25 — de lettertypen van de eigen server, niet meer van Google Fonts.

  A. Geen pagina vraagt nog iets aan fonts.googleapis.com of fonts.gstatic.com.
  B. Elke pagina die Oswald of Share Tech Mono gebruikt, linkt fonts/fonts.css,
     en die lettertypen laden echt (document.fonts.load), van de eigen server.
  C. fonts/: de drie lettertypebestanden, het stylesheet en de licenties staan
     er; .gitattributes houdt ze niet uit de release-ZIP.

Draaien vanuit de suite-root:  python3 _archief/overpass_rig/lettertypetest.py
"""
import glob, os, re, sys
HIER = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HIER, 'laadtest.py'), encoding='utf-8').read()
exec(_src.split('ok = fout = 0')[0])             # ROOT, NM, route, srv, BASIS
from playwright.sync_api import sync_playwright

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

GOOGLE = re.compile(r'fonts\.(googleapis|gstatic)\.com')
paginas = sorted(f for f in glob.glob('*.html'))
bron = {f: open(f, encoding='utf-8').read() for f in paginas}
# Pagina's die een van de twee lettertypen in hun opmaak noemen. privacy.html
# noemt Google Fonts in tekst (de geschiedenis), dat is geen verzoek.
# telrapport noemt Oswald alleen in de labels op de kaart en laadde hem nooit:
# daar staat een reserveletter, al sinds het begin. Bewust buiten v3.25 gelaten.
oswald = [f for f in paginas if f != 'telrapport.html'
          and re.search(r"font-family:\s*['\"]?Oswald|--font:\s*'Oswald'", bron[f])]
mono = [f for f in paginas if 'Share Tech Mono' in bron[f]]

print('== C. fonts/ ==')
for f in ['fonts.css', 'oswald-latin-wght-normal.woff2', 'oswald-latin-ext-wght-normal.woff2',
          'share-tech-mono-latin-400-normal.woff2', 'OFL-Oswald.txt', 'OFL-ShareTechMono.txt']:
    eis('fonts/%s bestaat' % f, os.path.exists(os.path.join(ROOT, 'fonts', f)))
attr = open(os.path.join(ROOT, '.gitattributes'), encoding='utf-8').read()
eis('.gitattributes houdt fonts/ niet uit de release-ZIP', not re.search(r'(?m)^\s*/?fonts\b.*export-ignore', attr))
css = open(os.path.join(ROOT, 'fonts', 'fonts.css'), encoding='utf-8').read()
eis('fonts.css verwijst alleen naar bestanden in de map zelf',
    all(os.path.exists(os.path.join(ROOT, 'fonts', u)) for u in re.findall(r'url\(([^)]+)\)', css)),
    re.findall(r'url\(([^)]+)\)', css))

print('\n== A. geen Google Fonts meer in de code ==')
in_code = [f for f in paginas if f != 'privacy.html' and GOOGLE.search(bron[f])]
eis('geen pagina noemt fonts.googleapis.com of fonts.gstatic.com', not in_code, in_code)
eis('%d pagina\'s gebruiken Oswald, %d Share Tech Mono' % (len(oswald), len(mono)), len(oswald) >= 10 and len(mono) >= 4,
    (oswald, mono))

with sync_playwright() as p:
    b = p.chromium.launch()
    print('\n== B. elke pagina laadt zijn lettertypen van de eigen server ==')
    for f in sorted(set(oswald) | set(mono)):
        eis('%s linkt fonts/fonts.css' % f, 'fonts/fonts.css' in bron[f])
        ctx = b.new_context(viewport={'width': 390, 'height': 844})
        pg = ctx.new_page(); verzoeken = []; fouten = []
        pg.on('request', lambda r: verzoeken.append(r.url))
        pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
        pg.route('**/*', route)
        pg.goto(BASIS + f, wait_until='load'); pg.wait_for_timeout(300)
        geladen = pg.evaluate("""async (namen) => {
            const uit = {};
            for (const n of namen) uit[n] = (await document.fonts.load('16px "' + n + '"', 'Abc 123')).length;
            return uit; }""", (['Oswald'] if f in oswald else []) + (['Share Tech Mono'] if f in mono else []))
        eis('%s: geladen %s' % (f, geladen), geladen and all(v > 0 for v in geladen.values()), geladen)
        google = [u for u in verzoeken if GOOGLE.search(u)]
        eigen = [u for u in verzoeken if u.startswith(BASIS + 'fonts/')]
        eis('%s: geen verzoek aan Google, wel aan fonts/ (%d)' % (f, len(eigen)), not google and eigen, (google, eigen))
        ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
