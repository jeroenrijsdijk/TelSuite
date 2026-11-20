#!/usr/bin/env python3
"""v3.63 — Telrapport: de straten van een capaciteitstelling.

Jay sleepte een capaciteits-ZIP van straten in telrapport: "komt er niks op het
scherm". Telrapport tekende een straat als vlak (L.polygon sluit zijn lijn) met
het getal op het zwaartepunt. Van een rechte straat is dat vlak bijna nul groot,
en dan rekent getCenter een punt tientallen kilometers verderop: fitBounds
zoomde uit tot zoom 10 en de straten waren onzichtbaar. De geometrie kwam
bovendien altijd van Overpass, terwijl de app hem in _netwerk.csv meegeeft;
faalde Overpass, dan kwam er niets, zonder melding.

Sinds v3.63:
  1. een straat is een lijn, uit _netwerk.csv; Overpass alleen voor wat daar
     ontbreekt. Een straat beslaat de wegen van zijn eigen tikken, niet alleen
     de ene way-id uit _capaciteit.csv;
  2. het getal staat op het midden van de eigen tikken (zonder tikken: halverwege
     de langste lijn). Terreinen blijven vlakken met het getal op het zwaartepunt.

  A. Een capaciteitstelling uit de app zelf (langs Noordstraat 3): een lijn,
     het getal tussen de tikken, ingezoomd, en geen Overpass-verzoek.
  B. Een gemaakte ZIP: een straat over twee wegen (de eerste bijna recht), een
     straat zonder naam, tikken die niet gesnapt zijn en een terrein; Overpass
     faalt. Alles uit _netwerk.csv, elk getal op het midden van zijn tikken, het
     terrein onveranderd, en alles in beeld.
  C. Een oude ZIP zonder _netwerk.csv en zonder telregels: de lijn komt van
     Overpass, het getal halverwege de lijn.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/capaciteittest.py
"""
import json, os, re, sys, urllib.parse, zipfile
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

UIT = '/tmp/capaciteittest'; os.makedirs(UIT, exist_ok=True)

def maak_zip(b):
    """Een capaciteitstelling met de app: noordwaarts langs Noordstraat 3."""
    ctx = nieuwe_context(b); pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'capaciteitstelling.html', wait_until='load'); pg.wait_for_timeout(600)
    ctx.set_geolocation({'latitude': LAT + 0.0003, 'longitude': LON + 0.00003, 'accuracy': 5})
    pg.evaluate('startSession()'); pg.wait_for_timeout(1200)
    for i in range(8):
        ctx.set_geolocation({'latitude': LAT + 0.0003 + i * 0.00012, 'longitude': LON + 0.00003, 'accuracy': 5})
        pg.wait_for_timeout(300)
        pg.evaluate("addEntry('regulier','%s')" % 'LR'[i % 2]); pg.wait_for_timeout(60)
    with pg.expect_download(timeout=20000) as d:
        pg.evaluate('exportZip()')
    pad = os.path.join(UIT, d.value.suggested_filename); d.value.save_as(pad)
    ctx.close()
    return pad, f

KOP_CAP = 'sessie_id;osm_way_id;naam;zijde;soort;capaciteit;eerste_waarneming;laatste_waarneming'
KOP_TEL = 'sessie_id;nr;tijdstip;type;zijde;straat;lat_marker;lon_marker;lat_gps;lon_gps;snapped;osm_way_id;hdg_kompas;hdg_gps;hdg_osm;hdg_gebruikt'
wkt = lambda pts: ', '.join('%.6f %.6f' % (o, a) for a, o in pts)

# B: Rechtestraat = way 9001 (drie punten, bijna op één lijn) + 9002 erachter.
R1 = [(LAT + 0.0020, LON + 0.0100), (LAT + 0.0026, LON + 0.0100 + 1e-6), (LAT + 0.0032, LON + 0.0100)]
R2 = [R1[-1], (LAT + 0.0040, LON + 0.0100)]
ZN = [(LAT + 0.0020, LON + 0.0110), (LAT + 0.0030, LON + 0.0110)]          # 9003, zonder naam
RING = [(LAT + 0.0020, LON + 0.0120), (LAT + 0.0020, LON + 0.0126), (LAT + 0.0026, LON + 0.0126),
        (LAT + 0.0026, LON + 0.0120), (LAT + 0.0020, LON + 0.0120)]

def maak_b():
    sid = '20261120_101500_tcb'; tik = []
    def zet(straat, way, la, lo, soort='regulier', snapped='1'):
        tik.append((straat, way, la, lo, soort, snapped))
    for i in range(6): zet('Rechtestraat', '9001', LAT + 0.0021 + i * 0.0002, LON + 0.01004)
    for i in range(4): zet('Rechtestraat', '9002', LAT + 0.0033 + i * 0.0002, LON + 0.01004, 'gehandicapt' if i < 2 else 'regulier')
    for i in range(3): zet('—', '9003', LAT + 0.0022 + i * 0.0003, LON + 0.01104)
    for i in range(2): zet('—', '', LAT + 0.0010 + i * 0.0001, LON + 0.0080, snapped='0')
    rijen = [KOP_TEL] + ['%s;%d;2026-11-20T10:%02d:00;%s;L;%s;%.6f;%.6f;%.6f;%.6f;%s;%s;;;;' %
                         (sid, n + 1, n, t[4], t[0], t[2], t[3], t[2], t[3], t[5], t[1]) for n, t in enumerate(tik)]
    pad = os.path.join(UIT, sid + '_cap.zip')
    with zipfile.ZipFile(pad, 'w') as z:
        z.writestr(sid + '_sessie.csv', 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n'
                   '%s;Jay;2026-11-20;2026-11-20 10:00:00;2026-11-20 10:20:00;capaciteit;15\n' % sid)
        z.writestr(sid + '_telregels.csv', '\n'.join(rijen))
        z.writestr(sid + '_capaciteit.csv', '\n'.join([KOP_CAP,
            '%s;9001;Rechtestraat;L+R;regulier;8;2026-11-20T10:00:00;2026-11-20T10:09:00' % sid,
            '%s;9001;Rechtestraat;L+R;gehandicapt;2;2026-11-20T10:06:00;2026-11-20T10:07:00' % sid,
            '%s;9003;(onbekend);L+R;regulier;3;2026-11-20T10:10:00;2026-11-20T10:12:00' % sid,
            '%s;;(niet gesnapped);L+R;regulier;2;2026-11-20T10:13:00;2026-11-20T10:14:00' % sid]))
        z.writestr(sid + '_terrein.csv', KOP_CAP + '\n%s;777001;P Test;nvt;regulier;20;2026-11-20T10:15:00;2026-11-20T10:16:00' % sid)
        z.writestr(sid + '_netwerk.csv', 'osm_way_id;highway;geometrie_wkt\n'
                   '9001;residential;LINESTRING (%s)\n9002;residential;LINESTRING (%s)\n9003;service;LINESTRING (%s)\n'
                   '777001;parking;POLYGON ((%s))\n' % (wkt(R1), wkt(R2), wkt(ZN), wkt(RING)))
    gem = lambda f: (sum(t[2] for t in tik if f(t)) / sum(1 for t in tik if f(t)), sum(t[3] for t in tik if f(t)) / sum(1 for t in tik if f(t)))
    return pad, {'Rechtestraat': gem(lambda t: t[0] == 'Rechtestraat'), '(onbekend)': gem(lambda t: t[1] == '9003'),
                 '(niet gesnapped)': gem(lambda t: t[5] == '0')}

def maak_c():
    sid = '20261120_103000_tcc'; pad = os.path.join(UIT, sid + '_cap.zip')
    with zipfile.ZipFile(pad, 'w') as z:
        z.writestr(sid + '_sessie.csv', 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n'
                   '%s;Jay;2026-11-20;2026-11-20 10:30:00;2026-11-20 10:40:00;capaciteit;7\n' % sid)
        z.writestr(sid + '_capaciteit.csv', KOP_CAP + '\n%s;9001;Rechtestraat;L+R;regulier;7;2026-11-20T10:31:00;2026-11-20T10:39:00' % sid)
    return pad

# Overpass: geteld per verzoek, met de gevraagde way-id's.
verzoeken = []
def overpass(antwoord):
    def r_(r):
        u = r.request.url
        if 'overpass' in u:
            q = urllib.parse.unquote_plus((r.request.post_data or '') + u)
            verzoeken.append(q)
            return antwoord(r, q)
        return route(r)
    return r_
nep_osm = lambda r, q: r.fulfill(body=OSM, content_type='application/json')
kapot = lambda r, q: r.fulfill(status=504, body='')
def met_9001(r, q):
    return r.fulfill(body=json.dumps({'version': 0.6, 'elements': [{'type': 'way', 'id': 9001,
        'geometry': [{'lat': a, 'lon': o} for a, o in R1]}]}), content_type='application/json')

KAART = r"""((sid) => {
  const L_ = capLayers[sid] || [];
  const lijnen = L_.filter(l => l instanceof L.Polyline && !(l instanceof L.Polygon));
  const vlakken = L_.filter(l => l instanceof L.Polygon);
  const getallen = L_.filter(l => l.getLatLng && !l.getLatLngs).map(l => {
    const ll = l.getLatLng(), d = document.createElement('div'); d.innerHTML = l.options.icon.options.html;
    return { n: +d.textContent, lat: ll.lat, lon: ll.lng, inBeeld: map.getBounds().contains(ll) }; });
  return { lijnen: lijnen.map(l => ({ n: l.getLatLngs().length, eerste: [l.getLatLngs()[0].lat, l.getLatLngs()[0].lng],
                                       tip: l.getTooltip() ? l.getTooltip().getContent() : '' })),
           vlakken: vlakken.length, getallen, zoom: map.getZoom(), zonder: sessions[sid].zonderGeom || [] };
})(%r)"""

def laad(b, zips, rt):
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); ctx.route('**/*', rt)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(800)
    verzoeken.clear()
    pg.set_input_files('#file-input', zips); pg.wait_for_timeout(3500)
    return ctx, pg, fouten

bij = lambda p, q, m=1e-6: abs(p[0] - q[0]) < m and abs(p[1] - q[1]) < m

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Een capaciteitstelling uit de app ==')
    za, jsf = maak_zip(b)
    eis('de app maakt een _cap.zip zonder JS-fouten', za.endswith('_cap.zip') and not jsf, (za, jsf))
    sid_a = os.path.basename(za)[:-len('_cap.zip')]
    tik_a = [r.split(';') for r in zipfile.ZipFile(za).read(sid_a + '_telregels.csv').decode().split('\n')[1:] if r]
    eis('de app geeft het netwerk mee in _netwerk.csv', any(n.endswith('_netwerk.csv') for n in zipfile.ZipFile(za).namelist()))
    ctx, pg, fouten = laad(b, [za], overpass(nep_osm))
    k = pg.evaluate(KAART % sid_a)
    eis('geen Overpass-verzoek: de straat komt uit _netwerk.csv', not verzoeken, len(verzoeken))
    eis('de straat is een lijn, geen vlak', len(k['lijnen']) >= 1 and k['vlakken'] == 0, k)
    # Eén tik ligt op de kruising met Dwarsstraat 5. De app zet hem onder de naam
    # van die weg (osmName), terwijl in 'straat' Noordstraat 3 blijft staan.
    cap_a = [r.split(';') for r in zipfile.ZipFile(za).read(sid_a + '_capaciteit.csv').decode().split('\n')[1:] if r]
    per_weg = {r[1]: int(r[5]) for r in cap_a}
    eis('een getal per regel in _capaciteit.csv (%s)' % per_weg,
        sorted(g['n'] for g in k['getallen']) == sorted(per_weg.values()), k['getallen'])
    for w, n in per_weg.items():
        eigen = [r for r in tik_a if r[11] == w]
        la = sum(float(r[6]) for r in eigen) / max(1, len(eigen)); lo = sum(float(r[7]) for r in eigen) / max(1, len(eigen))
        g = [g for g in k['getallen'] if g['n'] == n]
        eis('way %s: %d tikken, het getal %d op hun midden' % (w, len(eigen), n),
            len(eigen) == n and g and bij((g[0]['lat'], g[0]['lon']), (la, lo)), (g, la, lo, len(eigen)))
    eis('ingezoomd (zoom 15 of meer) en elk getal in beeld', k['zoom'] >= 15 and k['getallen'] and all(g['inBeeld'] for g in k['getallen']), k)
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    ctx.close()

    print('\n== B. Een straat over twee wegen, een straat zonder naam, niet gesnapt en een terrein; Overpass faalt ==')
    zb, midden = maak_b()
    ctx, pg, fouten = laad(b, [zb], overpass(kapot))
    k = pg.evaluate(KAART % '20261120_101500_tcb')
    eis('geen Overpass-verzoek: alles staat in _netwerk.csv', not verzoeken, len(verzoeken))
    eis('drie lijnen (Rechtestraat over 9001 en 9002, en 9003), één vlak (het terrein)',
        len(k['lijnen']) == 3 and k['vlakken'] == 1, k)
    eersten = sorted(round(l['eerste'][0], 6) for l in k['lijnen'])
    eis('de lijnen zijn 9001, 9002 en 9003 uit het netwerk',
        eersten == sorted(round(x, 6) for x in [R1[0][0], R2[0][0], ZN[0][0]]), eersten)
    eis('de tooltip van een lijn: naam en capaciteit',
        any('Rechtestraat' in l['tip'] and 'capaciteit: 10' in l['tip'] for l in k['lijnen']), [l['tip'] for l in k['lijnen']])
    per = {g['n']: g for g in k['getallen']}
    eis('vier getallen: 10, 3, 2 en 20', sorted(per) == [2, 3, 10, 20], sorted(per))
    for n, naam in [(10, 'Rechtestraat'), (3, '(onbekend)'), (2, '(niet gesnapped)')]:
        eis('%s: het getal op het midden van de eigen tikken' % naam,
            n in per and bij((per[n]['lat'], per[n]['lon']), midden[naam]), (per.get(n), midden[naam]))
    tc = pg.evaluate("(() => { const p = capLayers['20261120_101500_tcb'].find(l => l instanceof L.Polygon).getCenter(); return [p.lat, p.lng]; })()")
    eis('het terrein: het getal op het zwaartepunt van het vlak, zoals voor v3.63',
        20 in per and bij((per[20]['lat'], per[20]['lon']), tc), (per.get(20), tc))
    eis('alles in beeld, ingezoomd', all(g['inBeeld'] for g in k['getallen']) and k['zoom'] >= 15, k)
    eis('niets zonder geometrie', not k['zonder'], k['zonder'])
    pg.evaluate("""(() => { const m = capLayers['20261120_101500_tcb'].filter(l => l.getLatLng && !l.getLatLngs)
                    .find(l => l.options.icon.options.html.includes('>10<')); m.fire('click'); })()""")
    pg.wait_for_timeout(300)
    eis('klik op het getal: het detail van de Rechtestraat',
        pg.evaluate("document.getElementById('detail-title').textContent") == 'Rechtestraat')
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    ctx.close()

    print('\n== C. Oud: zonder _netwerk.csv en zonder telregels ==')
    zc = maak_c()
    ctx, pg, fouten = laad(b, [zc], overpass(met_9001))
    k = pg.evaluate(KAART % '20261120_103000_tcc')
    eis('de geometrie van 9001 komt van Overpass', len(verzoeken) == 1 and 'way(id:9001)' in verzoeken[0], verzoeken)
    eis('een lijn van drie punten, geen vlak', [l['n'] for l in k['lijnen']] == [3] and k['vlakken'] == 0, k)
    g = k['getallen'][0] if k['getallen'] else {}
    eis('het getal 7 halverwege de lijn', g.get('n') == 7 and bij((g['lat'], g['lon']), R1[1], 2e-5), (g, R1[1]))
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    ctx.close()
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
