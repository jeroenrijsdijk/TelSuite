#!/usr/bin/env python3
"""v3.14 planlinktest — een planning als link, in Chromium.

  A. Telplanning: Deel als link staat uit zonder wegen en aan met wegen; de
     dialoog toont app, aantal wegen en grootte; de link wijst naar de juiste app
     (auto, fiets, pocket); Kopieer zet hem op het klembord; geen
     lengtewaarschuwing bij een gewoon gebied, wel bij een te groot gebied.
  B. Parkeertelling en fietsparkeren openen de link: paarse wegen, teller
     ingevuld; na herladen nog steeds. Een kapotte link geeft een melding.
  C. Pocket-parkeren opent de link: meteen het parkeerscherm, een regel met de
     opdracht, de straten in paars op de kaart met 'gepland' in de legenda;
     tellen en Stop werken gewoon. Zonder planning: geen regel, geen legenda.
     Een kapotte link: de regel zegt waarom.
  D. De server-route blijft werken (?plan=/planningen/…), ook voor pocket, en
     Opdrachten bouwt voor pocket ?plan=… vóór #parkeren.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/planlinktest.py
"""
import os, sys, json
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

d = 0.003
GEOM = json.dumps({'type': 'Polygon', 'coordinates': [[[LON - d, LAT - d], [LON + d, LAT - d], [LON + d, LAT + d],
                                                        [LON - d, LAT + d], [LON - d, LAT - d]]]})
# Een planning zoals telplanning hem op de server zet (voor de server-route)
SERVERPLAN = json.dumps({'sessie_naam': 'Server-opdracht', 'datum': '2026-10-20', 'tijdstip': '09:00',
                         'teller': 'S9', 'tel_type': 'auto', 'n_wegen': 2, 'wegen': [
    {'osm_way_id': '1', 'naam': 'Noordstraat 3', 'highway': 'residential',
     'geometrie_wkt': 'LINESTRING (%.6f %.6f, %.6f %.6f)' % (LON, LAT - 0.002, LON, LAT + 0.002)},
    {'osm_way_id': '2', 'naam': 'Dwarsstraat 4', 'highway': 'residential',
     'geometrie_wkt': 'LINESTRING (%.6f %.6f, %.6f %.6f)' % (LON - 0.002, LAT, LON + 0.002, LAT)}]})

def route_plan(r):
    if r.request.url.split('?')[0].endswith('/planningen/test.json'):   # niet de pagina met ?plan=…
        return r.fulfill(body=SERVERPLAN, content_type='application/json')
    return route_met_osm(r)

def context(b, breed=False):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800} if breed else {'width': 390, 'height': 844},
                        accept_downloads=True, permissions=['geolocation', 'clipboard-read', 'clipboard-write'],
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5})
    ctx.route('**/*', route_plan)
    return ctx

def pagina(ctx, url):
    pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:120])); pg.on('dialog', lambda dl: dl.accept())
    pg.goto(url, wait_until='load'); pg.wait_for_timeout(700)
    return pg, f

DIALOOG = ("(()=>{var o=document.getElementById('link-overlay');return {open:o.classList.contains('open'),"
           "info:document.getElementById('link-info').textContent,link:document.getElementById('link-tekst').value,"
           "lang:document.getElementById('link-lang').textContent,open_href:document.getElementById('link-open').href,"
           "melding:document.getElementById('link-melding').textContent}})()")

def maak_link(pg, teltype, naam='Wijk Noord', teller='T07'):
    pg.evaluate("document.getElementById('meta-naam').value=%r;document.getElementById('meta-teller').value=%r;"
                "document.getElementById('meta-teltype').value=%r" % (naam, teller, teltype))
    pg.click('#btn-link'); pg.wait_for_timeout(400)
    return pg.evaluate(DIALOOG)

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. telplanning: Deel als link ==')
    ctx = context(b, breed=True)
    pg, f = pagina(ctx, BASIS + 'telplanning.html')
    eis('zonder wegen staat de knop uit', pg.evaluate("document.getElementById('btn-link').disabled"))
    pg.evaluate('fetchWaysForPolygon(%s)' % GEOM); pg.wait_for_timeout(1200)
    n = pg.evaluate('ways.filter(function(w){return w.visible&&w.selected}).length')
    eis('met wegen (%d geselecteerd) staat hij aan' % n, n > 0 and not pg.evaluate("document.getElementById('btn-link').disabled"))
    links = {}
    for tt, app, label in (('auto', 'parkeertelling.html#plan=1.', 'Autoparkeren'),
                           ('fiets', 'fietsparkeren.html#plan=1.', 'Fietsparkeren'),
                           ('pocket', 'pocket_count.html#parkeren&plan=1.', 'Pocket-parkeren')):
        dlg = maak_link(pg, tt)
        links[tt] = dlg['link']
        eis('%s: dialoog open, link naar %s' % (tt, app.split('#')[0]),
            dlg['open'] and dlg['link'].startswith(BASIS + app), dlg['link'][:80])
        eis('%s: info noemt %s, %d wegen en de grootte' % (tt, label, n),
            dlg['info'].startswith(label) and ('%d wegen' % n) in dlg['info'] and 'kB' in dlg['info'], dlg['info'])
        eis('%s: geen lengtewaarschuwing, Openen wijst naar dezelfde link' % tt,
            dlg['lang'] == '' and dlg['open_href'] == dlg['link'], (dlg['lang'], len(dlg['link'])))
        pg.evaluate('sluitLink()')
    print('       link voor %d wegen: %d tekens' % (n, len(links['auto'])))
    maak_link(pg, 'auto')
    pg.click('#link-kopieer'); pg.wait_for_timeout(300)
    eis('Kopieer: melding en de link op het klembord',
        'Gekopieerd' in pg.evaluate(DIALOOG)['melding'] and pg.evaluate('navigator.clipboard.readText()') == links['auto'],
        pg.evaluate(DIALOOG)['melding'])
    eis('Delen alleen als de browser het kan (hier niet)',
        pg.evaluate("getComputedStyle(document.getElementById('link-deel')).display") == 'none')
    pg.click('#btn-close-link'); pg.wait_for_timeout(100)
    eis('sluiten met het kruisje', not pg.evaluate(DIALOOG)['open'])
    # te groot: maak de geometrie van de wegen kunstmatig lang
    pg.evaluate("""ways.forEach(function(w){var c=[];for(var i=0;i<200;i++)c.push((4.3+Math.random()*0.01).toFixed(6)+' '+(51.85+Math.random()*0.01).toFixed(6));
                   w.wkt='LINESTRING ('+c.join(', ')+')';})""")
    dlg = maak_link(pg, 'auto')
    eis('een te groot gebied: waarschuwing, link wel gemaakt (%d tekens)' % len(dlg['link']),
        'Lange link' in dlg['lang'] and len(dlg['link']) > 6000, (dlg['lang'], len(dlg['link'])))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== B. parkeertelling en fietsparkeren openen de link ==')
    for app, tt in (('parkeertelling.html', 'auto'), ('fietsparkeren.html', 'fiets')):
        ctx = context(b)
        pg, f = pagina(ctx, links[tt])
        st = pg.evaluate("({n:planningWegen.length,lagen:planningLayer.getLayers().length,"
                         "teller:document.getElementById('inputTeller').value,status:document.getElementById('statusText').textContent})")
        eis('%s: %d wegen in paars (twee lijnen per weg)' % (app, n), st['n'] == n and st['lagen'] == 2 * n, st)
        eis('%s: teller ingevuld, status noemt de opdracht' % app,
            st['teller'] == 'T07' and 'Wijk Noord' in st['status'], st)
        pg.reload(wait_until='load'); pg.wait_for_timeout(700)
        eis('%s: na herladen nog steeds geladen' % app, pg.evaluate('planningWegen.length') == n)
        eis('%s: geen JS-fouten' % app, not f, f)
        pg2, f2 = pagina(ctx, BASIS + app + '#plan=1.kapot')
        s2 = pg2.evaluate("document.getElementById('statusText').textContent")
        eis('%s: kapotte link: melding, geen wegen' % app,
            'Opdracht laden mislukt' in s2 and 'beschadigd' in s2 and pg2.evaluate('planningWegen.length') == 0, s2)
        eis('%s: kapotte link: geen JS-fouten' % app, not f2, f2)
        ctx.close()

    print('\n== C. pocket-parkeren opent de link ==')
    PK = ("(()=>{var r=document.getElementById('pk-plan'),z=document.getElementById('parkeer-screen');"
          "return {scherm:getComputedStyle(z).display,ingang:document.documentElement.classList.contains('pk-ingang'),"
          "regel:r.textContent,zicht:r.getBoundingClientRect().height>0,fout:r.classList.contains('fout'),"
          "plan:pkPlanning&&pkPlanning.lijnen?pkPlanning.lijnen.length:null}})()")
    KAART = ("(()=>{openPkMap();return new Promise(function(k){setTimeout(function(){var n=0;"
             "pkMapLayers.eachLayer(function(l){if(l.options&&l.options.color==='#8e44ad')n++});"
             "k({paars:n,legenda:getComputedStyle(document.getElementById('pk-map-legend-plan')).display});},300)})})()")
    ctx = context(b)
    pg, f = pagina(ctx, links['pocket'])
    s = pg.evaluate(PK)
    eis('meteen het parkeerscherm (directe ingang, ook met &plan=)', s['scherm'] == 'flex' and s['ingang'], s)
    eis('regel boven de vakken: opdracht, %d straten' % n,
        s['zicht'] and 'Opdracht: Wijk Noord' in s['regel'] and ('%d straten' % n) in s['regel'] and not s['fout'], s)
    k = pg.evaluate(KAART)
    eis('kaart: %d straten in paars, gepland in de legenda' % n, k['paars'] == n and k['legenda'] != 'none', k)
    pg.evaluate('closePkMap()')
    for i in range(3):
        pg.evaluate("adjustParkeer('rechts_bezet',1)")
    eis('tellen werkt gewoon (3)', pg.evaluate('telCount') == 3)
    with pg.expect_download(timeout=8000) as dl:
        pg.evaluate('stopTelling()')
    eis('Stop levert een ZIP', dl.value.suggested_filename.endswith('.zip'), dl.value.suggested_filename)
    eis('geen JS-fouten', not f, f)
    ctx.close()
    ctx = context(b)
    pg, f = pagina(ctx, BASIS + 'pocket_count.html#parkeren')
    s = pg.evaluate(PK); k = pg.evaluate(KAART)
    eis('zonder planning: parkeerscherm, geen regel, geen paars, geen legenda',
        s['scherm'] == 'flex' and not s['zicht'] and k['paars'] == 0 and k['legenda'] == 'none', (s, k))
    pg2, f2 = pagina(ctx, BASIS + 'pocket_count.html#parkeren&plan=1.kapot')
    s = pg2.evaluate(PK)
    eis('kapotte link: parkeerscherm, regel zegt waarom',
        s['scherm'] == 'flex' and s['zicht'] and s['fout'] and 'niet geladen' in s['regel'] and 'beschadigd' in s['regel'], s)
    eis('geen JS-fouten', not f and not f2, (f, f2))
    ctx.close()

    print('\n== D. de server-route blijft werken ==')
    ctx = context(b)
    pg, f = pagina(ctx, BASIS + 'parkeertelling.html?plan=/planningen/test.json')
    eis('parkeertelling ?plan=: 2 wegen, teller S9',
        pg.evaluate('planningWegen.length') == 2 and pg.evaluate("document.getElementById('inputTeller').value") == 'S9')
    pg, f2 = pagina(ctx, BASIS + 'pocket_count.html?plan=/planningen/test.json#parkeren')
    s = pg.evaluate(PK)
    eis('pocket ?plan=…#parkeren: parkeerscherm en de opdracht', s['scherm'] == 'flex' and s['plan'] == 2
        and 'Server-opdracht' in s['regel'], s)
    ctx.close()
    ctx = context(b, breed=True)
    pg, f3 = pagina(ctx, BASIS + 'telplanning.html')
    with pg.expect_navigation():
        pg.evaluate("startOpdracht({tel_type:'pocket', bestand:'test.json'})")
    eis('Opdrachten, pocket: ?plan=… vóór #parkeren', pg.url == BASIS + 'pocket_count.html?plan=%2Fplanningen%2Ftest.json#parkeren', pg.url)
    pg.wait_for_timeout(700)
    eis('en pocket laadt hem', pg.evaluate('pkPlanning && pkPlanning.lijnen ? pkPlanning.lijnen.length : 0') == 2)
    eis('geen JS-fouten', not f and not f2 and not f3, (f, f2, f3))
    ctx.close()

    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d FOUT, %d OK' % (fout, ok)))
sys.exit(1 if fout else 0)
