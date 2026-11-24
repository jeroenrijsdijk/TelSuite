#!/usr/bin/env python3
"""v3.66 — Telplanning: de cache als terugval.

Jay: "En uit de lokale cache halen, als ophalen niet lukt?" Gekozen: telplanning
onthoudt zijn eigen antwoorden en leest ook de tegels van de telapps; en alleen
als de cache de hele contour dekt.

  A. Een goed antwoord gaat de cache in (telsuite_planning), met de knopen.
  B. Overpass faalt (beide servers): de wegen komen uit de cache, met een
     melding (datum dd-mm-jjjj, Vernieuwen) en zonder nieuwe pogingen; knippen
     kan (de knopen zijn er).
  C. Een grotere contour die de cache niet helemaal dekt: geen cache, de gewone
     nieuwe poging.
  D. Vernieuwen als Overpass weer werkt: de wegen zijn vers, de keuze en een knip
     blijven.
  E. Alleen tegels van de telapps (telsuite_osm, schema 3): gebruikt. Een tegel
     met schema 2: niet.
  F. De tegeldatabase: telplanning maakt hem nooit half aan; parkeertelling werkt
     er daarna gewoon mee.
  G. Opruimen: een gebied ouder dan 90 dagen en een gebied dat een nieuw gebied
     helemaal bevat, gaan weg.
  H. Overpass werkt: de cache doet niets (altijd eerst Overpass).

Hulp (server, CDN-omleiding, nep-OSM met knopen) komt uit hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/cachetest.py
"""
import json, os, sys
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
exec(_hsrc[_hsrc.index('LAT, LON = 51.8500'):_hsrc.index('def bevries(pg):')])

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))

STAND = {'overpass': 'ok'}
VRAGEN = []
def overpass(r):
    u = r.request.url
    if 'overpass' not in u:
        return route(r)
    VRAGEN.append(u)
    if STAND['overpass'] == 'kapot':
        return r.fulfill(status=500, body='fout', content_type='text/plain')
    return r.fulfill(body=OSM_KRUISEND, content_type='application/json')

def contour(d):
    return json.dumps({'type': 'Polygon', 'coordinates': [[[LON - d, LAT - d], [LON + d, LAT - d], [LON + d, LAT + d],
                                                           [LON - d, LAT + d], [LON - d, LAT - d]]]})
KLEIN, GROOT = contour(0.0015), contour(0.0035)
MELDING = ("(()=>{var e=document.getElementById('loading'),r=e.getBoundingClientRect();"
           "return {zicht:r.width>0&&r.height>0,tekst:e.textContent,wegen:ways.length,wacht:ophaalWacht.length,"
           "cache:ways.filter(w=>w.uitCache).length,status:document.getElementById('status-bar').textContent}})()")
AANTAL = """() => new Promise(res => { cacheDb().then(db => idbAlles(db, CACHE_STORE)).then(a => res(a.map(g => ({ts: g.ts, bbox: g.bbox, n: g.elements.length,
             knopen: g.elements.every(e => e.nodes && e.nodes.length)})))); })"""

def pagina(ctx, stand):
    STAND['overpass'] = stand
    pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:160])); pg.on('dialog', lambda d_: d_.accept())
    pg.goto(BASIS + 'telplanning.html', wait_until='load'); pg.wait_for_timeout(500)
    return pg, f
def laad(pg, geom, ms=1200):
    VRAGEN.clear()
    pg.evaluate('fetchWaysForPolygon(%s)' % geom); pg.wait_for_timeout(ms)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); ctx.route('**/*', overpass)

    print('== A. Een goed antwoord gaat de cache in ==')
    pg, f = pagina(ctx, 'ok')
    laad(pg, KLEIN)
    n_vers = pg.evaluate('ways.length')
    pg.wait_for_timeout(300)
    c = pg.evaluate(AANTAL)
    eis('wegen geladen (%d)' % n_vers, n_vers > 0 and pg.evaluate('ways.every(w => !w.uitCache)'))
    eis('één gebied in de cache, alle elementen, met knopen',
        len(c) == 1 and c[0]['n'] == len(json.loads(OSM_KRUISEND)['elements']) and c[0]['knopen'], c)
    bb = c[0]['bbox'] if c else [0, 0, 0, 0]
    eis('het gebied is de rechthoek met marge', bb[0] < LAT - 0.0015 and bb[2] > LAT + 0.0015 and bb[1] < LON - 0.0015 and bb[3] > LON + 0.0015, bb)
    eis('geen JS-fouten', not f, f)
    pg.close()

    print('\n== H. Overpass werkt: de cache doet niets ==')
    pg, f = pagina(ctx, 'ok')
    laad(pg, KLEIN)
    m = pg.evaluate(MELDING)
    eis('Overpass gevraagd, wegen vers, geen cachemelding', len(VRAGEN) == 1 and m['cache'] == 0 and not m['zicht'], (VRAGEN, m))
    pg.close()

    print('\n== B. Overpass faalt: de wegen uit de cache ==')
    pg, f = pagina(ctx, 'kapot')
    laad(pg, KLEIN, 1500)
    m = pg.evaluate(MELDING)
    eis('beide servers gevraagd (één ronde), daarna de cache', len(VRAGEN) == 2, VRAGEN)
    # de nep-Overpass geeft altijd het hele raster; de cache (en de echte Overpass) alleen wat de rechthoek met marge raakt
    ruim = pg.evaluate('contourBbox(%s, OPHAAL_MARGE_M)' % KLEIN)
    raakt = [e for e in json.loads(OSM_KRUISEND)['elements'] if any(ruim[0] <= n['lat'] <= ruim[2] and ruim[1] <= n['lon'] <= ruim[3] for n in e['geometry'])]
    eis('de wegen die de rechthoek raken (%d), allemaal uit de cache' % len(raakt), m['wegen'] == len(raakt) == m['cache'] and 0 < len(raakt) < n_vers, m)
    eis('een melding: uit de cache, met de redenen, de datum en Vernieuwen',
        m['zicht'] and 'uit de cache' in m['tekst'] and 'Server 1' in m['tekst'] and 'vandaag' in m['tekst'] and 'Vernieuwen' in m['tekst'], m['tekst'])
    import re
    eis('de datum als dd-mm-jjjj', re.search(r'op \d\d-\d\d-\d{4} \(vandaag\)', m['tekst']) is not None, m['tekst'])
    eis('geen nieuwe poging gepland', m['wacht'] == 0)
    eis('de statusregel zegt het', 'uit de cache' in m['status'], m['status'])
    eis('de knopen zijn er: knippen kan', pg.evaluate("ways.some(w => w.heel.nodes && [...w.heel.nodes.keys()].some(i => knipbaar(w.heel, i)))"))
    pg.evaluate("toggleWaySelect(ways.find(w => w.id === '3003'))")
    keuze3003 = pg.evaluate("ways.find(w => w.id === '3003').selected")
    pg.evaluate("(() => { const w = ways.find(w => w.id === '3002'); const i = [...w.heel.nodes.keys()].find(i => knipbaar(w.heel, i)); vervangStukken([w], [maakStuk(w, w.heel, 0, i, true), maakStuk(w, w.heel, i, w.tot, false)]); })()")
    eis('een knip op een weg uit de cache: de stukken blijven uit de cache', pg.evaluate("ways.filter(w => w.id === '3002').every(w => w.uitCache)") and pg.evaluate("ways.filter(w => w.id === '3002').length") == 2)

    print('\n== D. Vernieuwen als Overpass weer werkt ==')
    STAND['overpass'] = 'ok'; VRAGEN.clear()
    pg.click('#loading button.hoofd'); pg.wait_for_timeout(1200)
    m = pg.evaluate(MELDING)
    eis('Overpass gevraagd, de wegen zijn vers, melding weg', len(VRAGEN) == 1 and m['cache'] == 0 and m['wegen'] >= n_vers and not m['zicht'], (VRAGEN, m))
    eis('de keuze blijft (3003, omgezet in de cache: %s)' % keuze3003, pg.evaluate("ways.find(w => w.id === '3003').selected") is keuze3003)
    eis('de knip blijft (3002: gekozen, niet)', pg.evaluate("ways.filter(w => w.id === '3002').map(w => w.selected)") == [True, False],
        pg.evaluate("ways.filter(w => w.id === '3002').map(w => [w.van, w.tot, w.selected])"))
    eis('geen JS-fouten', not f, f)
    pg.close()

    print('\n== C. De cache dekt de contour niet helemaal ==')
    pg, f = pagina(ctx, 'kapot')
    pg.evaluate('OPHAAL_WACHT_MS = 60000')
    laad(pg, GROOT, 1500)
    m = pg.evaluate(MELDING)
    eis('geen cache, maar de gewone nieuwe poging', m['cache'] == 0 and m['wegen'] == 0 and m['wacht'] == 1 and 'Nieuwe poging' in m['tekst'], m)
    eis('geen JS-fouten', not f, f)
    pg.close()

    print('\n== G. Opruimen ==')
    pg, f = pagina(ctx, 'ok')
    pg.evaluate("""() => cacheDb().then(db => new Promise(res => { const st = db.transaction(CACHE_STORE, 'readwrite').objectStore(CACHE_STORE);
        st.add({ ts: Date.now() - 100 * 86400000, bbox: [1, 1, 2, 2], elements: [] });
        st.add({ ts: Date.now() - 86400000, bbox: [5, 5, 6, 6], elements: [] }).onsuccess = res; }))""")
    eis('nu drie gebieden (A plus twee)', len(pg.evaluate(AANTAL)) == 3)
    pg.evaluate("bewaarGebied([0, 0, 10, 10], [{type: 'way', id: 1, nodes: [1, 2], geometry: [{lat: 1, lon: 1}, {lat: 2, lon: 2}]}])"); pg.wait_for_timeout(400)
    c = pg.evaluate(AANTAL)
    eis('het oude (100 dagen) en het gebied dat het nieuwe bevat zijn weg; het gebied uit A blijft',
        len(c) == 2 and c[1]['bbox'] == [0, 0, 10, 10] and c[0]['bbox'][0] > 51, c)
    eis('geen JS-fouten', not f, f)
    pg.close()
    ctx.close()

    print('\n== E. Alleen tegels van de telapps ==')
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); ctx.route('**/*', overpass)
    pg, f = pagina(ctx, 'kapot')
    ZET = """(v) => tegelDb().then(db => new Promise(res => { const st = db.transaction(TILE_STORE, 'readwrite').objectStore(TILE_STORE);
        const ways = %s.elements; let n = 0;
        for (const ty of [5184, 5185]) for (const tx of [429, 430]) { n++; st.put({ key: 't_' + ty + '_' + tx, ts: Date.now() - 3 * 86400000, v: v, ways: ways }).onsuccess = () => { if (--n === 0) res(); }; } }))""" % OSM_KRUISEND
    pg.evaluate(ZET, 2)
    laad(pg, KLEIN, 1500)
    m = pg.evaluate(MELDING)
    eis('tegels met schema 2: niet gebruikt', m['cache'] == 0 and m['wegen'] == 0, m)
    pg.close()
    pg, f = pagina(ctx, 'kapot')
    pg.evaluate(ZET, 3)
    laad(pg, KLEIN, 1500)
    m = pg.evaluate(MELDING)
    eis('tegels met schema 3: de wegen uit de cache', m['cache'] > 0 and m['cache'] == m['wegen'], m)
    eis('de datum is die van de tegels: 3 dagen geleden', '3 dagen geleden' in m['tekst'], m['tekst'])
    eis('geen JS-fouten', not f, f)
    pg.close()
    ctx.close()

    print('\n== F. De tegeldatabase blijft heel voor de telapps ==')
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); ctx.route('**/*', overpass)
    pg, f = pagina(ctx, 'kapot')
    laad(pg, KLEIN, 1500)
    eis('lege cache: geen wegen, de gewone melding', pg.evaluate(MELDING)['cache'] == 0)
    pg.close()
    pg = ctx.new_page(); f2 = []
    pg.on('pageerror', lambda e: f2.append(e.message[:160]))
    pg.goto(BASIS + 'parkeertelling.html', wait_until='load'); pg.wait_for_timeout(500)
    stores = pg.evaluate("() => _tileDb().then(db => [...db.objectStoreNames].sort())")
    eis('parkeertelling opent de tegeldatabase met beide stores', stores == ['handoff', 'tiles'], stores)
    eis('geen JS-fouten', not f and not f2, (f, f2))
    ctx.close()
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
