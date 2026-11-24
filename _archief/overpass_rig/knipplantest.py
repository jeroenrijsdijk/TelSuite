#!/usr/bin/env python3
"""v3.64 — Telplanning: een deel van een weg plannen.

Jay: "in telplanning kun je alleen een compleet osm link selecteren. Wat komt
erbij kijken om maar een deel van een link te kunnen plannen?" Knippen: "Alleen
op een knoop - dat is bijna altijd een logisch zichtbare grens buiten", en
"Alleen knopen die de weg deelt met een andere weg".

Nep-Overpass: de Langestraat (way 500) met zes knopen. Knoop 3 deelt hij met
de Zijstraat (501), knoop 5 met een inrit (502); knoop 2 en 4 zijn vormpunten.
Verder een losse straat (503) zonder gedeelde knopen.

  A. Knipmodus: open stippen alleen op gedeelde knopen binnen een weg (3).
  B. Knippen met een echte klik: bij een vormpunt niet; bij knoop 3 en 5 wel
     (drie stukken, twee zwarte knippen). Een klik op een stuk kiest alleen dat
     stuk; het overzicht telt stukken.
  C. De planning: per gekozen stuk een regel met dezelfde osm_way_id; stukken die
     aan elkaar liggen worden één regel; alles gekozen = de hele weg, tot op de
     byte gelijk aan voor v3.64.
  D. Een knip weghalen.
  E. Een link heen en terug: twee losse stukken van één weg in de link; na het
     openen eerst de twee stukken, en zodra Overpass de weg geeft drie stukken
     op de knopen terug (gekozen, niet, gekozen) met hun knippen.
  F. Overpass kapot: de stukken uit de link blijven en gaan zo weer in de
     planning; knippen kan daar niet (melding).
  G. Dekking: geen stippen; de segmenten van de hele weg, één keer per weg.
  H. Parkeertelling opent de link met de stukken.

Hulp (server, CDN-omleiding) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/knipplantest.py
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

# Langestraat noord-zuid, knopen 11..16 om de ±45 m
LANG = [(LAT + i * 0.0004, LON) for i in range(6)]
def w(wid, nodes, pts, naam, hw='residential'):
    return {'type': 'way', 'id': wid, 'nodes': nodes, 'tags': {'highway': hw, 'name': naam},
            'geometry': [{'lat': a, 'lon': o} for a, o in pts]}
ELS = [w(500, [11, 12, 13, 14, 15, 16], LANG, 'Langestraat'),
       w(501, [21, 13, 22], [(LANG[2][0], LON - 0.0008), LANG[2], (LANG[2][0], LON + 0.0008)], 'Zijstraat'),
       w(502, [15, 31], [LANG[4], (LANG[4][0], LON + 0.0005)], '', 'service'),
       w(503, [41, 42, 43], [(LAT, LON + 0.0020), (LAT + 0.0005, LON + 0.0020), (LAT + 0.0010, LON + 0.0020)], 'Losse straat')]
NEP = json.dumps({'version': 0.6, 'elements': ELS})
WKT = lambda pts: 'LINESTRING (' + ', '.join('%.6f %.6f' % (o, a) for a, o in pts) + ')'
d = 0.003
GEOM = {'type': 'Polygon', 'coordinates': [[[LON - d, LAT - d], [LON + d, LAT - d], [LON + d, LAT + d],
                                            [LON - d, LAT + d], [LON - d, LAT - d]]]}
verzoeken = []
def maak_route(kapot=False):
    def r_(r):
        if r.request.url.split('?')[0].endswith(('leaflet.css', 'leaflet.min.css')):      # de rig breekt CSS af; voor echte klikken moeten de lagen goed liggen
            return r.fulfill(body=open(os.path.join(NM, 'leaflet/dist/leaflet.css'), 'rb').read(), content_type='text/css')
        if 'overpass' in r.request.url or 'interpreter' in r.request.url:
            verzoeken.append(1)
            return r.fulfill(status=504, body='') if kapot else r.fulfill(body=NEP, content_type='application/json')
        return route(r)
    return r_

def open_tp(b, kapot=False):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); ctx.route('**/*', maak_route(kapot))
    pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:160])); pg.on('dialog', lambda d_: d_.accept())
    pg.goto(BASIS + 'telplanning.html', wait_until='load'); pg.wait_for_timeout(700)
    return ctx, pg, f

STUKKEN = "ways.filter(w => w.id === '500').map(w => [w.van, w.tot, w.selected])"
def klik_bij(pg, knoop, dpx=0, dpy=-9):
    """Echte muisklik op de Langestraat, dpx/dpy pixels naast knoop (index 0..5)."""
    xy = pg.evaluate("""(i) => { const p = map.latLngToContainerPoint(ways.find(w => w.id === '500').heel.coords[i]);
                                const r = document.getElementById('map').getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }""", knoop)
    pg.mouse.click(xy[0] + dpx, xy[1] + dpy); pg.wait_for_timeout(150)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg, f = open_tp(b)
    pg.evaluate('fetchWaysForPolygon(%s)' % json.dumps(GEOM))
    pg.wait_for_function('ways.length === 4', timeout=15000)
    pg.evaluate("map.setView([%f, %f], 18)" % (LANG[2][0], LON)); pg.wait_for_timeout(300)

    print('== A. Knipmodus ==')
    eis('vier wegen, allemaal gekozen; nog geen stippen', pg.evaluate("ways.every(w => w.selected)") and
        pg.evaluate("document.querySelectorAll('.knip-kan, .knip-punt').length") == 0)
    pg.click('#btn-knip'); pg.wait_for_timeout(150)
    eis('de knop staat aan, met uitleg', pg.evaluate("document.getElementById('btn-knip').classList.contains('aan') && getComputedStyle(document.getElementById('knip-uitleg')).display !== 'none'"))
    eis('open stippen op de gedeelde knopen binnen een weg: 3 (Langestraat 2, Zijstraat 1; de inrit eindigt er)',
        pg.evaluate("document.querySelectorAll('.knip-kan').length") == 3,
        pg.evaluate("document.querySelectorAll('.knip-kan').length"))
    eis('knipbaar: alleen knoop 13 en 15 van de Langestraat',
        pg.evaluate("[0,1,2,3,4,5].filter(i => knipbaar(ways.find(w => w.id === '500').heel, i))") == [2, 4])

    print('\n== B. Knippen ==')
    klik_bij(pg, 1, dpy=0)
    eis('klik op een vormpunt: niet geknipt, wel een melding', pg.evaluate(STUKKEN) == [[0, 5, True]] and
        'geen knoop' in pg.evaluate("document.getElementById('status-bar').textContent"))
    klik_bij(pg, 2)
    eis('klik bij knoop 13: twee stukken', pg.evaluate(STUKKEN) == [[0, 2, True], [2, 5, True]], pg.evaluate(STUKKEN))
    klik_bij(pg, 4)
    eis('klik bij knoop 15: drie stukken', pg.evaluate(STUKKEN) == [[0, 2, True], [2, 4, True], [4, 5, True]], pg.evaluate(STUKKEN))
    eis('twee zwarte knippen', pg.evaluate("document.querySelectorAll('.knip-punt').length") == 2)
    eis('de Zijstraat is niet geknipt', pg.evaluate("ways.filter(w => w.id === '501').length") == 1)
    pg.click('#btn-knip'); pg.wait_for_timeout(150)
    eis('knipmodus uit: geen open stippen, de knippen blijven',
        pg.evaluate("document.querySelectorAll('.knip-kan').length") == 0 and pg.evaluate("document.querySelectorAll('.knip-punt').length") == 2)
    klik_bij(pg, 3, dpy=0)       # midden in het middelste stuk
    eis('een klik kiest alleen het middelste stuk uit', pg.evaluate(STUKKEN) == [[0, 2, True], [2, 4, False], [4, 5, True]], pg.evaluate(STUKKEN))
    st = pg.evaluate("document.getElementById('stats-line').innerText")
    eis('overzicht: 4 wegen in 6 stukken, 5 gekozen', '4 wegen zichtbaar, in 6 stukken' in st and '5 stukken geselecteerd' in st, st)
    eis('de legenda telt wegen, geen stukken (woonstraat 3)', pg.evaluate("document.getElementById('cnt-residential').textContent") == '3')

    print('\n== C. De planning ==')
    pl = pg.evaluate('maakPlanning()')
    lang = [x for x in pl['wegen'] if x['osm_way_id'] == '500']
    eis('Langestraat: twee regels, knoop 11–13 en 15–16', [x['geometrie_wkt'] for x in lang] == [WKT(LANG[0:3]), WKT(LANG[4:6])], lang)
    eis('n_wegen telt de regels (5)', pl['n_wegen'] == 5 == len(pl['wegen']), pl['n_wegen'])
    eis('de hele wegen: WKT zoals voor v3.64', next(x for x in pl['wegen'] if x['osm_way_id'] == '503')['geometrie_wkt'] == WKT(ELS[3]['geometry'] and [(q['lat'], q['lon']) for q in ELS[3]['geometry']]))
    pg.evaluate("toggleWaySelect(ways.find(w => w.id === '500' && w.van === 2))")
    pl = pg.evaluate('maakPlanning()')
    eis('alles gekozen: één regel, de hele weg, byte-gelijk', [x['geometrie_wkt'] for x in pl['wegen'] if x['osm_way_id'] == '500'] == [WKT(LANG)])
    pg.evaluate("toggleWaySelect(ways.find(w => w.id === '500' && w.van === 4))")
    pl = pg.evaluate('maakPlanning()')
    eis('laatste stuk uit: één regel, knoop 11–15', [x['geometrie_wkt'] for x in pl['wegen'] if x['osm_way_id'] == '500'] == [WKT(LANG[0:5])])

    print('\n== D. Een knip weghalen ==')
    pg.click('#btn-knip'); pg.wait_for_timeout(100)
    klik_bij(pg, 4)
    eis('klik bij de knip op knoop 15: twee stukken, het samengevoegde gekozen', pg.evaluate(STUKKEN) == [[0, 2, True], [2, 5, True]], pg.evaluate(STUKKEN))
    eis('nog één zwarte knip', pg.evaluate("document.querySelectorAll('.knip-punt').length") == 1)
    klik_bij(pg, 4)              # en weer terug: drie stukken
    pg.click('#btn-knip'); pg.wait_for_timeout(100)
    pg.evaluate("toggleWaySelect(ways.find(w => w.id === '500' && w.van === 2))")
    eis('weer drie stukken (gekozen, niet, gekozen)', pg.evaluate(STUKKEN) == [[0, 2, True], [2, 4, False], [4, 5, True]], pg.evaluate(STUKKEN))
    link = pg.evaluate("planlinkInpakken(maakPlanning())")
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== E. De link heen en terug ==')
    ctx, pg, f = open_tp(b)
    verzoeken.clear()
    pg.evaluate("openPlanningUitLink(%s)" % json.dumps('https://telonline.org/parkeertelling.html#plan=' + link))
    eis('direct na openen: de twee stukken uit de link', pg.evaluate("ways.filter(w => w.id === '500').length") in (2, 3))
    pg.wait_for_function("ways.filter(w => w.id === '500').length === 3", timeout=15000)
    eis('Overpass geeft de weg: drie stukken op de knopen, gekozen/niet/gekozen',
        pg.evaluate(STUKKEN) == [[0, 2, True], [2, 4, False], [4, 5, True]], pg.evaluate(STUKKEN))
    eis('de stukken hebben de knopen van de echte weg', pg.evaluate("ways.find(w => w.id === '500').heel.nodes") == ['11', '12', '13', '14', '15', '16'])
    pg.evaluate("map.setView([%f, %f], 18)" % (LANG[2][0], LON)); pg.wait_for_timeout(200)
    eis('twee zwarte knippen terug', pg.evaluate("document.querySelectorAll('.knip-punt').length") == 2)
    eis('de andere wegen uit de link gekozen, de omgeving niet',
        pg.evaluate("ways.filter(w => w.id !== '500').map(w => [w.id, w.selected]).sort()") == [['501', True], ['502', True], ['503', True]],
        pg.evaluate("ways.filter(w => w.id !== '500').map(w => [w.id, w.selected])"))
    pl = pg.evaluate('maakPlanning()')
    eis('dezelfde planning terug (twee regels voor de Langestraat)', [x['geometrie_wkt'] for x in pl['wegen'] if x['osm_way_id'] == '500'] == [WKT(LANG[0:3]), WKT(LANG[4:6])])
    pg.click('#btn-knip'); pg.wait_for_timeout(100)
    klik_bij(pg, 2)
    eis('ook na de link: een knip weghalen kan', pg.evaluate(STUKKEN) == [[0, 4, True], [4, 5, True]], pg.evaluate(STUKKEN))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== F. Overpass kapot ==')
    ctx, pg, f = open_tp(b, kapot=True)
    pg.evaluate("openPlanningUitLink(%s)" % json.dumps('https://telonline.org/parkeertelling.html#plan=' + link))
    pg.wait_for_timeout(2500)
    eis('de twee stukken uit de link blijven staan', pg.evaluate("ways.filter(w => w.id === '500').length") == 2)
    pl = pg.evaluate('maakPlanning()')
    eis('en gaan zo weer in de planning (twee regels, 5 decimalen uit de link)',
        len([x for x in pl['wegen'] if x['osm_way_id'] == '500']) == 2, pl['wegen'])
    pg.evaluate("toggleKnip(); knipBij(ways.find(w => w.id === '500'), L.latLng(%f, %f))" % LANG[1])
    eis('knippen: een melding dat de knopen nog ontbreken', 'nog geen knopen' in pg.evaluate("document.getElementById('status-bar').textContent"))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== G. Dekking ==')
    ctx, pg, f = open_tp(b)
    pg.evaluate("openPlanningUitLink(%s)" % json.dumps('https://telonline.org/parkeertelling.html#plan=' + link))
    pg.wait_for_function("ways.filter(w => w.id === '500').length === 3", timeout=15000)
    pg.evaluate("setMode('dekking')"); pg.wait_for_timeout(200)
    eis('in dekking geen stippen of knippen', pg.evaluate("document.querySelectorAll('.knip-kan, .knip-punt').length") == 0)
    seg = pg.evaluate("ways.filter(w => w.id === '500').map(w => w.segments.map(s => s.idx))")
    alle = pg.evaluate("ways.find(w => w.id === '500').heel.segments.map(s => s.idx)")
    eis('de segmenten van de hele weg, elk in precies één stuk', sorted(sum(seg, [])) == alle, (seg, alle))
    pg.evaluate("setMode('maken')"); pg.wait_for_timeout(100)
    eis('terug in Maken: de knippen weer zichtbaar', pg.evaluate("document.querySelectorAll('.knip-punt').length") == 2)
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== H. Parkeertelling opent de link ==')
    ctx = nieuwe_context(b); ctx.route('**/*', maak_route())
    pg = ctx.new_page(); f = []; pg.on('pageerror', lambda e: f.append(e.message[:160]))
    pg.goto(BASIS + 'parkeertelling.html#plan=' + link, wait_until='load'); pg.wait_for_timeout(1500)
    eis('vijf geplande regels, twee van de Langestraat',
        pg.evaluate("planningWegen.length") == 5 and pg.evaluate("planningWegen.filter(w => w.osm_way_id === '500').length") == 2)
    eis('geen JS-fouten', not f, f)
    ctx.close()
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
