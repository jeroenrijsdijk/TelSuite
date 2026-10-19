#!/usr/bin/env python3
"""v3.18 opslaantest — de ZIP opslaan in de parkeer-apps, per platform, in Chromium.

Aanleiding: een parkeertelling op Android (Chrome, Samsung S25) kreeg na Stop
de melding "ZIP niet opgeslagen", en ⬇ Download ZIP reageerde daarna niet. Het
gedeelde blok bewaarZip probeerde ook op Android eerst het deelvenster. Chrome
op Android deelt geen ZIP en weigert meteen (NotAllowedError); de app meldde
"niet opgeslagen", en elke tik op de knop deed hetzelfde, zonder ooit te
downloaden. Sinds v3.18: alleen iOS via het deelvenster, zoals pocket.

Het deelvenster is hier nagebootst zoals Chrome op Android het doet: canShare
zegt ja, share weigert.

  A. Android: Stop geeft een echte download (geen deelvenster), een geldige ZIP
     met alle tikken; de noodkopie gaat weg.
  B. Android, herstel (de telling van Jay): de telling staat nog in de
     noodkopie, de pagina gaat opnieuw open. ⬇ Download ZIP downloadt, en
     daarna is de kopie weg.
  C. Ingebouwde browser van een app (Android-WebView, "; wv)"): de download
     wordt aangeboden, maar telt niet als opgeslagen. De status zegt het, de
     kopie blijft, en heropenen biedt de telling weer aan.
  D. Desktop met een deelvenster (Chrome op Windows kent er een): gewoon een
     download.
  E. iPhone: nog steeds het deelvenster, geen download.
Voor parkeertelling, fietsparkeren en capaciteitstelling (gedeeld blok).

Hulp (server, CDN-omleiding, nep-Overpass, noodkopie) komt uit opruimtest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/opslaantest.py
"""
import os, sys, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

ANDROID = ('Mozilla/5.0 (Linux; Android 15; SM-S931B) AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/129.0.0.0 Mobile Safari/537.36')
WEBVIEW = ('Mozilla/5.0 (Linux; Android 15; SM-S931B Build/AP3A.240905.015; wv) AppleWebKit/537.36 '
           '(KHTML, like Gecko) Version/4.0 Chrome/129.0.0.0 Mobile Safari/537.36')
# Chrome op Android: canShare zegt ja, share weigert een ZIP meteen.
WEIGERT = ("window.__deelN=0;navigator.canShare=()=>true;"
           "navigator.share=()=>{window.__deelN++;return Promise.reject(new DOMException('Permission denied','NotAllowedError'));};")
STATUS = "document.getElementById('statusText').textContent"
PARKEER = [
    ('parkeertelling', 'parkeertelling.html', lambda i: "addEntry('goed','L')", '_car.zip'),
    ('fietsparkeren', 'fietsparkeren.html', lambda i: "addEntry('fiets','R')", '_fts.zip'),
    ('capaciteit', 'capaciteitstelling.html', lambda i: "addEntry('regulier','L')", '_cap.zip'),
]

def zip_inhoud(download):
    z = zipfile.ZipFile(download.path())
    namen = z.namelist()
    regels = [n for n in namen if n.endswith('_telregels.csv')]
    n = len(z.read(regels[0]).decode('utf-8').strip().split('\n')) - 1 if regels else -1
    return namen, n

with sync_playwright() as p:
    b = p.chromium.launch()

    for naam, app, tik, staart in PARKEER:
        print('\n== %s ==' % naam)

        print('-- A. Android: Stop downloadt --')
        ctx, pg, fouten = open_app(b, app, WEIGERT, ANDROID)
        pg.evaluate('startSession()'); pg.wait_for_timeout(500)
        loop(ctx, pg, 5, tik)
        with pg.expect_download(timeout=15000) as dl:
            pg.evaluate("document.getElementById('btnStop').click()")
        d = dl.value; pg.wait_for_timeout(300)
        namen, n = zip_inhoud(d)
        eis('%s: een echte download, %s' % (naam, staart), d.suggested_filename.endswith(staart), d.suggested_filename)
        eis('%s: geen deelvenster geprobeerd' % naam, pg.evaluate('window.__deelN') == 0, pg.evaluate('window.__deelN'))
        eis('%s: geldige ZIP met alle 5 tikken' % naam, n == 5, (namen, n))
        eis('%s: status zegt opgeslagen' % naam, 'ZIP opgeslagen' in pg.evaluate(STATUS), pg.evaluate(STATUS))
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: daarna geen kopie, geen melding' % naam, kopie == [] and melding is None and not fouten,
            (kopie, melding, fouten))
        ctx.close()

        print('-- B. Android: een herstelde telling alsnog opslaan --')
        ctx, pg, fouten = open_app(b, app, WEIGERT, ANDROID)
        pg.evaluate('startSession()'); pg.wait_for_timeout(500)
        loop(ctx, pg, 4, tik)
        kopie, melding = heropen(ctx, pg, app)          # niet gestopt: de kopie blijft
        eis('%s: heropenen biedt de telling aan' % naam, len(kopie) == 1 and melding is not None, (kopie, melding))
        eis('%s: ⬇ Download ZIP is aan' % naam, pg.evaluate("!document.getElementById('btnDlZip').disabled"))
        with pg.expect_download(timeout=15000) as dl:
            pg.evaluate("document.getElementById('btnDlZip').click()")
        d = dl.value; pg.wait_for_timeout(300)
        namen, n = zip_inhoud(d)
        eis('%s: één tik geeft de ZIP, met de 4 herstelde tikken' % naam,
            d.suggested_filename.endswith(staart) and n == 4 and pg.evaluate('window.__deelN') == 0,
            (d.suggested_filename, n, pg.evaluate('window.__deelN')))
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: daarna is de kopie weg' % naam, kopie == [] and melding is None and not fouten, (kopie, melding, fouten))
        ctx.close()

        print('-- C. ingebouwde browser: aangeboden, niet bevestigd --')
        ctx, pg, fouten = open_app(b, app, WEIGERT, WEBVIEW)
        pg.evaluate('startSession()'); pg.wait_for_timeout(500)
        loop(ctx, pg, 3, tik)
        with pg.expect_download(timeout=15000) as dl:
            pg.evaluate("document.getElementById('btnStop').click()")
        d = dl.value; pg.wait_for_timeout(300)
        eis('%s: de download wordt aangeboden, zonder deelvenster' % naam,
            d.suggested_filename.endswith(staart) and pg.evaluate('window.__deelN') == 0, d.suggested_filename)
        st = pg.evaluate(STATUS)
        eis('%s: de status noemt de ingebouwde browser, niet "opgeslagen"' % naam,
            'ingebouwde browser' in st and 'ZIP opgeslagen' not in st, st)
        eis('%s: de kopie blijft' % naam, len(pg.evaluate(KOPIE)) == 1, pg.evaluate(KOPIE))
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: heropenen biedt de telling weer aan' % naam, len(kopie) == 1 and melding is not None and not fouten,
            (kopie, melding, fouten))
        ctx.close()

        print('-- D. desktop met deelvenster: download --')
        ctx, pg, fouten = open_app(b, app, WEIGERT)
        pg.evaluate('startSession()'); pg.wait_for_timeout(500)
        loop(ctx, pg, 2, tik)
        with pg.expect_download(timeout=15000) as dl:
            pg.evaluate("document.getElementById('btnStop').click()")
        d = dl.value; pg.wait_for_timeout(300)
        eis('%s: download, geen deelvenster, opgeslagen' % naam,
            d.suggested_filename.endswith(staart) and pg.evaluate('window.__deelN') == 0
            and 'ZIP opgeslagen' in pg.evaluate(STATUS), (d.suggested_filename, pg.evaluate(STATUS)))
        ctx.close()

        print('-- E. iPhone: deelvenster --')
        ctx, pg, fouten = open_app(b, app, deelblad(['ok']), IPHONE)
        downloads = []; pg.on('download', lambda d: downloads.append(d.suggested_filename))
        pg.evaluate('startSession()'); pg.wait_for_timeout(500)
        loop(ctx, pg, 2, tik)
        pg.evaluate("document.getElementById('btnStop').click()"); pg.wait_for_timeout(1500)
        best = pg.evaluate('window.__deelBestanden')
        eis('%s: via het deelvenster, geen download' % naam,
            len(best) == 1 and best[0][0].endswith(staart) and downloads == [], (best, downloads))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d FOUT, %d OK' % (fout, ok)))
sys.exit(1 if fout else 0)
