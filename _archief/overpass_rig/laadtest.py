#!/usr/bin/env python3
"""v2.69/v2.70 laadtest — elke pagina echt laden in een browser (Chromium via Playwright).

Waarom: pocket_count.html liep bij het opstarten vast op een element dat pas ná
het script in de HTML staat. Het script stopte daar, en het sessieherstel draaide
nooit. node --check en de tagbalans zien zoiets niet; alleen echt laden wel.

Drie delen:
  A. elke HTML-pagina laadt zonder JS-fout
  B. pocket: de parkeer-ingang toont nooit het keuzemenu; herstel gaat voor
  C. index.html: links bestaan, NL/EN-sleutels compleet, niets breder dan 360 px

Nodig: pip install playwright (met Chromium) en in een node_modules:
leaflet@1.9.4, leaflet-draw@1.0.4, jszip, papaparse, @fontsource/oswald en
@fontsource/share-tech-mono. De CDN- en Google-Fonts-verzoeken worden naar die
lokale kopieën omgeleid; al het andere externe verkeer wordt geblokkeerd. Zonder
de echte lettertypen meet de breedtetoets een breder noodlettertype.
Zoekt node_modules via $TEL_NODE_MODULES, ./node_modules of /home/claude/node_modules.

Draaien vanuit de suite-root:  python3 _archief/overpass_rig/laadtest.py
"""
import functools, http.server, json, os, re, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.getcwd()
NM = next((p for p in [os.environ.get('TEL_NODE_MODULES', ''), os.path.join(ROOT, 'node_modules'),
                       '/home/claude/node_modules'] if p and os.path.isdir(p)), None)
if not NM:
    sys.exit('node_modules met leaflet/jszip/papaparse niet gevonden (zet TEL_NODE_MODULES)')
LIB = {'leaflet.min.js': 'leaflet/dist/leaflet.js', 'leaflet.js': 'leaflet/dist/leaflet.js',
       'leaflet.draw.js': 'leaflet-draw/dist/leaflet.draw.js',
       'jszip.min.js': 'jszip/dist/jszip.min.js', 'papaparse.min.js': 'papaparse/papaparse.min.js'}

FONT = {'o5': '@fontsource/oswald/files/oswald-latin-500-normal.woff2',
        'o7': '@fontsource/oswald/files/oswald-latin-700-normal.woff2',
        'stm': '@fontsource/share-tech-mono/files/share-tech-mono-latin-400-normal.woff2'}
FONTS_OK = all(os.path.exists(os.path.join(NM, f)) for f in FONT.values())
FONT_CSS = ("@font-face{font-family:'Oswald';font-weight:500;src:url(/_font/o5)}"
            "@font-face{font-family:'Oswald';font-weight:700;src:url(/_font/o7)}"
            "@font-face{font-family:'Share Tech Mono';src:url(/_font/stm)}")

class Stil(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Stil, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASIS = 'http://127.0.0.1:%d/' % srv.server_address[1]

def route(r):
    u = r.request.url
    if u.startswith(BASIS + '_font/') and FONTS_OK:
        return r.fulfill(body=open(os.path.join(NM, FONT[u.rsplit('/', 1)[1]]), 'rb').read(), content_type='font/woff2')
    if u.startswith(BASIS): return r.continue_()
    if 'fonts.googleapis.com' in u and FONTS_OK:
        return r.fulfill(body=FONT_CSS.replace('url(/', 'url(' + BASIS), content_type='text/css')
    naam = u.split('?')[0].rsplit('/', 1)[-1]
    if naam in LIB:
        return r.fulfill(body=open(os.path.join(NM, LIB[naam]), 'rb').read(), content_type='application/javascript')
    return r.abort()

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)))

def pagina(b, pad, init=None, breedte=390):
    ctx = b.new_context(viewport={'width': breedte, 'height': 844})
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
    pg.route('**/*', route)
    if init: pg.add_init_script(init)
    pg.goto(BASIS + pad, wait_until='load', timeout=20000); pg.wait_for_timeout(600)
    return ctx, pg, fouten

HERSTEL = json.dumps({"modus": "transect", "telType": "transect", "telLabel": "Transect", "telIcon": "x", "telCount": 1,
                      "telHistory": [{"ts": "2026-09-23T10:00:00.000Z", "lat": 51.85, "lon": 4.3, "type": "car"}],
                      "routeLog": [], "savedAt": "2026-09-23T10:01:00Z"})
MET_HERSTEL = ("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');"
               "localStorage.setItem('pocket_sessie', %s);}" % json.dumps(HERSTEL))
STAND = """() => ({ kies: getComputedStyle(document.getElementById('choose-screen')).display,
  park: getComputedStyle(document.getElementById('parkeer-screen')).display,
  melding: document.getElementById('restore-banner').style.display !== 'none',
  opslag: localStorage.getItem('pocket_sessie') !== null, modus: currentModus })"""

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. elke pagina laadt zonder JS-fout ==')
    for f in sorted(x for x in os.listdir(ROOT) if x.endswith('.html')):
        ctx, pg, fouten = pagina(b, f); ctx.close()
        eis(f, not fouten, fouten)

    print('\n== B. pocket: de parkeer-ingang toont nooit het keuzemenu ==')
    # Elk frame kijken of een van de andere drie modi zichtbaar is, ook heel even.
    WAAK = ("window.__menu=false;(function k(){var t=document.querySelector('[onclick=\"chooseTransect()\"]');"
            "if(t&&t.getClientRects().length)window.__menu=true;requestAnimationFrame(k);})();")
    def open_(pad, herstel=False):
        ctx, pg, fouten = pagina(b, pad, (MET_HERSTEL if herstel else '') + WAAK)
        pg.on('dialog', lambda d: d.accept())
        return ctx, pg, fouten
    def zichtbaar(pg, sel):
        return pg.evaluate("(()=>{var e=document.querySelector('%s');return !!(e&&e.getClientRects().length)})()" % sel)
    VOORBEELD = "document.getElementById('preview-overlay').classList.contains('visible')"
    GPS = "routeLog.push({ts:nowIso(),lat:51.85,lon:4.30,acc:5});routeLog.push({ts:nowIso(),lat:51.8503,lon:4.3004,acc:5});"

    ctx, pg, fouten = open_('pocket_count.html#parkeren'); st = pg.evaluate(STAND)
    eis('#parkeren: meteen het parkeerscherm',
        st['park'] == 'flex' and st['kies'] == 'none' and st['modus'] == 'parkeren' and not fouten, st)
    eis('tabtitel "Pocket Parkeren"', pg.title() == 'Pocket Parkeren', pg.title())
    pg.evaluate("adjustParkeer('links_bezet', 1);" + GPS + "stopTelling()"); pg.wait_for_timeout(1200)
    eis('Stop: voorbeeldscherm', pg.evaluate(VOORBEELD))
    pg.evaluate("closePreview()"); pg.wait_for_timeout(300); st = pg.evaluate(STAND)
    eis('Sluiten: verse parkeertelling (0 tikken)', st['park'] == 'flex' and pg.evaluate('telCount') == 0, st)
    eis('hele route tot hier: nooit het keuzemenu, ook niet even', not pg.evaluate('window.__menu'))
    pg.evaluate("pkBack()"); pg.wait_for_timeout(500)
    eis('Terug: naar de voorpagina', pg.url.endswith('/index.html'), pg.url)
    ctx.close()

    ctx, pg, fouten = open_('pocket_count.html#parkeren')
    pg.evaluate("adjustParkeer('rechts_leeg', 1); stopTelling()"); pg.wait_for_timeout(1200)
    eis('Stop zonder GPS-spoor (geen voorbeeldscherm): alleen de Parkeren-knop, geen doodlopend scherm',
        not pg.evaluate(VOORBEELD) and zichtbaar(pg, '[onclick="chooseParkeren()"]') and not pg.evaluate('window.__menu'))
    ctx.close()

    ctx, pg, fouten = open_('pocket_count.html#parkeren', herstel=True); st = pg.evaluate(STAND)
    eis('met onderbroken telling: herstelmelding, telling bewaard', st['melding'] and st['opslag'] and not fouten, st)
    eis('... met alleen de Parkeren-knop, zonder "Wat tel je?"',
        zichtbaar(pg, '[onclick="chooseParkeren()"]') and not zichtbaar(pg, '#choose-heading')
        and not pg.evaluate('window.__menu'))
    pg.evaluate("restoreDiscard()"); pg.wait_for_timeout(300); st = pg.evaluate(STAND)
    eis('Verwijder: door naar parkeren', st['park'] == 'flex' and not st['opslag'], st)
    ctx.close()

    ctx, pg, fouten = open_('pocket_count.html#parkeren', herstel=True)
    pg.evaluate("routeLog.push({ts:nowIso(),lat:51.85,lon:4.30,acc:5}); restoreDownload()"); pg.wait_for_timeout(1200)
    eis('Download bij herstel: voorbeeldscherm', pg.evaluate(VOORBEELD) and not fouten, fouten)
    pg.evaluate("closePreview()"); pg.wait_for_timeout(300); st = pg.evaluate(STAND)
    eis('... Sluiten: door naar parkeren, noodopslag leeg', st['park'] == 'flex' and not st['opslag'], st)
    eis('... en nergens het keuzemenu', not pg.evaluate('window.__menu'))
    ctx.close()

    print('\n== B2. gewone pocket blijft zoals hij was ==')
    ctx, pg, fouten = open_('pocket_count.html'); st = pg.evaluate(STAND)
    eis('zonder hash: het keuzemenu met vier modi', st['kies'] == 'flex' and pg.evaluate('window.__menu'), st)
    pg.evaluate("chooseParkeren()"); pg.evaluate("pkBack()"); pg.wait_for_timeout(300); st = pg.evaluate(STAND)
    eis('Parkeren gekozen, Terug: weer het keuzemenu (niet de voorpagina)',
        st['kies'] != 'none' and zichtbaar(pg, '[onclick="chooseTransect()"]') and pg.url.endswith('pocket_count.html'), (st, pg.url))
    ctx.close()
    ctx, pg, fouten = open_('pocket_count.html', herstel=True); st = pg.evaluate(STAND)
    eis('zonder hash met onderbroken telling: melding én de vier modi',
        st['melding'] and zichtbaar(pg, '[onclick="chooseTransect()"]') and not fouten, st)
    ctx.close()

    print('\n== C. index.html ==')
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    doelen = sorted(set(re.findall(r'href="([a-z_]+\.html)(?:#[a-z]+)?"', html)))
    ontbreekt = [d for d in doelen if not os.path.exists(os.path.join(ROOT, d))]
    eis('alle %d link-doelen bestaan' % len(doelen), not ontbreekt, ontbreekt)
    for d in ['telplanning.html', 'telreconstructie.html', 'telrapport.html', 'pocket_count.html#parkeren']:
        eis('voorpagina linkt naar ' + d, ('href="%s"' % d) in html)
    sleutels = set(re.findall(r'data-i18n="(\w+)"', html))
    en = html[html.index('  en: {'):html.index('  nl: {')]
    nl = html[html.index('  nl: {'):html.index('// Detectie')]
    ks = lambda d: set(re.findall(r'^\s{4}(\w+):', d, re.M))
    eis('elke data-i18n-sleutel bestaat in EN en NL', sleutels <= ks(en) and sleutels <= ks(nl),
        sorted((sleutels - ks(en)) | (sleutels - ks(nl))))
    eis('EN en NL hebben dezelfde sleutels', ks(en) == ks(nl), sorted(ks(en) ^ ks(nl)))
    if not FONTS_OK:
        print('  (lettertypen niet gevonden: breedtetoets overgeslagen)')
    for taal in (['nl', 'en'] if FONTS_OK else []):
        ctx, pg, fouten = pagina(b, 'index.html', "localStorage.setItem('tc_lang','%s')" % taal, breedte=360)
        w = pg.evaluate('document.documentElement.scrollWidth'); ctx.close()
        eis('%s: niets breder dan 360 px' % taal.upper(), w <= 360, w)

    print('\n== D. telplanning met afgeschermde planningmap (v2.75) ==')
    for status, verwacht in [(401, 'afgeschermd'), (500, 'serverfout (500)')]:
        ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
        def maak_weiger(code):
            def weiger(r, *_):   # Playwright geeft ook het request mee
                if '/planningen/' in r.request.url:
                    return r.fulfill(status=code, body='<html>geweigerd</html>', content_type='text/html')
                return route(r)
            return weiger
        pg.route('**/*', maak_weiger(status))
        pg.goto(BASIS + 'telplanning.html', wait_until='load'); pg.wait_for_timeout(500)
        pg.evaluate('loadOpdrachten()'); pg.wait_for_timeout(500)
        tekst = pg.evaluate("document.getElementById('opdrachten-list').textContent")
        eis('opdrachtenlijst bij %d: leesbare melding' % status, verwacht in tekst and not fouten, (tekst, fouten))
        ctx.close()

    print('\n== E. privacy ==')
    eis('voorpagina linkt naar privacy.html', 'href="privacy.html"' in html)
    for taal in ['nl', 'en']:
        blok = en if taal == 'en' else nl
        eis('introzin (%s) belooft niet meer dat "je data" op het toestel blijft' % taal.upper(),
            'your data stays' not in blok and 'je data blijft' not in blok)
    b.close()
srv.shutdown()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
