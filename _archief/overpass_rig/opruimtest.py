#!/usr/bin/env python3
"""v2.76/v2.77 opruimtest — noodopslag weg na een bevestigde download, en alleen dan.

Aanleiding: pocket schreef de noodkopie na Stop + Sluiten opnieuw weg bij de
eerstvolgende app-wissel (telHistory was nog gevuld), en bood bij heropenen een
telling aan die allang gedownload was. De parkeer-apps lieten het wegennet van
de sessie staan (een Overpass-antwoord dat na Stop binnenkwam), en Static liet
zijn kopie staan tot je Static weer opende.

  A. Normale route (download lukt): na download, Sluiten, app-wissel en
     weggaan staat er geen sessie-kopie meer, en heropenen geeft geen melding.
     Voor alle vijf de veld-apps (pocket in twee modi).
  B. iPhone, deelblad GEANNULEERD: de kopie blijft staan (de ZIP is niet
     opgeslagen) en heropenen biedt de telling weer aan. Sinds v2.77 ook in de
     parkeer-apps, zonder ongevraagde download.
  C. iPhone, deelblad VOLTOOID: de kopie verdwijnt meteen, ook zonder Sluiten.
  D. iPhone, eerst geannuleerd, dan via de knop in het voorbeeldscherm wel
     opgeslagen: pas dan weg.
  E. Voorkeuren blijven: taal, tellernaam en kantelmodus horen er te blijven.
  F. Parkeer-apps (v2.77): de ZIP-knop biedt dezelfde ZIP opnieuw aan, en
     nooit de ZIP van een vorige sessie.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/opruimtest.py
"""
import os, sys
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
exec(_hsrc[_hsrc.index('LAT, LON = 51.8500'):_hsrc.index('with sync_playwright() as p:')])

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

VERBERG = ("Object.defineProperty(document,'hidden',{value:true,configurable:true});"
           "Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});"
           "document.dispatchEvent(new Event('visibilitychange'));")
KOPIE = "Object.keys(localStorage).filter(k=>/_sessie/.test(k))"
MELDING = """(()=>{for (var i of ['restoreBanner','restore-banner','herstel-balk']){
  var e=document.getElementById(i); if(e && e.style.display!=='none') return i;} return null})()"""
TIK_STATIC = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
              "b[%d %% b.length].click()})()")
IPHONE = ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 '
          '(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')

def deelblad(uitkomsten):
    """Nep-deelblad (iOS): elke aanroep neemt de volgende uitkomst ('ok'/'annuleer')."""
    return ("window.__deel=%r;window.__deelN=0;navigator.canShare=()=>true;"
            "window.__deelBestanden=[];"
            "navigator.share=(d)=>{window.__deelBestanden.push((d&&d.files&&d.files[0])?[d.files[0].name,d.files[0].size]:null);"
            "var u=window.__deel[Math.min(window.__deelN++,window.__deel.length-1)];"
            "return u==='ok'?Promise.resolve():Promise.reject(new DOMException('geannuleerd','AbortError'));};"
            % list(uitkomsten))

def open_app(b, app, init='', ua=None):
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True,
                        permissions=['geolocation'], user_agent=ua,
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5})
    ctx.route('**/*', route_met_osm)
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(500)
    return ctx, pg, fouten

def heropen(ctx, pg, app):
    pg.goto(BASIS + 'index.html', wait_until='load'); pg.wait_for_timeout(300)   # pagehide
    pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(800)
    return pg.evaluate(KOPIE), pg.evaluate(MELDING)

APPS = [
  ('parkeertelling', 'parkeertelling.html', 'startSession()', lambda i: "addEntry('goed','L')", 'stopSession()', None),
  ('fietsparkeren', 'fietsparkeren.html', 'startSession()', lambda i: "addEntry('fiets','R')", 'stopSession()', None),
  ('capaciteit', 'capaciteitstelling.html', 'startSession()', lambda i: "addEntry('regulier','L')", 'stopSession()', None),
  ('pocket parkeren', 'pocket_count.html', 'startParkeren()', lambda i: "adjustParkeer('links_bezet',1)", 'stopTelling()', 'closePreview()'),
  ('pocket simpel', 'pocket_count.html', "startTelling('car','x','Auto')", lambda i: 'doTap()', 'stopTelling()', 'closePreview()'),
  ('Static', 'traffic_counter.html', 'startSession()', lambda i: TIK_STATIC % i, 'endSession()', None),
]

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. normale route: na een geslaagde download blijft er niets staan ==')
    for naam, app, start, tik, stop, sluit in APPS:
        ctx, pg, fouten = open_app(b, app)
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 5, tik)
        eis('%s: tijdens het tellen staat er een kopie' % naam, len(pg.evaluate(KOPIE)) >= 1, pg.evaluate(KOPIE))
        with pg.expect_download(timeout=15000):
            pg.evaluate(stop)
        pg.wait_for_timeout(900)                    # ook een Overpass-antwoord na Stop
        if sluit: pg.evaluate(sluit); pg.wait_for_timeout(200)
        pg.evaluate(VERBERG); pg.wait_for_timeout(200)
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: na download, app-wissel en weggaan geen kopie, geen melding' % naam,
            kopie == [] and melding is None and not fouten, (kopie, melding, fouten))
        ctx.close()

    print('\n== B. iPhone, deelblad geannuleerd: de kopie blijft ==')
    for naam, app, start, tik, stop, sluit in APPS:
        ctx, pg, fouten = open_app(b, app, deelblad(['annuleer']), IPHONE)
        downloads = []; pg.on('download', lambda d: downloads.append(d.suggested_filename))
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 5, tik)
        pg.evaluate(stop); pg.wait_for_timeout(1500)
        eis('%s: geen ongevraagde download na annuleren' % naam, downloads == [], downloads)
        pg.evaluate(VERBERG); pg.wait_for_timeout(200)
        eis('%s: na geannuleerd deelblad staat de kopie er nog' % naam, len(pg.evaluate(KOPIE)) == 1, pg.evaluate(KOPIE))
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: heropenen biedt de telling weer aan' % naam, len(kopie) == 1 and melding is not None and not fouten,
            (kopie, melding, fouten))
        ctx.close()

    print('\n== C. iPhone, deelblad voltooid: meteen weg, ook zonder Sluiten ==')
    for naam, app, start, tik, stop, sluit in APPS:
        ctx, pg, fouten = open_app(b, app, deelblad(['ok']), IPHONE)
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 5, tik)
        pg.evaluate(stop); pg.wait_for_timeout(1500)
        pg.evaluate(VERBERG); pg.wait_for_timeout(200)
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: opgeslagen via deelblad, geen Sluiten: geen kopie, geen melding' % naam,
            kopie == [] and melding is None and not fouten, (kopie, melding, fouten))
        ctx.close()

    print('\n== D. iPhone: eerst geannuleerd, dan via de knop alsnog opgeslagen ==')
    for naam, app, start, tik, stop, opnieuw in [
            ('pocket', 'pocket_count.html', 'startParkeren()', lambda i: "adjustParkeer('rechts_leeg',1)", 'stopTelling()', 'savePreviewZip()'),
            ('Static', 'traffic_counter.html', 'startSession()', lambda i: TIK_STATIC % i, 'endSession()', 'exportCSV()'),
            ('parkeertelling', 'parkeertelling.html', 'startSession()', lambda i: "addEntry('fout','R')", 'stopSession()', 'exportZip()'),
            ('fietsparkeren', 'fietsparkeren.html', 'startSession()', lambda i: "addEntry('wrak','L')", 'stopSession()', 'exportZip()'),
            ('capaciteit', 'capaciteitstelling.html', 'startSession()', lambda i: "addEntry('laadpaal','R')", 'stopSession()', 'exportZip()')]:
        ctx, pg, fouten = open_app(b, app, deelblad(['annuleer', 'ok']), IPHONE)
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 4, tik)
        pg.evaluate(stop); pg.wait_for_timeout(1500)
        eis('%s: na annuleren nog een kopie' % naam, len(pg.evaluate(KOPIE)) == 1)
        pg.evaluate(opnieuw); pg.wait_for_timeout(400)
        pg.evaluate(VERBERG); pg.wait_for_timeout(200)
        kopie, melding = heropen(ctx, pg, app)
        eis('%s: na alsnog opslaan weg, ook na app-wissel' % naam, kopie == [] and melding is None and not fouten,
            (kopie, melding, fouten))
        ctx.close()

    print('\n== E. voorkeuren blijven staan ==')
    ctx, pg, fouten = open_app(b, 'parkeertelling.html')
    pg.evaluate("document.getElementById('inputTeller').value='Jay'")
    pg.evaluate('startSession()'); pg.wait_for_timeout(500)
    loop(ctx, pg, 2, lambda i: "addEntry('goed','L')")
    with pg.expect_download(timeout=15000):
        pg.evaluate('stopSession()')
    pg.wait_for_timeout(900)
    eis('tellernaam blijft bewaard (bedoeld, staat in de privacyverklaring)',
        pg.evaluate("localStorage.getItem('parkeer_teller')") == 'Jay')
    ctx.close()

    print('\n== F. parkeer-apps: dezelfde ZIP opnieuw, nooit die van een vorige sessie ==')
    ctx, pg, fouten = open_app(b, 'parkeertelling.html', deelblad(['annuleer', 'ok', 'ok']), IPHONE)
    pg.evaluate('startSession()'); pg.wait_for_timeout(500)
    loop(ctx, pg, 3, lambda i: "addEntry('goed','L')")
    pg.evaluate('stopSession()'); pg.wait_for_timeout(1500)
    eis('na annuleren: status zegt dat de ZIP niet is opgeslagen',
        'niet opgeslagen' in pg.evaluate("document.getElementById('statusText').textContent"),
        pg.evaluate("document.getElementById('statusText').textContent"))
    pg.evaluate("(()=>{window.__inpak=0;var g=JSZip.prototype.generateAsync;"
                "JSZip.prototype.generateAsync=function(){window.__inpak++;return g.apply(this,arguments)};})()")
    pg.evaluate('exportZip()'); pg.wait_for_timeout(300)
    best = pg.evaluate('window.__deelBestanden')
    eis('opnieuw via de knop: hetzelfde bestand, zonder opnieuw in te pakken',
        len(best) == 2 and best[0] == best[1] and pg.evaluate('window.__inpak') == 0,
        (best, pg.evaluate('window.__inpak')))
    eis('status meldt opgeslagen', 'ZIP opgeslagen' in pg.evaluate("document.getElementById('statusText').textContent"))
    pg.evaluate('startSession()'); pg.wait_for_timeout(500)
    loop(ctx, pg, 3, lambda i: "addEntry('goed','L')")    # zelfde aantal tikken als de vorige sessie
    pg.evaluate('stopSession()'); pg.wait_for_timeout(1500)
    best = pg.evaluate('window.__deelBestanden')
    eis('nieuwe sessie met evenveel tikken: een nieuwe ZIP, niet die van de vorige',
        len(best) == 3 and best[2][0] != best[0][0], best)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
