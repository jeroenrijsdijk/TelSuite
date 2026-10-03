#!/usr/bin/env python3
"""v2.73 — Static door de keten.

  A. Static maakt een telling (12 tikken, onderbroken en doorgeteld) en exporteert.
     De ZIP moet de vorm van de suite hebben: _sessie, _telregels, _onderbrekingen,
     _overzicht, allemaal met dezelfde sessie_id (eindigend op _sta), en de
     bestanden moeten onderling kloppen.
  B. Telrapport leest drie vormen: de nieuwe ZIP, de ZIP van v2.18-v2.72 (alleen
     het overzicht) en de losse CSV. Geen melding, één stilstaand-sessie per keer.
  C. Een verzameling met een stilstaand-telling (ook uit een losse CSV) bewaart
     hem en laadt hem terug.
  D. De reconstructor weigert een stilstaand-telling met een duidelijke melding.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/statictest.py
"""
import io, json, os, sys, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
exec(_hsrc[_hsrc.index('LAT, LON = 51.8500'):_hsrc.index('def bevries(pg):')])

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

def csv_rijen(tekst):
    r = tekst.splitlines(); kop = r[0].split(';')
    return [dict(zip(kop, x.split(';'))) for x in r[1:] if x]

TIK = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
       "b[%d %% b.length].click()})()")
UIT = '/tmp/statictest'; os.makedirs(UIT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Static exporteert in de vorm van de suite ==')
    ctx = nieuwe_context(b); pg = ctx.new_page(); f1 = []
    pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(500)
    pg.evaluate('startSession()'); pg.wait_for_timeout(1200)
    for i in range(7): pg.evaluate(TIK % i)
    sid_voor = pg.evaluate('sessieId')
    opslag = pg.evaluate('JSON.stringify(Object.assign({}, localStorage))'); ctx.close()
    ctx = nieuwe_context(b)
    ctx.add_init_script("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');"
                        "var o=%s;for(var k in o)localStorage.setItem(k,o[k]);}" % opslag)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(2500)
    pg.evaluate('doortellenStatic()'); pg.wait_for_timeout(300)
    for i in range(5): pg.evaluate(TIK % (i + 7))
    pg.wait_for_timeout(33000)                    # > 30 s actief, dan komt er een uurfactor
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()')
    nieuw_zip = os.path.join(UIT, 'nieuw.zip'); d.value.save_as(nieuw_zip)
    ctx.close()
    z = zipfile.ZipFile(nieuw_zip); namen = z.namelist()
    eis('sessie_id eindigt op _sta en blijft gelijk na herstel', sid_voor.endswith('_sta') and all(n.startswith(sid_voor) for n in namen), (sid_voor, namen))
    eis('ZIP heet naar de sessie_id', os.path.basename(d.value.suggested_filename) == sid_voor + '.zip', d.value.suggested_filename)
    eis('vier bestanden', sorted(n[len(sid_voor):] for n in namen) == ['_onderbrekingen.csv', '_overzicht.csv', '_sessie.csv', '_telregels.csv'], namen)
    lees = lambda suf: z.read(sid_voor + suf).decode('utf-8')
    ses = csv_rijen(lees('_sessie.csv'))[0]; tel = csv_rijen(lees('_telregels.csv')); ond = csv_rijen(lees('_onderbrekingen.csv'))
    ovz = lees('_overzicht.csv').splitlines()
    eis('_sessie: app_type en modus standstill, 12 waarnemingen',
        ses['app_type'] == 'standstill' and ses['modus'] == 'standstill' and ses['n_waarnemingen'] == '12', ses)
    eis('_telregels: 12 regels, elk met datum en tijd', len(tel) == 12 and all(len(r['tijdstip']) == 19 and r['tijdstip'][10] == 'T' for r in tel), [r['tijdstip'] for r in tel[:3]])
    eis('_telregels: nummering 1..12 en richting a/b', [r['nr'] for r in tel] == [str(i) for i in range(1, 13)] and {r['richting'] for r in tel} <= {'a', 'b'})
    tot = [r for r in ovz if r.startswith('TOTAL;')][0].split(';')
    eis('_overzicht TOTAL = 12 = _telregels', tot[3] == '12', tot)
    per_type = {}
    for r in tel: per_type[(r['type'], r['richting'])] = per_type.get((r['type'], r['richting']), 0) + 1
    labels = {'car': 'Car', 'truck': 'Truck', 'moto': 'Motorcycle', 'bike': 'Bicycle', 'ped': 'Pedestrian'}
    klopt = True
    for code, lab in labels.items():
        rij = [r for r in ovz if r.startswith(lab + ';')][0].split(';')
        klopt &= int(rij[1]) == per_type.get((code, 'a'), 0) and int(rij[2]) == per_type.get((code, 'b'), 0)
    eis('_overzicht per type en richting = _telregels', klopt)
    eis('_onderbrekingen: één onderbreking van enkele seconden', len(ond) == 1 and 1 <= int(ond[0]['duur_s']) <= 6, ond)
    duur = [r for r in ovz if r.startswith('Observed duration;')][0].split(';')[1]
    h, m, s_ = map(int, duur.split(':'))
    eis('actieve_duur_s = Observed duration uit het overzicht (%s s)' % ses['actieve_duur_s'], abs(int(ses['actieve_duur_s']) - (h * 3600 + m * 60 + s_)) <= 1)
    fac = [r for r in ovz if r.startswith('Extrapolation factor;')]
    eis('uurfactor = Extrapolation factor', fac and abs(float(fac[0].split(';')[1]) - float(ses['uurfactor'])) < 0.001, (fac, ses['uurfactor']))
    eis('Static: geen JS-fouten', not f1, f1)

    # oude vormen, gemaakt uit hetzelfde overzicht
    oud_zip = os.path.join(UIT, 'traffic_count_2026-09-23-14-32-05.zip')
    with zipfile.ZipFile(oud_zip, 'w') as o: o.writestr('traffic_count_2026-09-23-14-32-05.csv', lees('_overzicht.csv'))
    los_csv = os.path.join(UIT, 'traffic_count_2026-09-23-14-32-05.csv')
    open(los_csv, 'w', encoding='utf-8').write(lees('_overzicht.csv'))

    print('\n== B. telrapport leest alle drie de vormen ==')
    def telrapport(bestanden):
        ctx = nieuwe_context(b, geo=False); pg = ctx.new_page(); meldingen = []; fouten = []
        pg.on('dialog', lambda d: (meldingen.append(d.message), d.accept()))
        pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
        pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(500)
        pg.set_input_files('#file-input', bestanden); pg.wait_for_timeout(1500)
        return ctx, pg, meldingen, fouten
    for naam, pad, sid_verwacht in [('nieuwe ZIP (v2.73)', nieuw_zip, sid_voor),
                                    ('ZIP van v2.18-v2.72', oud_zip, None),
                                    ('losse CSV', los_csv, None)]:
        ctx, pg, meldingen, fouten = telrapport([pad])
        st = pg.evaluate("Object.keys(sessions).map(k=>[k, sessions[k].appType, standStillData[k] ? standStillData[k].totalCount : null])")
        eis('%s: één stilstaand-sessie met 12, geen melding' % naam,
            len(st) == 1 and st[0][1] == 'standstill' and st[0][2] == 12 and not meldingen and not fouten, (st, meldingen, fouten))
        if sid_verwacht:
            eis('%s: sessie_id uit _sessie.csv' % naam, st and st[0][0] == sid_verwacht, st)
        eis('%s: origineel bewaard (voor verzamelingen)' % naam, pg.evaluate("Object.keys(originalFile).length") == 1)
        ctx.close()

    print('\n== C. verzameling met stilstaand-tellingen ==')
    ctx, pg, meldingen, fouten = telrapport([nieuw_zip, los_csv])
    eis('twee stilstaand-sessies geladen', pg.evaluate("Object.keys(sessions).length") == 2)
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('exportVerzameling()')
    verz = os.path.join(UIT, 'verzameling.zip'); d.value.save_as(verz)
    man = json.loads(zipfile.ZipFile(verz).read('verzameling.json'))
    eis('beide in de verzameling (ook die uit de losse CSV)', len(man['tellingen']) == 2 and not meldingen, (man['tellingen'], meldingen))
    ctx.close()
    ctx, pg, meldingen, fouten = telrapport([verz])
    pg.wait_for_timeout(1000)
    st = pg.evaluate("Object.keys(sessions).map(k=>[k, sessions[k].appType, standStillData[k] ? standStillData[k].totalCount : null])")
    eis('verzameling laadt beide terug', len(st) == 2 and all(x[1] == 'standstill' and x[2] == 12 for x in st) and not meldingen and not fouten, (st, meldingen, fouten))
    ctx.close()

    print('\n== D. reconstructor weigert een stilstaand-telling ==')
    ctx = nieuwe_context(b, geo=False); pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telreconstructie.html', wait_until='load'); pg.wait_for_timeout(500)
    pg.set_input_files('#file', [nieuw_zip]); pg.wait_for_timeout(1500)
    tekst = pg.evaluate('document.body.innerText')
    eis('duidelijke melding "niets te reconstrueren"', 'stilstaand-telling' in tekst and 'niets te reconstrueren' in tekst, tekst[:300])
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
