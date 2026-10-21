#!/usr/bin/env python3
"""v3.21 stukkentest — telrapport toont fiets- en autotellingen per stuk van ~40–60 m.

Aanleiding: een gereconstrueerde fietstelling (Jay, 21 okt 2026) had in
telrapport gaten in het netwerk, en tikken buiten elke cluster. Telrapport las
fiets en auto per hele weg en hield van een _recon (die per stuk is) alleen het
eerste stuk over. Jay koos daarop: alles per stuk, ook de originelen (B2).

Een kleine wijk: weg 501 (200 m noord-zuid, dus 5 stukken van 40 m), weg 502
(124 m oost-west over het midden, 3 stukken) en weg 503 (50 m, korter dan 60 m:
één stuk).

  A. Een origineel (fietsparkeren, zonder segment_index):
     - de wegen in stukken, met dezelfde knip als de reconstructor;
     - elke tik op het stuk waar hij langs de weg staat; de aantallen per stuk
       uit de telregels; het totaal klopt;
     - gelopen stukken zonder tikken (uit het GPS-spoor) gestreept, de rest grijs.
  B. Een _recon van een andere telling op dezelfde straten:
     - alle stukken uit zijn _netwerk.csv, niet alleen het eerste;
     - zijn eigen indeling (segment_index) en _bezocht.csv;
     - op een stuk dat beide tellingen hebben, tellen ze samen op.
  C. Een autotelling: per stuk bezet, vrij en de bezettingsgraad
     ((goed + fout + spec) / alles, zoals de app).
  D. De correctietool: een tik naar een andere weg verplaatst: het stuk en de
     aantallen opnieuw; de export krijgt geen _seg en geen segment_index erbij;
     een zijwissel gebruikt de hele weg.

Hulp (server, CDN-omleiding) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/stukkentest.py
"""
import os, sys, json, math, tempfile, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

TMP = tempfile.mkdtemp(prefix='stukkentest_')
M = 1 / 111320
LM = 1 / (111320 * math.cos(math.radians(LAT)))
# weg 501: noord-zuid, 200 m vanaf (LAT, LON); 502: oost-west over 501 op 90 m; 503: 50 m
W501 = [(LAT, LON), (LAT + 100 * M, LON), (LAT + 200 * M, LON)]
W502 = [(LAT + 90 * M, LON - 62 * LM), (LAT + 90 * M, LON + 62 * LM)]
W503 = [(LAT + 200 * M, LON), (LAT + 200 * M, LON + 50 * LM)]
WEGEN = {'501': W501, '502': W502, '503': W503}
def wkt(pts): return 'LINESTRING (' + ', '.join('%.7f %.7f' % (o, a) for a, o in pts) + ')'
def op501(m, zij=4): return (LAT + m * M, LON + zij * LM)      # 4 m rechts van de as

def tik(sid, nr, typ, wid, pos, straat, extra=''):
    la, lo = pos
    return '%s;%d;2026-10-21 10:%02d:00;%s;R;%s;%.6f;%.6f;%.6f;%.6f;1;%s;0;0;0;0%s\n' % (
        sid, nr, nr, typ, straat, la, lo, la, lo, wid, extra)

TEL_KOP = 'sessie_id;nr;tijdstip;type;zijde;straat;lat_marker;lon_marker;lat_gps;lon_gps;snapped;osm_way_id;hdg_kompas;hdg_gps;hdg_osm;hdg_gebruikt'
def gps(sid):   # langs heel 501, elke 5 m
    return 'sessie_id;tijdstip;lat;lon;nauwkeurigheid\n' + ''.join(
        '%s;2026-10-21 10:00:%02d;%.7f;%.7f;5\n' % (sid, i % 60, LAT + i * 5 * M, LON) for i in range(41))

def maak_zip(naam, bestanden):
    pad = os.path.join(TMP, naam)
    with zipfile.ZipFile(pad, 'w') as z:
        for n, t in bestanden.items(): z.writestr(n, t)
    return pad

# A: origineel, fiets. Tikken op 501 bij 10, 50, 55 en 130 m, en één op 502.
SA = '20261021_100000_ori'
A_TEL = (TEL_KOP + '\n' + tik(SA, 1, 'fiets', '501', op501(10), 'Lintweg') + tik(SA, 2, 'fiets', '501', op501(50), 'Lintweg')
         + tik(SA, 3, 'wrak', '501', op501(55), 'Lintweg') + tik(SA, 4, 'fiets', '501', op501(130), 'Lintweg')
         + tik(SA, 5, 'fiets', '502', (LAT + 94 * M, LON + 5 * LM), 'Dwars'))
ZA = maak_zip(SA + '_fts.zip', {
    SA + '_sessie.csv': 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n%s;T1;2026-10-21;2026-10-21 10:00:00;2026-10-21 10:10:00;fiets;5\n' % SA,
    SA + '_telregels.csv': A_TEL,
    SA + '_straten.csv': 'sessie_id;naam;osm_way_ids;fiets;brommer;breed;wrak;totaal;eerste_waarneming;laatste_waarneming\n'
                         '%s;Lintweg;501;3;0;0;1;4;;\n%s;Dwars;502;1;0;0;0;1;;\n' % (SA, SA),
    SA + '_netwerk.csv': 'osm_way_id;highway;geometrie_wkt\n' + ''.join('%s;cycleway;%s\n' % (w, wkt(g)) for w, g in WEGEN.items()),
    SA + '_gps.csv': gps(SA)})

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1280, 'height': 860}, accept_downloads=True)
    ctx.route('**/*', route_met_osm)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(500)

    # De recon-ZIP's _netwerk.csv maken we met de knip van telrapport zelf; die is
    # byte-identiek aan de reconstructor (valideer.py).
    def knip(g): return pg.evaluate('(g) => splitWayIntoSegments(g)', [[a, o] for a, o in g])
    STUKKEN = {w: knip(g) for w, g in WEGEN.items()}
    eis('de knip: 501 in 5 stukken, 502 in 3, 503 (50 m) in 1',
        [len(STUKKEN[w]) for w in ('501', '502', '503')] == [5, 3, 1], [len(STUKKEN[w]) for w in STUKKEN])

    print('== A. origineel (fiets) ==')
    pg.set_input_files('#file-input', [ZA]); pg.wait_for_timeout(1500)
    PER = """(k) => wayData[k] ? wayData[k].sessions.map(e => e.zeroVisited ? 'nul' : e.totaal) : null"""
    sleutels = pg.evaluate("Object.keys(wayData).sort()")
    eis('alle stukken in wayData (5 + 3 + 1)', sleutels == sorted(['501:%d' % i for i in range(5)] + ['502:%d' % i for i in range(3)] + ['503:0']), sleutels)
    lengtes = pg.evaluate("['501:0','501:1','501:2','501:3','501:4'].map(k => Math.round(segmentLengthM(wayData[k].geometry)))")
    eis('elk stuk van 501 is 40 m', lengtes == [40] * 5, lengtes)
    tellen = {k: pg.evaluate(PER, k) for k in ['501:0', '501:1', '501:2', '501:3', '501:4', '502:1']}
    eis('tikken op hun stuk: 10 m -> stuk 0, 50 en 55 m -> stuk 1, 130 m -> stuk 3, de tik op 502 -> zijn middelste stuk',
        tellen['501:0'] == [1] and tellen['501:1'] == [2] and tellen['501:3'] == [1] and tellen['502:1'] == [1], tellen)
    eis('gelopen stukken zonder tikken (uit het GPS-spoor): 501 stuk 2 en 4', tellen['501:2'] == ['nul'] and tellen['501:4'] == ['nul'], tellen)
    eis('de teller "fietsen": 4 (type fiets; het wrak telt daar niet, zoals voorheen)', pg.evaluate("document.getElementById('s-fietsen').textContent") == '4',
        pg.evaluate("document.getElementById('s-fietsen').textContent"))
    eis('totaal per stuk telt wel alle types: stuk 1 = fiets + wrak = 2', pg.evaluate("wayHeat('501:1').total") == 2)
    dek = pg.evaluate("clusterDekking('%s')" % SA)
    eis('alle 5 tikken in een cluster', dek['geplaatst'] == 5 and dek['buiten'] == 0, dek)
    kleur = pg.evaluate("({geteld: wayLayers['501:1'].options.color, nul: wayLayers['501:2'].options.dashArray, grijs: wayLayers['503:0'].options.color})")
    eis('geteld in kleur, nul gestreept, niet gelopen grijs', kleur['geteld'] != '#3a3d42' and kleur['nul'] and kleur['grijs'] == '#3a3d42', kleur)

    print('\n== B. _recon van een andere telling ==')
    SB = '20261021_110000_rec'
    seg = lambda w, i: STUKKEN[w][i]
    B_TEL = (TEL_KOP + ';segment_index;recon_status\n'
             + tik(SB, 1, 'fiets', '501', op501(45), 'Lintweg', ';1;ok') + tik(SB, 2, 'fiets', '501', op501(170), 'Lintweg', ';4;ok')
             + tik(SB, 3, 'brommer', '501', op501(175), 'Lintweg', ';4;ok'))
    ZB = maak_zip(SB + '_fts_recon.zip', {
        SB + '_sessie.csv': 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b;reconstructie\n'
                            '%s;2026-10-21;2026-10-21 11:00:00;2026-10-21 11:10:00;fiets;;3;;;;v3.21\n' % SB,
        SB + '_telregels.csv': B_TEL,
        SB + '_straten.csv': 'sessie_id;naam;osm_way_ids;fiets;brommer;breed;wrak;totaal;eerste_waarneming;laatste_waarneming\n%s;Lintweg;501;2;1;0;0;3;;\n' % SB,
        SB + '_netwerk.csv': 'osm_way_id;segment_index;segment_count;highway;geometrie_wkt\n' + ''.join(
            '%s;%d;%d;cycleway;%s\n' % (w, i, len(st), wkt(sg)) for w, st in STUKKEN.items() for i, sg in enumerate(st)),
        SB + '_bezocht.csv': 'sessie_id;datum;osm_way_id;segment_index;segment_count;straat;start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen\n'
                             + ''.join('%s;2026-10-21;501;%d;5;Lintweg;11:00:00;11:01:00;60;8;%d\n' % (SB, i, n) for i, n in [(0, 0), (1, 1), (2, 0), (3, 0), (4, 2)]),
        SB + '_gps.csv': gps(SB)})
    pg.set_input_files('#file-input', [ZB]); pg.wait_for_timeout(1500)
    alle = all(pg.evaluate("(k) => !!wayData[k]", '%s:%d' % (w, i)) for w, st in STUKKEN.items() for i in range(len(st)))
    eis('alle stukken uit het _netwerk.csv van de _recon (tot v3.21: alleen het eerste)', alle)
    t1, t4 = pg.evaluate(PER, '501:1'), pg.evaluate(PER, '501:4')
    eis('zijn eigen indeling (segment_index): stuk 1 en stuk 4', 1 in t1 and 2 in t4, (t1, t4))
    eis('op stuk 1 tellen beide tellingen samen op (origineel 2, _recon 1 -> 3)',
        sorted(t1) == [1, 2] and pg.evaluate("wayHeat('501:1').total") == 3, (t1, pg.evaluate("wayHeat('501:1')")))
    t0 = pg.evaluate(PER, '501:0')
    eis('_bezocht.csv: stuk 0 gelopen zonder tikken (naast de tik van het origineel)', 'nul' in t0 and 1 in t0, t0)
    eis('alle tikken van de _recon in een cluster', pg.evaluate("clusterDekking('%s').buiten" % SB) == 0)

    print('\n== C. autotelling ==')
    SC = '20261021_120000_aut'
    C_TEL = (TEL_KOP + '\n' + tik(SC, 1, 'goed', '501', op501(5), 'Lintweg') + tik(SC, 2, 'goed', '501', op501(15), 'Lintweg')
             + tik(SC, 3, 'leeg', '501', op501(25), 'Lintweg') + tik(SC, 4, 'leeg', '501', op501(35), 'Lintweg')
             + tik(SC, 5, 'fout', '501', op501(60), 'Lintweg'))
    ZC = maak_zip(SC + '_car.zip', {
        SC + '_sessie.csv': 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n%s;T2;2026-10-21;2026-10-21 12:00:00;2026-10-21 12:10:00;auto;5\n' % SC,
        SC + '_telregels.csv': C_TEL,
        SC + '_straten.csv': 'sessie_id;naam;osm_way_ids;goed;fout;leeg;spec;bezet;vrij;bezettingsgraad_pct;eerste_waarneming;laatste_waarneming\n'
                             '%s;Lintweg;501;2;1;2;0;3;2;60;;\n' % SC,
        SC + '_netwerk.csv': 'osm_way_id;highway;geometrie_wkt\n' + ''.join('%s;residential;%s\n' % (w, wkt(g)) for w, g in WEGEN.items()),
        SC + '_gps.csv': gps(SC)})
    pg.set_input_files('#file-input', [ZC]); pg.wait_for_timeout(1500)
    AUTO = """(k) => wayData[k].sessions.filter(e => e.sid === '%s').map(e => [e.bezet, e.vrij, e.bezettingsgraad_pct, !!e.zeroVisited])""" % SC
    a0, a1 = pg.evaluate(AUTO, '501:0'), pg.evaluate(AUTO, '501:1')
    eis('stuk 0: 2 goed en 2 leeg -> bezet 2, vrij 2, 50 %', a0 == [[2, 2, 50, False]], a0)
    eis('stuk 1: 1 fout -> bezet 1, vrij 0, 100 %', a1 == [[1, 0, 100, False]], a1)
    eis('het totaal bezet: 3', pg.evaluate("document.getElementById('s-bezet').textContent") == '3',
        pg.evaluate("document.getElementById('s-bezet').textContent"))

    print('\n== D. de correctietool ==')
    r = pg.evaluate("""(sid) => { var r = telData[sid].find(x => x.nr === '1');
        r.osm_way_id = '502'; r.lat_marker = String(%f); r.lon_marker = String(%f);
        naCorrectie(sid, r); return {seg: r._seg}; }""" % (LAT + 94 * M, LON - 50 * LM), SA)
    na0, na502 = pg.evaluate("(k) => wayData[k].sessions.filter(e => e.sid === '%s').map(e => e.zeroVisited ? 'nul' : e.totaal)" % SA, '501:0'), \
                 pg.evaluate("(k) => wayData[k].sessions.filter(e => e.sid === '%s').map(e => e.totaal)" % SA, '502:0')
    eis('een tik van 501 naar het westen van 502: stuk opnieuw (502 stuk 0), aantallen opnieuw',
        r['seg'] == 0 and na502 == [1] and 1 not in na0, (r, na0, na502))
    exp = pg.evaluate("buildTelregelsCsv('%s')" % SA).split('\n')[0]
    eis('de export krijgt geen _seg en geen segment_index erbij', '_seg' not in exp and 'segment_index' not in exp, exp)
    heel = pg.evaluate("(w) => Math.round(segmentLengthM(heleWeg(w)))", '501')
    eis('de zijwissel en de keuzelijst gebruiken de hele weg (200 m), niet het eerste stuk', heel == 200, heel)
    eis('geen JS-fouten', not fouten, fouten)
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d FOUT, %d OK' % (fout, ok)))
sys.exit(1 if fout else 0)
