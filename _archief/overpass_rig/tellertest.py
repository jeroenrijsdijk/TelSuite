#!/usr/bin/env python3
"""v3.37 tellertest — de teller van telonline.org (teller/index.php) en de voorpagina.

Jay: "De echte wens is dat er op de voorpagina van telonline.org "Al 253
tellingen gedaan"." en "Dan dus een kleine eigen teller op de server. We staan
op 409 tellingen op dit moment."

De teller draait hier in de ingebouwde server van PHP (php -S), met de suite als
webmap en een opslagmap in een tijdelijke map (TELLER_MAP). Zonder PHP wordt de
test overgeslagen (en dat staat erbij).

  A. De server: begint op 409; een nieuwe vingerafdruk telt, dezelfde niet
     (ook niet in hoofdletters); onzin geeft 400, PUT 405; de rem geeft 429;
     twintig tegelijk tellen precies twintig; alleen vingerafdrukken bewaard,
     geen IP; de opslag is niet via de website te lezen; opslag in de webmap
     wordt geweigerd.
  B. De voorpagina: "Al 409 tellingen gedaan", in het Engels "409 counts so far";
     zonder teller staat er niets.
  C. Een telapp (Static, via bewaarZip): de telling telt mee, één keer; de
     voorpagina volgt.
  D. Niet meetellen: de knop in de privacyverklaring. Global Privacy Control telt
     niet (Jay: "GPC eruit, de knop blijft").
  E. Zonder verbinding: de vingerafdruk wacht en gaat mee bij het volgende openen.

Draaien vanuit de suite-root:  python3 _archief/overpass_rig/tellertest.py
"""
import concurrent.futures, hashlib, json, os, shutil, socket, subprocess, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request

ROOT = os.getcwd()
PHP = shutil.which('php')
if not PHP:
    print('PHP ontbreekt: tellertest overgeslagen')
    sys.exit(0)

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

def vrije_poort():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def start(map_, max_per_uur=1000, werkers=1):
    poort = vrije_poort()
    env = dict(os.environ, TELLER_MAP=map_, TELLER_MAX_PER_UUR=str(max_per_uur))
    if werkers > 1: env['PHP_CLI_SERVER_WORKERS'] = str(werkers)   # echt tegelijk, zodat flock iets te doen heeft
    p = subprocess.Popen([PHP, '-S', '127.0.0.1:%d' % poort, '-t', ROOT], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    basis = 'http://127.0.0.1:%d/' % poort
    for _ in range(50):
        try: urllib.request.urlopen(basis + 'robots.txt', timeout=1); break
        except Exception: time.sleep(0.1)
    return p, basis

def vraag(basis, methode='GET', h=None, pad='teller/'):
    data = urllib.parse.urlencode({'h': h}).encode() if h is not None else None
    req = urllib.request.Request(basis + pad, data=data, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b'null'), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read()
        try: body = json.loads(body)
        except Exception: body = body[:80]
        return e.code, body, dict(e.headers)

sha = lambda t: hashlib.sha256(t.encode()).hexdigest()
vinger = lambda naam: sha('telonline.org teller ' + naam[:-4] if naam.endswith('.zip') else 'telonline.org teller ' + naam)

print('== A. De server ==')
r = subprocess.run([PHP, '-l', 'teller/index.php'], capture_output=True, text=True)
eis('php -l: geen fouten', r.returncode == 0, r.stdout + r.stderr)
tmp = tempfile.mkdtemp(prefix='teller_')
p, B = start(os.path.join(tmp, 'opslag'), max_per_uur=4)
try:
    st, d, _ = vraag(B)
    eis('GET: {"tellingen": 409}, het begin', (st, d) == (200, {'tellingen': 409}), (st, d))
    h1 = sha('een')
    st, d, _ = vraag(B, 'POST', h1)
    eis('een nieuwe vingerafdruk: 410, nieuw', (st, d) == (200, {'tellingen': 410, 'nieuw': True}), (st, d))
    st, d, _ = vraag(B, 'POST', h1)
    eis('dezelfde nog eens: 410, niet nieuw', (st, d) == (200, {'tellingen': 410, 'nieuw': False}), (st, d))
    st, d, _ = vraag(B, 'POST', h1.upper())
    eis('in hoofdletters: dezelfde', d == {'tellingen': 410, 'nieuw': False}, d)
    for onzin in ['', 'abc', 'g' * 64, h1 + '0', '../' + h1[:61]]:
        st, d, _ = vraag(B, 'POST', onzin)
        if st != 400: break
    eis('onzin (leeg, te kort, geen hex, te lang, een pad): 400', st == 400, (onzin, st, d))
    st, d, hd = vraag(B, 'PUT', h1)
    eis('PUT: 405, met Allow: GET, POST', st == 405 and hd.get('Allow') == 'GET, POST', (st, hd.get('Allow')))
    for i in range(3): vraag(B, 'POST', sha('rem%d' % i))
    st, d, hd = vraag(B, 'POST', sha('rem-te-veel'))
    eis('de rem (hier 4 per uur): de vijfde nieuwe in een uur krijgt 429, en telt niet', st == 429 and d.get('tellingen') == 413 and hd.get('Retry-After') == '3600', (st, d))
    st, d, _ = vraag(B, 'POST', h1)
    eis('een bekende vingerafdruk gaat niet tegen de rem in', (st, d) == (200, {'tellingen': 413, 'nieuw': False}), (st, d))
    st, d, _ = vraag(B, 'GET', pad='teller/gezien.txt')
    eis('de lijst is niet via de website te lezen (404)', st == 404, st)
    st, d, hd = vraag(B)
    eis('GET mag een minuut in de cache', 'max-age=60' in hd.get('Cache-Control', ''), hd.get('Cache-Control'))
finally:
    p.terminate(); p.wait()
opslag = os.path.join(tmp, 'opslag')
inhoud = open(os.path.join(opslag, 'gezien.txt')).read()
eis('in de opslag: alleen vingerafdrukken, één per regel (4 stuks)', inhoud.splitlines() == [h1] + [sha('rem%d' % i) for i in range(3)], inhoud.splitlines())
alles = ''.join(open(os.path.join(opslag, f)).read() for f in os.listdir(opslag))
eis('geen IP-adres bewaard', '127.0.0.1' not in alles and sorted(os.listdir(opslag)) == ['gezien.txt', 'recent.txt'], sorted(os.listdir(opslag)))

# Tien keer, elke keer met een opslagmap die er nog niet is: de eerste verzoeken
# komen dan tegelijk bij een lege server. Zonder de tweede is_dir na mkdir gaf
# dat soms een 503 (gevonden in de eerste ronde van v3.37).
uitslag = []
for ronde in range(10):
    p, B = start(os.path.join(tmp, 'druk%d' % ronde), werkers=4)
    try:
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            rs = list(ex.map(lambda i: vraag(B, 'POST', sha('tegelijk%d' % i)), range(20)))
        uitslag.append((sorted({(st, json.dumps(d)) for st, d, _ in rs if st != 200 or d.get('nieuw') is not True}), vraag(B)[1]))
    finally:
        p.terminate(); p.wait()
eis('twintig nieuwe tegelijk op een lege server (4 PHP-werkers, 10 keer): elk antwoord 200 en nieuw, precies 429 tellingen',
    all(x == ([], {'tellingen': 429}) for x in uitslag), uitslag)
binnen = os.path.join(ROOT, 'teller', '_test_opslag')
p, B = start(binnen)
try:
    st, d, _ = vraag(B)
    eis('opslag in de webmap: geweigerd (503), niets op straat', st == 503 and 'webmap' in str(d), (st, d))
finally:
    p.terminate(); p.wait(); shutil.rmtree(binnen, ignore_errors=True)

# ── De browser ───────────────────────────────────────────────────────────────
from playwright.sync_api import sync_playwright
NM = next((x for x in [os.environ.get('TEL_NODE_MODULES', ''), os.path.join(ROOT, 'node_modules'),
                       '/home/claude/node_modules'] if x and os.path.isdir(x)), None)
LIB = {'leaflet.min.js': 'leaflet/dist/leaflet.js', 'leaflet.js': 'leaflet/dist/leaflet.js',
       'jszip.min.js': 'jszip/dist/jszip.min.js', 'papaparse.min.js': 'papaparse/papaparse.min.js'}
p, B = start(os.path.join(tmp, 'browser'))
def route(r):
    u = r.request.url
    if u.startswith(B): return r.continue_()
    naam = u.split('?')[0].rsplit('/', 1)[-1]
    if NM and naam in LIB:
        return r.fulfill(body=open(os.path.join(NM, LIB[naam]), 'rb').read(), content_type='application/javascript')
    return r.abort()
TELLER = "() => { const t = document.getElementById('teller'); return t.hidden ? null : t.textContent; }"
def bewaar(pg, naam):
    """Een ZIP opslaan in Static, zoals de app het doet (bewaarZip), en wachten op de teller."""
    pg.evaluate("n => bewaarZip(new Blob(['PK'], { type: 'application/zip' }), n)", naam)
def aantal(): return vraag(B)[1]['tellingen']

try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        print('\n== B. De voorpagina ==')
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, locale='nl-NL', accept_downloads=True); ctx.route('**/*', route)
        pg = ctx.new_page(); fouten = []
        pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
        pg.goto(B + 'index.html', wait_until='load'); pg.wait_for_function("!document.getElementById('teller').hidden", timeout=5000)
        eis('NL: "Al 409 tellingen gedaan"', pg.evaluate(TELLER) == 'Al 409 tellingen gedaan', pg.evaluate(TELLER))
        pg.click('.lang-btn[data-lang="en"]')
        eis('EN: "409 counts so far"', pg.evaluate(TELLER) == '409 counts so far', pg.evaluate(TELLER))
        pg.click('.lang-btn[data-lang="nl"]')
        eis('de regel staat onder de titel, boven de introductie', pg.evaluate(
            "document.getElementById('teller').getBoundingClientRect().bottom <= document.querySelector('.intro-note').getBoundingClientRect().top + 1"))

        print('\n== C. Een telling telt mee, één keer ==')
        app = ctx.new_page(); app.on('pageerror', lambda e: fouten.append(e.message[:160]))
        app.goto(B + 'traffic_counter.html', wait_until='load'); app.wait_for_timeout(300)
        with app.expect_response(lambda r: r.url == B + 'teller/' and r.request.method == 'POST') as resp:
            bewaar(app, '20261025_120000_tst_sta.zip')
        verzoek = resp.value.request
        eis('bij het opslaan: één POST naar /teller/ met alleen h = de vingerafdruk van de ZIP-naam',
            urllib.parse.parse_qs(verzoek.post_data) == {'h': [vinger('20261025_120000_tst_sta.zip')]}, verzoek.post_data)
        eis('de teller staat op 410', aantal() == 410)
        with app.expect_response(lambda r: r.url == B + 'teller/' and r.request.method == 'POST'):
            bewaar(app, '20261025_120000_tst_sta.zip')
        eis('dezelfde telling nog eens opgeslagen: blijft 410', aantal() == 410)
        pg.reload(wait_until='load'); pg.wait_for_function("!document.getElementById('teller').hidden", timeout=5000)
        eis('de voorpagina volgt: "Al 410 tellingen gedaan"', pg.evaluate(TELLER) == 'Al 410 tellingen gedaan', pg.evaluate(TELLER))
        eis('niets blijft wachten', app.evaluate("localStorage.getItem('telsuite_teller_wacht')") is None)

        print('\n== D. Niet meetellen ==')
        pr = ctx.new_page(); pr.goto(B + 'privacy.html', wait_until='load')
        knop = pr.locator('.teller-knop[data-taal="nl"]')
        eis('privacyverklaring: "Op dit toestel niet meetellen", "Dit toestel telt mee."',
            knop.inner_text() == 'Op dit toestel niet meetellen' and pr.inner_text('.teller-stand[data-taal="nl"]') == 'Dit toestel telt mee.')
        knop.click()
        eis('na de klik: uitgezet, en de knop zegt "weer meetellen" (ook de Engelse)',
            pr.evaluate("localStorage.getItem('telsuite_niet_tellen')") == '1' and knop.inner_text() == 'Op dit toestel weer meetellen'
            and pr.inner_text('.teller-knop[data-taal="en"]') == 'Count on this device again')
        posts = []
        app.on('request', lambda r: posts.append(r.url) if r.url == B + 'teller/' and r.method == 'POST' else None)
        bewaar(app, '20261025_130000_uit_sta.zip'); app.wait_for_timeout(800)
        eis('uitgezet: een nieuwe telling stuurt niets en telt niet', posts == [] and aantal() == 410, posts)
        knop.click()
        eis('weer aangezet', pr.evaluate("localStorage.getItem('telsuite_niet_tellen')") is None and knop.inner_text() == 'Op dit toestel niet meetellen')
        ctx2 = b.new_context(locale='nl-NL', accept_downloads=True); ctx2.route('**/*', route)
        ctx2.add_init_script("Object.defineProperty(Navigator.prototype, 'globalPrivacyControl', { get: () => true });")
        g = ctx2.new_page(); gposts = []
        g.on('request', lambda r: gposts.append(r.url) if r.url == B + 'teller/' and r.method == 'POST' else None)
        g.goto(B + 'traffic_counter.html', wait_until='load'); g.wait_for_timeout(300)
        with g.expect_response(lambda r: r.url == B + 'teller/' and r.request.method == 'POST'):
            bewaar(g, '20261025_140000_gpc_sta.zip')
        eis('Global Privacy Control telt niet (Jay: "GPC eruit, de knop blijft"): verstuurd en geteld (411)', len(gposts) == 1 and aantal() == 411, [gposts, aantal()])
        g.goto(B + 'privacy.html', wait_until='load')
        eis('de privacyverklaring: "Dit toestel telt mee.", en over GPC geen woord',
            g.inner_text('.teller-stand[data-taal="nl"]') == 'Dit toestel telt mee.' and 'Global Privacy Control' not in g.content())
        ctx2.close()

        print('\n== E. Zonder verbinding ==')
        ctx.set_offline(True)
        bewaar(app, '20261025_150000_off_sta.zip'); app.wait_for_timeout(800)
        wacht = json.loads(app.evaluate("localStorage.getItem('telsuite_teller_wacht')") or '[]')
        eis('offline: de vingerafdruk wacht in deze browser', wacht == [vinger('20261025_150000_off_sta.zip')] and aantal() == 411, wacht)
        ctx.set_offline(False)
        with app.expect_response(lambda r: r.url == B + 'teller/' and r.request.method == 'POST', timeout=15000):
            app.reload(wait_until='load')
        app.wait_for_timeout(300)
        eis('weer online, de app opnieuw open: alsnog geteld (412), en er wacht niets meer',
            aantal() == 412 and app.evaluate("localStorage.getItem('telsuite_teller_wacht')") is None, [aantal(), app.evaluate("localStorage.getItem('telsuite_teller_wacht')")])
        eis('geen JS-fouten', not fouten, fouten)
        ctx.close()

        print('\n== B2. Zonder teller ==')
        ctx3 = b.new_context(); ctx3.route('**/*', lambda r: r.fulfill(status=404, body='') if r.request.url.startswith(B + 'teller/') else route(r))
        q = ctx3.new_page(); q.goto(B + 'index.html', wait_until='load'); q.wait_for_timeout(500)
        eis('geen teller (404): de voorpagina laat de regel weg', q.evaluate(TELLER) is None)
        ctx3.close(); b.close()
finally:
    p.terminate(); p.wait()
    shutil.rmtree(tmp, ignore_errors=True)
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
