#!/usr/bin/env python3
"""v3.1 — GeoPackage-export uit telrapport, van telling tot QGIS.

  A. Echte tellingen maken met de veld-apps (nagebootste GPS langs een straat,
     nep-wegennet): parkeertelling, pocket-parkeren en pocket-winkelstraat.
  B. Die drie in telrapport laden en "bewaar kaart als GeoPackage" doen.
  C. Het bestand controleren met SQLite: GeoPackage-kenmerken, tabellen,
     omhullende, precies de stippen/bollen/wegvakken/routes die op de kaart
     staan (tot op de coördinaat), en een standaardstijl per laag die elke
     categorie in de data dekt.
  D. Wat je uitzet gaat niet mee (de sessie staat wel in 'sessies', op_kaart 0).
  E. In de correctiemodus weigert de export; pocket-stippen blijven daar niet
     versleepbaar (de export-tag heet bewust niet _telregel).
  F. Naam kiezen (v3.2): het Opslaan-als-venster (hier nagebootst) levert de
     naam waar het project naar verwijst; annuleren schrijft niets; zonder dat
     venster vraagt telrapport de naam en downloadt het bestand onder die naam.
  G. Als PyQGIS er is: QGIS opent het bestand, elke laag krijgt zijn opmaak
     (categorieën met de kleuren van telrapport, taartdiagram, labels), en de
     kaart wordt naar een PNG gerenderd. Sinds v3.2 ook het project: geopend
     vanuit een andere map, RD New, lagenboom en ondergronden, opmaak A4 met
     rond schaalgetal, legenda en noordpijl, als PNG geëxporteerd; en de
     RD-benadering van telrapport tegen PROJ. Zonder PyQGIS: overgeslagen.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast;
sql.js uit dezelfde node_modules (npm install sql.js@1.14.2).
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/gpkgtest.py
PyQGIS-Python kiezen: TEL_QGIS_PYTHON=/usr/bin/python3.12 (standaard: zoeken).
"""
import base64, io, json, os, re, sqlite3, struct, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
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

SQLJS = os.path.join(NM, 'sql.js', 'dist')
if not os.path.exists(os.path.join(SQLJS, 'sql-wasm.wasm')):
    sys.exit('sql.js niet gevonden in %s (npm install sql.js@1.14.2 buiten de repo)' % NM)
def route_gpkg(r):
    u = r.request.url
    if '/sql.js/' in u and u.endswith(('sql-wasm.js', 'sql-wasm.wasm')):
        f = u.rsplit('/', 1)[1]
        return r.fulfill(body=open(os.path.join(SQLJS, f), 'rb').read(),
                         content_type='application/wasm' if f.endswith('.wasm') else 'application/javascript')
    return route_met_osm(r)

UIT = '/tmp/gpkgtest'; os.makedirs(UIT, exist_ok=True)

def loop_langs_straat(ctx, pg, n, tik):
    """Noordwaarts langs 'Noordstraat 3' (lon = LON), 2 m ernaast, 13 m per stap."""
    for i in range(n):
        ctx.set_geolocation({'latitude': LAT + 0.0003 + i * 0.00012, 'longitude': LON + 0.00003, 'accuracy': 5})
        pg.wait_for_timeout(300)
        pg.evaluate(tik(i))
        pg.wait_for_timeout(60)

def maak_zip(b, app, start, tik, stop, n=12):
    ctx = nieuwe_context(b); pg = ctx.new_page(); f = []
    pg.on('pageerror', lambda e: f.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(600)
    ctx.set_geolocation({'latitude': LAT + 0.0003, 'longitude': LON + 0.00003, 'accuracy': 5})
    pg.evaluate(start); pg.wait_for_timeout(1200)
    loop_langs_straat(ctx, pg, n, tik)
    with pg.expect_download(timeout=20000) as d:
        pg.evaluate(stop)
    pad = os.path.join(UIT, d.value.suggested_filename); d.value.save_as(pad)
    ctx.close()
    return pad, f

def gp_geom(blob):
    """GeoPackage-geometrie terug naar coördinaten; controleert de kop onderweg."""
    assert blob[:2] == b'GP', 'geen GP-kop'
    vlag = blob[3]; env = (vlag >> 1) & 7; le = vlag & 1
    srs = struct.unpack('<i' if le else '>i', blob[4:8])[0]
    o = 8 + {0: 0, 1: 32}[env]
    bo = '<' if blob[o] == 1 else '>'
    typ = struct.unpack(bo + 'I', blob[o + 1:o + 5])[0]; o += 5
    if typ == 1:
        return srs, 'POINT', [struct.unpack(bo + 'dd', blob[o:o + 16])]
    n = struct.unpack(bo + 'I', blob[o:o + 4])[0]; o += 4
    return srs, 'LINESTRING', [struct.unpack(bo + 'dd', blob[o + 16 * i:o + 16 * i + 16]) for i in range(n)]

def qml_categorieen(qml):
    x = ET.fromstring(re.sub(r'<!DOCTYPE[^>]*>', '', qml))
    return [c.get('value') for c in x.iter('category')], x

def lees_gpkg(pad):
    db = sqlite3.connect(pad)
    return db, {r[0]: r for r in db.execute('select * from gpkg_contents')}

# Wat telrapport op de kaart heeft staan, in dezelfde termen als de export.
OP_KAART = r"""(() => {
  const r6 = x => Math.round(x * 1e7) / 1e7;
  const dots = [], cl = [], wv = [], rt = [];
  Object.keys(dotLayers).forEach(sid => Object.values(dotLayers[sid] || {}).forEach(a => a.forEach(m => {
    if (map.hasLayer(m)) { const ll = m.getLatLng(); dots.push([sid, r6(ll.lng), r6(ll.lat)]); } })));
  Object.keys(clusterLayers).forEach(sid => (clusterLayers[sid] || []).forEach(m => {
    if (m._cluster && map.hasLayer(m)) cl.push([sid, m._cluster.total]); }));
  Object.keys(wayLayers).forEach(k => { const g = (wayData[k] || {}).geometry || [];
    if (map.hasLayer(wayLayers[k]) && g.length >= 2 && !(g.length === 2 && g[0][0] === g[1][0] && g[0][1] === g[1][1])) wv.push(k); });
  Object.keys(gpsLayers).forEach(sid => { if (map.hasLayer(gpsLayers[sid]) && sessions[sid]) rt.push(sid); });
  return { dots, cl, wv, rt, sessies: Object.keys(sessions) };
})()"""

# Het Opslaan-als-venster (showSaveFilePicker) bestaat niet zonder scherm; dit
# doet wat de browser doet: een naam teruggeven (window.__kies_naam) en de
# geschreven bytes opvangen. '__annuleer__' bootst annuleren na.
OPSLAAN_STUB = r"""
window.__opslaan = { voorstel: null, naam: null, bytes: null, aantal: 0 };
window.showSaveFilePicker = async function (o) {
  window.__opslaan.aantal++;
  window.__opslaan.voorstel = o.suggestedName;
  if (window.__kies_naam === '__annuleer__') { var e = new Error('geannuleerd'); e.name = 'AbortError'; throw e; }
  var naam = window.__kies_naam || o.suggestedName, delen = [];
  return { name: naam, createWritable: async function () { return {
    write: async function (b) { delen.push(b); },
    close: async function () {
      var buf = new Uint8Array(await new Blob(delen).arrayBuffer()), s = '';
      for (var i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
      window.__opslaan.naam = naam; window.__opslaan.bytes = btoa(s);
    } }; } };
};
"""

def exporteer(pg, naam):
    pg.evaluate("window.__opslaan.bytes = null; window.__kies_naam = %r" % naam)
    pg.evaluate('exportGeoPackage()')
    pg.wait_for_function('window.__opslaan.bytes !== null', timeout=30000)
    o = pg.evaluate('window.__opslaan')
    pad = os.path.join(UIT, naam)
    open(pad, 'wb').write(base64.b64decode(o['bytes']))
    return pad, o['voorstel']

def project_qgs(pad):
    db = sqlite3.connect(pad)
    try:
        rij = db.execute('select name, content from qgis_projects').fetchall()
    except sqlite3.OperationalError:
        return [], None
    finally:
        db.close()
    z = zipfile.ZipFile(io.BytesIO(bytes.fromhex(rij[0][1]))) if rij else None
    return [r[0] for r in rij], z

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Tellingen maken met de veld-apps ==')
    zips, jsfout = [], []
    for app, start, tik, stop in [
        ('parkeertelling.html', 'startSession()',
         lambda i: "addEntry('%s','%s')" % (['goed', 'fout', 'leeg', 'spec'][i % 4], 'LR'[i % 2]), 'exportZip()'),
        ('pocket_count.html', 'startParkeren()',
         lambda i: "adjustParkeer('%s',1)" % ['links_bezet', 'rechts_leeg', 'links_leeg', 'rechts_bezet'][i % 4], 'stopTelling()'),
        ('pocket_count.html', 'startWinkelstraat()',
         lambda i: "adjustWinkel('%s',1)" % ['tegemoet', 'stilstaand'][i % 2], 'stopTelling()')]:
        z, f = maak_zip(b, app, start, tik, stop)
        zips.append(z); jsfout += f
        eis('%s -> %s' % (app, os.path.basename(z)), z.endswith('.zip'))
    eis('geen JS-fouten in de veld-apps', not jsfout, jsfout)

    print('\n== B. Telrapport: laden en exporteren ==')
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}, accept_downloads=True)
    ctx.route('**/*', route_gpkg)
    ctx.add_init_script(OPSLAAN_STUB)
    pg = ctx.new_page(); fouten, meldingen, vragen = [], [], []
    prompt_antwoord = [None]          # None = standaardwaarde, '__weg__' = annuleren
    def dialoog(d):
        meldingen.append(d.message)
        if d.type == 'prompt':
            vragen.append(d.default_value)
            if prompt_antwoord[0] == '__weg__': return d.dismiss()
            return d.accept(prompt_antwoord[0]) if prompt_antwoord[0] is not None else d.accept()
        d.accept()
    pg.on('dialog', dialoog)
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(800)
    pg.set_input_files('#file-input', zips); pg.wait_for_timeout(3500)
    kaart = pg.evaluate(OP_KAART)
    eis('drie tellingen geladen', len(kaart['sessies']) == 3, kaart['sessies'])
    eis('er staan stippen, bollen, wegvakken en routes op de kaart (%d/%d/%d/%d)'
        % (len(kaart['dots']), len(kaart['cl']), len(kaart['wv']), len(kaart['rt'])),
        kaart['dots'] and kaart['cl'] and kaart['wv'] and kaart['rt'])
    pad, voorstel = exporteer(pg, 'alles.gpkg')
    eis('Opslaan-als stelt telrapport_<datum>_<tijd>.gpkg voor', re.match(r'^telrapport_\d{8}_\d{4}\.gpkg$', voorstel or ''), voorstel)
    rd_js = pg.evaluate("[[51.85,4.30],[53.2,6.56],[50.85,5.69],[52.37,4.89],[51.44,3.57]].map(p => GPKG_PROJECT.rd(p[0], p[1]))")

    print('\n== C. Het bestand ==')
    db, inhoud = lees_gpkg(pad)
    eis('application_id = GPKG', db.execute('pragma application_id').fetchone()[0] == 1196444487)
    eis('user_version = 10200', db.execute('pragma user_version').fetchone()[0] == 10200)
    eis('integrity_check ok', db.execute('pragma integrity_check').fetchone()[0] == 'ok')
    srs = {r[0] for r in db.execute('select srs_id from gpkg_spatial_ref_sys')}
    eis('verplichte ruimtelijke referenties -1, 0, 4326', {-1, 0, 4326} <= srs, srs)
    lagen = ['waarnemingen', 'clusters', 'wegvakken', 'route']
    eis('vier kaartlagen als features', all(inhoud.get(t, [None, None])[1] == 'features' for t in lagen),
        {t: inhoud.get(t, [None, None])[1] for t in lagen})
    eis('sessies, export_info en layer_styles als attributes',
        all(inhoud.get(t, [None, None])[1] == 'attributes' for t in ['sessies', 'export_info', 'layer_styles']))
    gc = {r[0]: r for r in db.execute('select * from gpkg_geometry_columns')}
    eis('geometriekolommen POINT/POINT/LINESTRING/LINESTRING in EPSG:4326',
        [gc[t][2] for t in lagen] == ['POINT', 'POINT', 'LINESTRING', 'LINESTRING'] and all(gc[t][3] == 4326 for t in lagen),
        {t: gc.get(t) for t in lagen})

    def coords(tabel):
        rijen = db.execute('select geom, * from "%s"' % tabel).fetchall()
        return [gp_geom(r[0]) for r in rijen], rijen
    g, rijen = coords('waarnemingen')
    eis('elke geometrie: GP-kop, EPSG:4326, juiste soort', all(s == 4326 and t == 'POINT' for s, t, _ in g))
    kol = [c[1] for c in db.execute('pragma table_info(waarnemingen)')]
    sid_i = kol.index('sessie_id') + 1
    in_bestand = sorted([r[sid_i], round(x, 7), round(y, 7)] for (_, _, [(x, y)]), r in zip(g, rijen))
    eis('waarnemingen = de stippen op de kaart, tot op 1e-7 graad (%d)' % len(in_bestand),
        in_bestand == sorted(kaart['dots']), (len(in_bestand), len(kaart['dots'])))
    ncl = db.execute('select sessie_id, totaal from clusters').fetchall()
    eis('clusters = de bollen op de kaart, met hun totaal (%d)' % len(ncl),
        sorted(map(list, ncl)) == sorted(kaart['cl']), (ncl[:5], kaart['cl'][:5]))
    nkol = [c[1] for c in db.execute('pragma table_info(clusters)') if re.match(r'^(auto|fiets|pocket|transect)_', c[1])]
    som = db.execute('select count(*) from clusters where totaal != ' + ('+'.join(nkol) or '0')).fetchone()[0]
    eis('per bol: som van de typekolommen = totaal (%s)' % ', '.join(nkol), som == 0, som)
    eis('wegvakken = de lijnen op de kaart (%d)' % len(kaart['wv']),
        db.execute('select count(*) from wegvakken').fetchone()[0] == len(kaart['wv']))
    gw, _ = coords('wegvakken')
    eis('wegvakken zijn lijnen met >= 2 punten', all(t == 'LINESTRING' and len(c) >= 2 for _, t, c in gw))
    eis('route: één lijn per telling op de kaart',
        sorted(r[0] for r in db.execute('select sessie_id from route')) == sorted(kaart['rt']))
    bb = inhoud['waarnemingen'][5:9]
    xs = [c[0][0] for _, _, c in g]; ys = [c[0][1] for _, _, c in g]
    eis('omhullende in gpkg_contents klopt', abs(bb[0] - min(xs)) < 1e-9 and abs(bb[3] - max(ys)) < 1e-9, (bb, min(xs), max(ys)))

    st = {r[0]: (r[1], r[2]) for r in db.execute('select f_table_name, useAsDefault, styleQML from layer_styles')}
    eis('per kaartlaag één standaardstijl', sorted(st) == sorted(lagen) and all(v[0] == 1 for v in st.values()), sorted(st))
    for tabel, veld in [('waarnemingen', 'categorie'), ('wegvakken', 'klasse'), ('route', 'sessie_id')]:
        cats, _ = qml_categorieen(st[tabel][1])
        data = {r[0] for r in db.execute('select distinct "%s" from %s' % (veld, tabel))}
        eis('%s: stijl dekt elke %s in de data (%d)' % (tabel, veld, len(data)), data <= set(cats), data - set(cats))
    _, x = qml_categorieen(st['clusters'][1])
    velden = [a.get('field').strip('"') for a in x.iter('attribute')]
    eis('clusters: het taartdiagram heeft een punt per typekolom', sorted(velden) == sorted(nkol), (velden, nkol))
    kleur = {a.get('field').strip('"'): a.get('color') for a in x.iter('attribute')}
    app_kleur = pg.evaluate("(() => { const u = {}; for (const a in APP_CONFIG) for (const t in APP_CONFIG[a].colors) u[(a+'_'+t).toLowerCase()] = APP_CONFIG[a].colors[t]; return u; })()")
    eis('taartkleuren = de kleuren van telrapport', all(kleur[v] == app_kleur.get(v) for v in kleur), kleur)
    ses = db.execute('select sessie_id, op_kaart from sessies').fetchall()
    eis('sessies: alle drie, op_kaart = 1', sorted(s for s, _ in ses) == sorted(kaart['sessies']) and all(o == 1 for _, o in ses), ses)
    info = dict(db.execute('select sleutel, waarde from export_info'))
    eis('export_info: clusterafstand en formaatversie', info.get('clusterafstand_m') == '8' and info.get('formaat_versie') == '1', info)
    db.close()
    namen, zq = project_qgs(pad)
    eis('qgis_projects: één project "telrapport"', namen == ['telrapport'], namen)
    eis('inhoud = .qgz (als hex) met telrapport.qgs', zq is not None and zq.namelist() == ['telrapport.qgs'], zq and zq.namelist())
    qgs = zq.read('telrapport.qgs').decode('utf-8')
    try:
        ET.fromstring(qgs); goed = True
    except ET.ParseError as e:
        goed = str(e)
    eis('project is geldige XML', goed is True, goed)
    bronnen = re.findall(r'<datasource>\./([^<|]+)\|layername=([^<]+)</datasource>', qgs)
    eis('lagen verwijzen naar de gekozen naam (./alles.gpkg|layername=…)',
        sorted(t for _, t in bronnen) == sorted(lagen) and all(n == 'alles.gpkg' for n, _ in bronnen), bronnen)
    eis("laag-id's eindigen op _telrapport (korte id's vervangt QGIS)",
        all(i.endswith('_telrapport') for i in re.findall(r'<id>([^<]+)</id>', qgs)))

    print('\n== D. Wat je uitzet, gaat niet mee ==')
    weg = pg.evaluate("Object.keys(sessions).find(s => sessions[s].appType === 'auto')")
    pg.evaluate("sessions[%r].visible = false; applySessionVisibility(%r); recolorAll();" % (weg, weg))
    pg.wait_for_timeout(300)
    kaart2 = pg.evaluate(OP_KAART)
    pad2, _ = exporteer(pg, 'zonder_auto.gpkg')
    db, _ = lees_gpkg(pad2)
    eis('waarnemingen zonder de uitgezette telling',
        db.execute('select count(*) from waarnemingen where sessie_id = ?', (weg,)).fetchone()[0] == 0
        and db.execute('select count(*) from waarnemingen').fetchone()[0] == len(kaart2['dots']))
    eis('ook geen clusters en route van die telling',
        db.execute('select count(*) from clusters where sessie_id = ?', (weg,)).fetchone()[0] == 0
        and db.execute('select count(*) from route where sessie_id = ?', (weg,)).fetchone()[0] == 0)
    eis('in sessies staat hij wel, met op_kaart = 0',
        db.execute('select op_kaart from sessies where sessie_id = ?', (weg,)).fetchone() == (0,))
    cats, _ = qml_categorieen(db.execute("select styleQML from layer_styles where f_table_name='waarnemingen'").fetchone()[0])
    eis('legenda zonder de types van de uitgezette telling', not any(c.startswith('auto|') for c in cats), cats)
    db.close()
    pg.evaluate("sessions[%r].visible = true; applySessionVisibility(%r); recolorAll();" % (weg, weg))

    print('\n== E. Correctiemodus ==')
    pg.evaluate('toggleEditMode()'); pg.wait_for_timeout(300)
    pocket_bewerkbaar = pg.evaluate("Object.keys(editMarkers).filter(s => sessions[s].appType === 'pocket').reduce((a, s) => a + editMarkers[s].length, 0)")
    eis('pocket-stippen niet versleepbaar (export-tag is geen _telregel)', pocket_bewerkbaar == 0, pocket_bewerkbaar)
    n_meld = len(meldingen); n_opslaan = pg.evaluate('window.__opslaan.aantal')
    gestart = []
    pg.on('download', lambda d: gestart.append(d))
    pg.evaluate('exportGeoPackage()'); pg.wait_for_timeout(800)
    eis('export weigert met een melding, nog vóór het Opslaan-als-venster',
        len(meldingen) == n_meld + 1 and 'correctiemodus' in meldingen[-1] and not gestart
        and pg.evaluate('window.__opslaan.aantal') == n_opslaan, meldingen[-1:])
    pg.evaluate('toggleEditMode()'); pg.wait_for_timeout(300)

    print('\n== F. Naam kiezen ==')
    n_opslaan = pg.evaluate('window.__opslaan.aantal')
    pg.evaluate("window.__opslaan.bytes = null; window.__kies_naam = '__annuleer__'")
    pg.evaluate('exportGeoPackage()'); pg.wait_for_timeout(1500)
    eis('Opslaan-als geannuleerd: niets geschreven, geen download',
        pg.evaluate('window.__opslaan.aantal') == n_opslaan + 1 and pg.evaluate('window.__opslaan.bytes') is None and not gestart)
    pg.evaluate('delete window.showSaveFilePicker')
    prompt_antwoord[0] = 'Meting Spijkenisse'
    with pg.expect_download(timeout=30000) as d:
        pg.evaluate('exportGeoPackage()')
    eis('zonder Opslaan-als: naam gevraagd, met het voorstel als standaard',
        vragen and re.match(r'^telrapport_\d{8}_\d{4}\.gpkg$', vragen[-1]), vragen[-1:])
    eis('download heet zoals gekozen, .gpkg erachter', d.value.suggested_filename == 'Meting Spijkenisse.gpkg', d.value.suggested_filename)
    pad3 = os.path.join(UIT, 'Meting Spijkenisse.gpkg'); d.value.save_as(pad3)
    _, z3 = project_qgs(pad3)
    eis('het project verwijst naar die naam', z3 and './Meting Spijkenisse.gpkg|layername=' in z3.read('telrapport.qgs').decode('utf-8'))
    prompt_antwoord[0] = '__weg__'; n_dl = len(gestart)
    pg.evaluate('exportGeoPackage()'); pg.wait_for_timeout(1500)
    eis('naamvraag geannuleerd: geen download', len(gestart) == n_dl, len(gestart) - n_dl)
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    ctx.close()
    b.close()

print('\n== G. QGIS ==')
def zoek_qgis():
    kandidaten = [os.environ.get('TEL_QGIS_PYTHON', '')] + ['/usr/bin/python3.12', '/usr/bin/python3', sys.executable]
    for k in kandidaten:
        if k and os.path.exists(k) and subprocess.run([k, '-c', 'import qgis.core'], capture_output=True,
                                                      env=dict(os.environ, QT_QPA_PLATFORM='offscreen')).returncode == 0:
            return k
qpy = zoek_qgis()
if not qpy:
    print('  OVERGESLAGEN: geen PyQGIS gevonden (zet TEL_QGIS_PYTHON)')
else:
    png = os.path.join(UIT, 'kaart_qgis.png'); opmaak_png = os.path.join(UIT, 'opmaak_qgis.png')
    r = subprocess.run([qpy, os.path.join(HIER, 'gpkg_qgis.py'), pad, png, opmaak_png], capture_output=True, text=True,
                       env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), timeout=300)
    regel = [x for x in r.stdout.splitlines() if x.startswith('{')]
    eis('QGIS draait het script', bool(regel), r.stderr[-400:])
    if regel:
        q = json.loads(regel[-1]); L = q['lagen']
        print('  (QGIS %s)' % q['qgis'])
        db, _ = lees_gpkg(pad)
        for t in lagen + ['sessies', 'export_info']:
            n = db.execute('select count(*) from "%s"' % t).fetchone()[0]
            eis('%s: geldig in QGIS, %d objecten' % (t, n), L[t].get('geldig') and L[t].get('aantal') == n, L[t])
        eis('kaartlagen in EPSG:4326', all(L[t]['crs'] == 'EPSG:4326' for t in lagen))
        for t in ['waarnemingen', 'wegvakken', 'route']:
            eis('%s: QGIS past de categorie-opmaak toe' % t, L[t]['opmaak'] == 'categorizedSymbol', L[t]['opmaak'])
        stijl = dict(db.execute("select f_table_name, styleQML from layer_styles"))
        for t in ['waarnemingen', 'wegvakken', 'route']:
            _, x = qml_categorieen(stijl[t])
            verwacht = []
            for c in x.iter('category'):
                sym = [s for s in x.iter('symbol') if s.get('name') == c.get('symbol')][0]
                o = {e.get('name'): e.get('value') for e in sym.iter('Option')}
                rgb = (o.get('color') or o.get('line_color')).split(',')[:3]
                verwacht.append([c.get('value'), c.get('label'), '#%02x%02x%02x' % tuple(int(v) for v in rgb)])
            eis('%s: categorieën, labels en kleuren zoals bedoeld (%d)' % (t, len(verwacht)),
                L[t]['categorieen'] == verwacht, (L[t]['categorieen'][:3], verwacht[:3]))
        d = L['clusters'].get('diagram') or {}
        eis('clusters: taartdiagram met een punt per typekolom', d.get('soort') == 'LinearlyInterpolated'
            and sorted(v.strip('"') for v in d.get('velden', [])) == sorted(nkol), d)
        eis('clusters: geen stip eronder, wel het totaal als label', L['clusters']['opmaak'] == 'nullSymbol' and L['clusters']['labels'],
            (L['clusters']['opmaak'], L['clusters']['labels']))
        lb = L['clusters'].get('label') or {}
        eis('clusters: het cijfer is vet via HTML <b> (fontWeight verschilt tussen QGIS 3 en 4)',
            lb.get('html') and lb.get('expressie') and '<b>' in lb.get('veld', '') and '"totaal"' in lb.get('veld', ''), lb)
        eis('kaart gerenderd: %s' % png, q.get('png') and os.path.getsize(png) > 20000)
        db.close()

        pj = q.get('project') or {}
        eis('project geopend vanuit een andere map', pj.get('gelezen') is True, pj.get('gelezen'))
        eis('project-CRS RD New (EPSG:28992)', pj.get('crs') == 'EPSG:28992', pj.get('crs'))
        eis('lagenboom: bollen, stippen, spoor, wegvakken, dan de ondergronden (alleen PDOK grijs aan)',
            pj.get('boom') == [['Clusterbollen', True], ['Waarnemingen', True], ['GPS-spoor', True], ['Wegvakken', True],
                               ['PDOK BRT-A grijs', True], ['PDOK luchtfoto', False], ['OpenStreetMap', False]], pj.get('boom'))
        eis('ondergronden in de groep "Ondergrond"', pj.get('groepen') == ['Ondergrond'], pj.get('groepen'))
        PL = pj.get('lagen', {})
        vect = {i: l for i, l in PL.items() if l['aanbieder'] == 'ogr'}
        eis("vier kaartlagen geldig, met hun id's", sorted(vect) == sorted(t + '_telrapport' for t in lagen)
            and all(l['geldig'] for l in vect.values()), {i: l['geldig'] for i, l in vect.items()})
        eis('kaartlagen houden hun opmaak in het project',
            [vect.get(t + '_telrapport', {}).get('opmaak') for t in ['clusters', 'waarnemingen', 'route', 'wegvakken']]
            == ['nullSymbol', 'categorizedSymbol', 'categorizedSymbol', 'categorizedSymbol']
            and vect.get('clusters_telrapport', {}).get('diagram'), vect)
        ras = sorted(i for i, l in PL.items() if l['aanbieder'] == 'wms')
        eis('ondergronden aanwezig (PDOK via WMTS, OSM via XYZ)', ras == ['osm_telrapport', 'pdok_grijs_telrapport', 'pdok_lucht_telrapport']
            and 'layers=grijs' in PL['pdok_grijs_telrapport']['bron'] and 'tileMatrixSet=EPSG:28992' in PL['pdok_grijs_telrapport']['bron'], ras)
        eis('standaardbeeld omvat de telling', pj.get('beeld_bevat_data') is True)
        o = pj.get('opmaak') or {}
        eis('opmaak "A4 liggend": kaart, legenda, schaalstok, noordpijl, drie teksten',
            (o.get('kaarten'), o.get('legendas'), o.get('schaalstokken'), o.get('plaatjes'), len(o.get('labels', []))) == (1, 1, 1, 1, 3), o)
        eis('kaart in RD op een rond schaalgetal (1:%s), telling helemaal in beeld' % o.get('schaal'),
            o.get('kaart_crs') == 'EPSG:28992' and o.get('schaal', 1) % 250 == 0 and o.get('kaart_bevat_data'), o)
        eis('legenda: Waarnemingen, GPS-spoor, Wegvakken, gekoppeld (geen ondergrond, geen dubbele bolkleuren)',
            o.get('legenda') == ['Waarnemingen', 'GPS-spoor', 'Wegvakken'] and o.get('legenda_gekoppeld'), o.get('legenda'))
        eis('titel met datum, bronvermelding met PDOK en OpenStreetMap',
            any(l.startswith('Telrapport · ') for l in o.get('labels', [])) and any('Kadaster' in l and 'OpenStreetMap' in l for l in o.get('labels', [])),
            o.get('labels'))
        eis('opmaak als PNG: %s' % opmaak_png, o.get('png') and os.path.getsize(opmaak_png) > 30000)
        afw = max(((a - x) ** 2 + (b_ - y) ** 2) ** .5 for (a, b_), (x, y) in zip(rd_js, q['rd_punten']))
        eis('RD-benadering in telrapport < 1 m van PROJ (max %.2f m)' % afw, afw < 1.0)
        print('  BEKEND  hernoemd bestand: het project vindt %s van de 4 lagen. QGIS onthoudt de bestandsnaam;'
              ' daarom kies je de naam bij het opslaan.' % pj.get('hernoemd_geldig'))
        r3 = subprocess.run([qpy, os.path.join(HIER, 'gpkg_qgis.py'), pad3], capture_output=True, text=True,
                            env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), timeout=300)
        q3 = json.loads([x for x in r3.stdout.splitlines() if x.startswith('{')][-1]).get('project', {})
        eis('naam met spatie ("Meting Spijkenisse.gpkg"): project vindt alle lagen',
            sum(1 for l in q3.get('lagen', {}).values() if l['aanbieder'] == 'ogr' and l['geldig']) == 4)

print('\n%d OK, %d FOUT' % (ok, fout))
if fout == 0:
    print('ALLE %d TESTS OK' % ok)
sys.exit(1 if fout else 0)
