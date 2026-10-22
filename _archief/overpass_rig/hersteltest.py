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

v3.27: de kaart-PNG van de parkeer-apps wordt pixelrij voor pixelrij vergeleken,
zonder de kopbalk. Daar staat het tijdstip van exporteren in (tot op de minuut).
Viel de referentie in een andere minuut dan de herstelde export, dan verschilde
het bestand; dat was de "wisselvallige" fout (fietsparkeren: _kaart.png).
Pocket bewaart sinds v3.27 ook het wegennet, dus _netwerk.csv hoort na herstel
gelijk te zijn.

Hulp (server, CDN-omleiding, lettertypen) komt uit laadtest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/hersteltest.py
"""
import io, json, os, struct, sys, zipfile, zlib
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

# v3.27: een raster waarin de straten elkaar op de kruisingen raken (gedeelde
# knooppunten), zodat er aansluitingen (snap.adjacency) zijn om te herstellen.
def _osm_kruisend():
    lats = [LAT - 0.004 + i * 0.0009 for i in range(14)]
    lons = [LON - 0.0045 + k * 0.0015 for k in range(7)]
    knoop = lambda i, k: 500000 + i * 100 + k
    els = [{'type': 'way', 'id': 3000 + k, 'nodes': [knoop(i, k) for i in range(14)],
            'geometry': [{'lat': lats[i], 'lon': lons[k]} for i in range(14)],
            'tags': {'highway': 'residential', 'name': 'Lengtestraat %d' % k}} for k in range(7)]
    els += [{'type': 'way', 'id': 4000 + i, 'nodes': [knoop(i, k) for k in range(7)],
             'geometry': [{'lat': lats[i], 'lon': lons[k]} for k in range(7)],
             'tags': {'highway': 'living_street', 'name': 'Breedtestraat %d' % i}} for i in range(14)]
    return json.dumps({'version': 0.6, 'elements': els})
OSM_KRUISEND = _osm_kruisend()
OSM_LEEG = json.dumps({'version': 0.6, 'elements': []})

def route_met(osm):
    def r_(r):
        if 'overpass' in r.request.url:
            return r.fulfill(body=osm, content_type='application/json')
        return route(r)
    return r_
route_met_osm = route_met(OSM)

def nieuwe_context(b, geo=True, osm=None):
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True,
                        permissions=['geolocation'] if geo else [],
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5} if geo else None)
    ctx.route('**/*', route_met(osm) if osm else route_met_osm)
    return ctx

def bevries(pg):
    return pg.evaluate('JSON.stringify(Object.assign({}, localStorage))')

def zip_van(pg, js, wacht=15000):
    with pg.expect_download(timeout=wacht) as d:
        pg.evaluate(js)
    return zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))

def inhoud(z):
    """bestandsnaam zonder sessie-id -> regels (sessie-id in de inhoud -> SID).
    Een PNG blijft bytes; die vergelijkt png_verschil."""
    sid = next((n[:-len('_sessie.csv')] for n in z.namelist() if n.endswith('_sessie.csv')), '')
    uit = {}
    for n in z.namelist():
        kort = n[len(sid):] if sid and n.startswith(sid) else n
        if n.endswith('.png'): uit[kort] = z.read(n); continue
        tekst = z.read(n).decode('utf-8', 'replace')
        uit[kort] = (tekst.replace(sid, 'SID') if sid else tekst).splitlines()
    return uit

def png_rijen(data):
    """(breedte, hoogte, [gefilterde rijen]) uit een PNG, zonder externe module.
    De rijen zijn nog gefilterd; dezelfde pixels geven bij dezelfde encoder
    dezelfde bytes, behalve de eerste rij na een verschil (filter kijkt omhoog)."""
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'geen PNG'
    i, idat, ihdr = 8, b'', None
    while i < len(data):
        n, soort = struct.unpack('>I4s', data[i:i + 8])
        if soort == b'IHDR': ihdr = struct.unpack('>IIBB', data[i + 8:i + 18])
        elif soort == b'IDAT': idat += data[i + 8:i + 8 + n]
        i += 12 + n
    w, h, diepte, kleur = ihdr
    bpp = {6: 4, 2: 3, 4: 2, 0: 1}[kleur] * diepte // 8
    ruw, stap = zlib.decompress(idat), 1 + w * bpp
    return w, h, [ruw[r * stap:(r + 1) * stap] for r in range(h)]

def png_verschil(a, b):
    """Rijen die verschillen buiten de kopbalk. De kop (W x 4%) draagt het
    exporttijdstip; de eerste rij eronder kan door het filter meeverschillen."""
    wa, ha, ra = png_rijen(a); wb, hb, rb = png_rijen(b)
    if (wa, ha) != (wb, hb): return 'maat %dx%d tegen %dx%d' % (wa, ha, wb, hb)
    kop = round(wa * 0.04) + 1
    anders = [r for r in range(ha) if ra[r] != rb[r] and r > kop]
    return 'rijen %s' % anders[:5] if anders else ''

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
    """bekend_weg: bestanden die na herstel bewust ontbreken (pocket bewaart de
    snap-trace niet in de noodopslag; het wegennet wel, sinds v3.27). Die worden
    gemeld als BEKEND, niet als fout."""
    a, b_ = inhoud(ref), inhoud(her)
    weg = sorted(set(a) - set(b_)); erbij = sorted(set(b_) - set(a))
    for f in [f for f in weg if f in bekend_weg]:
        print('  BEKEND %s: %s ontbreekt na herstel (bewust niet in de noodopslag)' % (naam, f))
    weg = [f for f in weg if f not in bekend_weg]
    eis(naam + ': zelfde bestanden in de ZIP', not weg and not erbij,
        {'alleen zonder onderbreking': weg, 'alleen na herstel': erbij})
    for f in sorted(set(a) & set(b_)):
        if f.endswith('.png'):
            v = png_verschil(a[f], b_[f])
            eis('%s: %s gelijk (pixels, zonder de kopbalk met het exporttijdstip)' % (naam, f), not v, v)
            continue
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

def herlaad_met(b, pad, opslag, geo=False, osm=None):
    ctx = nieuwe_context(b, geo, osm)
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
        melding = pg.evaluate("(function(){var e=document.getElementById('herstel-melding');return e&&e.style.display!=='none'?e.textContent:null})()")   # v3.22: gedeelde melding
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
        pg.wait_for_function('Object.keys(snap.elements).length > 0', timeout=20000)   # pocket haalt het netwerk ~4 s na de start
        loop(ctx, pg, 12, tik)
        pg.wait_for_function('!snap.fetchInFlight', timeout=10000)   # geen netwerk meer onderweg
        n_voor = pg.evaluate('telHistory.length'); gps_voor = pg.evaluate('routeLog.length')
        net_voor = pg.evaluate('Object.keys(snap.elements).length')
        opslag = bevries(pg)
        eis('12 tikken geteld', n_voor == 12, n_voor)
        eis('GPS-route opgebouwd: %d punten, wegennet %d wegen' % (gps_voor, net_voor), gps_voor >= 10 and net_voor > 0, (gps_voor, net_voor))
        ref = zip_van(pg, 'stopTelling()')
        ctx.close()
        ctx, pg, fouten2 = herlaad_met(b, 'pocket_count.html', opslag)
        melding = pg.evaluate("document.getElementById('herstel-melding').style.display !== 'none'")
        eis('na crash: herstelmelding', melding)
        eis('na crash: alle 12 tikken terug', pg.evaluate('telHistory.length') == 12, pg.evaluate('telHistory.length'))
        eis('na crash: GPS-spoor terug', pg.evaluate('routeLog.length') == gps_voor, (pg.evaluate('routeLog.length'), gps_voor))
        eis('na crash: wegennet terug (v3.27)', pg.evaluate('Object.keys(snap.elements).length') == net_voor,
            (pg.evaluate('Object.keys(snap.elements).length'), net_voor))
        her = zip_van(pg, 'restoreDownload()')
        vergelijk('pocket ' + modus, ref, her, bekend_weg=('_snap_trace.csv',))
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
            pg.evaluate("!!document.querySelector('#herstel-melding button[onclick=\"hervatSessie()\"]') && document.getElementById('herstel-melding').style.display !== 'none'"))
        pg.evaluate(hervat); pg.wait_for_timeout(800)
        eis('na Doortellen: sessie loopt, melding en knop weg',
            pg.evaluate('sessionActive') and pg.evaluate("document.getElementById('herstel-melding').style.display === 'none'"))
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
        and pg.evaluate("document.getElementById('herstel-melding').style.display !== 'none'"))
    ctx.close()

    # ------------------------------------------------ pocket: het wegennet (v3.27)
    # Tellen in een netwerk met kruisingen, crash, herladen in een browser die
    # GEEN wegennet meer krijgt (Overpass leeg, geen tegels), Doortellen, stoppen.
    # Alles wat de ZIP aan wegen heeft, moet dus uit de noodkopie komen. Tot
    # v3.27 had deze ZIP geen _netwerk.csv.
    print('\n== pocket: het wegennet in de noodkopie (v3.27) ==')
    ctx = nieuwe_context(b, osm=OSM_KRUISEND); pg = ctx.new_page(); f1 = []
    pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(600)
    pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(400)
    pg.wait_for_function('Object.keys(snap.elements).length > 0', timeout=20000)   # pocket haalt het netwerk ~4 s na de start
    loop(ctx, pg, 6, lambda i: 'doTap()')
    pg.wait_for_function('!snap.fetchInFlight', timeout=10000)
    wegen_voor = sorted(pg.evaluate('Object.keys(snap.elements)'))
    aansl = "JSON.stringify(Object.keys(snap.adjacency).sort().map(k=>[k,Object.keys(snap.adjacency[k]).sort()]))"
    aansl_voor = pg.evaluate(aansl)
    sid = pg.evaluate('pocketSid()')
    kopie = pg.evaluate("JSON.parse(localStorage.getItem('pocket_sessie_netwerk') || 'null')")
    eis('noodkopie van het netwerk: deze telling, alle %d wegen' % len(wegen_voor),
        bool(kopie) and kopie.get('sessieId') == sid and sorted(kopie.get('wegen', {})) == wegen_voor and len(wegen_voor) == 21,
        (kopie and kopie.get('sessieId'), sid, len(wegen_voor)))
    eis('per weg: soort, naam, coördinaten en knooppunten',
        bool(kopie) and all(len(r) == 4 and r[0] and r[1] and len(r[2]) == 2 * len(r[3]) >= 4 for r in kopie['wegen'].values()))
    opslag = bevries(pg); ctx.close()

    ctx, pg, f2 = herlaad_met(b, 'pocket_count.html', opslag, geo=True, osm=OSM_LEEG)
    eis('na crash: alle wegen terug', sorted(pg.evaluate('Object.keys(snap.elements)')) == wegen_voor)
    eis('na crash: de aansluitingen terug (%d wegen met buren)' % len(json.loads(aansl_voor)),
        pg.evaluate(aansl) == aansl_voor and len(json.loads(aansl_voor)) == 21)
    pg.evaluate('hervatTelling()'); pg.wait_for_timeout(500)
    eis('na Doortellen: het netwerk blijft (de start wist het niet)', sorted(pg.evaluate('Object.keys(snap.elements)')) == wegen_voor)
    eis('na Doortellen: de noodkopie van het netwerk staat er weer',
        pg.evaluate("(JSON.parse(localStorage.getItem('pocket_sessie_netwerk')||'{}').sessieId)") == sid)
    for i in range(6):
        ctx.set_geolocation({'latitude': LAT + (i + 8) * 0.00012, 'longitude': LON + (i + 8) * 0.00005, 'accuracy': 5})
        pg.wait_for_timeout(250); pg.evaluate('doTap()'); pg.wait_for_timeout(60)
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('stopTelling()')
    z = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
    nw = [x for x in z.namelist() if x.endswith('_netwerk.csv')]
    ids = sorted(set(r.split(';')[0] for r in z.read(nw[0]).decode('utf-8').splitlines()[1:])) if nw else []
    eis('ZIP: _netwerk.csv met alle wegen van vóór de onderbreking', ids == wegen_voor, (nw, len(ids)))
    tr = z.read([x for x in z.namelist() if x.endswith('_telregels.csv')][0]).decode('utf-8').splitlines()
    k = tr[0].split(';').index('osm_way_id')
    wid = [r.split(';')[k] for r in tr[1:]]
    eis('ZIP: alle 12 tikken op een weg uit dat netwerk', len(wid) == 12 and all(w in wegen_voor for w in wid), wid)
    pg.wait_for_timeout(300)
    eis('na de export: noodkopie en netwerkkopie samen weg',
        pg.evaluate("localStorage.getItem('pocket_sessie') === null && localStorage.getItem('pocket_sessie_netwerk') === null"))
    eis('geen JS-fouten', not f1 and not f2, f1 + f2)
    ctx.close()

    print('\n== pocket: netwerkkopie van een andere telling, en een volle opslag ==')
    vreemd = json.loads(opslag)
    vreemd['pocket_sessie_netwerk'] = json.dumps({'sessieId': '20200101_000000_xyz_pkt_s', 'wegen': {
        '99': ['residential', 'Elders', [LAT, LON, LAT + 0.001, LON], [1, 2]]}})
    ctx, pg, f3 = herlaad_met(b, 'pocket_count.html', json.dumps(vreemd))
    eis('een netwerk van een andere telling wordt niet geladen',
        pg.evaluate('Object.keys(snap.elements).length') == 0 and pg.evaluate('telHistory.length') == 6)
    ctx.close()

    # Opslag vol, 1: het netwerk past niet. De telling gaat door, de tikken worden
    # nog bewaard, er is geen melding, en het netwerk wordt niet meer geprobeerd.
    VOL_NET = ("(()=>{var z=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){"
               "if(k==='pocket_sessie_netwerk'){window._netPogingen=(window._netPogingen||0)+1;"
               "throw new DOMException('vol','QuotaExceededError');}return z.call(this,k,v)}})()")
    # Opslag vol, 2: de tikken passen alleen als het netwerk ruimte maakt.
    VOL_TIK = ("(()=>{var z=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){"
               "if(k==='pocket_sessie'&&this.getItem('pocket_sessie_netwerk')!==null)"
               "throw new DOMException('vol','QuotaExceededError');return z.call(this,k,v)}})()")
    EXTRA = json.dumps([{'type': 'way', 'id': 9001, 'nodes': [1, 2],                # het netwerk groeit
                         'geometry': [{'lat': LAT, 'lon': LON}, {'lat': LAT + 0.001, 'lon': LON}],
                         'tags': {'highway': 'footway'}}])
    for naam, vol in (('het netwerk past niet', VOL_NET), ('de tikken passen alleen zonder netwerk', VOL_TIK)):
        ctx = nieuwe_context(b, osm=OSM_KRUISEND); pg = ctx.new_page(); f4 = []
        pg.on('pageerror', lambda e: f4.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(600)
        pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(400)
        pg.wait_for_function('Object.keys(snap.elements).length > 0', timeout=20000)   # pocket haalt het netwerk ~4 s na de start
        pg.evaluate(vol)
        loop(ctx, pg, 4, lambda i: 'doTap()')
        pg.wait_for_function('!snap.fetchInFlight', timeout=10000)
        pg.evaluate('snapVerwerkNetwerk(%s, %f, %f, ++snap.fetchSeq, "test")' % (EXTRA, LAT, LON))
        pg.evaluate('doTap()')
        st = pg.evaluate("({tik: (JSON.parse(localStorage.getItem('pocket_sessie')||'{}').telHistory||[]).length,"
                         " net: localStorage.getItem('pocket_sessie_netwerk') !== null, vol: !!document.getElementById('kopie-vol'),"
                         " uit: netwerkKopieUit, pogingen: window._netPogingen || 0})")
        eis('opslag vol (%s): alle 5 tikken bewaard, geen netwerk, geen melding' % naam,
            st['tik'] == 5 and not st['net'] and not st['vol'] and st['uit'], st)
        if vol is VOL_NET:
            eis('opslag vol: het netwerk wordt daarna niet opnieuw geprobeerd', st['pogingen'] == 1, st)
        eis('geen JS-fouten', not f4, f4)
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
    eis('Static: herstelmelding met Doortellen', pg.evaluate("document.getElementById('herstel-melding').style.display !== 'none'")
        and pg.evaluate("!!document.querySelector('#herstel-melding button[onclick=\"doortellenStatic()\"]')"))
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
