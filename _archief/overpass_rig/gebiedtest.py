#!/usr/bin/env python3
"""v3.19 gebiedtest — gebied vooraf ophalen, planning uit een link, verversafstand. In Chromium.

  A. Parkeertelling opent een planning-link:
     - één verzoek naar Overpass, met bboxen en zonder 'around', en een regel
       "gebied klaar (… tegels, … kB opgehaald)";
     - precies die tegels staan daarna in de tegelcache, vers, schema 2, met de
       geplande straat in de tegels waar hij ligt;
     - Start en lopen over de geplande straat: geen enkel verzoek meer, en de
       app snapt gewoon (het netwerk komt uit de tegels);
     - opnieuw openen: geen verzoek, "al bewaard".
  B. Fietsparkeren en pocket-parkeren: hetzelfde bij het openen. Pocket zet
     het kort in de opdrachtregel, met het hele verhaal in de tooltip.
  C. Als het misgaat:
     - rate-limit bij server 1: niet ook server 2 vragen; de regel zegt het; in
       het veld haalt de app de wegen onderweg op, zoals vroeger;
     - een afgebroken antwoord (remark) bij server 1: server 2 levert;
     - beide servers kapot: niets in de cache, de regel zegt het;
     - een te groot gebied: geen verzoek.
  D. Verversafstand (v3.19: 220 m in de parkeer-apps, 170 m in pocket): op
     200 m van het vorige middelpunt geen nieuw verzoek, op 240 m wel; pocket
     op 150 m niet, op 190 m wel.
  F. Tegelschema 3 (v3.20): de tegels dragen de knooppunten van elke weg.
     - het gebied vooraf haalt op met 'out body geom'; een tegel van schema 2
       (zonder knooppunten, zoals v3.19 ze schreef) telt als ontbrekend en
       wordt opnieuw opgehaald;
     - pocket bouwt uit die tegels de aansluitingen tussen straten;
     - de reconstructor haalt een tegel van schema 2 opnieuw op en heeft dan
       buren;
     - parkeertelling haalt in het veld ook met knooppunten op, maar bewaart ze
       niet in zijn eigen netwerk (noodkopie en _netwerk.csv blijven even groot).
  E. Telplanning: planning uit een link.
     - telplanning.html#plan=…: naam, datum, tijd, teller en teltype terug, de
       geplande straten gekozen, de omgeving erbij (één verzoek) en niet gekozen;
     - Deel als link geeft dezelfde planning; een straat uit de omgeving erbij
       klikken komt in de nieuwe link;
     - plakken in het veld (link naar parkeertelling of pocket) werkt ook;
     - een link zonder #plan= of een kapotte link: een melding, niets gewist.

Hulp (server, CDN-omleiding, nep-Overpass-raster) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/gebiedtest.py
"""
import os, sys, json, re
from urllib.parse import unquote
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

RASTER = json.loads(OSM)['elements']
M = 1 / 111320

# Nep-Overpass die bbox-vragen echt beantwoordt (wegen met een punt in een bbox)
REQ = []                             # (soort, server, zoekvraag)
SCEN = {'1': 'ok', '2': 'ok', 'around': 'ok'}
def route_gebied(r, *_):
    u = r.request.url
    if 'overpass' not in u:
        return route(r)
    if 'data=' in u:
        q = unquote(u.split('data=', 1)[1])
    else:
        q = unquote((r.request.post_data or '').split('data=', 1)[-1])
    server = '1' if 'overpass-api.de' in u else '2'
    soort = 'poly' if 'poly:' in q else ('around' if 'around' in q else 'bbox')
    REQ.append((soort, server, q))
    sc = SCEN[server] if not (soort == 'around' and SCEN['around'] != 'ok') else SCEN['around']
    if sc == '429':
        return r.fulfill(status=429, body='rate limited', content_type='text/plain')
    if sc == '500':
        return r.fulfill(status=500, body='kapot', content_type='text/plain')
    if sc == 'remark':
        return r.fulfill(body=json.dumps({'version': 0.6, 'elements': [], 'remark': 'runtime error: Query timed out'}),
                         content_type='application/json')
    els = RASTER
    if soort == 'bbox':
        bb = [tuple(map(float, m)) for m in re.findall(r'\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\)', q)]
        els = [e for e in RASTER if any(s <= pt['lat'] <= n and w <= pt['lon'] <= o
                                        for pt in e['geometry'] for (s, w, n, o) in bb)]
    if 'out tags geom' in q:     # zoals Overpass: 'out tags' geeft geen knooppunten
        els = [{k: v for k, v in e.items() if k != 'nodes'} for e in els]
    return r.fulfill(body=json.dumps({'version': 0.6, 'elements': els}), content_type='application/json')

def soorten(*s):
    return [x for x in REQ if x[0] in s]

def context(b, breed=False):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800} if breed else {'width': 390, 'height': 844},
                        accept_downloads=True, permissions=['geolocation'],
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5})
    ctx.route('**/*', route_gebied)
    return ctx

def pagina(ctx, url):
    pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:160])); pg.on('dialog', lambda dl: dl.accept())
    pg.goto(url, wait_until='load'); pg.wait_for_timeout(500)
    return pg, f

def wkt(e):
    return 'LINESTRING (' + ', '.join('%.6f %.6f' % (pt['lon'], pt['lat']) for pt in e['geometry']) + ')'
def weg(wid):
    e = next(x for x in RASTER if x['id'] == wid)
    return {'osm_way_id': str(wid), 'naam': e['tags']['name'], 'highway': 'residential', 'geometrie_wkt': wkt(e)}
GEPLAND = [1003, 2004]               # Noordstraat 3 (noord-zuid door het startpunt), Dwarsstraat 4
PLANNING = {'sessie_naam': 'Wijk Noord', 'datum': '2026-10-24', 'tijdstip': '09:30', 'teller': 'T07',
            'tel_type': 'auto', 'n_wegen': 2, 'wegen': [weg(w) for w in GEPLAND]}

STATUS = "document.getElementById('statusText').textContent"
TEGELS = """() => _tileDb().then(db => new Promise(res => {
  var q = db.transaction('tiles', 'readonly').objectStore('tiles').getAll();
  q.onsuccess = () => res(q.result.map(t => ({key: t.key, ts: t.ts, v: t.v, ids: (t.ways || []).map(w => String(w.id)),
                                               knopen: (t.ways || []).every(w => w.nodes && w.nodes.length >= 2)})));
}))"""
# v3.20: tegels zoals v3.19 ze schreef: schema 2, wegen zonder knooppunten
ZAAI_OUD = """(keys) => _tileDb().then(db => new Promise(res => {
  var tx = db.transaction('tiles', 'readwrite'), st = tx.objectStore('tiles');
  keys.forEach(k => st.put({key: k, ts: Date.now(), v: 2, ways: []}));
  tx.oncomplete = () => res(keys.length);
}))"""

with sync_playwright() as p:
    b = p.chromium.launch()

    # De link maken we met het blok planlink zelf, in telplanning
    ctx = context(b, breed=True)
    pg, _ = pagina(ctx, BASIS + 'telplanning.html')
    WAARDE = pg.evaluate('(p) => planlinkInpakken(p)', PLANNING)
    GROOT = dict(PLANNING, wegen=[{'osm_way_id': '9', 'naam': 'Lange weg', 'highway': 'residential',
                                   'geometrie_wkt': 'LINESTRING (4.20 51.80, 4.40 51.80, 4.40 51.90)'}])
    WAARDE_GROOT = pg.evaluate('(p) => planlinkInpakken(p)', GROOT)
    ctx.close()

    print('== A. parkeertelling: gebied vooraf ==')
    REQ.clear()
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    st = pg.evaluate(STATUS)
    eis('één verzoek, met bboxen en zonder around', len(REQ) == 1 and REQ[0][0] == 'bbox', [x[:2] for x in REQ])
    eis('de regel: opdracht, tegels en kB', st.startswith('Opdracht: Wijk Noord') and re.search(r'gebied klaar \(\d+ tegels, \d+ kB opgehaald\)', st), st)
    verwacht = pg.evaluate("gebiedTegels(PLANNING_LIJNEN, ROAD_FETCH_RADIUS).map(t => t.key)".replace(
        'PLANNING_LIJNEN', json.dumps([[[pt['lat'], pt['lon']] for pt in next(x for x in RASTER if x['id'] == w)['geometry']] for w in GEPLAND])))
    teg = pg.evaluate(TEGELS)
    eis('precies die tegels in de cache (%d)' % len(verwacht), sorted(t['key'] for t in teg) == sorted(verwacht), (sorted(t['key'] for t in teg), sorted(verwacht)))
    nu = pg.evaluate('Date.now()')
    eis('vers en schema 3, met knooppunten (v3.20)', all(t['v'] == 3 and t['knopen'] and nu - t['ts'] < 60000 for t in teg), teg[:2])
    eis('de zoekvraag vraagt de knooppunten (out body geom)', REQ[0][2].endswith('out body geom;'), REQ[0][2][-40:])
    hier = [t for t in teg if t['key'] == 't_5185_430']
    eis('Noordstraat 3 staat in de tegel waar hij ligt', hier and '1003' in hier[0]['ids'], hier)
    eis('een verzoek per server is niet nodig: alleen server 1', all(x[1] == '1' for x in REQ))
    pg.evaluate('startSession()'); pg.wait_for_timeout(800)
    for i in range(6):                                   # 300 m naar het noorden, over Noordstraat 3
        ctx.set_geolocation({'latitude': LAT + i * 60 * M, 'longitude': LON, 'accuracy': 5})
        pg.wait_for_timeout(500)
        pg.evaluate("addEntry('goed','L')")
    pg.wait_for_timeout(800)
    eis('lopen over de geplande straat: geen enkel verzoek meer', len(REQ) == 1, [x[:2] for x in REQ])
    netw = pg.evaluate("({n: snap.networkElements.length, status: snap.status, ways: entries.map(e => e.osmWayId)})")
    eis('en de app snapt op Noordstraat 3: het netwerk komt uit de tegels',
        netw['n'] > 0 and netw['status'] == 'ok' and netw['ways'].count('1003') >= 4, netw)
    eis('geen JS-fouten', not fouten, fouten)
    pg.close()
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    eis('opnieuw openen: geen verzoek, "al bewaard"', len(REQ) == 1 and 'al bewaard' in pg.evaluate(STATUS),
        (len(REQ), pg.evaluate(STATUS)))
    ctx.close()

    print('\n== B. fietsparkeren en pocket ==')
    REQ.clear()
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'fietsparkeren.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    eis('fietsparkeren: één bbox-verzoek, gebied klaar', len(REQ) == 1 and REQ[0][0] == 'bbox', [x[:2] for x in REQ])
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    REQ.clear()
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'pocket_count.html#parkeren&plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('pk-plan').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    regel = pg.evaluate("({t: document.getElementById('pk-plan').textContent, title: document.getElementById('pk-plan').title})")
    # Pocket-parkeren start meteen, dus de eerste fetch van het veld kan het gebied
    # nog net voor zijn (één gewoon verzoek). Daarom tellen we hier alleen bboxen.
    eis('pocket: één bbox-verzoek', len(soorten('bbox')) == 1, [x[:2] for x in REQ])
    eis('pocket: kort in de regel, het hele verhaal in de tooltip',
        'gebied klaar · zie Kaart' in regel['t'] and re.search(r'gebied klaar \(\d+ tegels, \d+ kB opgehaald\)', regel['title']), regel)
    pg.evaluate('startParkeren()'); pg.wait_for_timeout(600)
    n_voor = len(REQ)
    for i in range(5):
        ctx.set_geolocation({'latitude': LAT + i * 60 * M, 'longitude': LON, 'accuracy': 5})
        pg.wait_for_timeout(500)
    pg.wait_for_timeout(800)
    trace = pg.evaluate("snap.trace.map(t => t.event).filter(e => /fetch|tegel/.test(e))")
    eis('pocket: lopen zonder verzoek, de trace zegt "tegelcache"', len(REQ) == n_voor and 'tegelcache' in trace, (len(REQ), n_voor, trace))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== C. als het misgaat ==')
    REQ.clear(); SCEN['1'] = '429'
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied niet klaargezet') >= 0", timeout=15000)
    eis('rate-limit bij server 1: server 2 niet gevraagd, de regel zegt het',
        [x[:2] for x in REQ] == [('bbox', '1')] and 'overbelast' in pg.evaluate(STATUS), ([x[:2] for x in REQ], pg.evaluate(STATUS)))
    eis('niets in de cache', pg.evaluate(TEGELS) == [])
    SCEN['1'] = 'ok'
    pg.evaluate('startSession()'); pg.wait_for_timeout(2000)
    eis('in het veld: de app haalt de wegen onderweg op, zoals vroeger', len(soorten('around')) >= 1 and
        pg.evaluate('snap.networkElements.length') > 0, [x[:2] for x in REQ])
    ctx.close()
    REQ.clear(); SCEN['1'] = 'remark'
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    eis('afgebroken antwoord bij server 1: server 2 levert', [x[:2] for x in REQ] == [('bbox', '1'), ('bbox', '2')] and
        len(pg.evaluate(TEGELS)) > 0, [x[:2] for x in REQ])
    ctx.close()
    REQ.clear(); SCEN['1'] = SCEN['2'] = '500'
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied niet klaargezet') >= 0", timeout=15000)
    eis('beide servers kapot: twee pogingen, niets in de cache, de regel zegt het',
        len(REQ) == 2 and pg.evaluate(TEGELS) == [] and 'geen server' in pg.evaluate(STATUS), ([x[:2] for x in REQ], pg.evaluate(STATUS)))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    SCEN['1'] = SCEN['2'] = 'ok'
    REQ.clear()
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE_GROOT)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('te groot') >= 0", timeout=15000)
    eis('te groot gebied: geen verzoek, de regel zegt het', REQ == [] and 'tegels)' in pg.evaluate(STATUS), pg.evaluate(STATUS))
    ctx.close()

    print('\n== D. verversafstand ==')
    for naam, app, start, kort, lang in [('parkeertelling', 'parkeertelling.html', 'startSession()', 200, 240),
                                         ('capaciteit', 'capaciteitstelling.html', 'startSession()', 200, 240),
                                         ('pocket', 'pocket_count.html', 'startParkeren()', 150, 190)]:
        REQ.clear()
        ctx = context(b)
        pg, fouten = pagina(ctx, BASIS + app)
        pg.evaluate(start); pg.wait_for_timeout(1500)
        n0 = len(soorten('around'))
        ctx.set_geolocation({'latitude': LAT + kort * M, 'longitude': LON, 'accuracy': 5}); pg.wait_for_timeout(1500)
        n1 = len(soorten('around'))
        ctx.set_geolocation({'latitude': LAT + lang * M, 'longitude': LON, 'accuracy': 5}); pg.wait_for_timeout(1500)
        n2 = len(soorten('around'))
        eis('%s: op %d m geen nieuw verzoek, op %d m wel' % (naam, kort, lang), n0 == 1 and n1 == 1 and n2 == 2, (n0, n1, n2))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    print('\n== F. tegelschema 3 (v3.20) ==')
    REQ.clear()
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html')
    pg.evaluate(ZAAI_OUD, verwacht)                      # de tegels van v3.19, zonder knooppunten
    pg.close()                                           # een hash-wissel laadt de pagina niet opnieuw
    pg, fouten = pagina(ctx, BASIS + 'parkeertelling.html#plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('statusText').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    teg = pg.evaluate(TEGELS)
    eis('tegels van schema 2 (zoals v3.19 ze schreef): opnieuw opgehaald, nu schema 3 met knooppunten',
        len(soorten('bbox')) == 1 and 'kB opgehaald' in pg.evaluate(STATUS) and all(t['v'] == 3 and t['knopen'] for t in teg),
        ([x[:2] for x in REQ], pg.evaluate(STATUS)))
    pg.evaluate('startSession()'); pg.wait_for_timeout(800)
    ctx.set_geolocation({'latitude': LAT + 400 * M, 'longitude': LON + 0.03, 'accuracy': 5}); pg.wait_for_timeout(1500)
    rond = soorten('around')
    eis('in het veld buiten het gebied: ook met knooppunten (out body geom)', rond and rond[-1][2].endswith('out body geom;'),
        [x[2][-30:] for x in rond])
    pg.wait_for_timeout(500)
    kaal = pg.evaluate("snap.networkElements.every(e => !('nodes' in e)) && snap.networkElements.length > 0")
    opslag = pg.evaluate("localStorage.getItem(LS_KEY + '_netwerk') || ''")
    eis('maar het eigen netwerk en de noodkopie zonder knooppunten (zo groot als vroeger)',
        kaal and opslag and '"nodes"' not in opslag, (kaal, len(opslag)))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    REQ.clear(); SCEN['around'] = '500'                  # het netwerk kan alleen uit de tegels komen
    ctx = context(b)
    pg, fouten = pagina(ctx, BASIS + 'pocket_count.html#parkeren&plan=' + WAARDE)
    pg.wait_for_function("document.getElementById('pk-plan').textContent.indexOf('gebied klaar') >= 0", timeout=15000)
    for i in range(5):
        ctx.set_geolocation({'latitude': LAT + i * 60 * M, 'longitude': LON, 'accuracy': 5})
        pg.wait_for_timeout(500)
    pg.wait_for_timeout(800)
    adj = pg.evaluate("({n: Object.keys(snap.adjacency).length, el: Object.keys(snap.elements).length})")
    SCEN['around'] = 'ok'
    eis('pocket: de wegen uit de tegels komen met knooppunten in de aansluitingen (v3.19: geen)',
        adj['el'] > 0 and adj['n'] == adj['el'], adj)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    REQ.clear()
    ctx = context(b, breed=True)
    pg, fouten = pagina(ctx, BASIS + 'telreconstructie.html')
    BB = {'la0': LAT - 0.002, 'la1': LAT + 0.002, 'lo0': LON - 0.002, 'lo1': LON + 0.002}
    sleutels = pg.evaluate("(b) => coveringTiles(b).map(t => t.key)", BB)
    pg.evaluate("(keys) => OSMCACHE.put(keys.map(k => ({key: k, ts: Date.now(), v: 2, ways: []})))", sleutels)
    res = pg.evaluate("(b) => cacheGefetchteRoute(b).then(r => ({n: r.ways.length, vers: r.vers, tegels: r.tegels, "
                      "buren: Object.keys(MATCHER.buildAdjacency(r.ways)).length}))", BB)
    eis('reconstructor: tegels van schema 2 opnieuw opgehaald, met buren', res['vers'] == res['tegels'] == len(sleutels) and
        res['n'] > 0 and res['buren'] > 0 and len(REQ) == 1, (res, [x[:2] for x in REQ]))
    res = pg.evaluate("(b) => cacheGefetchteRoute(b).then(r => ({vers: r.vers}))", BB)
    eis('reconstructor: daarna uit de cache (schema 3), geen verzoek', res['vers'] == 0 and len(REQ) == 1, (res, len(REQ)))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== E. telplanning: planning uit een link ==')
    VELDEN = """() => ({naam: document.getElementById('meta-naam').value, datum: document.getElementById('meta-datum').value,
      tijd: document.getElementById('meta-tijd').value, teller: document.getElementById('meta-teller').value,
      teltype: document.getElementById('meta-teltype').value,
      gekozen: ways.filter(w => w.selected).map(w => w.id).sort(), alle: ways.length,
      link: !document.getElementById('btn-link').disabled,
      wis: document.getElementById('btn-clear').style.display !== 'none'})"""
    REQ.clear()
    ctx = context(b, breed=True)
    pg, fouten = pagina(ctx, BASIS + 'telplanning.html#plan=' + WAARDE)
    pg.wait_for_function('ways.length > 2', timeout=15000); pg.wait_for_timeout(300)
    v = pg.evaluate(VELDEN)
    eis('naam, datum, tijd, teller en teltype terug',
        (v['naam'], v['datum'], v['tijd'], v['teller'], v['teltype']) == ('Wijk Noord', '2026-10-24', '09:30', 'T07', 'auto'), v)
    eis('de geplande straten gekozen, en alleen die', v['gekozen'] == sorted(str(w) for w in GEPLAND), v['gekozen'])
    eis('de omgeving erbij, niet gekozen (%d straten)' % v['alle'], v['alle'] == len(RASTER), v['alle'])
    eis('één verzoek voor de omgeving', [x[0] for x in REQ] == ['poly'], [x[:2] for x in REQ])
    eis('Deel als link en Wis alles staan aan', v['link'] and v['wis'], v)
    terug = pg.evaluate("planlinkInpakken(maakPlanning()).then(planlinkUitpakken)")
    eis('Deel als link geeft dezelfde planning', sorted(w['osm_way_id'] for w in terug['wegen']) == sorted(str(w) for w in GEPLAND) and
        (terug['sessie_naam'], terug['datum'], terug['tijdstip'], terug['teller'], terug['tel_type']) ==
        ('Wijk Noord', '2026-10-24', '09:30', 'T07', 'auto'), terug)
    pg.evaluate("toggleWaySelect(ways.find(w => w.id === '1004'))")
    terug = pg.evaluate("planlinkInpakken(maakPlanning()).then(planlinkUitpakken)")
    eis('een straat uit de omgeving erbij: in de nieuwe link', sorted(w['osm_way_id'] for w in terug['wegen']) == ['1003', '1004', '2004'],
        [w['osm_way_id'] for w in terug['wegen']])
    eis('geen JS-fouten', not fouten, fouten)
    pg.close()
    pg, fouten = pagina(ctx, BASIS + 'telplanning.html')
    pg.fill('#link-invoer', 'https://telonline.org/pocket_count.html#parkeren&plan=' + WAARDE + '.')
    pg.click('#btn-link-invoer'); pg.wait_for_function('ways.length > 2', timeout=15000); pg.wait_for_timeout(300)
    v = pg.evaluate(VELDEN)
    eis('plakken (pocket-link, met een punt erachter) en Openen: de planning staat er',
        v['gekozen'] == sorted(str(w) for w in GEPLAND) and v['naam'] == 'Wijk Noord' and
        pg.evaluate("document.getElementById('link-invoer').value") == '', v)
    pg.fill('#link-invoer', 'https://telonline.org/parkeertelling.html')
    pg.press('#link-invoer', 'Enter'); pg.wait_for_timeout(300)
    st = pg.evaluate("document.getElementById('status-bar').textContent")
    eis('een link zonder #plan=: een melding, de planning blijft staan',
        st.startswith('Geen planning') and pg.evaluate("ways.filter(w => w.selected).length") == 2, st)
    pg.fill('#link-invoer', 'https://telonline.org/parkeertelling.html#plan=1.abcdef')
    pg.click('#btn-link-invoer'); pg.wait_for_timeout(500)
    st = pg.evaluate("document.getElementById('status-bar').textContent")
    eis('een kapotte link: een melding, de planning blijft staan',
        st.startswith('Link openen mislukt') and pg.evaluate("ways.filter(w => w.selected).length") == 2, st)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d FOUT, %d OK' % (fout, ok)))
sys.exit(1 if fout else 0)
