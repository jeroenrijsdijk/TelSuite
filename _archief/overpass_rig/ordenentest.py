#!/usr/bin/env python3
"""v3.31 ordenentest — Ordenen (telarchief.html) in Chromium, op echte bestanden.

De archiefmap is een map in de Origin Private File System van Chromium: dezelfde
FileSystemDirectoryHandle als een map op de schijf, maar zonder venster om te
kiezen. showDirectoryPicker wordt daarvoor nagebootst.

  A. Plan: elke ZIP krijgt de goede bestemming (soort, originelen bij een
     reconstructie, dubbel, al goed, overslaan, naamconflict).
  B. Uitvoeren: de bestanden staan daarna precies waar het plan zei, met
     dezelfde inhoud (vingerafdruk); een uitgevinkte rij blijft liggen; niets
     is weg; het logboek heeft een regel per verplaatsing.
  C. Opnieuw lezen: alles staat goed, behalve wat uitgevinkt was.
  D. Zonder move(): kopiëren, nalezen, origineel weg. Zelfde uitkomst.
  E. Zonder showDirectoryPicker (Firefox, Safari): alleen bekijken via een
     mapkeuze; het plan klopt, Uitvoeren staat uit.
  v3.32:
  F. Voortgang: bij het lezen eerst "Mappen doorzoeken" (balk zonder einde),
     dan "Lezen: k van n", bij Uitvoeren "Verplaatsen: k van n", telkens met
     het bestand; ondertussen staan de knoppen en vinkjes uit; daarna weg.
  G. Het logboek heet ordenen_logboek_<jjjjmmdd>_<uummss>.csv, met de tijd van
     de ronde; een tweede ronde geeft een tweede logboek, het eerste blijft
     zoals het was; een bezette naam krijgt _2. Een oud ordenen_logboek.csv
     (v3.31) blijft onaangeroerd.

Hulp (server, CDN-omleiding) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/ordenentest.py
"""
import base64, hashlib, io, os, re, shutil, sys, tempfile, zipfile
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

KOP = 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b'
def zipje(sid, app_type, modus='', recon='', extra=b''):
    b = io.BytesIO(); z = zipfile.ZipFile(b, 'w')
    kop = KOP + (';reconstructie' if recon else '')
    z.writestr(sid + '_sessie.csv', kop + '\n' + ';'.join([sid, '2026-10-20', '10:00:00', '10:20:00', app_type, '', '3', modus, '', ''] + ([recon] if recon else [])) + '\n')
    z.writestr(sid + '_telregels.csv', 'sessie_id;nr\n' + sid + ';1\n' + extra.decode())
    z.close(); return b.getvalue()

def losse_zip(naam, inhoud):
    b = io.BytesIO(); z = zipfile.ZipFile(b, 'w'); z.writestr(naam, inhoud); z.close(); return b.getvalue()

car = zipje('20261020_100000_abc', 'auto')
BESTANDEN = {
    '20261020_100000_abc_car.zip': car,
    '20261020_100000_abc_car (1).zip': car,                                            # dubbel
    '20261020_100000_abc_recon.zip': zipje('20261020_100000_abc', 'auto', 'parkeren', 'v3.30'),
    '20261020_110000_def_fts.zip': zipje('20261020_110000_def', 'fiets'),            # wordt uitgevinkt
    'veld/20261020_120000_ghi_pkt_w.zip': zipje('20261020_120000_ghi_pkt_w', 'pocket', 'winkelstraat'),
    'Pocket simpel/20261020_130000_jkl_pkt_s.zip': zipje('20261020_130000_jkl_pkt_s', 'pocket', 'simpel'),  # staat goed
    'TelVerzameling_20261020.zip': losse_zip('verzameling.json', '{"versie":1}'),
    'foto.zip': losse_zip('foto.txt', 'geen telling'),
    'notitie.txt': b'geen zip',
    'Autoparkeren/20261020_140000_mno_car.zip': zipje('20261020_140000_mno', 'auto', extra=b'x;1\n'),
    '20261020_140000_mno_car.zip': zipje('20261020_140000_mno', 'auto', extra=b'y;2\n'),  # zelfde naam, andere inhoud
    '20261020_150000_pqr_sta.zip': zipje('20261020_150000_pqr_sta', 'standstill', 'standstill'),
    'ordenen_logboek.csv': b'tijdstip;van;naar;reden;sha256\n2026-10-23 22:00:00;a_car.zip;Autoparkeren/a_car.zip;Autoparkeren;x\n',  # van v3.31
}

VERWACHT = {
    'Autoparkeren/originelen/20261020_100000_abc_car.zip': BESTANDEN['20261020_100000_abc_car.zip'],
    'dubbel/20261020_100000_abc_car (1).zip': car,
    'Autoparkeren/20261020_100000_abc_recon.zip': BESTANDEN['20261020_100000_abc_recon.zip'],
    '20261020_110000_def_fts.zip': BESTANDEN['20261020_110000_def_fts.zip'],          # uitgevinkt: blijft
    'Winkelstraat/20261020_120000_ghi_pkt_w.zip': BESTANDEN['veld/20261020_120000_ghi_pkt_w.zip'],
    'Pocket simpel/20261020_130000_jkl_pkt_s.zip': BESTANDEN['Pocket simpel/20261020_130000_jkl_pkt_s.zip'],
    'Verzamelingen/TelVerzameling_20261020.zip': BESTANDEN['TelVerzameling_20261020.zip'],
    'foto.zip': BESTANDEN['foto.zip'],
    'notitie.txt': BESTANDEN['notitie.txt'],
    'Autoparkeren/20261020_140000_mno_car.zip': BESTANDEN['Autoparkeren/20261020_140000_mno_car.zip'],
    '20261020_140000_mno_car.zip': BESTANDEN['20261020_140000_mno_car.zip'],            # naamconflict: blijft
    'Stilstaand/20261020_150000_pqr_sta.zip': BESTANDEN['20261020_150000_pqr_sta.zip'],
    'ordenen_logboek.csv': BESTANDEN['ordenen_logboek.csv'],                             # blijft onaangeroerd
}
LOGNAAM = re.compile(r'^ordenen_logboek_(\d{8})_(\d{6})(_\d+)?\.csv$')

KIEZER = """
window.showDirectoryPicker = async function () {
  const root = await navigator.storage.getDirectory();
  return root.getDirectoryHandle('archief', { create: true });
};"""
VUL = """async (bestanden) => {
  const root = await navigator.storage.getDirectory();
  try { await root.removeEntry('archief', { recursive: true }); } catch (e) {}
  const arch = await root.getDirectoryHandle('archief', { create: true });
  for (const [pad, b64] of Object.entries(bestanden)) {
    const delen = pad.split('/'); let d = arch;
    for (const m of delen.slice(0, -1)) d = await d.getDirectoryHandle(m, { create: true });
    const h = await d.getFileHandle(delen[delen.length - 1], { create: true });
    const w = await h.createWritable(); await w.write(Uint8Array.from(atob(b64), c => c.charCodeAt(0))); await w.close();
  }
}"""
BOOM = """async () => {
  const root = await navigator.storage.getDirectory(), arch = await root.getDirectoryHandle('archief');
  const uit = {};
  async function loop(d, pad) {
    for await (const [n, h] of d.entries()) {
      const p = pad ? pad + '/' + n : n;
      if (h.kind === 'directory') await loop(h, p);
      else { const buf = new Uint8Array(await (await h.getFile()).arrayBuffer()); let s = '';
             for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
             uit[p] = btoa(s); }
    }
  }
  await loop(arch, ''); return uit;
}"""
PLAN = """() => Object.fromEntries(acties.map(a => [a.van, [a.status, a.naar]]))"""
# Elke aanroep van voortgang() vastleggen, met wat er daarna op het scherm staat.
VOLG = """() => {
  window.__vg = [];
  const echt = window.voortgang;
  window.voortgang = function () {
    echt.apply(this, arguments);
    const blok = document.getElementById('voortgang'), balk = document.getElementById('voortgang-balk');
    window.__vg.push({ zicht: !blok.classList.contains('hide'), tekst: document.getElementById('voortgang-tekst').textContent,
      waarde: balk.hasAttribute('value') ? balk.value : null, max: balk.max,
      knoppen: ['kies', 'opnieuw', 'uitvoeren'].map(id => document.getElementById(id).disabled),
      vinkjes: [...document.querySelectorAll('#plan input')].filter(i => !i.disabled).length });
  };
}"""
RUST = """() => ({ zicht: !document.getElementById('voortgang').classList.contains('hide'),
  knoppen: ['kies', 'opnieuw'].map(id => document.getElementById(id).disabled) })"""

def logs(boom):
    return sorted(k for k in boom if LOGNAAM.match(k))

def kijk_lezen(pg, n, label):
    vg = pg.evaluate('window.__vg'); zoek = [v for v in vg if v['tekst'].startswith('Mappen doorzoeken')]
    lees = [v for v in vg if v['tekst'].startswith('Lezen') and v['zicht']]
    eis('%s: eerst "Mappen doorzoeken", balk zonder einde, tot %d ZIP\'s gevonden' % (label, n),
        zoek and all(v['waarde'] is None and v['zicht'] for v in zoek) and zoek[-1]['tekst'].startswith("Mappen doorzoeken: %d ZIP's gevonden" % n)
        and vg.index(zoek[-1]) < vg.index(lees[0]), [v['tekst'] for v in zoek][-3:])
    eis('%s: dan "Lezen: k van %d" voor k = 1..%d, met het bestand en de balk op k-1 van %d' % (label, n, n, n),
        [v['tekst'].split(' \u00b7 ')[0] for v in lees] == ['Lezen: %d van %d' % (k, n) for k in range(1, n + 1)]
        and all(v['waarde'] == k and v['max'] == n and ' \u00b7 ' in v['tekst'] for k, v in enumerate(lees)), [v['tekst'] for v in lees][:3])
    eis('%s: tijdens het lezen staan Kies, Opnieuw en Uitvoeren uit' % label, all(all(v['knoppen']) for v in vg if v['zicht']))
    rust = pg.evaluate(RUST)
    eis('%s: na het lezen is de balk weg en kun je weer kiezen' % label, rust == {'zicht': False, 'knoppen': [False, False]}, rust)

def b64(d): return {k: base64.b64encode(v).decode() for k, v in d.items()}
def sha(v): return hashlib.sha256(v).hexdigest()

def ronde(b, zonder_move, label):
    ctx = b.new_context(viewport={'width': 1300, 'height': 900}); ctx.route('**/*', route_met_osm)
    ctx.add_init_script(KIEZER + ("\ndelete FileSystemFileHandle.prototype.move;" if zonder_move else
        "\nwindow.__moves = 0; (function (m) { FileSystemFileHandle.prototype.move = function () { window.__moves++; return m.apply(this, arguments); }; })(FileSystemFileHandle.prototype.move);"))
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.goto(BASIS + 'telarchief.html', wait_until='load'); pg.wait_for_timeout(300)
    pg.evaluate(VUL, b64(BESTANDEN))
    eis('%s: move() %s' % (label, 'weggehaald' if zonder_move else 'aanwezig'),
        pg.evaluate("typeof FileSystemFileHandle.prototype.move") == ('undefined' if zonder_move else 'function'))
    pg.evaluate(VOLG)
    pg.click('#kies')
    pg.wait_for_function("!document.getElementById('plan-sect').classList.contains('hide') && acties.length > 0 && !BEZIG", timeout=20000)
    pg.click('#tab-ordenen')                   # v3.33: Ordenen is een tabblad naast Overzicht
    plan = pg.evaluate(PLAN)
    if not zonder_move:
        print('\n== F. Voortgang bij lezen ==')
        kijk_lezen(pg, 11, 'lezen')
    if not zonder_move:
        print('\n== A. Het plan ==')
        verwacht_plan = {
            '20261020_100000_abc_car.zip': ['verplaatsen', 'Autoparkeren/originelen/20261020_100000_abc_car.zip'],
            '20261020_100000_abc_car (1).zip': ['verplaatsen', 'dubbel/20261020_100000_abc_car (1).zip'],
            '20261020_100000_abc_recon.zip': ['verplaatsen', 'Autoparkeren/20261020_100000_abc_recon.zip'],
            '20261020_110000_def_fts.zip': ['verplaatsen', 'Fietsparkeren/20261020_110000_def_fts.zip'],
            'veld/20261020_120000_ghi_pkt_w.zip': ['verplaatsen', 'Winkelstraat/20261020_120000_ghi_pkt_w.zip'],
            'Pocket simpel/20261020_130000_jkl_pkt_s.zip': ['goed', 'Pocket simpel/20261020_130000_jkl_pkt_s.zip'],
            'TelVerzameling_20261020.zip': ['verplaatsen', 'Verzamelingen/TelVerzameling_20261020.zip'],
            'foto.zip': ['overslaan', None],
            'Autoparkeren/20261020_140000_mno_car.zip': ['goed', 'Autoparkeren/20261020_140000_mno_car.zip'],
            '20261020_140000_mno_car.zip': ['conflict', 'Autoparkeren/20261020_140000_mno_car.zip'],
            '20261020_150000_pqr_sta.zip': ['verplaatsen', 'Stilstaand/20261020_150000_pqr_sta.zip'],
        }
        for pad, (st, naar) in sorted(verwacht_plan.items()):
            eis('%s -> %s%s' % (pad, st, (' ' + naar) if st == 'verplaatsen' else ''), plan.get(pad) == [st, naar], plan.get(pad))
        eis('alleen ZIP-bestanden gelezen (notitie.txt niet)', 'notitie.txt' not in plan)
        kpi = pg.evaluate("[...document.querySelectorAll('#kpi b')].map(b => +b.textContent)")
        eis('tellers: 7 verplaatsen, 1 dubbel, 2 goed, 1 blijft liggen, 1 conflict', kpi == [7, 1, 2, 1, 1], kpi)
        eis('wat al goed staat, staat niet in de tabel (tot je het aanvinkt)',
            not pg.evaluate("[...document.querySelectorAll('#plan tr.goed')].length"))
        pg.check('#toon-goed')
        eis('aangevinkt: ook de twee die goed staan', pg.evaluate("document.querySelectorAll('#plan tr.goed').length") == 2)
        eis('knop: Uitvoeren (7)', pg.evaluate("document.getElementById('uitvoeren').textContent") == 'Uitvoeren (7)')
    # de fietstelling uitvinken
    pg.uncheck('#plan tr[data-pad="20261020_110000_def_fts.zip"] input')
    eis('%s: na uitvinken: Uitvoeren (6)' % label, pg.evaluate("document.getElementById('uitvoeren').textContent") == 'Uitvoeren (6)')
    pg.evaluate('window.__vg = []')
    todo = pg.evaluate("acties.filter(a => a.status === 'verplaatsen' && a.aan).map(a => a.van)")
    pg.click('#uitvoeren')
    pg.wait_for_function("document.getElementById('plan-melding').textContent.indexOf('verplaatst') >= 0 && !BEZIG", timeout=30000)
    if not zonder_move:
        print('\n== F. Voortgang bij Uitvoeren ==')
        vg = pg.evaluate('window.__vg'); vp = [v for v in vg if v['tekst'].startswith('Verplaatsen') and v['zicht']]
        eis('"Verplaatsen: k van 6" voor k = 1..6, telkens met het bestand dat gaat',
            [v['tekst'] for v in vp] == ['Verplaatsen: %d van 6 \u00b7 %s' % (k + 1, todo[k]) for k in range(6)]
            and all(v['waarde'] == k and v['max'] == 6 for k, v in enumerate(vp)), [v['tekst'] for v in vp][:2])
        eis('daarna "Logboek schrijven" en (v3.33) "Catalogus bijwerken", de balk vol, en dan weg (zonder tekst)',
            [v['tekst'] for v in vg[-3:-1]] == ['Logboek schrijven', 'Catalogus bijwerken'] and all(v['waarde'] == 6 and v['max'] == 6 for v in vg[-3:-1])
            and not vg[-1]['zicht'] and vg[-1]['tekst'] == '', vg[-3:])
        eis('tijdens Uitvoeren staan de knoppen en alle vinkjes uit',
            all(all(v['knoppen']) and v['vinkjes'] == 0 for v in vg if v['zicht']), [v for v in vg if v['zicht'] and (not all(v['knoppen']) or v['vinkjes'])][:1])
        rust = pg.evaluate(RUST)
        eis('daarna is de balk weg; Opnieuw lezen kan weer', rust == {'zicht': False, 'knoppen': [False, False]}, rust)
        print('\n== B. Uitvoeren ==')
    boom = {k: base64.b64decode(v) for k, v in pg.evaluate(BOOM).items()}
    boom.pop('catalogus.csv', None)            # v3.33: afgeleid; archieftest.py kijkt ernaar
    lognamen = logs(boom)
    log1 = boom.pop(lognamen[0], b'') if len(lognamen) == 1 else b''
    log = log1.decode('utf-8')
    eis('%s: precies de verwachte bestanden op de verwachte plek' % label, sorted(boom) == sorted(VERWACHT),
        {'teveel': sorted(set(boom) - set(VERWACHT)), 'mist': sorted(set(VERWACHT) - set(boom))})
    eis('%s: elke inhoud ongewijzigd (vingerafdruk)' % label,
        all(sha(boom.get(p, b'')) == sha(v) for p, v in VERWACHT.items()),
        [p for p, v in VERWACHT.items() if sha(boom.get(p, b'')) != sha(v)])
    eis('%s: niets weg: evenveel bestanden als ervoor' % label, len(boom) == len(BESTANDEN))
    regels = log.strip().splitlines()
    eis('%s: logboek met kop en 6 regels (van;naar;reden;sha256)' % label,
        regels and regels[0] == 'tijdstip;van;naar;reden;sha256' and len(regels) == 7
        and any(';veld/20261020_120000_ghi_pkt_w.zip;Winkelstraat/20261020_120000_ghi_pkt_w.zip;' in r for r in regels)
        and all(r.split(';')[4] == sha(VERWACHT[r.split(';')[2]]) for r in regels[1:]), regels[:3])
    m = LOGNAAM.match(lognamen[0]) if len(lognamen) == 1 else None
    tijd = regels[1].split(';')[0] if len(regels) > 1 else ''
    eis('%s: een logboek, met in de naam de tijd van de ronde (%s)' % (label, lognamen),
        m and not m.group(3) and m.group(1) + '_' + m.group(2) == re.sub(r'[-:]', '', tijd).replace(' ', '_')
        and all(r.split(';')[0] == tijd for r in regels[1:]), [lognamen, tijd])
    eis('%s: de melding noemt het logboek' % label, bool(lognamen) and lognamen[0] in pg.evaluate("document.getElementById('plan-melding').textContent"))
    if not zonder_move:
        eis('met move(): elke verplaatsing een hernoeming (6 keer move, geen kopie)', pg.evaluate('window.__moves') == 6, pg.evaluate('window.__moves'))
    eis('%s: in de tabel staat bij elke verplaatsing een vinkje' % label,
        pg.evaluate("document.querySelectorAll('#plan td.uitkomst.ok').length") == 6)
    if not zonder_move: print('\n== C. Opnieuw lezen ==')
    pg.click('#opnieuw')
    pg.wait_for_function("acties.every(a => a.van !== 'veld/20261020_120000_ghi_pkt_w.zip') && acties.length > 0", timeout=20000)
    plan2 = pg.evaluate(PLAN)
    te_doen = sorted(p for p, (st, _) in plan2.items() if st == 'verplaatsen')
    eis('%s: daarna staat alles goed, op de uitgevinkte fietstelling na' % label, te_doen == ['20261020_110000_def_fts.zip'], te_doen)
    eis('%s: de logboeken tellen niet als ZIP' % label, not [k for k in plan2 if k.endswith('.csv')])
    if not zonder_move:
        print('\n== G. Een tweede ronde: een tweede logboek ==')
        # Een bezette naam, zonder op de klok te wachten (v3.33: onder belasting
        # was "de komende 15 seconden bezetten" niet genoeg). De naam van deze
        # ronde ligt vast op 24-10-2026 08:10:12; dat bestand staat er al.
        # Dan moet de ronde _2 nemen, en niets overschrijven.
        bezet = pg.evaluate("""async () => {
          const echt = ORDENEN.logboekNaam, vast = new Date(2026, 9, 24, 8, 10, 12);
          ORDENEN.logboekNaam = (d, k) => echt(vast, k);
          const arch = await (await navigator.storage.getDirectory()).getDirectoryHandle('archief'), n = echt(vast);
          const w = await (await arch.getFileHandle(n, { create: true })).createWritable(); await w.write('bezet\\n'); await w.close();
          return [n]; }""")
        pg.check('#plan tr[data-pad="20261020_110000_def_fts.zip"] input')
        pg.click('#uitvoeren')
        pg.wait_for_function("document.getElementById('plan-melding').textContent.indexOf('verplaatst') >= 0 && !BEZIG", timeout=30000)
        boom2 = {k: base64.b64decode(v) for k, v in pg.evaluate(BOOM).items()}
        nieuw = [k for k in logs(boom2) if k not in lognamen and k not in bezet]
        r2 = boom2[nieuw[0]].decode('utf-8').strip().splitlines() if len(nieuw) == 1 else []
        eis('de fietstelling staat nu in Fietsparkeren', 'Fietsparkeren/20261020_110000_def_fts.zip' in boom2 and '20261020_110000_def_fts.zip' not in boom2)
        eis('een tweede logboek, met _2 (de naam was bezet), met kop en 1 regel', nieuw == ['ordenen_logboek_20261024_081012_2.csv']
            and r2[0] == 'tijdstip;van;naar;reden;sha256' and len(r2) == 2 and ';Fietsparkeren/20261020_110000_def_fts.zip;' in r2[1], [nieuw, r2])
        eis('het eerste logboek is onveranderd, de bezette namen ook',
            boom2.get(lognamen[0]) == log1 and all(boom2.get(n) == b'bezet\n' for n in bezet) and bezet, [len(bezet)])
        eis('het oude ordenen_logboek.csv (v3.31) is onaangeroerd', boom2.get('ordenen_logboek.csv') == BESTANDEN['ordenen_logboek.csv'])
    eis('%s: geen JS-fouten' % label, not fouten, fouten)
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch()
    ronde(b, False, 'met move()')
    print('\n== D. Zonder move(): kopiëren, nalezen, origineel weg ==')
    ronde(b, True, 'zonder move()')

    print('\n== E. Zonder showDirectoryPicker: alleen bekijken ==')
    tmp = tempfile.mkdtemp(prefix='ordenen_')
    arch = os.path.join(tmp, 'archief')
    for pad, data in BESTANDEN.items():
        os.makedirs(os.path.dirname(os.path.join(arch, pad)), exist_ok=True)
        open(os.path.join(arch, pad), 'wb').write(data)
    ctx = b.new_context(viewport={'width': 1300, 'height': 900}); ctx.route('**/*', route_met_osm)
    ctx.add_init_script("delete window.showDirectoryPicker;")
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.goto(BASIS + 'telarchief.html', wait_until='load'); pg.wait_for_timeout(300)
    eis('geen knop Kies, wel de mapkeuze om te bekijken, en uitleg waarom',
        pg.evaluate("document.getElementById('kies').classList.contains('hide') && !document.getElementById('alleen-lezen').classList.contains('hide')")
        and 'Chrome of Edge' in pg.evaluate("document.getElementById('melding').textContent"))
    pg.evaluate(VOLG)
    pg.set_input_files('#map-invoer', arch)
    pg.wait_for_function("acties.length > 0 && !BEZIG", timeout=20000)
    vg = pg.evaluate('window.__vg'); lees = [v['tekst'].split(' \u00b7 ')[0] for v in vg if v['tekst'].startswith('Lezen') and v['zicht']]
    eis('ook hier "Lezen: k van 11", en daarna geen balk', lees == ['Lezen: %d van 11' % k for k in range(1, 12)]
        and not pg.evaluate(RUST)['zicht'], lees)
    plan3 = pg.evaluate(PLAN)
    eis('het plan is hetzelfde als in Chrome (paden zonder de gekozen map)',
        plan3.get('veld/20261020_120000_ghi_pkt_w.zip') == ['verplaatsen', 'Winkelstraat/20261020_120000_ghi_pkt_w.zip']
        and plan3.get('20261020_100000_abc_car.zip') == ['verplaatsen', 'Autoparkeren/originelen/20261020_100000_abc_car.zip']
        and len(plan3) == 11, plan3)
    eis('Uitvoeren staat uit, de vinkjes ook',
        pg.evaluate("document.getElementById('uitvoeren').disabled && [...document.querySelectorAll('#plan input')].every(i => i.disabled)"))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    shutil.rmtree(tmp, ignore_errors=True)
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
