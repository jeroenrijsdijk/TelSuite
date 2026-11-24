#!/usr/bin/env python3
"""v3.65 — Overpass vaker laten slagen.

Jay: "is er een manier om de overpass query wat vaker te laten slagen? het gaat
moeizaam". Meestal: "Server 1: geen verbinding of een fout bij de server.
Server 2: geen antwoord binnen 45 s." Gekozen: een kleinere maxsize (ook in de
telapps), een rechthoek in plaats van poly plus cirkel, en zelf opnieuw
proberen; geen derde server.

  A. Telplanning vraagt een rechthoek (de contour plus 100 m), met maxsize
     64 MiB, geen poly en geen around.
  B. "out of memory": dezelfde server nog een keer, zonder maxsize.
  C. Beide servers een storing: een melding met aftelling, en na de wachttijd
     zelf opnieuw; dan de wegen.
  D. Nu proberen: meteen. Stoppen: mislukt, met Opnieuw, en geen poging meer.
  E. Wis alles tijdens het wachten: geen poging meer.
  F. Een afgebroken vraag (time-out in Overpass): niet opnieuw (dan helpt een
     kleiner gebied, geen wachten).
  G. De telapps: maxsize 32 MiB rond je positie, 128 MiB voor het gebied vooraf.

Hulp (server, CDN-omleiding, nep-OSM) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/ophaaltest.py
"""
import json, os, re, sys, urllib.parse
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
exec(_hsrc[_hsrc.index('LAT, LON = 51.8500'):_hsrc.index('def bevries(pg):')])
ROOT = os.path.dirname(os.path.dirname(HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))

# Per server een rij antwoorden; de laatste blijft gelden.
RIJ = {'1': ['ok'], '2': ['ok']}
VRAGEN = {'1': [], '2': []}
GEHEUGEN = json.dumps({'version': 0.6, 'osm3s': json.loads(OSM).get('osm3s', {}), 'elements': [],
                       'remark': 'runtime error: Query run out of memory using about 64 MB of RAM.'})
AFGEBROKEN = json.dumps(dict(json.loads(OSM), remark='runtime error: Query timed out in "query" at line 1 after 26 seconds.'))
def overpass(r):
    u = r.request.url
    if 'overpass' not in u:
        return route(r)
    s = '1' if 'overpass-api.de' in u else '2'
    q = urllib.parse.unquote_plus(r.request.post_data or u.split('data=', 1)[-1])
    VRAGEN[s].append(q)
    rij = RIJ[s]; actie = rij.pop(0) if len(rij) > 1 else rij[0]
    if actie == '500': return r.fulfill(status=500, body='fout', content_type='text/plain')
    if actie == '429': return r.fulfill(status=429, body='rate limited', content_type='text/plain')
    body = {'ok': OSM, 'geheugen': GEHEUGEN, 'afgebroken': AFGEBROKEN}[actie]
    return r.fulfill(body=body, content_type='application/json')

d = 0.003
GEOM = json.dumps({'type': 'Polygon', 'coordinates': [[[LON - d, LAT - d], [LON + d, LAT - d], [LON + d, LAT + d],
                                                      [LON - d, LAT + d], [LON - d, LAT - d]]]})
MELDING = ("(()=>{var e=document.getElementById('loading'),r=e.getBoundingClientRect();"
           "return {zicht:r.width>0&&r.height>0,klasse:e.className,tekst:e.textContent,wegen:ways.length,"
           "wacht:ophaalWacht.length,status:document.getElementById('status-bar').textContent}})()")

def planning(b, rij1, rij2, wacht=None):
    RIJ['1'] = list(rij1); RIJ['2'] = list(rij2); VRAGEN['1'].clear(); VRAGEN['2'].clear()
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); ctx.route('**/*', overpass)
    pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:160]))
    pg.goto(BASIS + 'telplanning.html', wait_until='load'); pg.wait_for_timeout(500)
    if wacht is not None: pg.evaluate('OPHAAL_WACHT_MS = %d' % wacht)
    pg.evaluate('fetchWaysForPolygon(%s)' % GEOM)
    return ctx, pg, f

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. De zoekvraag ==')
    ctx, pg, f = planning(b, ['ok'], ['ok'])
    pg.wait_for_timeout(800)
    q = VRAGEN['1'][0] if VRAGEN['1'] else ''
    eis('één vraag aan server 1, wegen geladen', len(VRAGEN['1']) == 1 and pg.evaluate('ways.length') > 0, VRAGEN)
    eis('maxsize 64 MiB, timeout 25, out body geom', '[timeout:25][maxsize:67108864]' in q and 'out body geom' in q, q)
    eis('een rechthoek: geen poly, geen around', 'poly:' not in q and 'around' not in q, q)
    m = re.search(r'\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\)', q)
    bb = [float(x) for x in m.groups()] if m else []
    marge_lat = (LAT - d - bb[0]) * 111320 if bb else 0
    eis('de rechthoek is de contour plus ±100 m', bb and 95 < marge_lat < 105 and bb[0] < LAT - d and bb[2] > LAT + d
        and bb[1] < LON - d and bb[3] > LON + d, (bb, marge_lat))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== B. "out of memory" ==')
    ctx, pg, f = planning(b, ['geheugen', 'ok'], ['ok'])
    pg.wait_for_timeout(1000)
    eis('server 1 twee keer, server 2 niet', len(VRAGEN['1']) == 2 and len(VRAGEN['2']) == 0, VRAGEN)
    eis('de tweede keer zonder maxsize', len(VRAGEN['1']) == 2 and 'maxsize' in VRAGEN['1'][0] and 'maxsize' not in VRAGEN['1'][1], VRAGEN['1'])
    eis('wegen geladen, geen melding', pg.evaluate('ways.length') > 0 and not pg.evaluate(MELDING)['zicht'], pg.evaluate(MELDING))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== C. Een storing bij beide servers, dan zelf opnieuw ==')
    ctx, pg, f = planning(b, ['500', 'ok'], ['500'], wacht=1500)
    pg.wait_for_timeout(600)
    m = pg.evaluate(MELDING)
    eis('een melding met de redenen en een aftelling', m['zicht'] and 'lukt nog niet' in m['tekst'] and 'Server 1: geen verbinding' in m['tekst']
        and 'Nieuwe poging over' in m['tekst'] and 'poging 2 van 3' in m['tekst'] and m['wacht'] == 1, m)
    eis('Nu proberen en Stoppen', 'Nu proberen' in m['tekst'] and 'Stoppen' in m['tekst'], m['tekst'])
    eis('de statusregel zegt het ook', 'nieuwe poging' in m['status'], m['status'])
    pg.wait_for_timeout(1800)
    m = pg.evaluate(MELDING)
    eis('na de wachttijd zelf opnieuw: wegen geladen, melding weg', len(VRAGEN['1']) == 2 and m['wegen'] > 0 and not m['zicht'] and m['wacht'] == 0, (VRAGEN, m))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== D. Nu proberen en Stoppen ==')
    ctx, pg, f = planning(b, ['500', 'ok'], ['500'], wacht=60000)
    pg.wait_for_timeout(600)
    pg.click('#loading button.hoofd'); pg.wait_for_timeout(600)
    eis('Nu proberen: meteen, wegen geladen', len(VRAGEN['1']) == 2 and pg.evaluate('ways.length') > 0 and not pg.evaluate(MELDING)['zicht'], VRAGEN)
    ctx.close()
    ctx, pg, f = planning(b, ['500'], ['500'], wacht=800)
    pg.wait_for_timeout(500)
    pg.click('#loading button:not(.hoofd)'); pg.wait_for_timeout(1200)
    m = pg.evaluate(MELDING)
    eis('Stoppen: mislukt, met Opnieuw, geen nieuwe poging', 'mislukt' in m['tekst'] and 'Opnieuw' in m['tekst'] and len(VRAGEN['1']) == 1 and m['wacht'] == 0, (VRAGEN, m))
    RIJ['1'] = ['ok']
    pg.click('#loading button.hoofd'); pg.wait_for_timeout(600)
    eis('Opnieuw: wegen geladen', pg.evaluate('ways.length') > 0 and not pg.evaluate(MELDING)['zicht'])
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== E. Wis alles tijdens het wachten ==')
    ctx, pg, f = planning(b, ['500'], ['500'], wacht=800)
    pg.wait_for_timeout(500)
    pg.evaluate('clearAll()'); pg.wait_for_timeout(1200)
    m = pg.evaluate(MELDING)
    eis('geen nieuwe poging, geen melding', len(VRAGEN['1']) == 1 and m['wacht'] == 0 and not m['zicht'], (VRAGEN, m))
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('\n== F. Afgebroken: niet opnieuw ==')
    ctx, pg, f = planning(b, ['afgebroken'], ['afgebroken'], wacht=300)
    pg.wait_for_timeout(1200)
    m = pg.evaluate(MELDING)
    eis('meteen mislukt, met het advies van een kleiner gebied', 'mislukt' in m['tekst'] and 'kleiner gebied' in m['tekst']
        and len(VRAGEN['1']) == 1 and m['wacht'] == 0 and 'pogingen' not in m['tekst'], (VRAGEN, m))
    eis('geen JS-fouten', not f, f)
    ctx.close()
    b.close()

print('\n== G. De telapps ==')
def lees(n): return open(os.path.join(ROOT, n), encoding='utf-8').read()
for n in ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html', 'pocket_count.html']:
    t = lees(n)
    eis('%s: rond je positie [timeout:8][maxsize:33554432]' % n, "[out:json][timeout:8][maxsize:33554432];(" in t and "[out:json][timeout:8];(" not in t)
for n in ['parkeertelling.html', 'fietsparkeren.html', 'pocket_count.html']:
    eis('%s: gebied vooraf [maxsize:134217728]' % n, "[out:json][timeout:25][maxsize:134217728];(' + delen.join('')" in lees(n))
eis('capaciteitstelling: terreinen rond je positie ook met maxsize', "[out:json][timeout:10][maxsize:33554432];(node[amenity=parking]" in lees('capaciteitstelling.html'))

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
