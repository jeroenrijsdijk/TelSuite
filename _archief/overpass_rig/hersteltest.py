#!/usr/bin/env python3
"""Hersteltest — blijft een telling bewaard als de browser wegvalt?

Per veld-app:
  1. telling starten in Chromium, met GPS (nagebootst, bewegend) en een reeks tikken;
  2. direct na de laatste tik de opslag bevriezen. Dat is de toestand bij een
     harde crash of een weggeveegde tab: geen pagehide, geen unload, niets;
  3. de ZIP die de app ZONDER onderbreking zou maken (referentie);
  4. nieuwe browser met alleen die bevroren opslag: pagina laden, kijken of
     de herstelmelding komt, en de ZIP uit de herstelde telling maken;
  5. de twee ZIP's bestand voor bestand, regel voor regel vergelijken.

Hulp (server, CDN-omleiding, lettertypen) komt uit laadtest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/hersteltest.py
"""
import io, json, os, sys, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HIER, 'laadtest.py'), encoding='utf-8').read()
exec(_src.split('ok = fout = 0')[0])             # ROOT, NM, route, srv, BASIS
from playwright.sync_api import sync_playwright

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

LAT, LON = 51.8500, 4.3000

# Nep-Overpass (v2.72): een raster van woonstraten rond het startpunt, zodat de
# apps echt snappen en _netwerk.csv / _bezocht.csv / snap-trace gevuld raken.
def _osm_raster():
    els, nid = [], 1
    def weg(wid, pts, naam):
        nonlocal nid
        nodes = list(range(nid, nid + len(pts))); nid += len(pts)
        els.append({'type': 'way', 'id': wid, 'nodes': nodes,
                    'geometry': [{'lat': a, 'lon': o} for a, o in pts],
                    'tags': {'highway': 'residential', 'name': naam}})
    for k in range(-3, 4):      # noord-zuid, ~100 m uit elkaar
        o = LON + k * 0.0015
        weg(1000 + k + 3, [(LAT - 0.004 + i * 0.001, o) for i in range(13)], 'Noordstraat %d' % (k + 3))
    for j in range(-4, 9):      # oost-west
        a = LAT + j * 0.0009
        weg(2000 + j + 4, [(a, LON - 0.0045 + i * 0.0015) for i in range(7)], 'Dwarsstraat %d' % (j + 4))
    return json.dumps({'version': 0.6, 'elements': els})
OSM = _osm_raster()
def route_met_osm(r):
    if 'overpass' in r.request.url:
        return r.fulfill(body=OSM, content_type='application/json')
    return route(r)

def nieuwe_context(b, geo=True):
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True,
                        permissions=['geolocation'] if geo else [],
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5} if geo else None)
    ctx.route('**/*', route_met_osm)
    return ctx

def bevries(pg):
    return pg.evaluate('JSON.stringify(Object.assign({}, localStorage))')

def zip_van(pg, js, wacht=15000):
    with pg.expect_download(timeout=wacht) as d:
        pg.evaluate(js)
    return zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))

def inhoud(z):
    """bestandsnaam zonder sessie-id -> regels (sessie-id in de inhoud -> SID).
    Pocket maakt de sessie-id pas bij het stoppen; na herstel is die dus nieuw."""
    sid = next((n[:-len('_sessie.csv')] for n in z.namelist() if n.endswith('_sessie.csv')), '')
    uit = {}
    for n in z.namelist():
        kort = n[len(sid):] if sid and n.startswith(sid) else n
        tekst = z.read(n).decode('utf-8', 'replace')
        uit[kort] = (tekst.replace(sid, 'SID') if sid else tekst).splitlines()
    return uit

def zonder_exporttijd(f, regels):
    """Wat alleen van het moment van exporteren afhangt, telt niet mee:
    eind_tijd in _sessie.csv en de <time> in de GPX-kop."""
    if f.endswith('sessie.csv') and len(regels) > 1:
        kop = regels[0].split(';')
        if 'eind_tijd' in kop:
            k = kop.index('eind_tijd')
            return [regels[0]] + [';'.join(c[:k] + c[k + 1:]) for c in (r.split(';') for r in regels[1:])]
    if f.endswith('.gpx'):
        uit, in_kop = [], False
        for r in regels:
            if '<metadata>' in r: in_kop = True
            if not (in_kop and '<time>' in r): uit.append(r)
            if '</metadata>' in r: in_kop = False
        return uit
    return regels

def vergelijk(naam, ref, her, bekend_weg=()):
    """bekend_weg: bestanden die na herstel bewust ontbreken (pocket bewaart het
    wegennet en de snap-trace niet in de noodopslag: te groot, en de tikken dragen
    hun eigen wayId). Die worden gemeld als BEKEND, niet als fout."""
    a, b_ = inhoud(ref), inhoud(her)
    weg = sorted(set(a) - set(b_)); erbij = sorted(set(b_) - set(a))
    for f in [f for f in weg if f in bekend_weg]:
        print('  BEKEND %s: %s ontbreekt na herstel (bewust niet in de noodopslag)' % (naam, f))
    weg = [f for f in weg if f not in bekend_weg]
    eis(naam + ': zelfde bestanden in de ZIP', not weg and not erbij,
        {'alleen zonder onderbreking': weg, 'alleen na herstel': erbij})
    for f in sorted(set(a) & set(b_)):
        a[f], b_[f] = zonder_exporttijd(f, a[f]), zonder_exporttijd(f, b_[f])
        verschil = [(i, x, y) for i, (x, y) in enumerate(zip(a[f], b_[f])) if x != y]
        eis('%s: %s gelijk (%d regels)' % (naam, f, len(a[f])),
            len(a[f]) == len(b_[f]) and not verschil,
            {'regels': (len(a[f]), len(b_[f])), 'eerste verschil': verschil[:2]})

def loop(ctx, pg, n, tik):
    for i in range(n):
        ctx.set_geolocation({'latitude': LAT + i * 0.00012, 'longitude': LON + i * 0.00005, 'accuracy': 5})
        pg.wait_for_timeout(250)
        pg.evaluate(tik(i))
        pg.wait_for_timeout(60)

def herlaad_met(b, pad, opslag, geo=False):
    ctx = nieuwe_context(b, geo)
    ctx.add_init_script("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');"
                        "var o=%s;for(var k in o)localStorage.setItem(k,o[k]);}" % opslag)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
    pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + pad, wait_until='load'); pg.wait_for_timeout(900)
    return ctx, pg, fouten

with sync_playwright() as p:
    b = p.chromium.launch()

    # ------------------------------------------------ parkeer-apps (3)
    APPS = [('parkeertelling.html', ['goed', 'fout', 'leeg', 'spec']),
            ('fietsparkeren.html', ['fiets', 'brommer', 'breed', 'wrak']),
            ('capaciteitstelling.html', ['regulier', 'gehandicapt', 'gereserveerd', 'laadpaal'])]
    for app, typen in APPS:
        print('\n== %s ==' % app)
        ctx = nieuwe_context(b); pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(600)
        pg.evaluate('startSession()'); pg.wait_for_timeout(400)
        loop(ctx, pg, 12, lambda i: "addEntry('%s','%s')" % (typen[i % 4], 'LR'[i % 2]))
        n_voor = pg.evaluate('entries.length'); gps_voor = pg.evaluate('gpsLog.length')
        opslag = bevries(pg)
        eis('12 tikken geteld, %d GPS-punten' % gps_voor, n_voor == 12, n_voor)
        ref = zip_van(pg, 'exportZip()')
        ctx.close()
        ctx, pg, fouten2 = herlaad_met(b, app, opslag)
        melding = pg.evaluate("(function(){var e=document.getElementById('restoreBanner');return e&&e.style.display!=='none'?e.textContent:null})()")
        eis('na crash: herstelmelding', bool(melding), melding)
        eis('na crash: alle 12 tikken terug', pg.evaluate('entries.length') == 12, pg.evaluate('entries.length'))
        eis('na crash: GPS-spoor terug', pg.evaluate('gpsLog.length') == gps_voor, (pg.evaluate('gpsLog.length'), gps_voor))
        her = zip_van(pg, 'exportZip()')
        vergelijk(app.split('.')[0], ref, her)
        eis('geen JS-fouten', not fouten and not fouten2, fouten + fouten2)
        ctx.close()

    # ------------------------------------------------ pocket (4 modi)
    MODI = [('simpel', "startTelling('car','x','Auto')", lambda i: 'doTap()'),
            ('transect', 'startTransect()', lambda i: "adjustTransect('car','%s',1)" % 'ab'[i % 2]),
            ('winkelstraat', 'startWinkelstraat()', lambda i: "adjustWinkel('%s',1)" % ['tegemoet', 'stilstaand'][i % 2]),
            ('parkeren', 'startParkeren()', lambda i: "adjustParkeer('%s',1)" % ['links_bezet', 'rechts_leeg', 'links_leeg', 'rechts_bezet'][i % 4])]
    for modus, start, tik in MODI:
        print('\n== pocket_count.html — %s ==' % modus)
        ctx = nieuwe_context(b); pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(600)
        pg.evaluate(start); pg.wait_for_timeout(400)
        loop(ctx, pg, 12, tik)
        n_voor = pg.evaluate('telHistory.length'); gps_voor = pg.evaluate('routeLog.length')
        opslag = bevries(pg)
        eis('12 tikken geteld', n_voor == 12, n_voor)
        eis('GPS-route opgebouwd zonder wegennet (Overpass geblokkeerd): %d punten' % gps_voor, gps_voor >= 10, gps_voor)
        ref = zip_van(pg, 'stopTelling()')
        ctx.close()
        ctx, pg, fouten2 = herlaad_met(b, 'pocket_count.html', opslag)
        melding = pg.evaluate("document.getElementById('restore-banner').style.display !== 'none'")
        eis('na crash: herstelmelding', melding)
        eis('na crash: alle 12 tikken terug', pg.evaluate('telHistory.length') == 12, pg.evaluate('telHistory.length'))
        eis('na crash: GPS-spoor terug', pg.evaluate('routeLog.length') == gps_voor, (pg.evaluate('routeLog.length'), gps_voor))
        her = zip_van(pg, 'restoreDownload()')
        vergelijk('pocket ' + modus, ref, her, bekend_weg=('_snap_trace.csv', '_netwerk.csv'))
        eis('geen JS-fouten', not fouten and not fouten2, fouten + fouten2)
        ctx.close()

    # ------------------------------------------------ doortellen na herstel
    # 6 tikken, crash, herladen, Doortellen, nog 6 tikken, stoppen. Verwacht: één
    # telling met alle 12 tikken in de juiste volgorde, dezelfde starttijd (en bij
    # de parkeer-apps dezelfde sessie-id), en een GPS-spoor dat na de onderbreking
    # verder loopt.
    def telregels(z, kol_type, kol_zijde):
        n = [x for x in z.namelist() if x.endswith('_telregels.csv')][0]
        r = z.read(n).decode('utf-8').splitlines()
        kop = r[0].split(';')
        return [(c[kop.index(kol_type)], c[kop.index(kol_zijde)] if kol_zijde else '') for c in (x.split(';') for x in r[1:])]
    def sessie(z):
        n = [x for x in z.namelist() if x.endswith('_sessie.csv')][0]
        r = z.read(n).decode('utf-8').splitlines(); return dict(zip(r[0].split(';'), r[1].split(';')))
    def gpsregels(z):
        n = [x for x in z.namelist() if x.endswith('_gps.csv')]
        return len(z.read(n[0]).decode('utf-8').splitlines()) - 1 if n else 0

    DOOR = [('parkeertelling.html', 'startSession()', 'hervatSessie()', lambda i: "addEntry('%s','%s')" % (['goed', 'fout', 'leeg', 'spec'][i % 4], 'LR'[i % 2]),
             'exportZip()', 'stopSession()', ('type', 'zijde'), [(['goed', 'fout', 'leeg', 'spec'][i % 4], 'LR'[i % 2]) for i in range(12)]),
            ('fietsparkeren.html', 'startSession()', 'hervatSessie()', lambda i: "addEntry('%s','%s')" % (['fiets', 'brommer', 'breed', 'wrak'][i % 4], 'LR'[i % 2]),
             'exportZip()', 'stopSession()', ('type', 'zijde'), [(['fiets', 'brommer', 'breed', 'wrak'][i % 4], 'LR'[i % 2]) for i in range(12)]),
            ('capaciteitstelling.html', 'startSession()', 'hervatSessie()', lambda i: "addEntry('%s','%s')" % (['regulier', 'gehandicapt', 'gereserveerd', 'laadpaal'][i % 4], 'LR'[i % 2]),
             'exportZip()', 'stopSession()', ('type', 'zijde'), [(['regulier', 'gehandicapt', 'gereserveerd', 'laadpaal'][i % 4], 'LR'[i % 2]) for i in range(12)])]
    for app, start, hervat, tik, _exp, stop, kol, verwacht in DOOR:
        print('\n== doortellen: %s ==' % app)
        ctx = nieuwe_context(b); pg = ctx.new_page(); f1 = []
        pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(600)
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 6, tik)
        sid_voor = pg.evaluate('sessionId'); start_voor = pg.evaluate('sessionStartTime'); gps_voor = pg.evaluate('gpsLog.length')
        opslag = bevries(pg); ctx.close()
        ctx, pg, f2 = herlaad_met(b, app, opslag, geo=True)
        eis('Doortellen-knop zichtbaar bij de herstelmelding',
            pg.evaluate("getComputedStyle(document.getElementById('btnHervat')).display !== 'none'"))
        pg.evaluate(hervat); pg.wait_for_timeout(800)
        eis('na Doortellen: sessie loopt, melding en knop weg',
            pg.evaluate('sessionActive') and pg.evaluate("document.getElementById('restoreBanner').style.display === 'none'"))
        for i in range(6):
            ctx.set_geolocation({'latitude': LAT + (i + 8) * 0.00012, 'longitude': LON + (i + 8) * 0.00005, 'accuracy': 5})
            pg.wait_for_timeout(250); pg.evaluate(tik(i + 6)); pg.wait_for_timeout(60)
        with pg.expect_download(timeout=15000) as d:
            pg.evaluate(stop)
        z = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
        rg = telregels(z, *kol)
        eis('alle 12 tikken in één ZIP, in de goede volgorde', rg == verwacht, rg)
        ses = sessie(z)
        eis('zelfde sessie-id als vóór de onderbreking', sid_voor in ''.join(z.namelist()), (sid_voor, z.namelist()[:2]))
        eis('GPS-spoor loopt door na de onderbreking (%d -> %d punten)' % (gps_voor, gpsregels(z)), gpsregels(z) > gps_voor)
        eis('geen JS-fouten', not f1 and not f2, f1 + f2)
        ctx.close()

    POCKET_DOOR = [('simpel', "startTelling('car','x','Auto')", lambda i: 'doTap()'),
                   ('transect', 'startTransect()', lambda i: "adjustTransect('car','%s',1)" % 'ab'[i % 2]),
                   ('winkelstraat', 'startWinkelstraat()', lambda i: "adjustWinkel('%s',1)" % ['tegemoet', 'stilstaand'][i % 2]),
                   ('parkeren', 'startParkeren()', lambda i: "adjustParkeer('%s',1)" % ['links_bezet', 'rechts_leeg', 'links_leeg', 'rechts_bezet'][i % 4])]
    TELLER = {'transect': "(()=>{var s=0;TC_TYPES.forEach(t=>s+=tcCounts[t.id].a+tcCounts[t.id].b);return s})()",
              'winkelstraat': "(()=>{var s=0;for(var k in wsCounts)s+=wsCounts[k];return s})()",
              'parkeren': "(()=>{var s=0;for(var k in pkCounts)s+=pkCounts[k];return s})()",
              'simpel': "+document.getElementById('big-count').textContent"}
    for modus, start, tik in POCKET_DOOR:
        print('\n== doortellen: pocket %s ==' % modus)
        ctx = nieuwe_context(b); pg = ctx.new_page(); f1 = []
        pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(600)
        pg.evaluate(start); pg.wait_for_timeout(400)
        loop(ctx, pg, 6, tik)
        start_voor = pg.evaluate('startTime.toISOString()'); gps_voor = pg.evaluate('routeLog.length')
        opslag = bevries(pg); ctx.close()
        ctx, pg, f2 = herlaad_met(b, 'pocket_count.html', opslag, geo=True)
        pg.evaluate('hervatTelling()'); pg.wait_for_timeout(500)
        eis('na Doortellen: modus %s draait, teller op 6' % modus,
            pg.evaluate('currentModus') == modus and pg.evaluate(TELLER[modus]) == 6, (pg.evaluate('currentModus'), pg.evaluate(TELLER[modus])))
        for i in range(6):
            ctx.set_geolocation({'latitude': LAT + (i + 8) * 0.00012, 'longitude': LON + (i + 8) * 0.00005, 'accuracy': 5})
            pg.wait_for_timeout(250); pg.evaluate(tik(i + 6)); pg.wait_for_timeout(60)
        eis('teller loopt door tot 12', pg.evaluate(TELLER[modus]) == 12 and pg.evaluate('telHistory.length') == 12,
            (pg.evaluate(TELLER[modus]), pg.evaluate('telHistory.length')))
        with pg.expect_download(timeout=15000) as d:
            pg.evaluate('stopTelling()')
        z = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
        n = [x for x in z.namelist() if x.endswith('_telregels.csv')][0]
        eis('alle 12 tikken in één ZIP', len(z.read(n).decode().splitlines()) - 1 == 12)
        eis('starttijd van vóór de onderbreking', pg.evaluate('startTime.toISOString()') == start_voor)
        eis('GPS-route loopt door (%d -> %d punten)' % (gps_voor, gpsregels(z)), gpsregels(z) > gps_voor)
        eis('geen JS-fouten', not f1 and not f2, f1 + f2)
        ctx.close()

    print('\n== pocket: nieuwe telling bij herstelmelding vraagt eerst ==')
    ctx = nieuwe_context(b, geo=False)
    ctx.add_init_script("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');"
                        "var o=%s;for(var k in o)localStorage.setItem(k,o[k]);}" % opslag)
    pg = ctx.new_page(); pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(600)
    vragen = []
    pg.on('dialog', lambda d: (vragen.append(d.message), d.dismiss()))
    pg.evaluate('chooseTransect()'); pg.wait_for_timeout(200)
    eis('bevestiging gevraagd', any('herstelde telling' in v for v in vragen), vragen)
    eis('na Annuleren: herstelde telling staat er nog', pg.evaluate("localStorage.getItem('pocket_sessie') !== null")
        and pg.evaluate("document.getElementById('restore-banner').style.display !== 'none'"))
    ctx.close()

    # ------------------------------------------------ Static
    print('\n== traffic_counter.html (Static) ==')
    TIK = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
           "b[%d %% b.length].click()})()")
    ctx = nieuwe_context(b); pg = ctx.new_page(); f1 = []
    pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(500)
    pg.evaluate('startSession()'); pg.wait_for_timeout(1200)
    for i in range(7): pg.evaluate(TIK % i)
    opslag = bevries(pg); ctx.close()
    eis('Static: noodopslag aanwezig na de tikken', 'static_sessie' in json.loads(opslag))
    ctx, pg, f2 = herlaad_met(b, 'traffic_counter.html', opslag)
    eis('Static: herstelbalk met Doortellen', pg.evaluate("document.getElementById('herstel-balk').style.display !== 'none'")
        and pg.evaluate("document.getElementById('herstel-door').style.display !== 'none'"))
    eis('Static: alle 7 tikken terug', pg.evaluate("document.getElementById('grand-total').textContent") == '7')
    pg.wait_for_timeout(2500)                      # de onderbreking duurt nog even
    pg.evaluate('doortellenStatic()'); pg.wait_for_timeout(300)
    for i in range(5): pg.evaluate(TIK % (i + 7))
    pg.wait_for_timeout(1500)
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()')
    zz = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
    csv = zz.read([x for x in zz.namelist() if x.endswith('_overzicht.csv')][0]).decode('utf-8').splitlines()   # v2.73: ZIP met vier bestanden
    tot = [r for r in csv if r.startswith('TOTAL;')]
    eis('Static: export telt 12', tot and tot[0].split(';')[3] == '12', tot)
    eis('Static: timestamplog heeft 12 regels', sum(1 for r in csv if r[:2].isdigit() and r.count(';') == 2) == 12)
    onder = [r for r in csv if r.startswith('Interruption')]
    eis('Static: onderbreking in de export (%d regels)' % len(onder), len(onder) == 2, onder)
    duur = [r for r in csv if r.startswith('Observed duration;')][0].split(';')[1]
    h, m, sec = map(int, duur.split(':'))
    eis('Static: geobserveerde duur zonder de onderbreking (%s)' % duur, h * 3600 + m * 60 + sec <= 4, duur)
    eis('Static: na End + download is de noodkopie meteen weg (v2.76; was: bij het volgende bezoek)',
        pg.evaluate("localStorage.getItem('static_sessie')") is None)
    eis('Static: geen JS-fouten', not f1 and not f2, f1 + f2)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
