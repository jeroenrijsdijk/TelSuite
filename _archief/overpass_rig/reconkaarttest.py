#!/usr/bin/env python3
"""v3.28 reconkaarttest — de kaart-PNG in de _recon.zip, in Chromium.

Jay: "De kaart png mag heel basic zijn - gewoon om met een viewer even snel te
kijken wat er in de zip zit. Ondergrond is niet nodig. Netwerk en tikken is
genoeg." Keuze: in de ZIP, als <sid>_kaart.png (dezelfde naam als in de ZIP's
van de parkeer-apps).

  A. Een parkeertelling maken (nagebootste GPS langs een straat, nep-wegennet)
     en die in telreconstructie laden.
  B. De _recon.zip (bouwZipBlob): er zit <sid>_kaart.png in, een geldige PNG van
     1600 px breed, met een kop en een legenda.
  C. Wat erop staat (het plaatje in de pagina gedecodeerd): elke soort tik in
     zijn kleur, het wegennet in grijs, het GPS-spoor in oranje; geen
     kaarttegels (geen enkel verzoek om tegels nodig).
  D. Twee keer exporteren geeft hetzelfde plaatje (geen exporttijdstip erin).
  E. Zonder tikken en GPS: geen plaatje, de ZIP komt er wel.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/reconkaarttest.py
"""
import base64, io, os, struct, sys, zipfile
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

TYPEN = ['goed', 'fout', 'leeg', 'spec']

# De recon-ZIP als base64, en het plaatje erin geteld per kleur. Een tik is een
# cirkel met 90% dekking op wit; het midden heeft dus 0,9 * kleur + 0,1 * wit.
TEL = r"""async () => {
  const blob = await bouwZipBlob();
  const buf = new Uint8Array(await blob.arrayBuffer());
  let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
  const zip = await JSZip.loadAsync(blob);
  const f = zip.file(S.sid + '_kaart.png');
  const uit = { zip: btoa(s), sid: S.sid, kleuren: {}, grijs: 0, oranje: 0 };
  if (!f) return uit;
  const bmp = await createImageBitmap(await f.async('blob'));
  const c = document.createElement('canvas'); c.width = bmp.width; c.height = bmp.height;
  const g = c.getContext('2d'); g.drawImage(bmp, 0, 0);
  const d = g.getImageData(0, 64, c.width, c.height - 64 - 56).data;   // alleen het kaartvlak
  const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const doel = {};
  Object.keys(S.typeKleuren.map).forEach(t => { const k = hex(S.typeKleuren.map[t]); doel[t] = k.map(v => Math.round(0.9 * v + 25.5)); uit.kleuren[t] = 0; });
  const bij = (r, gg, b, k, tol) => Math.abs(r - k[0]) <= tol && Math.abs(gg - k[1]) <= tol && Math.abs(b - k[2]) <= tol;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], gg = d[i + 1], b = d[i + 2];
    for (const t in doel) if (bij(r, gg, b, doel[t], 3)) uit.kleuren[t]++;
    if (bij(r, gg, b, [185, 180, 170], 4)) uit.grijs++;
    if (bij(r, gg, b, [255, 124, 38], 12)) uit.oranje++;
  }
  uit.geplaatst = {}; S.taps.forEach(tp => { if (tp.status === 'ok') uit.geplaatst[tp.type] = (uit.geplaatst[tp.type] || 0) + 1; });
  return uit;
}"""

def png_maat(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'geen PNG'
    return struct.unpack('>II', data[16:24])

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Een parkeertelling, en de reconstructie ervan ==')
    ctx = nieuwe_context(b); pg = ctx.new_page(); f1 = []
    pg.on('pageerror', lambda e: f1.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'parkeertelling.html', wait_until='load'); pg.wait_for_timeout(600)
    ctx.set_geolocation({'latitude': LAT + 0.0003, 'longitude': LON + 0.00003, 'accuracy': 5})
    pg.evaluate('startSession()'); pg.wait_for_timeout(1200)
    for i in range(12):
        ctx.set_geolocation({'latitude': LAT + 0.0003 + i * 0.00012, 'longitude': LON + 0.00003, 'accuracy': 5})
        pg.wait_for_timeout(300)
        pg.evaluate("addEntry('%s','%s')" % (TYPEN[i % 4], 'LR'[i % 2]))
    with pg.expect_download(timeout=20000) as d:
        pg.evaluate('exportZip()')
    veld = os.path.join('/tmp', d.value.suggested_filename); d.value.save_as(veld)
    ctx.close()
    eis('parkeertelling -> %s' % os.path.basename(veld), veld.endswith('.zip'))

    TEGELS = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    def r_(r):
        if any(t in r.request.url for t in ('basemaps.cartocdn.com', 'service.pdok.nl', 'tile.openstreetmap.org')):
            TEGELS.append(r.request.url)
            return r.fulfill(status=404, body='')
        return route_met_osm(r)
    ctx.route('**/*', r_)
    pg = ctx.new_page(); f2 = []
    pg.on('pageerror', lambda e: f2.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telreconstructie.html', wait_until='load'); pg.wait_for_timeout(600)
    pg.set_input_files('#file', veld)
    pg.wait_for_function("S.taps && S.taps.length === 12 && S.typeKleuren && S.taps.every(t => t.status)", timeout=30000)
    pg.wait_for_timeout(500)
    eis('reconstructie klaar: 12 tikken', pg.evaluate('S.taps.length') == 12)

    print('\n== B. De _recon.zip ==')
    uit = pg.evaluate(TEL)
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(uit['zip'])))
    naam = uit['sid'] + '_kaart.png'
    eis('<sid>_kaart.png in de ZIP (%s)' % naam, naam in z.namelist(), z.namelist())
    png = z.read(naam) if naam in z.namelist() else b''
    try:
        w, h = png_maat(png)
    except Exception as e:
        w, h = 0, str(e)
    eis('geldige PNG, 1600 px breed, kaartvlak van 700 tot 1600 px plus kop en legenda (%sx%s)' % (w, h),
        w == 1600 and isinstance(h, int) and 700 + 120 <= h <= 1600 + 120, (w, h))
    if png:
        open('/tmp/reconkaarttest.png', 'wb').write(png); print('  (plaatje: /tmp/reconkaarttest.png)')
    eis('de CSV-bestanden zijn er nog allemaal', all(any(n.endswith(s) for n in z.namelist())
        for s in ('_sessie.csv', '_telregels.csv', '_netwerk.csv', '_reconstructie_log.csv', '_gps.csv')), z.namelist())

    print('\n== C. Wat erop staat ==')
    for t in sorted(uit['geplaatst']):
        eis('tik "%s" in zijn kleur (%d geplaatst, %d px)' % (t, uit['geplaatst'][t], uit['kleuren'].get(t, 0)),
            uit['kleuren'].get(t, 0) >= 20 * uit['geplaatst'][t], uit['kleuren'])
    eis('alle vier de soorten geplaatst', sorted(uit['geplaatst']) == sorted(TYPEN), uit['geplaatst'])
    eis('wegennet in grijs (%d px)' % uit['grijs'], uit['grijs'] > 500, uit['grijs'])
    eis('GPS-spoor in oranje (%d px)' % uit['oranje'], uit['oranje'] > 50, uit['oranje'])
    n_tegels = len(TEGELS)
    pg.evaluate('kaartPng()')
    pg.wait_for_timeout(300)
    eis('het plaatje vraagt geen kaarttegels', len(TEGELS) == n_tegels, TEGELS[n_tegels:])

    print('\n== D. Twee keer exporteren ==')
    uit2 = pg.evaluate(TEL)
    z2 = zipfile.ZipFile(io.BytesIO(base64.b64decode(uit2['zip'])))
    eis('hetzelfde plaatje, byte voor byte (geen exporttijdstip erin)', naam in z2.namelist() and z2.read(naam) == png)

    print('\n== E. Zonder tikken en GPS ==')
    leeg = pg.evaluate("""async () => {
      const t = S.taps, g = S.gps; S.taps = []; S.gps = [];
      try {
        const p = await kaartPng();
        const zip = await JSZip.loadAsync(await bouwZipBlob());
        return { png: p, namen: Object.keys(zip.files) };
      } finally { S.taps = t; S.gps = g; }
    }""")
    eis('geen plaatje, de ZIP komt er wel', leeg['png'] is None and not any(n.endswith('_kaart.png') for n in leeg['namen'])
        and any(n.endswith('_telregels.csv') for n in leeg['namen']), leeg)
    eis('geen JS-fouten', not f1 and not f2, f1 + f2)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
