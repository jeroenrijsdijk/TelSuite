#!/usr/bin/env python3
"""v3.30 vingerafdruktest — de SHA-256 van de ZIP na het opslaan, in Chromium.

Uit verantwoording.html (v3.4), bewijswaarde punt 1: de vingerafdruk van de ZIP
tonen, met een knop die een mail met de code opent. Jay: "Je mag de 5 punten
repareren."

  A. In de vijf veld-apps (parkeertelling, fietsparkeren, capaciteitstelling,
     Static, pocket): na het opslaan staat onder de deelwaarschuwing de
     SHA-256 van precies het bestand dat de browser kreeg (nagerekend met
     hashlib), met de bestandsnaam; de mail-link heeft de naam, de code en hoe
     je controleert. Eén regel, ook na een tweede ZIP.
  B. Pocket in het Engels: de regel en de mail in het Engels.
  C. Zonder crypto.subtle: geen regel, geen fout, de ZIP komt er gewoon.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit hersteltest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/vingerafdruktest.py
"""
import hashlib, os, sys
from urllib.parse import unquote
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

REGEL = """() => { const v = document.getElementById('vingerafdruk'), w = document.getElementById('deel-waarschuwing');
  const a = v && v.querySelector('a');
  return v ? { code: v.getAttribute('data-sha256'), tekst: v.textContent, href: a ? a.getAttribute('href') : '',
               onder: !!(w && w.nextElementSibling === v), aantal: document.querySelectorAll('#vingerafdruk').length } : null; }"""
TIK_STATIC = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
              "b[%d %% b.length].click()})()")
APPS = [('parkeertelling.html', 'startSession()', "addEntry('goed','L')", 'exportZip()'),
        ('fietsparkeren.html', 'startSession()', "addEntry('fiets','R')", 'exportZip()'),
        ('capaciteitstelling.html', 'startSession()', "addEntry('regulier','L')", 'exportZip()'),
        ('traffic_counter.html', 'startSession()', None, 'exportZip()'),
        ('pocket_count.html', "startTelling('car','x','Auto')", 'doTap()', 'stopTelling()')]

def tel_en_bewaar(ctx, pg, start, tik, bewaar, n=3):
    pg.evaluate(start); pg.wait_for_timeout(600)
    for i in range(n):
        ctx.set_geolocation({'latitude': LAT + i * 0.0001, 'longitude': LON, 'accuracy': 5})
        pg.wait_for_timeout(250)
        pg.evaluate(tik if tik else TIK_STATIC % i)
    with pg.expect_download(timeout=20000) as d:
        pg.evaluate(bewaar)
    pad = os.path.join('/tmp', 'vinger_' + d.value.suggested_filename); d.value.save_as(pad)
    pg.wait_for_function("!!document.getElementById('vingerafdruk')", timeout=10000)
    return d.value.suggested_filename, hashlib.sha256(open(pad, 'rb').read()).hexdigest()

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. Na het opslaan: de vingerafdruk van het bestand ==')
    for app, start, tik, bewaar in APPS:
        ctx = nieuwe_context(b); pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
        pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(600)
        naam, sha = tel_en_bewaar(ctx, pg, start, tik, bewaar)
        r = pg.evaluate(REGEL)
        eis('%s: de code is de SHA-256 van het gedownloade bestand' % app, r and r['code'] == sha, (r and r['code'], sha))
        eis('%s: onder de deelwaarschuwing, met naam en code in beeld' % app,
            r and r['onder'] and naam in r['tekst'] and sha in r['tekst'] and r['tekst'].startswith('Vingerafdruk (SHA-256) van'), r)
        mail = unquote(r['href']) if r else ''
        eis('%s: mail-link met naam, code en hoe je controleert' % app,
            mail.startswith('mailto:?subject=Vingerafdruk telling ' + naam) and sha in mail and 'certutil -hashfile' in mail
            and 'shasum -a 256' in mail, mail[:200])
        if app == 'traffic_counter.html':
            for i in range(2): pg.evaluate(TIK_STATIC % (i + 5))
            with pg.expect_download(timeout=20000) as d:
                pg.evaluate(bewaar)
            pad = os.path.join('/tmp', 'vinger2_' + d.value.suggested_filename); d.value.save_as(pad)
            sha2 = hashlib.sha256(open(pad, 'rb').read()).hexdigest()
            pg.wait_for_function("document.getElementById('vingerafdruk').getAttribute('data-sha256') === %r" % sha2, timeout=10000)
            eis('%s: een tweede ZIP vervangt de regel (één regel, de nieuwe code)' % app,
                pg.evaluate(REGEL)['aantal'] == 1 and sha2 != sha, (pg.evaluate(REGEL)['aantal'], sha2 == sha))
        eis('%s: geen JS-fouten' % app, not fouten, fouten)
        ctx.close()

    print('\n== B. Pocket in het Engels ==')
    ctx = nieuwe_context(b); pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(500)
    pg.evaluate('toggleLang()')
    naam, sha = tel_en_bewaar(ctx, pg, "startTelling('car','x','Auto')", 'doTap()', 'stopTelling()')
    r = pg.evaluate(REGEL)
    mail = unquote(r['href'])
    eis('pocket (en): Engelse regel en mail, zelfde code',
        r['code'] == sha and r['tekst'].startswith('Fingerprint (SHA-256) of') and 'Mail this code to yourself' in r['tekst']
        and mail.startswith('mailto:?subject=Fingerprint of count ' + naam) and 'To check:' in mail, (r['tekst'][:80], mail[:80]))
    eis('pocket (en): geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== C. Zonder crypto.subtle ==')
    ctx = nieuwe_context(b)
    ctx.add_init_script("Object.defineProperty(Crypto.prototype, 'subtle', { get: function () { return undefined; } });")
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'parkeertelling.html', wait_until='load'); pg.wait_for_timeout(600)
    pg.evaluate('startSession()'); pg.wait_for_timeout(600)
    pg.evaluate("addEntry('goed','L')")
    with pg.expect_download(timeout=20000) as d:
        pg.evaluate('exportZip()')
    pg.wait_for_timeout(800)
    eis('geen crypto.subtle: de ZIP komt er, zonder regel en zonder fout',
        d.value.suggested_filename.endswith('.zip') and pg.evaluate("!document.getElementById('vingerafdruk')") and not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
