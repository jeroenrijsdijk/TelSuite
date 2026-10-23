#!/usr/bin/env python3
"""v3.29 deeltest — de waarschuwing bij het delen van een ZIP, in Chromium.

Jay: "Als mensen een telling doen vanuit huis, en ze leveren de .zip aan
derden, verraden ze de plek van hun woning. Dat is een waarschuwing waard."
Eén regel onder de knop waarmee je de ZIP bewaart, zonder iets weg te klikken.

  A. De vier veld-apps met een vaste knop (parkeertelling, fietsparkeren,
     capaciteitstelling, Static): de regel staat direct onder de knop, is
     zichtbaar, staat er één keer (ook na een tweede aanroep), en past op een
     telefoon van 360 px zonder zijwaarts schuiven. Static noemt het adres.
  B. Pocket: de regel staat in het voorbeeldscherm onder de kop met ZIP
     opslaan, in de taal van dat moment (Nederlands, dan Engels).
  C. Telreconstructie en telrapport: een vaste regel onder de knop.
  D. Privacyverklaring en handleiding hebben een stuk *Een ZIP delen*.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/deeltest.py
"""
import os, re, sys
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

ROUTE_NL = 'Deel je deze ZIP, dan deel je je route en je plek. Begon je thuis, dan staat je huis erin.'
ADRES_NL = 'Deel je deze ZIP, dan deel je je plek en adres. Tel je vanuit huis, dan staat je huis erin.'
ROUTE_EN = 'Sharing this ZIP shares your route and where you were. If you started at home, your home is in it.'

STAAT = """(knop) => { const k = document.getElementById(knop), w = document.getElementById('deel-waarschuwing');
  const r = w && w.getBoundingClientRect();
  return { onder: !!(k && w && k.nextElementSibling === w), tekst: w ? w.textContent : null,
           zichtbaar: !!(w && w.offsetParent !== null && r.height > 0),
           aantal: document.querySelectorAll('#deel-waarschuwing').length,
           schuift: document.documentElement.scrollWidth > document.documentElement.clientWidth }; }"""

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Veld-apps met een vaste knop ==')
    for app, knop, tekst in [('parkeertelling.html', 'btnDlZip', ROUTE_NL), ('fietsparkeren.html', 'btnDlZip', ROUTE_NL),
                             ('capaciteitstelling.html', 'btnDlZip', ROUTE_NL), ('traffic_counter.html', 'btn-zip', ADRES_NL)]:
        ctx = nieuwe_context(b); ctx.set_default_timeout(15000)
        pg = ctx.new_page(); pg.set_viewport_size({'width': 360, 'height': 780}); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + app, wait_until='load')
        pg.wait_for_function("!!document.getElementById('deel-waarschuwing')", timeout=10000)
        st = pg.evaluate(STAAT, knop)
        eis('%s: direct onder de knop, zichtbaar' % app, st['onder'] and st['zichtbaar'], st)
        eis('%s: de tekst%s' % (app, ' met adres' if tekst is ADRES_NL else ''), (st['tekst'] or '').endswith(tekst), st['tekst'])
        pg.evaluate("deelWaarschuwing(document.getElementById(%r), %s)" % (knop, 'true' if tekst is ADRES_NL else 'false'))
        eis('%s: één regel, ook na een tweede aanroep; geen zijwaarts schuiven op 360 px' % app,
            pg.evaluate(STAAT, knop)['aantal'] == 1 and not st['schuift'], pg.evaluate(STAAT, knop))
        eis('%s: geen JS-fouten' % app, not fouten, fouten)
        ctx.close()

    print('\n== B. Pocket: in het voorbeeldscherm, in de taal van dat moment ==')
    ctx = nieuwe_context(b); pg = ctx.new_page(); pg.set_viewport_size({'width': 360, 'height': 780}); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(500)
    eis('pocket: geen regel zolang er niets te bewaren is', pg.evaluate("!document.getElementById('deel-waarschuwing')"))
    for taal, verwacht in [('nl', ROUTE_NL), ('en', ROUTE_EN)]:
        if taal == 'en':
            pg.evaluate('closePreview()'); pg.wait_for_timeout(200)
            pg.evaluate('toggleLang()')
        pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(300)
        for i in range(3): pg.evaluate('doTap()')
        with pg.expect_download(timeout=15000):
            pg.evaluate('stopTelling()')
        pg.wait_for_timeout(400)
        st = pg.evaluate(STAAT, 'preview-header')
        eis('pocket (%s): onder de kop met ZIP opslaan, zichtbaar, in het %s' % (taal, 'Nederlands' if taal == 'nl' else 'Engels'),
            st['onder'] and st['zichtbaar'] and (st['tekst'] or '').endswith(verwacht) and st['aantal'] == 1, st)
    eis('pocket: geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== C. Telreconstructie en telrapport ==')
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); ctx.route('**/*', route_met_osm)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
    for app, knop, nodig in [('telreconstructie.html', 'exportBtn', 'Begon hij thuis'),
                             ('telrapport.html', None, 'Begon een telling thuis')]:
        pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(500)
        if knop:
            st = pg.evaluate(STAAT, knop)
            eis('%s: direct onder de downloadknop' % app, st['onder'] and nodig in (st['tekst'] or ''), st)
        else:
            st = pg.evaluate("""() => { const w = document.getElementById('deel-waarschuwing');
              const v = w && w.previousElementSibling;
              return { na_gpkg: !!(v && v.querySelector('#export-gpkg-btn')), tekst: w ? w.textContent : null,
                       zichtbaar: !!(w && w.offsetParent !== null) }; }""")
            eis('%s: onder verzameling en GeoPackage, zichtbaar' % app, st['na_gpkg'] and st['zichtbaar'] and nodig in (st['tekst'] or ''), st)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()

print('\n== D. Privacyverklaring en handleiding ==')
ROOT_ = os.path.normpath(os.path.join(HIER, '..', '..'))
pv = open(os.path.join(ROOT_, 'privacy.html'), encoding='utf-8').read()
hl = open(os.path.join(ROOT_, 'traffic_counter_help.html'), encoding='utf-8').read()
eis('privacyverklaring: kopje "Een ZIP delen", en "Sharing a ZIP" in het Engelse deel',
    '<h2>Een ZIP delen</h2>' in pv and '<strong>Sharing a ZIP:</strong>' in pv)
eis('handleiding: sectie #delen, in de inhoudsopgave', 'id="delen"' in hl and 'href="#delen"' in hl)
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
