#!/usr/bin/env python3
"""v3.22 — één herstelmelding in de vijf veld-apps.

Tot v3.22 had elke soort app een eigen melding voor een herstelde telling: de
parkeer-apps een gele balk met een losse Doortellen-knop en zonder Weggooien,
pocket een blok met drie knoppen, Static een Engelse balk. Nu één gedeeld blok.

  A. Na een crash: in alle vijf dezelfde melding. Zelfde opbouw, zelfde tekst
     ("Onderbroken telling hersteld: 4 tikken, gestart uu:mm, laatst bewaard
     uu:mm."), dezelfde drie knoppen. Alleen de functies achter de knoppen
     verschillen per app.
  B. Weggooien: eerst een vraag. Nee: alles blijft. Ja: melding weg, kopie weg,
     de telling op de lijst van afgesloten tellingen, het scherm leeg, en na
     herladen geen melding meer.
  C. Een nieuwe telling terwijl de melding staat: eerst een vraag. Nee: alles
     blijft. Ja: de herstelde telling is weggegooid en de nieuwe loopt.
  D. Download ZIP vanuit de melding: parkeer-apps en Static slaan op, en daarna
     zijn melding en kopie weg. Pocket gaat naar zijn voorbeeldscherm.
  E. Static, gestopt maar niet opgeslagen (deelblad geannuleerd): "Afgeronde
     telling, nog niet opgeslagen", zonder Doortellen.
  F. Static: een tussentijdse ZIP laat de telling lopen en de kopie staan.
  G. Tekst in het Engels (pocket kent een taalknop) en tijden van een andere dag.
  H. Static is Nederlands en gebruikt het palet van telrapport.

Hulp (server, nep-Overpass, opslag bevriezen) komt uit hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/herstelmeldingtest.py
"""
import io, json, os, re, sys, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_hsrc = open(os.path.join(HIER, 'hersteltest.py'), encoding='utf-8').read()
exec(_hsrc.split('\nok = fout = 0\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
exec(_hsrc[_hsrc.index('LAT, LON = 51.8500'):_hsrc.index('with sync_playwright() as p:')])

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

TIK_STATIC = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
              "b[%d %% b.length].click()})()")
IPHONE = ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 '
          '(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')
ANNULEER = ("navigator.canShare=()=>true;"
            "navigator.share=()=>Promise.reject(new DOMException('geannuleerd','AbortError'));")

# naam, pagina, start, tik, aantal na herstel, sleutel, functie Doortellen
APPS = [
    ('parkeertelling', 'parkeertelling.html', 'startSession()', lambda i: "addEntry('goed','L')",
     'entries.length', 'parkeertelling_sessie', 'hervatSessie'),
    ('fietsparkeren', 'fietsparkeren.html', 'startSession()', lambda i: "addEntry('fiets','R')",
     'entries.length', 'fietsparkeren_sessie', 'hervatSessie'),
    ('capaciteit', 'capaciteitstelling.html', 'startSession()', lambda i: "addEntry('regulier','L')",
     'entries.length + terreinEntries.length', 'capaciteitstelling_sessie', 'hervatSessie'),
    ('pocket', 'pocket_count.html', 'startParkeren()', lambda i: "adjustParkeer('links_bezet',1)",
     'telCount', 'pocket_sessie', 'hervatTelling'),
    ('Static', 'traffic_counter.html', 'startSession()', lambda i: TIK_STATIC % i,
     "+document.getElementById('grand-total').textContent", 'static_sessie', 'doortellenStatic'),
]

MELDING = """(()=>{var e=document.getElementById('herstel-melding');
  if(!e||e.style.display==='none') return null;
  var k=[...e.querySelectorAll('button')];
  var vorm=e.innerHTML.replace(/onclick="[^"]*"/g,'').replace(/>[^<]*</g,'><');
  return {tekst:e.querySelector('p').textContent, knoppen:k.map(x=>x.textContent),
          acties:k.map(x=>x.getAttribute('onclick')), vorm:vorm}})()"""
AFGESLOTEN = "JSON.parse(localStorage.getItem('telsuite_afgesloten')||'[]')"


def telling(b, app, start, tik, n=4, init='', ua=None):
    """Telling met n tikken; geeft de bevroren opslag en het id van de telling."""
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True,
                        permissions=['geolocation'], user_agent=ua,
                        geolocation={'latitude': LAT, 'longitude': LON, 'accuracy': 5})
    ctx.route('**/*', route_met_osm)
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(600)
    pg.evaluate(start); pg.wait_for_timeout(500)
    loop(ctx, pg, n, tik)
    return ctx, pg


def herlaad(b, app, opslag, geo=True):
    """Nieuwe browser met de bevroren opslag; vragen worden beantwoord volgens
    antwoord['ja'] en bewaard in antwoord['vragen']."""
    ctx = nieuwe_context(b, geo)
    ctx.add_init_script("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');"
                        "var o=%s;for(var k in o)localStorage.setItem(k,o[k]);}" % opslag)
    pg = ctx.new_page(); fouten = []; antwoord = {'ja': True, 'vragen': []}
    pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
    def vraag(d):
        antwoord['vragen'].append(d.message)
        d.accept() if antwoord['ja'] else d.dismiss()
    pg.on('dialog', vraag)
    pg.goto(BASIS + app, wait_until='load'); pg.wait_for_timeout(900)
    return ctx, pg, fouten, antwoord


def knop(pg, label):
    """Klik de knop in de melding met dit label (de tekst, niet de CSS-hoofdletters)."""
    return pg.evaluate("(l)=>{var k=[...document.querySelectorAll('#herstel-melding button')]"
                       ".find(x=>x.textContent===l);if(!k)return false;k.click();return true}", label)


with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. na een crash: in alle vijf dezelfde melding ==')
    opslagen, vormen = {}, {}
    for naam, app, start, tik, aantal, sleutel, door in APPS:
        ctx, pg = telling(b, app, start, tik)
        opslagen[naam] = (bevries(pg), pg.evaluate("(()=>{var k=Object.keys(localStorage).find(x=>/_sessie$/.test(x));"
                                                   "var d=JSON.parse(localStorage.getItem(k));return d.telling})()"))
        ctx.close()
        ctx, pg, fouten, _ = herlaad(b, app, opslagen[naam][0])
        m = pg.evaluate(MELDING)
        eis('%s: melding zichtbaar' % naam, m is not None)
        if m is None:
            ctx.close(); continue
        patroon = r'^\u26a0\ufe0f Onderbroken telling hersteld( \([^)]+\))?: 4 tikken, gestart \d\d:\d\d, laatst bewaard \d\d:\d\d\.$'
        eis('%s: tekst "%s"' % (naam, m['tekst']), re.match(patroon, m['tekst']) is not None, m['tekst'])
        eis('%s: drie knoppen' % naam,
            m['knoppen'] == ['\u25b6 Doortellen', '\u2193 Download ZIP', '\u2715 Weggooien'], m['knoppen'])
        eis('%s: Doortellen roept %s() aan, Weggooien vraagt eerst (herstelWeg)' % (naam, door),
            m['acties'][0] == door + '()' and m['acties'][2] == 'herstelWeg()', m['acties'])
        vormen[naam] = m['vorm']
        eis('%s: aantal terug (4)' % naam, pg.evaluate(aantal) == 4, pg.evaluate(aantal))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()
    eis('alle vijf dezelfde opbouw en opmaak', len(set(vormen.values())) == 1 and len(vormen) == 5,
        {k: v[:80] for k, v in vormen.items()})

    print('\n== B. weggooien: eerst een vraag ==')
    for naam, app, start, tik, aantal, sleutel, door in APPS:
        opslag, id_ = opslagen[naam]
        ctx, pg, fouten, antwoord = herlaad(b, app, opslag)
        antwoord['ja'] = False
        knop(pg, '\u2715 Weggooien'); pg.wait_for_timeout(300)
        eis('%s: nee -> melding en kopie blijven' % naam,
            pg.evaluate(MELDING) is not None and pg.evaluate("localStorage.getItem(%r)!==null" % sleutel)
            and len(antwoord['vragen']) == 1 and 'weggooien' in antwoord['vragen'][0], antwoord['vragen'])
        antwoord['ja'] = True
        knop(pg, '\u2715 Weggooien'); pg.wait_for_timeout(400)
        eis('%s: ja -> melding weg, kopie weg, telling op de lijst' % naam,
            pg.evaluate(MELDING) is None and pg.evaluate("localStorage.getItem(%r)===null" % sleutel)
            and id_ in pg.evaluate(AFGESLOTEN), (pg.evaluate(MELDING), pg.evaluate(AFGESLOTEN), id_))
        eis('%s: het scherm is leeg (0)' % naam, pg.evaluate(aantal) == 0, pg.evaluate(aantal))
        pg.reload(wait_until='load'); pg.wait_for_timeout(800)
        eis('%s: na herladen geen melding' % naam, pg.evaluate(MELDING) is None)
        if naam in ('parkeertelling', 'Static'):
            antwoord['vragen'].clear()
            pg.evaluate(start); pg.wait_for_timeout(400)
            eis('%s: daarna gewoon Start, zonder vraag' % naam,
                not antwoord['vragen'] and pg.evaluate("typeof sessionActive!=='undefined'?sessionActive:state==='running'"),
                antwoord['vragen'])
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    print('\n== C. een nieuwe telling terwijl de melding staat ==')
    for naam, app, start, tik, aantal, sleutel, door in APPS:
        if naam == 'Static':
            continue   # Static: Start staat uit zolang de melding er is
        opslag, id_ = opslagen[naam]
        ctx, pg, fouten, antwoord = herlaad(b, app, opslag)
        antwoord['ja'] = False
        pg.evaluate(start); pg.wait_for_timeout(400)
        eis('%s: nee -> niets begonnen, melding en kopie blijven' % naam,
            pg.evaluate(MELDING) is not None and pg.evaluate(aantal) == 4
            and antwoord['vragen'] and 'Nieuwe telling starten?' in antwoord['vragen'][0]
            and '(4 tikken)' in antwoord['vragen'][0], antwoord['vragen'])
        antwoord['ja'] = True
        pg.evaluate(start); pg.wait_for_timeout(500)
        eis('%s: ja -> de herstelde telling is weggegooid, de nieuwe loopt' % naam,
            pg.evaluate(MELDING) is None and id_ in pg.evaluate(AFGESLOTEN) and pg.evaluate(aantal) == 0,
            (pg.evaluate(MELDING), pg.evaluate(AFGESLOTEN)))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()
    ctx, pg, fouten, _ = herlaad(b, 'traffic_counter.html', opslagen['Static'][0])
    eis('Static: Start staat uit zolang de melding er is', pg.evaluate("document.getElementById('btn-start').disabled"))
    ctx.close()

    print('\n== D. Download ZIP vanuit de melding ==')
    for naam, app, start, tik, aantal, sleutel, door in APPS:
        opslag, id_ = opslagen[naam]
        ctx, pg, fouten, _ = herlaad(b, app, opslag)
        if naam == 'pocket':
            knop(pg, '\u2193 Download ZIP'); pg.wait_for_timeout(1200)
            eis('pocket: melding weg, voorbeeldscherm', pg.evaluate(MELDING) is None and
                pg.evaluate("getComputedStyle(document.getElementById('preview-overlay')).display!=='none'"))
            ctx.close(); continue
        with pg.expect_download(timeout=15000) as d:
            knop(pg, '\u2193 Download ZIP')
        z = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
        pg.wait_for_timeout(400)
        regels = z.read([n for n in z.namelist() if n.endswith('_telregels.csv')][0]).decode('utf-8').splitlines()
        eis('%s: ZIP met de 4 herstelde tikken' % naam, len(regels) == 5, len(regels))
        eis('%s: opgeslagen -> melding weg, kopie weg' % naam,
            pg.evaluate(MELDING) is None and pg.evaluate("localStorage.getItem(%r)===null" % sleutel)
            and id_ in pg.evaluate(AFGESLOTEN))
        if naam == 'Static':
            eis('Static: de telling is afgerond, Start weer beschikbaar',
                pg.evaluate('state') == 'ended' and not pg.evaluate("document.getElementById('btn-start').disabled"))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    print('\n== E. Static: gestopt, ZIP niet opgeslagen ==')
    ctx, pg = telling(b, 'traffic_counter.html', 'startSession()', lambda i: TIK_STATIC % i, 3, ANNULEER, IPHONE)
    pg.evaluate('endSession()'); pg.wait_for_timeout(1500)
    eis('deelblad geannuleerd: status zegt "niet opgeslagen"',
        'niet opgeslagen' in pg.evaluate("document.getElementById('statusText').textContent"),
        pg.evaluate("document.getElementById('statusText').textContent"))
    opslag = bevries(pg); ctx.close()
    ctx, pg, fouten, _ = herlaad(b, 'traffic_counter.html', opslag)
    m = pg.evaluate(MELDING)
    eis('melding "Afgeronde telling, nog niet opgeslagen: 3 tikken, ... gestopt ..."',
        m and re.match(r'^\u26a0\ufe0f Afgeronde telling, nog niet opgeslagen: 3 tikken, gestart \d\d:\d\d, gestopt \d\d:\d\d\.$', m['tekst']),
        m and m['tekst'])
    eis('zonder Doortellen', m and m['knoppen'] == ['\u2193 Download ZIP', '\u2715 Weggooien'], m and m['knoppen'])
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== F. Static: tussentijdse ZIP ==')
    ctx, pg = telling(b, 'traffic_counter.html', 'startSession()', lambda i: TIK_STATIC % i, 3)
    with pg.expect_download(timeout=15000):
        pg.evaluate('exportZip()')
    pg.wait_for_timeout(400)
    eis('de telling loopt door en de kopie blijft',
        pg.evaluate('state') == 'running' and pg.evaluate("localStorage.getItem('static_sessie')!==null"))
    pg.evaluate(TIK_STATIC % 4); pg.wait_for_timeout(200)
    eis('en hij schrijft nog (4 tikken in de kopie)',
        len(json.loads(pg.evaluate("localStorage.getItem('static_sessie')"))['history']) == 4)
    ctx.close()

    print('\n== G. Engels, en een andere dag ==')
    ctx, pg, fouten, _ = herlaad(b, 'pocket_count.html', opslagen['pocket'][0])
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(100)
    pg.evaluate("herstelToon({n:1,start:'2026-10-15T10:05:00',laatst:new Date(2026,9,15,10,7),afgerond:true})")
    m = pg.evaluate(MELDING)
    eis('Engels: "Finished count, not saved yet: 1 tap, started Thu 15-10 10:05, ended Thu 15-10 10:07."',
        m and m['tekst'] == '\u26a0\ufe0f Finished count, not saved yet: 1 tap, started Thu 15-10 10:05, ended Thu 15-10 10:07.',
        m and m['tekst'])
    eis('Engels: knoppen', m and m['knoppen'] == ['\u2193 Download ZIP', '\u2715 Discard'], m and m['knoppen'])
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(100)
    eis('Nederlands, andere dag: "gestart do 15-10 10:05"',
        pg.evaluate("herstelTijd('2026-10-15 10:05:31')") == 'do 15-10 10:05')
    eis('vandaag: alleen de tijd', pg.evaluate("herstelTijd(new Date(new Date().setHours(9,4)))") == '09:04')
    eis('onleesbaar: een vraagteken', pg.evaluate("herstelTijd('gisteren')") == '?')
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== H. Static: Nederlands, palet van telrapport ==')
    ctx = nieuwe_context(b); pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120]))
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(500)
    tekst = pg.evaluate('document.body.innerText')
    eis('<html lang="nl">', pg.evaluate('document.documentElement.lang') == 'nl')
    eis('geen Engelse bediening meer', not re.search(r'Press Start|Counting|Undo Last|Export CSV|Reset\b|Location / Notes|Dir A', tekst),
        re.findall(r'Press Start|Counting|Undo Last|Export CSV|Reset\b|Location / Notes|Dir A', tekst))
    eis('Start, Stop, Download ZIP, ongedaan maken, Wissen',
        all(w in tekst.upper() for w in ['START', 'STOP', 'DOWNLOAD ZIP', 'ONGEDAAN MAKEN', 'WISSEN']))
    kleuren = pg.evaluate("TYPES.map(t=>getComputedStyle(document.querySelector('#card-'+t.id+' .btn-dir')).backgroundColor)")
    eis('kaartkleuren = telrapport (rood, oranje, geel, paars, magenta)',
        kleuren == ['rgb(204, 0, 0)', 'rgb(224, 120, 0)', 'rgb(230, 184, 0)', 'rgb(119, 0, 204)', 'rgb(212, 0, 122)'], kleuren)
    inkt = pg.evaluate("getComputedStyle(document.querySelector('#card-moto .btn-dir')).color")
    eis('donkere tekst op het geel van de motor', inkt == 'rgb(26, 25, 24)', inkt)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
