#!/usr/bin/env python3
"""v3.17 onderhoudtest — opruimen van de backlog, in Chromium.

  A. Telrapport, pocket zonder _netwerk.csv. Stond op de opruimlijst als
     terugval voor oude ZIP's, maar pocket schrijft het bestand alleen als er bij
     Stop een netwerk in het geheugen is; na Doortellen ontbreekt het soms. Dan
     haalt telrapport de geometrie van de getelde ways via Overpass: dat moet
     blijven werken, zonder melding. Een pocket-ZIP mét netwerk laadt zonder één
     Overpass-verzoek.
  B. Capaciteitstelling, parkeerterreinen zoeken (zoekTerreinen):
     - een tweede zoekpunt binnen 150 m van een eerder: geen verzoek;
     - verder weg: wel, en de terreinen van eerst blijven op de kaart;
     - elk terrein wordt één keer getekend, ook na herhaald zoeken;
     - een geteld terrein houdt zijn donkere rand na verder zoeken;
     - tijdens een sessie: de polygonen in het netwerk, zonder dubbelen;
     - een rate-limit bij de eerste server: niet de tweede belasten, en die plek
       later opnieuw proberen.
  (Het bbox-filter voor verzamelingen staat in functest_bbox.js.)

Hulp (server, CDN-omleiding, nep-Overpass) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/onderhoudtest.py
"""
import os, sys, io, json, re, tempfile, zipfile
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

TMP = tempfile.mkdtemp(prefix='onderhoudtest_')

def pocket_zip(naam, sid, met_netwerk=True):
    d = 7 / 111320
    z = zipfile.ZipFile(os.path.join(TMP, naam), 'w')
    z.writestr(sid + '_sessie.csv', 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b\n'
               '%s;2026-10-16;2026-10-16 10:00:00;2026-10-16 10:01:30;pocket;parkeren;4;parkeren;;\n' % sid)
    regels = ''.join('%s;%d;2026-10-16 10:00:%02d;bezet;%.6f;%.6f;1003;0;Noordstraat 3;0.9;green;0.9;green;rechts;1.2\n'
                     % (sid, i + 1, i * 20, LAT + 2 * i * d, LON) for i in range(4))
    z.writestr(sid + '_telregels.csv', 'sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat;conf;conf_level;'
               'gps_stab;gps_level;richting;snelheid\n' + regels)
    z.writestr(sid + '_gps.csv', 'sessie_id;tijdstip;lat;lon;nauwkeurigheid;osm_way_id;segment_index;straat\n' +
               ''.join('%s;2026-10-16 10:00:%02d;%.6f;%.6f;5;1003;0;Noordstraat 3\n' % (sid, i * 10, LAT + i * d, LON) for i in range(9)))
    if met_netwerk:
        z.writestr(sid + '_netwerk.csv', 'osm_way_id;segment_index;segment_count;highway;geometrie_wkt\n'
                   '1003;0;1;residential;LINESTRING (%.6f %.6f, %.6f %.6f)\n' % (LON, LAT - 0.004, LON, LAT + 0.008))
    z.close()
    return os.path.join(TMP, naam)

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. telrapport: pocket met en zonder _netwerk.csv ==')
    OVP = []
    def route_a(r, *_):
        if 'overpass' in r.request.url: OVP.append(r.request.url)
        return route_met_osm(r)
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}); ctx.route('**/*', route_a)
    pg = ctx.new_page(); fouten = []; meldingen = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.on('dialog', lambda d: (meldingen.append(d.message), d.accept()))
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(600)
    zonder = pocket_zip('oud_pkt_p.zip', '20261016_100000_oud_pkt_p', met_netwerk=False)
    met = pocket_zip('nieuw_pkt_p.zip', '20261016_110000_nwe_pkt_p')
    OVP.clear()
    pg.set_input_files('#file-input', [zonder]); pg.wait_for_timeout(2000)
    eis('zonder netwerk (zoals na Doortellen): geladen, geen melding',
        pg.evaluate("!!sessions['20261016_100000_oud_pkt_p']") and not meldingen, meldingen)
    eis('zonder netwerk: de geometrie van de getelde way komt via Overpass (één verzoek)',
        len(OVP) == 1 and 'way(id' in unquote(OVP[0]) and '1003' in OVP[0], OVP)
    meldingen.clear(); OVP.clear()
    pg.set_input_files('#file-input', [met]); pg.wait_for_timeout(2000)
    eis('gewone pocket-ZIP: geladen, zonder melding', pg.evaluate("!!sessions['20261016_110000_nwe_pkt_p']") and not meldingen, meldingen)
    eis('gewone pocket-ZIP: geen Overpass-verzoek', not OVP, OVP)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== B. capaciteitstelling: parkeerterreinen zoeken ==')
    PARK = {'1': [], '2': []}
    SCEN = {'1': 'ok'}
    def route_b(r, *_):
        u = unquote(r.request.url)
        if 'overpass' in u and 'amenity=parking' in u:
            server = '1' if 'overpass-api.de' in u else '2'
            PARK[server].append(u)
            if server == '1' and SCEN['1'] == '429':
                return r.fulfill(status=429, body='rate limited', content_type='text/plain')
            m = re.search(r'around:\d+,(-?[\d.]+),(-?[\d.]+)', u)
            la, lo = float(m.group(1)), float(m.group(2))
            # Eén terrein per zoekvraag, op het zoekpunt, met een id uit de plek
            # (afgerond op ~110 m, zodat dichtbij zoeken hetzelfde terrein vindt)
            tid = int(round(la * 1000)) * 100000 + int(round(lo * 1000))
            dd = 0.0003
            geo = [{'lat': la - dd, 'lon': lo - dd}, {'lat': la - dd, 'lon': lo + dd},
                   {'lat': la + dd, 'lon': lo + dd}, {'lat': la + dd, 'lon': lo - dd}, {'lat': la - dd, 'lon': lo - dd}]
            body = {'version': 0.6, 'elements': [{'type': 'way', 'id': tid, 'tags': {'amenity': 'parking', 'name': 'P%d' % tid, 'capacity': '20'},
                                                  'geometry': geo}]}
            return r.fulfill(body=json.dumps(body), content_type='application/json')
        return route_met_osm(r)
    ctx, pg, fouten = open_app(b, 'capaciteitstelling.html')
    ctx.unroute('**/*'); ctx.route('**/*', route_b)
    pg.evaluate('kiesTerreinModus()'); pg.wait_for_timeout(800)
    TOESTAND = "({v:terreinVerzoeken,mk:terreinMarkers.length,pl:terreinPolygons.length,ids:terreinPolygons.map(p=>p.terreinData.id)})"
    def zoek(la, lo, wacht=600):
        pg.evaluate('zoekTerreinen(%f,%f)' % (la, lo)); pg.wait_for_timeout(wacht)
        return pg.evaluate(TOESTAND)
    m = 1 / 111320
    A = (LAT + 0.02, LON)
    v0 = pg.evaluate('terreinVerzoeken'); n1 = len(PARK['1'])
    s = zoek(*A)
    eis('eerste zoekpunt: één verzoek, één terrein getekend', s['v'] == v0 + 1 and len(PARK['1']) == n1 + 1 and s['pl'] >= 1, (s, v0))
    pl_a = s['pl']
    s = zoek(A[0] + 100 * m, A[1])
    eis('100 m verder: geen verzoek', s['v'] == v0 + 1 and len(PARK['1']) == n1 + 1, s)
    s = zoek(A[0] + 140 * m, A[1] + 0 * m)
    eis('140 m verder: nog steeds geen verzoek', s['v'] == v0 + 1, s)
    s = zoek(A[0] + 400 * m, A[1])
    eis('400 m verder: wel een verzoek, het eerste terrein blijft staan', s['v'] == v0 + 2 and s['pl'] == pl_a + 1, s)
    s = zoek(*A)
    eis('terug naar het begin: geen verzoek, niets dubbel getekend', s['v'] == v0 + 2 and s['pl'] == pl_a + 1
        and len(set(s['ids'])) == len(s['ids']), s)

    print('-- tellen in een sessie --')
    pg.evaluate('startSession()'); pg.wait_for_timeout(800)
    s = zoek(*A)
    NET = "snap.networkElements.filter(e=>e.tags&&e.tags.amenity==='parking').map(e=>String(e.id))"
    net = pg.evaluate(NET)
    eis('sessie: het terrein bij het zoekpunt staat in het netwerk, één keer', len(net) >= 1 and len(set(net)) == len(net), net)
    zoek(*A); zoek(A[0] + 50 * m, A[1])
    net2 = pg.evaluate(NET)
    eis('herhaald zoeken: geen dubbelen in het netwerk', len(set(net2)) == len(net2) and len(net2) == len(net), (net, net2))
    tid = pg.evaluate("terreinPolygons.find(p=>Math.abs(p.terreinData.lat-%f)<0.001).terreinData.id" % A[0])
    pg.evaluate("selecteerTerrein(terreinPolygons.find(p=>p.terreinData.id===%r).terreinData)" % tid)
    pg.evaluate("document.getElementById('inp-regulier').value=12; slaTerreinOp()"); pg.wait_for_timeout(200)
    zoek(A[0] + 800 * m, A[1]); zoek(*A)
    kleur = pg.evaluate("terreinPolygons.find(p=>p.terreinData.id===%r).options.color" % tid)
    eis('een geteld terrein houdt zijn donkere rand na verder zoeken', kleur == '#1a1918', kleur)
    eis('geteld terrein komt in de export van _terrein.csv', '12' in pg.evaluate('buildTerreinCsvString()'))

    print('-- rate-limit --')
    SCEN['1'] = '429'
    v1 = pg.evaluate('terreinVerzoeken'); a1, a2 = len(PARK['1']), len(PARK['2'])
    C = (LAT - 0.03, LON)
    s = zoek(*C, wacht=800)
    eis('rate-limit bij server 1: server 2 niet gevraagd', len(PARK['1']) == a1 + 1 and len(PARK['2']) == a2, (len(PARK['1']), len(PARK['2'])))
    SCEN['1'] = 'ok'
    s = zoek(C[0] + 10 * m, C[1], wacht=800)
    eis('dezelfde plek later: opnieuw geprobeerd (mislukt zoeken wordt niet onthouden)', len(PARK['1']) == a1 + 2, len(PARK['1']))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d FOUT, %d OK' % (fout, ok)))
sys.exit(1 if fout else 0)
