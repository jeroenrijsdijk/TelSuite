#!/usr/bin/env python3
"""v3.33 archieftest — het Overzicht van Archief (telarchief.html) in Chromium.

Jay: "De catalogus is puur bedoeld als 'wanneer en waar' zijn er tellingen
gedaan. Ik wil kunnen checken op dubbele bestanden. Ik wil kunnen zien of er
bestanden zijn zonder _recon versie." En: "geintegreerd in de html van ordenen -
een kaartje, een overzicht. Met als basis een csv".

Het archief is een map in de Origin Private File System, zoals in ordenentest.py.
De ZIP's hebben een GPS-spoor dat thuis begint en dan in het telgebied loopt.

  A. catalogus.csv: geschreven in de moedermap, met de afgesproken kop, een
     regel per telling of verzameling, en de goede waarden (recon, dubbel_van,
     plek als mediaan van het spoor, de telplek van Static, bytes, sha256).
  B. Tellers en tabel: aantallen, dubbel, zelfde telling, zonder reconstructie,
     zonder plek; de tabel met de nieuwste bovenaan.
  C. Kaart: elke telling met een plek staat erop (stip of bol); op één plek
     samen een bol, en bij inzoomen tot het eind een lijstje om te kiezen.
  D. Filters: een teller aanklikken, een soort uit, een periode.
  E. Route: een rij aanklikken tekent het spoor uit de ZIP.
  F. Na Uitvoeren (Ordenen): catalogus.csv met de nieuwe paden, en de route
     werkt nog voor een verplaatst bestand.
  G. Alleen bekijken (zonder showDirectoryPicker): niets geschreven, de CSV als
     download, met dezelfde inhoud (op de wijzigdatum na).
  H. Op 390 px: niets breder dan het scherm.

Hulp (server, CDN-omleiding) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/archieftest.py
"""
import base64, hashlib, io, os, re, shutil, sys, tempfile, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))

# Leaflet met zijn stylesheet, zodat de kaart echt staat (ook voor het bekijken).
def route_archief(r):
    if r.request.url.split('?')[0].endswith('/leaflet.css'):
        return r.fulfill(body=open(os.path.join(NM, 'leaflet/dist/leaflet.css'), 'rb').read(), content_type='text/css')
    return route(r)

KOP = 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b'
THUIS = (51.8700, 4.3300)
def spoor(lat, lon, n=21):
    """Drie punten thuis, dan n punten heen en weer door een straat rond (lat, lon)."""
    pts = [THUIS] * 3 + [(lat + (i - n // 2) * 0.0001, lon) for i in range(n)]
    return pts
def zipje(sid, app_type, datum, tijd, modus='', recon='', gps=None, extra=b'', plek=None):
    b = io.BytesIO(); z = zipfile.ZipFile(b, 'w')
    kop = KOP + (';reconstructie' if recon else '') + (';lat;lon' if plek else '')
    w = [sid, datum, tijd, tijd[:3] + '30:00', app_type, '', '7', modus, '', ''] + ([recon] if recon else []) + (['%.6f' % plek[0], '%.6f' % plek[1]] if plek else [])
    z.writestr(sid + '_sessie.csv', kop + '\n' + ';'.join(w) + '\n')
    z.writestr(sid + '_telregels.csv', 'sessie_id;nr\n' + sid + ';1\n' + extra.decode())
    if gps:
        z.writestr(sid + '_gps.csv', 'sessie_id;tijdstip;lat;lon;nauwkeurigheid\n' +
                   ''.join('%s;%sT10:%02d:00;%.6f;%.6f;5\n' % (sid, datum, i % 60, a, o) for i, (a, o) in enumerate(gps)))
    z.close(); return b.getvalue()
def losse_zip(naam, inhoud):
    b = io.BytesIO(); z = zipfile.ZipFile(b, 'w'); z.writestr(naam, inhoud); z.close(); return b.getvalue()

LAT, LON = 51.8500, 4.3000
abc = zipje('20261001_100000_abc', 'auto', '2026-10-01', '10:00:00', gps=spoor(LAT, LON))
BESTANDEN = {
    '20261001_100000_abc_car.zip': abc,
    '20261001_100000_abc_car (1).zip': abc,                                           # dubbel
    'Autoparkeren/20261001_100000_abc_recon.zip': zipje('20261001_100000_abc', 'auto', '2026-10-01', '10:00:00', 'parkeren', 'v3.30', spoor(LAT, LON)),
    '20261002_090000_def_fts.zip': zipje('20261002_090000_def', 'fiets', '2026-10-02', '09:00:00', gps=spoor(51.8450, 4.3100)),
    'veld/20261003_110000_ghi_pkt_w.zip': zipje('20261003_110000_ghi_pkt_w', 'pocket', '2026-10-03', '11:00:00', 'winkelstraat', gps=spoor(51.8520, 4.3050)),
    'Winkelstraat/20260915_110000_rep_pkt_w.zip': zipje('20260915_110000_rep_pkt_w', 'pocket', '2026-09-15', '11:00:00', 'winkelstraat', gps=spoor(51.8520, 4.3050)),
    '20261004_120000_jkl_sta.zip': zipje('20261004_120000_jkl_sta', 'standstill', '2026-10-04', '12:00:00', 'standstill', plek=(51.8514, 4.3312)),
    '20261005_130000_mno_cap.zip': zipje('20261005_130000_mno', 'capaciteit', '2026-10-05', '13:00:00', gps=spoor(51.8400, 4.2900)),
    'a/20261006_140000_xyz_fts.zip': zipje('20261006_140000_xyz', 'fiets', '2026-10-06', '14:00:00', gps=spoor(51.8480, 4.2950), extra=b'x;1\n'),
    'b/20261006_140000_xyz_fts.zip': zipje('20261006_140000_xyz', 'fiets', '2026-10-06', '14:00:00', gps=spoor(51.8480, 4.2950), extra=b'y;2\n'),
    '20261007_150000_zzz_car.zip': zipje('20261007_150000_zzz', 'auto', '2026-10-07', '15:00:00'),       # zonder plek
    'TelVerzameling_20261020.zip': losse_zip('verzameling.json', '{"versie":1}'),
    'foto.zip': losse_zip('foto.txt', 'geen telling'),
}
NTELLING, NREGELS = 11, 12      # foto.zip is geen telling; de verzameling krijgt wel een regel

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
LEES = """async (naam) => {
  const arch = await (await navigator.storage.getDirectory()).getDirectoryHandle('archief');
  try { return await (await (await arch.getFileHandle(naam)).getFile()).text(); } catch (e) { return null; }
}"""
TABEL = """() => [...document.querySelectorAll('#catalogus-tabel tr[data-i]')].map(tr => rijen[+tr.getAttribute('data-i')].pad)"""
# Wat er op de kaart staat: per laag het aantal tellingen (een stip 1, een bol het getal erin).
KAARTSTAND = """() => { const uit = []; puntLaag.eachLayer(l => {
  if (l instanceof L.CircleMarker) uit.push(1);
  else uit.push(+l.getElement().textContent.trim()); }); return uit; }"""

def b64(d): return {k: base64.b64encode(v).decode() for k, v in d.items()}
def sha(v): return hashlib.sha256(v).hexdigest()
def csv_regels(t): return [r.split(';') for r in t.strip().split('\n')]
def per_pad(regels): return {r[11]: dict(zip(regels[0], r)) for r in regels[1:]}

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1300, 'height': 900}, accept_downloads=True); ctx.route('**/*', route_archief)
    ctx.add_init_script(KIEZER + "\nwindow.__moves = 0;")
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.goto(BASIS + 'telarchief.html', wait_until='load'); pg.wait_for_timeout(300)
    pg.evaluate(VUL, b64(BESTANDEN))
    pg.click('#kies')
    pg.wait_for_function("rijen.length > 0 && !BEZIG", timeout=30000)

    print('== A. catalogus.csv in de moedermap ==')
    tekst = pg.evaluate(LEES, 'catalogus.csv') or ''
    regels = csv_regels(tekst); pp = per_pad(regels) if regels else {}
    eis('geschreven, met de afgesproken kop',
        regels and ';'.join(regels[0]) == 'sessie_id;soort;datum;weekdag;start_tijd;eind_tijd;n_waarnemingen;recon;dubbel_van;lat;lon;pad;bytes;gewijzigd;sha256', regels[:1])
    eis('een regel per telling of verzameling (%d), niet voor foto.zip' % NREGELS, len(regels) == NREGELS + 1 and 'foto.zip' not in pp, sorted(pp))
    eis('elke regel 15 velden; eindigt op een nieuwe regel', all(len(r) == 15 for r in regels) and tekst.endswith('\n'))
    a = pp.get('20261001_100000_abc_car.zip', {})
    eis('auto-origineel met reconstructie: recon ja, Autoparkeren, do 2026-10-01, 10:00:00',
        [a.get(k) for k in ('sessie_id', 'soort', 'datum', 'weekdag', 'start_tijd', 'recon')] == ['20261001_100000_abc', 'Autoparkeren', '2026-10-01', 'do', '10:00:00', 'ja'], a)
    eis('plek: het midden van het spoor, niet thuis (binnen 20 m van de straat)',
        a and abs(float(a['lat']) - LAT) < 0.0002 and abs(float(a['lon']) - LON) < 0.0002 and re.fullmatch(r'\d+\.\d{6}', a['lat']), [a.get('lat'), a.get('lon')])
    eis('bytes en sha256 van het bestand zelf; gewijzigd als datum en tijd',
        a and a['bytes'] == str(len(abc)) and a['sha256'] == sha(abc) and re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d', a['gewijzigd']), [a.get('bytes'), a.get('gewijzigd')])
    eis('de kopie: dubbel_van wijst naar het origineel', pp.get('20261001_100000_abc_car (1).zip', {}).get('dubbel_van') == '20261001_100000_abc_car.zip')
    eis('de reconstructie: recon zelf', pp.get('Autoparkeren/20261001_100000_abc_recon.zip', {}).get('recon') == 'zelf')
    eis('zonder reconstructie: fiets, pocket en een auto zonder spoor staan op nee',
        [pp.get(k, {}).get('recon') for k in ('20261002_090000_def_fts.zip', 'veld/20261003_110000_ghi_pkt_w.zip', '20261007_150000_zzz_car.zip')] == ['nee'] * 3)
    eis('Static: de telplek uit _sessie.csv; recon n.v.t.',
        [pp.get('20261004_120000_jkl_sta.zip', {}).get(k) for k in ('lat', 'lon', 'recon', 'soort')] == ['51.851400', '4.331200', 'n.v.t.', 'Stilstaand'])
    eis('capaciteit en verzameling: n.v.t.; de verzameling met de datum uit de naam en zonder plek',
        pp.get('20261005_130000_mno_cap.zip', {}).get('recon') == 'n.v.t.' and
        [pp.get('TelVerzameling_20261020.zip', {}).get(k) for k in ('recon', 'datum', 'weekdag', 'lat', 'soort')] == ['n.v.t.', '2026-10-20', 'di', '', 'Verzamelingen'])
    eis('zonder spoor en zonder telplek: lat en lon leeg', [pp.get('20261007_150000_zzz_car.zip', {}).get(k) for k in ('lat', 'lon')] == ['', ''])
    eis('de CSV is wat de pagina toont (ORDENEN.csvTekst van dezelfde regels)', pg.evaluate("ORDENEN.csvTekst(rijen)") == tekst)
    eis('de melding noemt catalogus.csv', 'catalogus.csv' in pg.evaluate("document.getElementById('melding').textContent"))

    print('\n== B. Tellers en tabel ==')
    eis('het tabblad Overzicht staat open', pg.evaluate("document.body.getAttribute('data-tab')") == 'overzicht'
        and pg.is_visible('#kaart') and not pg.is_visible('#uitvoeren'))
    tel = pg.inner_text('#tellers')
    eis('tellers: 11 tellingen en 1 verzameling, sep 2026 – okt 2026, 1 dubbel, 2 zelfde telling, 6 zonder reconstructie, 1 zonder plek',
        all(x in tel for x in ['11 tellingen en 1 verzameling', 'sep 2026 \u2013 okt 2026', '1 dubbel', '2 zelfde telling, andere inhoud',
                               '6 zonder reconstructie', '1 zonder plek']), tel)
    tab = pg.evaluate(TABEL)
    eis('de tabel: alle %d regels, de nieuwste bovenaan' % NREGELS, len(tab) == NREGELS and tab[0] == 'TelVerzameling_20261020.zip'
        and tab[-1] == 'Winkelstraat/20260915_110000_rep_pkt_w.zip', tab[:2] + tab[-1:])

    print('\n== C. Kaart ==')
    stand = pg.evaluate(KAARTSTAND)
    eis('elke telling met een plek staat op de kaart (10 = 12 - verzameling - zonder plek)', sum(stand) == 10, stand)
    eis('origineel, kopie en reconstructie op één plek: één bol van 3', 3 in stand, stand)
    # tot het eind inzoomen op die plek: nog steeds één bol; aanklikken geeft een lijstje
    pg.evaluate("kaart.setView([%f, %f], kaart.getMaxZoom(), { animate: false })" % (LAT, LON)); pg.wait_for_timeout(300)
    pg.evaluate("""() => { let bol = null; puntLaag.eachLayer(l => { if (!(l instanceof L.CircleMarker) && l.getElement().textContent.trim() === '3') bol = l; });
                         bol.fire('click'); }""")
    pg.wait_for_timeout(200)
    lijst = pg.evaluate("[...document.querySelectorAll('.leaflet-popup .lijst a')].map(a => a.textContent)")
    eis('helemaal ingezoomd: de bol geeft een lijstje met de drie bestanden', len(lijst) == 3 and all('20261001_100000_abc' in x for x in lijst), lijst)
    pg.click('.leaflet-popup .lijst a >> nth=0'); pg.wait_for_timeout(300)
    eis('uit het lijstje kiezen: de gegevens in een popup, de rij gemarkeerd',
        '20261001_100000_abc' in pg.inner_text('.leaflet-popup .pop') and pg.evaluate("document.querySelectorAll('#catalogus-tabel tr.gekozen').length") == 1)

    print('\n== D. Filters ==')
    pg.click('#tellers button[data-toon="zonder"]')
    tab = pg.evaluate(TABEL)
    eis('teller "zonder reconstructie" aanklikken: alleen die 6', len(tab) == 6 and all(pg.evaluate("rijen.filter(r => r.pad === %r)[0].recon" % t) == 'nee' for t in tab), tab)
    eis('de kaart volgt: 5 met een plek (de auto zonder spoor niet)', sum(pg.evaluate(KAARTSTAND)) == 5, pg.evaluate(KAARTSTAND))
    pg.click('#tellers button[data-toon="zonder"]')
    eis('nog eens klikken: weer alles', len(pg.evaluate(TABEL)) == NREGELS)
    pg.click('#tellers button[data-toon="dubbel"]')
    eis('"dubbel": de kopie en het origineel', sorted(pg.evaluate(TABEL)) == ['20261001_100000_abc_car (1).zip', '20261001_100000_abc_car.zip'], pg.evaluate(TABEL))
    pg.check('#f-controle input[value="zelfde"]')
    eis('"zelfde telling, andere inhoud": de twee fietstellingen', sorted(pg.evaluate(TABEL)) == ['a/20261006_140000_xyz_fts.zip', 'b/20261006_140000_xyz_fts.zip'])
    pg.check('#f-controle input[value="alles"]')
    pg.uncheck('#f-soorten input[data-soort="auto"]')
    eis('soort Autoparkeren uit: 8 over', len(pg.evaluate(TABEL)) == 8 and not any('_car' in t or '_recon' in t for t in pg.evaluate(TABEL)), pg.evaluate(TABEL))
    pg.click('#f-soorten a >> text=alle')
    pg.fill('#f-van', '2026-10-03'); pg.fill('#f-tot', '2026-10-05'); pg.dispatch_event('#f-tot', 'change')
    eis('periode 3 t/m 5 oktober: pocket, Static, capaciteit', sorted(pg.evaluate(TABEL)) == ['20261004_120000_jkl_sta.zip', '20261005_130000_mno_cap.zip', 'veld/20261003_110000_ghi_pkt_w.zip'], pg.evaluate(TABEL))
    pg.fill('#f-van', ''); pg.fill('#f-tot', ''); pg.dispatch_event('#f-tot', 'change')
    eis('periode leeg: weer alles', len(pg.evaluate(TABEL)) == NREGELS)

    print('\n== E. Route ==')
    pg.click('#catalogus-tabel tr[data-i] >> text=20261002_090000_def')
    pg.wait_for_function("routeLaag.getLayers().length === 1", timeout=5000)
    n = pg.evaluate("routeLaag.getLayers()[0].getLatLngs().length")
    eis('een rij aanklikken: het spoor uit de ZIP (24 punten), in de kleur van de soort',
        n == 24 and pg.evaluate("routeLaag.getLayers()[0].options.color") == '#2980b9', n)
    eis('en de gegevens in een popup', '20261002_090000_def' in pg.inner_text('.leaflet-popup .pop') and 'nog geen reconstructie' in pg.inner_text('.leaflet-popup .pop'))
    if os.environ.get('ARCHIEF_PNG'):                # om te bekijken: ARCHIEF_PNG=/pad/archief.png
        pg.screenshot(path=os.environ['ARCHIEF_PNG'])

    print('\n== F. Na Uitvoeren: catalogus.csv met de nieuwe paden ==')
    pg.click('#tab-ordenen')
    pg.click('#uitvoeren')
    pg.wait_for_function("document.getElementById('plan-melding').textContent.indexOf('verplaatst') >= 0 && !BEZIG", timeout=30000)
    tekst2 = pg.evaluate(LEES, 'catalogus.csv') or ''
    pp2 = per_pad(csv_regels(tekst2))
    eis('nog steeds %d regels, nu met de nieuwe paden' % NREGELS, len(pp2) == NREGELS and 'Fietsparkeren/20261002_090000_def_fts.zip' in pp2
        and 'Autoparkeren/originelen/20261001_100000_abc_car.zip' in pp2 and '20261002_090000_def_fts.zip' not in pp2, sorted(pp2))
    eis('de kopie staat in dubbel/ en wijst naar het origineel op zijn nieuwe plek',
        pp2.get('dubbel/20261001_100000_abc_car (1).zip', {}).get('dubbel_van') == 'Autoparkeren/originelen/20261001_100000_abc_car.zip')
    eis('de melding van Ordenen noemt de catalogus', 'catalogus.csv' in pg.inner_text('#plan-melding'))
    pg.click('#tab-overzicht')
    pg.click('#catalogus-tabel tr[data-i] >> text=20261002_090000_def')
    pg.wait_for_function("routeLaag.getLayers().length === 1", timeout=5000)
    eis('de route van een verplaatst bestand: nog steeds uit de ZIP', pg.evaluate("routeLaag.getLayers()[0].getLatLngs().length") == 24)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== G. Alleen bekijken: de CSV als download ==')
    tmp = tempfile.mkdtemp(prefix='archief_')
    arch = os.path.join(tmp, 'archief')
    for pad, data in BESTANDEN.items():
        os.makedirs(os.path.dirname(os.path.join(arch, pad)), exist_ok=True)
        open(os.path.join(arch, pad), 'wb').write(data)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True); ctx.route('**/*', route_archief)
    ctx.add_init_script("delete window.showDirectoryPicker;")
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.goto(BASIS + 'telarchief.html', wait_until='load'); pg.wait_for_timeout(300)
    pg.set_input_files('#map-invoer', arch)
    pg.wait_for_function("rijen.length > 0 && !BEZIG", timeout=30000)
    eis('de melding zegt dat de pagina hier niets schrijft', 'download' in pg.inner_text('#melding'))
    with pg.expect_download() as d:
        pg.click('#download-catalogus')
    dl = open(d.value.path(), encoding='utf-8').read()
    zonder_tijd = lambda t: [r[:13] + r[14:] for r in csv_regels(t)]
    eis('download catalogus.csv: dezelfde regels als in Chrome (op de wijzigdatum na)',
        d.value.suggested_filename == 'catalogus.csv' and sorted(zonder_tijd(dl)) == sorted(zonder_tijd(tekst)),
        [d.value.suggested_filename, set(map(tuple, zonder_tijd(dl))) ^ set(map(tuple, zonder_tijd(tekst)))])
    pg.click('#catalogus-tabel tr[data-i] >> text=20261002_090000_def')
    pg.wait_for_function("routeLaag.getLayers().length === 1", timeout=5000)
    eis('ook hier tekent een klik de route (uit het gekozen bestand)', pg.evaluate("routeLaag.getLayers()[0].getLatLngs().length") == 24)

    print('\n== H. Op 390 px ==')
    breed = pg.evaluate("document.documentElement.scrollWidth")
    eis('de pagina is niet breder dan het scherm (%d px)' % breed, breed <= 390)
    eis('de kaart staat boven de filters, en is zichtbaar', pg.evaluate(
        "document.getElementById('kaart').getBoundingClientRect().bottom <= document.querySelector('.filters').getBoundingClientRect().top + 1")
        and pg.is_visible('#kaart'))
    if os.environ.get('ARCHIEF_PNG'):
        pg.screenshot(path=os.environ['ARCHIEF_PNG'].replace('.png', '_390.png'), full_page=True)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    shutil.rmtree(tmp, ignore_errors=True)
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
