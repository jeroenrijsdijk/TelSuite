#!/usr/bin/env python3
"""v3.34 passantentest — Passanten per uur (passanten.html) in Chromium.

Jay: "Qua winkelstraat kan ik me voorstellen dat het een eigen rapport is - op
basis van de aanbeboden winkeltellingen rektn hij - je selecteert een dag en
uur en op het netwerk verschijnen de gemeten gemiddelden in passanten per uur,
ook als tekstueel label. Basiskaart eronder en niet teveel opties." En: "Zet de
loopsnelheid maar op 1,1 m/s. Middel alle gemeten zaterdagen naar 1 waarde."

De ZIP's worden hier gemaakt: een Voorstraat van 200 m (vijf stukken van 40 m),
heen en terug gelopen; een Kerkstraat van 90 m (twee stukken), alleen heen; een
Steegje van 25 m (één stuk, één passage: de richting komt uit de GPS). Twee
zaterdagen om 13 uur en een donderdag om 11 uur, een reconstructie die voor
het origineel gaat, en een pocket-simpel-ZIP die overgeslagen wordt.

De verwachte waarden rekent deze test zelf uit, los van de pagina, met de
formule van het rekenrig: q = 3600 · Σm / Σ(L/v + t), per looprichting, dan
opgeteld; v = 1,1 m/s.

  A. Inlezen: welke ZIP's meedoen, welke niet en waarom; de reconstructie gaat
     voor het origineel.
  B. Dag en uur: alleen wat gemeten is, is aan te klikken; de standaardkeuze.
  C. Kaart: elk gemeten stuk heeft de goede waarde, als label; één richting
     gemeten geeft een sterretje; niet op dit moment gemeten is grijs.
  D. Labels: overlappen nooit; bij inzoomen komen ze terug.
  E. Popup: straat, waarde, marge, hoe vaak en op welke dagen, richtingen,
     stilstaanders per 100 m.
  S. (v3.36) Eén looprichting: opgehoogd met de verhouding tussen de richtingen
     elders in dezelfde straat op hetzelfde moment (ook als die straat andersom
     getekend is), anders x 2; richting deels onbekend: niet opgehoogd.
  v3.35:
  W. Weekoverzicht: een klik op een stuk straat opent een tabel ma-zo x 0-23
     met passanten per uur, gem. per dag en per uur (samen gerekend), de
     details van een cel, en "Toon op de kaart". Ook een grijs stuk opent het.
  F. Twee zaterdagen worden één waarde (eerst optellen, dan delen).
  G. Op 390 px: niets breder dan het scherm.

Hulp (server, CDN-omleiding) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/passantentest.py
"""
import io, json, math, os, re, shutil, sys, tempfile, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))

# ── testgegevens ────────────────────────────────────────────────────────────
LAT0, LON0 = 51.8500, 4.3000
M_LAT = 111320.0
M_LON = 111320.0 * math.cos(math.radians(LAT0))
V_VOET = 1.1

def punt(dx, dy):
    """dx meter naar het oosten, dy meter naar het noorden -> (lat, lon)."""
    return (LAT0 + dy / M_LAT, LON0 + dx / M_LON)

WEGEN = {   # way_id: (naam, begin (dx, dy), eind (dx, dy), aantal stukken)
    1001: ('Voorstraat', (0, 0), (200, 0), 5),
    1002: ('Kerkstraat', (200, 0), (200, 90), 2),
    1003: ('Steegje', (0, 0), (0, -25), 1),
    # v3.36 slimmer ophogen: nog twee stukken Voorstraat, elk maar één kant op gelopen.
    # 1004 ligt dezelfde kant op getekend als 1001, 1005 andersom (van oost naar west).
    1004: ('Voorstraat', (200, 0), (300, 0), 2),
    1005: ('Voorstraat', (400, 0), (300, 0), 2),
}

def stuk(way, seg):
    """(begin, eind) in meters van stuk seg van een rechte weg."""
    _, a, b, n = WEGEN[way]
    f0, f1 = seg / n, (seg + 1) / n
    return ((a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0),
            (a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1))

def haversine(p, q):
    R, rad = 6371000, math.pi / 180
    la1, la2, dla, dlo = p[0] * rad, q[0] * rad, (q[0] - p[0]) * rad, (q[1] - p[1]) * rad
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def lengte(way, seg):
    """Zoals de pagina hem ziet: uit de WKT van _netwerk.csv, met zes decimalen."""
    a, b = stuk(way, seg)
    r = lambda pt: (round(pt[0], 6), round(pt[1], 6))
    return haversine(r(punt(*a)), r(punt(*b)))

def hms(s): return '%02d:%02d:%02d' % (s // 3600, s // 60 % 60, s % 60)

def sessie_zip(sid, datum, start, passages, wees=0, modus='winkelstraat', recon='', naam=None):
    """passages: [(way, seg, 'heen'|'terug', duur_s, n_tegemoet, n_stil)], achter elkaar gelopen."""
    t = start; bez, tel, gps = [], [], []
    nr = 0
    for way, seg, kant, duur, nteg, nstil in passages:
        a, b = stuk(way, seg)
        if kant == 'terug': a, b = b, a
        if kant == 'ter plekke':          # midden van het stuk, 3 m verder: de richting is niet te zien
            m_ = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); L_ = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            a, b = m_, (m_[0] + 3 * (b[0] - a[0]) / L_, m_[1] + 3 * (b[1] - a[1]) / L_)
        t0, t1 = t, t + duur
        for i in range(0, duur + 1, 2):
            f = i / duur
            la, lo = punt(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            gps.append('%s;%sT%s;%.6f;%.6f;5;%d;%d;%s' % (sid, datum, hms(t0 + i), la, lo, way, seg, WEGEN[way][0]))
        typen = ['tegemoet'] * nteg + ['stilstaand'] * nstil
        for i, ty in enumerate(typen):
            ts = t0 + 1 + (i * (duur - 2)) // max(1, len(typen))
            la, lo = punt((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            nr += 1
            tel.append('%s;%d;%sT%s;%s;%.6f;%.6f;%d;%d;%s;;;;;;1.0' % (sid, nr, datum, hms(ts), ty, la, lo, way, seg, WEGEN[way][0]))
        bez.append('%s;%s;%d;%d;%s;%s;%s;%d;%d;%d' % (sid, datum, way, seg, WEGEN[way][0], hms(t0), hms(t1), duur, duur // 2 + 1, nteg + nstil))
        t = t1 + 1
    for i in range(wees):        # tikken buiten elke passage: tellen nergens mee
        nr += 1
        tel.append('%s;%d;%sT%s;tegemoet;%.6f;%.6f;1001;2;Voorstraat;;;;;;1.0' % (sid, nr, datum, hms(t + 30 + i), LAT0, LON0))
    net = ['osm_way_id;segment_index;segment_count;highway;geometrie_wkt']
    for way, (nm, a, b, n) in sorted(WEGEN.items()):
        for s in range(n):
            p, q = stuk(way, s)
            (la1, lo1), (la2, lo2) = punt(*p), punt(*q)
            net.append('%d;%d;%d;pedestrian;LINESTRING (%.6f %.6f, %.6f %.6f)' % (way, s, n, lo1, la1, lo2, la2))
    kop = 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b' + (';reconstructie' if recon else '')
    rij = ';'.join([sid, datum, hms(start), hms(t), 'pocket', 'ped', str(len(tel)), modus, '', ''] + ([recon] if recon else []))
    bz = io.BytesIO(); z = zipfile.ZipFile(bz, 'w')
    z.writestr(sid + '_sessie.csv', kop + '\n' + rij + '\n')
    z.writestr(sid + '_telregels.csv', 'sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat;conf;conf_level;gps_stab;gps_level;richting;snelheid\n' + '\n'.join(tel) + '\n')
    z.writestr(sid + '_bezocht.csv', 'sessie_id;datum;osm_way_id;segment_index;straat;start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen\n' + '\n'.join(bez) + '\n')
    z.writestr(sid + '_gps.csv', 'sessie_id;tijdstip;lat;lon;nauwkeurigheid;osm_way_id;segment_index;straat\n' + '\n'.join(gps) + '\n')
    z.writestr(sid + '_netwerk.csv', '\n'.join(net) + '\n')
    z.close()
    return (naam or (sid + ('_recon' if recon else '') + '.zip')), bz.getvalue(), passages, datum, start

HEEN = lambda duur, teg, stil: [(1001, s, 'heen', duur, teg[s], stil[s]) for s in range(5)]
TERUG = lambda duur, teg, stil: [(1001, s, 'terug', duur, teg[s], stil[s]) for s in (4, 3, 2, 1, 0)]
S1 = ('20261024_130500_abc_pkt_w', '2026-10-24', 13 * 3600 + 5 * 60,       # zaterdag
      HEEN(35, [6, 8, 5, 7, 9], [1, 0, 2, 0, 1]) + TERUG(40, [7, 6, 9, 4, 5], [0, 1, 1, 0, 0]) +
      [(1002, 0, 'heen', 40, 3, 0), (1002, 1, 'heen', 40, 4, 1)] +            # Kerkstraat: één richting
      [(1003, 0, 'heen', 20, 2, 0)] +                                         # Steegje: richting uit de GPS
      [(1004, 0, 'heen', 40, 4, 0), (1004, 1, 'heen', 40, 5, 0),               # Voorstraat-oost: alleen heen (v3.36)
       (1005, 0, 'heen', 40, 3, 0), (1005, 1, 'heen', 40, 6, 0)])              # Voorstraat, andersom getekend: alleen heen
S1_RECON = (S1[0], S1[1], S1[2], [(w, s, k, d, t + (1 if (w, s) == (1001, 0) else 0), st) for (w, s, k, d, t, st) in S1[3]])
S2 = ('20261017_132000_def_pkt_w', '2026-10-17', 13 * 3600 + 20 * 60,      # zaterdag
      HEEN(30, [5, 5, 5, 5, 5], [0, 0, 0, 0, 0]) + TERUG(30, [4, 4, 4, 4, 4], [0, 0, 0, 0, 0]) +
      [(1003, 0, 'ter plekke', 30, 3, 0)])                                    # Steegje: richting onbekend (v3.36)
S3 = ('20261022_110000_ghi_pkt_w', '2026-10-22', 11 * 3600,                # donderdag
      HEEN(45, [2, 3, 2, 3, 2], [0, 0, 0, 0, 0]) + TERUG(45, [3, 2, 3, 2, 3], [0, 0, 0, 0, 0]))

def archief():
    """{naam: bytes} en de passages per sessie zoals de pagina ze moet gebruiken."""
    uit, gebruikt = {}, []
    for spec, extra in ((S1, dict(wees=3)), (S1_RECON, dict(recon='v3.33', wees=2)), (S2, {}), (S3, {})):
        naam, data, pas, datum, start = sessie_zip(*spec, **extra)
        uit[naam] = data
        if spec is not S1: gebruikt.append((datum, start, pas))       # S1 zelf: de reconstructie gaat voor
    naam, data, *_ = sessie_zip('20261023_100000_jkl_pkt_s', '2026-10-23', 10 * 3600, HEEN(30, [1] * 5, [0] * 5), modus='simpel')
    uit[naam] = data                                                     # pocket simpel: geen winkelstraat
    uit['foto.zip'] = b'PK\x05\x06' + b'\x00' * 18                        # lege ZIP: ook overslaan
    return uit, gebruikt

DAG = {'2026-10-24': 5, '2026-10-17': 5, '2026-10-22': 3}   # 0 = maandag
def verwacht(gebruikt, v=V_VOET):
    """{(way, seg, dag, uur): dict(q, m, compleet, stil100, n, datums)} met de formule van het rig."""
    cel = {}
    for datum, start, pas in gebruikt:
        t = start
        for way, seg, kant, duur, nteg, nstil in pas:
            t0, t1 = t, t + duur; t = t1 + 1
            uur = ((t0 + t1) // 2) // 3600
            k = (way, seg, DAG[datum], uur)
            c = cel.setdefault(k, {'stromen': {}, 'stil': 0, 'L': 0.0, 'n': 0, 'datums': set()})
            # richting: A = oplopende segment_index; een losse passage op een way: uit de GPS (begin -> eind van de way)
            r = {'heen': 'A', 'terug': 'B'}.get(kant, '?')
            s = c['stromen'].setdefault(r, [0, 0.0])
            L = lengte(way, seg)
            s[0] += nteg; s[1] += L / v + duur
            c['stil'] += nstil; c['L'] += L; c['n'] += 1; c['datums'].add(datum)
    uit = {}
    for k, c in cel.items():
        q = sum(3600 * m / w for m, w in c['stromen'].values())
        uit[k] = dict(q=q, m=sum(m for m, _ in c['stromen'].values()), compleet=set(c['stromen']) == {'A', 'B'},
                      stil100=100 * c['stil'] / c['L'], n=c['n'], datums=sorted(c['datums']), stromen=c['stromen'])
    return uit

def schat(c):
    """v3.36: precies één gemeten stroom en niet compleet -> x 2 (evenveel de andere kant op)."""
    return c['q'] * (2 if not c['compleet'] and len(c['stromen']) == 1 else 1)

MIN_TEGEN = 10
def richting_weg(way):
    _, a, b, _ = WEGEN[way]
    dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy)
    return dx / n, dy / n

def schat_slim(V, k):
    """v3.36: zoals schat(), maar met de verhouding uit dezelfde straat op hetzelfde moment.
    Geeft (q, bron, rho)."""
    c = V[k]; way, seg, dag, uur = k
    if c['compleet'] or len(c['stromen']) != 1: return c['q'], '', None
    r_ = next(iter(c['stromen']))
    if r_ == '?': return 2 * c['q'], 'twee', None
    d0 = richting_weg(way); zelf = [0, 0.0]; ander = [0, 0.0]
    for (w2, s2, d2, u2), c2 in V.items():
        if (w2, s2) == (way, seg) or (d2, u2) != (dag, uur) or WEGEN[w2][0].lower() != WEGEN[way][0].lower(): continue
        if not {'A', 'B'} <= set(c2['stromen']): continue
        d1 = richting_weg(w2); cos = d0[0] * d1[0] + d0[1] * d1[1]
        if abs(cos) < 0.5: continue
        rz = r_ if cos > 0 else ('B' if r_ == 'A' else 'A'); ra = 'B' if rz == 'A' else 'A'
        zelf[0] += c2['stromen'][rz][0]; zelf[1] += c2['stromen'][rz][1]
        ander[0] += c2['stromen'][ra][0]; ander[1] += c2['stromen'][ra][1]
    if zelf[0] < MIN_TEGEN or ander[0] < MIN_TEGEN: return 2 * c['q'], 'twee', None
    rho = (ander[0] / ander[1]) / (zelf[0] / zelf[1])
    return c['q'] * (1 + rho), 'straat', rho

def samen(cellen):
    """Cellen samennemen zoals de kolom gem.: per richting optellen, dan delen. (q, compleet)"""
    st = {}
    for c in cellen:
        for r_, (m, w) in c['stromen'].items():
            a = st.setdefault(r_, [0, 0.0]); a[0] += m; a[1] += w
    return sum(3600 * m / w for m, w in st.values()), set(st) == {'A', 'B'}

if __name__ != '__main__':
    pass   # alleen de gegevens (zo leest een ander script ze in)
else:
    _hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
    exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
        "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
    ok = fout = 0
    def eis(naam, v, x=None):
        global ok, fout
        if v: ok += 1; print('  OK   ' + naam)
        else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))
    def route_kaart(r):
        if r.request.url.split('?')[0].endswith('/leaflet.css'):
            return r.fulfill(body=open(os.path.join(NM, 'leaflet/dist/leaflet.css'), 'rb').read(), content_type='text/css')
        return route(r)

    BESTANDEN, GEBRUIKT = archief()
    V = verwacht(GEBRUIKT)
    tmp = tempfile.mkdtemp(prefix='passanten_')
    PADEN = []
    for naam, data in BESTANDEN.items():
        PADEN.append(os.path.join(tmp, naam)); open(PADEN[-1], 'wb').write(data)
    GEMETEN = """() => GEMETEN.map(x => ({ k: x.seg.key, q: x.c.q, m: x.c.m, compleet: x.c.compleet, kStil: x.c.kStil, n: x.c.n, tekst: labelTekst(x.c, x.seg) }))"""
    LABELS = """() => [...document.querySelectorAll('.qlabel span')].map(e => { const b = e.getBoundingClientRect(); return [e.textContent, b.left, b.top, b.right, b.bottom]; })"""
    def overlap(lab):
        return any(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4] for i, a in enumerate(lab) for b in lab[i + 1:])
    def sleutel(k): w, sg = k.split('/'); return int(w), int(sg)

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 1300, 'height': 900}); ctx.route('**/*', route_kaart)
        pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
        pg.goto(BASIS + 'passanten.html', wait_until='load'); pg.wait_for_timeout(300)
        pg.set_input_files('#bestanden', PADEN)
        pg.wait_for_function("GEMETEN.length > 0", timeout=20000); pg.wait_for_timeout(300)

        print('== A. Inlezen ==')
        ses = pg.evaluate("Object.fromEntries(Object.entries(SESSIES).map(([k, v]) => [k, [v.recon, v.naam]]))")
        eis('drie winkelstraat-tellingen doen mee', sorted(ses) == sorted([S1[0], S2[0], S3[0]]), ses)
        eis('van de eerste de reconstructie, niet het origineel', ses.get(S1[0]) == [True, S1[0] + '_recon.zip'], ses.get(S1[0]))
        over = dict(pg.evaluate("OVERGESLAGEN"))
        eis('niet meegenomen, met de reden: het origineel, de pocket-simpel-ZIP, een ZIP zonder telling',
            over == {S1[0] + '.zip': 'origineel; de reconstructie doet mee', '20261023_100000_jkl_pkt_s.zip': 'geen winkelstraat-telling',
                     'foto.zip': 'geen telling van telonline.org'}, over)
        mel = pg.inner_text('#melding')
        eis('de melding noemt wat niet meedoet, en de tikken buiten een passage', 'Niet meegenomen' in mel and 'foto.zip' in mel and '2 van de' in mel, mel)
        sam = pg.inner_text('#samenvatting')
        eis('samenvatting: 3 tellingen, 1 donderdag, 2 zaterdagen, 12 stukken straat', sam == '3 tellingen \u00b7 1 donderdag, 2 zaterdagen \u00b7 12 stukken straat', sam)

        print('\n== B. Dag en uur ==')
        knoppen = pg.evaluate("[...document.querySelectorAll('#dagen button')].map(b => [b.textContent, b.disabled, b.getAttribute('aria-pressed')])")
        eis('alleen donderdag en zaterdag zijn aan te klikken; zaterdag staat aan (daar zijn de meeste stukken gemeten)',
            [k[0] for k in knoppen if not k[1]] == ['do', 'za'] and [k[0] for k in knoppen if k[2] == 'true'] == ['za'], knoppen)
        eis('uur: alleen 13 (en die staat aan)', pg.evaluate("[...document.querySelectorAll('#uren button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '!' : ''))") == ['13!'])

        print('\n== C. Kaart: zaterdag 13 uur ==')
        gem = pg.evaluate(GEMETEN)
        eis('12 stukken straat gemeten op zaterdag 13 uur', len(gem) == 12, [g['k'] for g in gem])
        fout_q = [(g['k'], g['q'], V[sleutel(g['k']) + (5, 13)]['q']) for g in gem if abs(g['q'] - V[sleutel(g['k']) + (5, 13)]['q']) > 1e-6]
        eis('elke waarde volgens de formule: 3600 · Σm / Σ(L/1,1 + t), per looprichting, opgeteld', not fout_q, fout_q)
        eis('het label is de afgeronde waarde (v3.36: één richting \u00d7 2)', all(g['tekst'].rstrip('*') == str(round(schat_slim(V, sleutel(g['k']) + (5, 13))[0])) for g in gem), [g['tekst'] for g in gem])
        eis('Kerkstraat (alleen heen): het label is tweemaal de gemeten stroom, met een sterretje',
            [g['tekst'] for g in gem if g['k'] == '1002/1'] == [str(round(2 * V[(1002, 1, 5, 13)]['q'])) + '*'], [g['tekst'] for g in gem if g['k'] == '1002/1'])
        eis('Steegje (een keer heen, een keer ter plekke: richting deels onbekend): het gemeten totaal, niet \u00d7 2, wel een sterretje',
            [g['tekst'] for g in gem if g['k'] == '1003/0'] == [str(round(V[(1003, 0, 5, 13)]['q'])) + '*'] and len(V[(1003, 0, 5, 13)]['stromen']) == 2,
            [g['tekst'] for g in gem if g['k'] == '1003/0'])
        ster = sorted(g['k'] for g in gem if g['tekst'].endswith('*'))
        eis('een sterretje alleen waar niet in beide richtingen gelopen is: Kerkstraat, Steegje, Voorstraat-oost (4 stukken)', ster == ['1002/0', '1002/1', '1003/0', '1004/0', '1004/1', '1005/0', '1005/1'], ster)
        pg.click('#dagen button[data-dag="3"]'); pg.wait_for_timeout(200)
        grijs = pg.evaluate("lijnLaag.getLayers().filter(l => l.options.color === GRIJS).length")
        eis('donderdag: uur springt naar 11; Kerkstraat, Steegje en Voorstraat-oost (7 stukken) zijn grijs, de Voorstraat is gemeten',
            pg.evaluate("UUR") == 11 and grijs == 7 and len(pg.evaluate(GEMETEN)) == 5, [pg.evaluate("UUR"), grijs])
        eis('donderdag 11 uur: ook volgens de formule', all(abs(g['q'] - V[sleutel(g['k']) + (3, 11)]['q']) < 1e-6 for g in pg.evaluate(GEMETEN)))
        eis('de kleurschaal loopt over alle dagen (zelfde maximum op donderdag als op zaterdag)',
            abs(pg.evaluate("MAXQ") - max(schat_slim(V, k)[0] for k in V)) < 1e-6)
        pg.click('#dagen button[data-dag="5"]'); pg.wait_for_timeout(200)

        print('\n== S. Slimmer ophogen (v3.36) ==')
        q4, b4, rho4 = schat_slim(V, (1004, 0, 5, 13)); q5, b5, rho5 = schat_slim(V, (1005, 0, 5, 13))
        tekst = lambda k: [g['tekst'] for g in gem if g['k'] == k]
        eis('Voorstraat-oost (dezelfde kant op getekend): opgehoogd met de verhouding uit de rest van de Voorstraat (× %.2f), niet × 2' % (1 + rho4),
            b4 == 'straat' and abs(rho4 - 1) > 0.05 and tekst('1004/0') == [str(round(q4)) + '*'] and tekst('1004/1') == [str(round(schat_slim(V, (1004, 1, 5, 13))[0])) + '*'],
            [rho4, tekst('1004/0'), tekst('1004/1')])
        eis('het andersom getekende stuk: de verhouding omgedraaid (× %.2f = 1 + 1/%.2f)' % (1 + rho5, rho4),
            b5 == 'straat' and abs(rho5 - 1 / rho4) < 1e-9 and tekst('1005/0') == [str(round(q5)) + '*'], [rho4, rho5, tekst('1005/0')])
        pagina = pg.evaluate("[schat(SEGMENTEN['1004/0'].cells['5:13'], SEGMENTEN['1004/0']), schat(SEGMENTEN['1005/0'].cells['5:13'], SEGMENTEN['1005/0'])]")
        eis('de pagina rekent dezelfde verhouding, over de 5 stukken Voorstraat die heen en terug gelopen zijn',
            abs(pagina[0]['rho'] - rho4) < 1e-9 and abs(pagina[1]['rho'] - rho5) < 1e-9 and pagina[0]['stukken'] == 5, pagina)
        t4 = pg.evaluate("(() => { const d = document.createElement('div'); d.innerHTML = popupHtml(SEGMENTEN['1004/0'], SEGMENTEN['1004/0'].cells['5:13']); return d.textContent; })()")
        eis('de details zeggen waar de verhouding vandaan komt',
            'Elders in de Voorstraat is op zaterdag 13:00 wél in beide richtingen gelopen (5 stukken)' in t4
            and ('keer zoveel de andere kant op. Opgehoogd: × %s' % ('%.2f' % (1 + rho4)).replace('.', ',')) in t4, t4)
        tk2 = pg.evaluate("(() => { const d = document.createElement('div'); d.innerHTML = popupHtml(SEGMENTEN['1002/0'], SEGMENTEN['1002/0'].cells['5:13']); return d.textContent; })()")
        eis('Kerkstraat: geen andere Kerkstraat in beide richtingen, dus × 2, en dat staat erbij',
            'In deze straat is op zaterdag 13:00 niet genoeg in beide richtingen geteld' in tk2 and '× 2' in tk2, tk2)
        terug = pg.evaluate("() => { MIN_TEGEN = 1000; SCHATTINGEN = {}; const c = SEGMENTEN['1004/0'].cells['5:13'], x = schat(c, SEGMENTEN['1004/0']); MIN_TEGEN = 10; SCHATTINGEN = {}; return [x.bron, x.q / c.q]; }")
        eis('te weinig tegenliggers in de vergelijking (drempel even op 1000): terug naar × 2', terug == ['twee', 2], terug)

        print('\n== D. Labels ==')
        lab = pg.evaluate(LABELS)
        eis('labels raken elkaar nooit (bij het eerste beeld, %d labels)' % len(lab), lab and not overlap(lab), lab)
        pg.evaluate("kaart.setZoom(15, { animate: false })"); pg.wait_for_timeout(300)
        lab15 = pg.evaluate(LABELS)
        eis('uitgezoomd: minder labels (%d), nog steeds zonder overlap, de drukste blijft' % len(lab15),
            0 < len(lab15) < 12 and not overlap(lab15) and str(round(max(schat_slim(V, sleutel(g['k']) + (5, 13))[0] for g in gem))) in [x[0].rstrip('*') for x in lab15], [x[0] for x in lab15])
        pg.evaluate("kaart.setZoom(19, { animate: false })"); pg.wait_for_timeout(300)
        lab19 = pg.evaluate(LABELS)
        eis('ingezoomd: alle 12 labels terug', len(lab19) == 12 and not overlap(lab19), len(lab19))
        pg.evaluate("kaart.fitBounds(L.latLngBounds([].concat(...Object.values(SEGMENTEN).map(lijnVan))).pad(0.15), { animate: false })"); pg.wait_for_timeout(300)

        print('\n== E. Popup ==')
        v0 = V[(1001, 0, 5, 13)]
        t = pg.evaluate("(() => { const d = document.createElement('div'); d.innerHTML = popupHtml(SEGMENTEN['1001/0'], SEGMENTEN['1001/0'].cells['5:13']); return d.textContent; })()")
        eis('Voorstraat: de waarde, "zaterdag 13:00–14:00", 4 keer langs op 2 zaterdagen, beide richtingen, stilstaanders',
            'Voorstraat' in t and '≈ %d passanten per uur' % round(v0['q']) in t and 'zaterdag 13:00–14:00' in t and '4 keer langsgelopen, op 2 zaterdagen (17-10, 24-10)' in t
            and 'in beide richtingen gemeten' in t and ('stilstaand: %s per 100 m' % ('%.1f' % v0['stil100']).replace('.', ',')) in t, t)
        mg = pg.evaluate("marge(SEGMENTEN['1001/0'].cells['5:13'])")
        eis('de marge omsluit de waarde', mg[0] < v0['q'] < mg[1], mg)
        tk = pg.evaluate("(() => { const d = document.createElement('div'); d.innerHTML = popupHtml(SEGMENTEN['1002/0'], SEGMENTEN['1002/0'].cells['5:13']); return d.textContent; })()")
        eis('Kerkstraat: "* maar één looprichting gemeten", 1 keer op zaterdag 24-10-2026', '* maar één looprichting gemeten' in tk and '1 keer langsgelopen, op zaterdag 24-10-2026' in tk, tk)

        print('\n== W. Weekoverzicht (v3.35) ==')
        # Klik op de Voorstraat, stuk 1: op de kaart staat zaterdag 13 uur.
        pg.evaluate("""lijnLaag.getLayers().find(l => { const ll = l.getLatLngs(), g = SEGMENTEN['1001/0'].geom;
            return Math.abs(ll[0].lat - g[0][1]) < 1e-9 && Math.abs(ll[0].lng - g[0][0]) < 1e-9; }).fire('click')""")
        pg.wait_for_timeout(200)
        eis('een klik op een stuk straat opent het weekoverzicht, met de straat en de lengte',
            pg.is_visible('#week') and pg.inner_text('#week-titel') == 'Voorstraat' and pg.inner_text('#week-sub').startswith('40 m \u00b7 6 keer langsgelopen, op 3 dagen'),
            [pg.inner_text('#week-titel'), pg.inner_text('#week-sub')])
        rijen = pg.evaluate("[...document.querySelectorAll('#week-tabel tbody tr')].map(tr => [...tr.children].map(x => x.textContent))")
        eis('7 dagen (ma-zo), 24 uren, een kolom gem., en een rij gem.',
            len(rijen) == 8 and [x[0] for x in rijen] == ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo', 'gem.'] and all(len(x) == 26 for x in rijen),
            [len(rijen), [len(x) for x in rijen]])
        cel = lambda d, h: rijen[d][1 + h]
        eis('za 13 uur en do 11 uur: de afgeronde waarde; de rest leeg',
            cel(5, 13) == str(round(V[(1001, 0, 5, 13)]['q'])) and cel(3, 11) == str(round(V[(1001, 0, 3, 11)]['q']))
            and sum(1 for d in range(7) for h in range(24) if cel(d, h)) == 2, [cel(5, 13), cel(3, 11)])
        za, do_ = V[(1001, 0, 5, 13)], V[(1001, 0, 3, 11)]
        q_alles, _ = samen([za, do_])
        eis('gem. per dag is die dag; gem. over alles: beide cellen samen gerekend (%.0f), niet het gemiddelde (%.0f)' % (q_alles, (za['q'] + do_['q']) / 2),
            rijen[5][25] == str(round(za['q'])) and rijen[3][25] == str(round(do_['q'])) and rijen[7][25] == str(round(q_alles))
            and rijen[7][14] == str(round(za['q'])) and rijen[7][12] == str(round(do_['q'])) and abs(q_alles - (za['q'] + do_['q']) / 2) > 1,
            [rijen[5][25], rijen[3][25], rijen[7][25]])
        eis('de cel van de kaart (za 13) is gekozen; eronder de details: waarde, 4 keer op 2 zaterdagen, beide richtingen, stilstaanders',
            pg.evaluate("document.querySelector('#week-tabel td.sel').getAttribute('data-cel')") == '5:13'
            and all(x in pg.inner_text('#week-detail') for x in ['\u2248 %d passanten per uur' % round(za['q']), 'zaterdag 13:00\u201314:00',
                                                                 '4 keer langsgelopen, op 2 zaterdagen (17-10, 24-10)', 'in beide richtingen gemeten',
                                                                 'stilstaand: %s per 100 m' % ('%.1f' % za['stil100']).replace('.', ',')]),
            pg.inner_text('#week-detail'))
        mg = pg.evaluate("marge(SEGMENTEN['1001/0'].cells['5:13'])")
        eis('de marge omsluit de waarde', mg[0] < za['q'] < mg[1], mg)
        pg.click('#week-tabel td[data-cel="3:11"]')
        eis('klik op do 11: die cel gekozen, de details van donderdag', 'donderdag 11:00\u201312:00' in pg.inner_text('#week-detail')
            and pg.evaluate("document.querySelector('#week-tabel td.sel').getAttribute('data-cel')") == '3:11')
        pg.click('#week-detail button')
        eis('"Toon donderdag 11:00 op de kaart": het weekoverzicht dicht, de kaart op donderdag 11 uur',
            not pg.is_visible('#week') and pg.evaluate("[DAG, UUR]") == [3, 11]
            and pg.evaluate("document.querySelector('#dagen button[aria-pressed=true]').textContent") == 'do')
        # Op donderdag is de Kerkstraat grijs; ook die opent het weekoverzicht.
        pg.evaluate("""lijnLaag.getLayers().find(l => { const ll = l.getLatLngs(), g = SEGMENTEN['1002/0'].geom;
            return Math.abs(ll[0].lat - g[0][1]) < 1e-9 && Math.abs(ll[0].lng - g[0][0]) < 1e-9; }).fire('click')""")
        pg.wait_for_timeout(200)
        tk = pg.inner_text('#week-detail')
        eis('een grijs stuk (Kerkstraat op donderdag): het weekoverzicht op het moment dat wel gemeten is, met het sterretje',
            pg.inner_text('#week-titel') == 'Kerkstraat' and '* maar \u00e9\u00e9n looprichting gemeten' in tk and '1 keer langsgelopen, op zaterdag 24-10-2026' in tk
            and pg.evaluate("document.querySelector('#week-tabel td.sel').textContent") == str(round(2 * V[(1002, 0, 5, 13)]['q'])) + '*', tk)
        k0 = V[(1002, 0, 5, 13)]
        eis('de details: wat gemeten is, en \u00d7 2 met de aanname', ('* maar \u00e9\u00e9n looprichting gemeten: %d per uur' % round(k0['q'])) in tk
            and 'evenveel mensen de andere kant op lopen: \u00d7 2' in tk and ('\u2248 %d* passanten per uur' % round(2 * k0['q'])) in tk, tk)
        mg2 = pg.evaluate("marge(SEGMENTEN['1002/0'].cells['5:13'])")
        mg1 = pg.evaluate("(() => { const c = SEGMENTEN['1002/0'].cells['5:13'], g = poissonMarge(c.m); return [g[0] * c.q / c.m, g[1] * c.q / c.m]; })()")
        eis('de marge gaat \u00d7 2 mee, en omsluit de opgehoogde waarde', abs(mg2[0] - 2 * mg1[0]) < 1e-9 and abs(mg2[1] - 2 * mg1[1]) < 1e-9 and mg2[0] < 2 * k0['q'] < mg2[1], [mg1, mg2])
        rijen_k = pg.evaluate("[...document.querySelectorAll('#week-tabel tbody tr')].map(tr => [...tr.children].map(x => x.textContent))")
        eis('ook gem. (za, en alles samen) is \u00d7 2: er is maar één richting gemeten',
            rijen_k[5][25] == rijen_k[7][25] == str(round(2 * k0['q'])) + '*', [rijen_k[5][25], rijen_k[7][25]])
        pg.keyboard.press('Escape')
        eis('Escape sluit het weekoverzicht', not pg.is_visible('#week'))
        pg.click('#dagen button[data-dag="5"]'); pg.wait_for_timeout(200)

        print('\n== F. Twee zaterdagen worden één waarde ==')
        apart = [verwacht([g])[(1001, 2, 5, 13)]['q'] for g in GEBRUIKT if g[0] in ('2026-10-24', '2026-10-17')]
        samen = V[(1001, 2, 5, 13)]['q']
        eis('Voorstraat stuk 3 op zaterdag: eerst optellen, dan delen (%.0f), niet het gemiddelde van de twee zaterdagen (%.0f)' % (samen, sum(apart) / 2),
            abs(pg.evaluate("SEGMENTEN['1001/2'].cells['5:13'].q") - samen) < 1e-6 and abs(samen - sum(apart) / 2) > 1, apart)
        eis('geen JS-fouten', not fouten, fouten)
        if os.environ.get('PASSANTEN_PNG'):
            pg.screenshot(path=os.environ['PASSANTEN_PNG'])
        ctx.close()

        print('\n== G. Op 390 px ==')
        ctx = b.new_context(viewport={'width': 390, 'height': 844}); ctx.route('**/*', route_kaart)
        pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
        pg.goto(BASIS + 'passanten.html', wait_until='load'); pg.wait_for_timeout(300)
        pg.set_input_files('#bestanden', PADEN)
        pg.wait_for_function("GEMETEN.length > 0", timeout=20000); pg.wait_for_timeout(300)
        breed = pg.evaluate("document.documentElement.scrollWidth")
        eis('niets breder dan het scherm (%d px); de kaart en de knoppen zijn zichtbaar' % breed,
            breed <= 390 and pg.is_visible('#kaart') and pg.is_visible('#dagen button[data-dag="5"]'))
        pg.evaluate("openWeek(SEGMENTEN['1001/0'])"); pg.wait_for_timeout(200)
        breed = pg.evaluate("document.documentElement.scrollWidth")
        eis('het weekoverzicht op 390 px: de tabel schuift in zijn kader, de pagina niet (%d px)' % breed,
            breed <= 390 and pg.evaluate("document.querySelector('.week-tabel').scrollWidth > document.querySelector('.week-tabel').clientWidth"))
        if os.environ.get('PASSANTEN_PNG'):
            pg.screenshot(path=os.environ['PASSANTEN_PNG'].replace('.png', '_week_390.png'))
        pg.keyboard.press('Escape')
        if os.environ.get('PASSANTEN_PNG'):
            pg.screenshot(path=os.environ['PASSANTEN_PNG'].replace('.png', '_390.png'))
        eis('geen JS-fouten', not fouten, fouten)
        ctx.close(); b.close()
    shutil.rmtree(tmp, ignore_errors=True)
    srv.shutdown()
    print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
    sys.exit(1 if fout else 0)
