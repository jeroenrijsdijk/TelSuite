#!/usr/bin/env python3
"""v3.23 — Static: GPS luisteren en middelen.

Jay: "Die 20m ondergrens gps preciesie zou ik nog wel wat fijner willen, maar
als je echt geen goede gps heb, wil je toch graag een keer gaan tellen. De
wachttijd mag niet te lang oplopen." En: "grenzen van 8m en 15m. 3 minuten
luisteren is prima".

  A. De schatter (gpsSchatting) los, met nagebootste metingen en vaste ruis:
     middelen wordt beter dan één meting; een uitschieter telt niet; wie na
     Start nog naar zijn plek loopt, komt op zijn plek uit; twee metingen kort
     na elkaar zijn niet beter dan één; nooit beter dan 3 m; de niveaus.
  B. De app met een versnelde klok: tellen kan vanaf Start, zonder positie; de
     plek wordt beter en telt af; na 3 minuten stopt het luisteren; de ZIP
     draagt het gemiddelde en de echte grens (15 m).
  C. Een goede GPS: eerder klaar dan 3 minuten.
  D. Een slechte GPS: grof, maar de telling loopt gewoon; "No (> 15m".
  E. Stop voor de 3 minuten om zijn: de schatting van dat moment gaat mee.
  F. Het adres: pas opzoeken als de plek redelijk is, opnieuw na 15 m
     verschuiving, en na een mislukt verzoek 30 s pauze.
  G. Geen toestemming voor GPS: tellen gaat gewoon.

Draaien vanuit de suite-root:  python3 _archief/overpass_rig/gpsmiddeltest.py
"""
import io, json, math, os, re, sys, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HIER, 'laadtest.py'), encoding='utf-8').read()
exec(_src.split('ok = fout = 0')[0])             # ROOT, NM, route, srv, BASIS
from playwright.sync_api import sync_playwright

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:300]))

LAT, LON = 51.8500, 4.3000
KX, KY = 111320 * math.cos(math.radians(LAT)), 110540
def verschuif(dx, dy):           # meters oost, noord -> lat, lon
    return LAT + dy / KY, LON + dx / KX

TIK = ("(()=>{var b=[...document.querySelectorAll('[onclick^=\"adjust(\"]')].filter(b=>!/-1\\)/.test(b.getAttribute('onclick')));"
       "b[%d %% b.length].click()})()")

# Vaste ruis (zelfde reeks bij elke run), gemaakt in de pagina.
RUIS = """
  function rng(z){ return function(){ z = (z * 1664525 + 1013904223) % 4294967296; return z / 4294967296; }; }
  function normaal(r){ return Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r()); }
  var KX = 111320 * Math.cos(LAT * Math.PI / 180), KY = 110540;
  function punt(dx, dy, t, acc){ return { t: t, lat: LAT + dy / KY, lon: LON + dx / KX, acc: acc }; }
  function afst(p){ return Math.hypot((p.lon - LON) * KX, (p.lat - LAT) * KY); }
"""

def schatting(pg, scenario):
    return pg.evaluate("(()=>{var LAT=%f,LON=%f;%s%s})()" % (LAT, LON, RUIS, scenario))


def app(b, init='', geo=True, adres=None):
    """Static met een nep-klok, nep-GPS en een nep-Nominatim. adres: lijst die
    elke aanvraag bewaart; de antwoorden volgen adres_antwoord."""
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True,
                        permissions=['geolocation'] if geo else [],
                        # de eerste meting die de browser geeft: 32 m ernaast en grof
                        geolocation=dict(zip(('latitude', 'longitude'), verschuif(25, -20)), accuracy=30) if geo else None)
    def r(rt):
        u = rt.request.url
        if 'nominatim' in u:
            if adres is not None:
                adres.append(u)
                if adres_antwoord.get('fout'):
                    return rt.abort()
                return rt.fulfill(body=json.dumps({'address': {'road': 'Voorstraat', 'house_number': str(len(adres)),
                                                              'town': 'Spijkenisse', 'country': 'Nederland'}}),
                                  content_type='application/json')
            return rt.abort()
        return route(rt)
    ctx.route('**/*', r)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:120])); pg.on('dialog', lambda d: d.accept())
    pg.clock.install()
    if init: pg.add_init_script(init)
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(300)
    return ctx, pg, fouten

adres_antwoord = {}

def meet(ctx, pg, dx, dy, acc, s=1):
    """Eén GPS-meting op (dx, dy) meter van het telpunt, dan s seconden verder."""
    la, lo = verschuif(dx, dy)
    ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': acc})
    pg.wait_for_timeout(30)
    pg.clock.run_for(s * 1000)

NAUW = "document.getElementById('disp-nauw').textContent"
PLEK = "document.getElementById('disp-gps').textContent"

def zip_lees(d):
    z = zipfile.ZipFile(io.BytesIO(open(d.value.path(), 'rb').read()))
    lees = lambda suf: z.read([n for n in z.namelist() if n.endswith(suf)][0]).decode('utf-8')
    kop, rij = lees('_sessie.csv').splitlines()[:2]
    return dict(zip(kop.split(';'), rij.split(';'))), lees('_overzicht.csv').splitlines()


with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. de schatter los ==')
    ctx = b.new_context(); pg = ctx.new_page(); pg.route('**/*', route)
    pg.goto(BASIS + 'traffic_counter.html', wait_until='load'); pg.wait_for_timeout(300)
    r = schatting(pg, """
      var g = rng(7), m = [];
      for (var i = 0; i <= 120; i++) m.push(punt(6 * normaal(g), 6 * normaal(g), i * 1000, 8));
      var s1 = gpsSchatting(m.slice(0, 1), 0), s = gpsSchatting(m, 120000);
      return { een: afst(m[0]), eenSigma: s1.sigma, fout: afst(s), sigma: s.sigma, n: s.n };""")
    eis('2 minuten ruis van ±6 m: het gemiddelde ligt binnen 3 m (één meting: %.1f m, gemiddelde: %.1f m)' % (r['een'], r['fout']),
        r['fout'] <= 3, r)
    eis('de opgegeven afwijking daalt van ±8 m naar ±%.1f m, en is eerlijk (niet kleiner dan de echte fout)' % r['sigma'],
        r['eenSigma'] == 8 and 3 <= r['sigma'] <= 6 and r['sigma'] >= r['fout'], r)

    r = schatting(pg, """
      var g = rng(11), m = [];
      for (var i = 0; i <= 60; i++) m.push(punt(4 * normaal(g), 4 * normaal(g), i * 1000, 6));
      var zonder = gpsSchatting(m, 60000);
      m.push(punt(60, -40, 60500, 10));
      var met = gpsSchatting(m, 60500);
      return { verschil: Math.hypot((met.lon - zonder.lon) * KX, (met.lat - zonder.lat) * KY), nz: zonder.n, nm: met.n };""")
    eis('een uitschieter van 72 m telt niet mee (verschuiving %.2f m)' % r['verschil'], r['verschil'] < 0.01 and r['nm'] == r['nz'], r)

    r = schatting(pg, """
      var g = rng(3), m = [], t = 0;
      for (var i = 0; i < 20; i++, t += 1000) m.push(punt(40 - 2 * i, 0, t, 6));          // 20 s lopen naar de plek
      for (var j = 0; j < 100; j++, t += 1000) m.push(punt(3 * normaal(g), 3 * normaal(g), t, 6));
      var s = gpsSchatting(m, t - 1000);
      return { fout: afst(s), sigma: s.sigma };""")
    eis('na Start nog 40 m lopen: de schatting komt op de plek uit (%.1f m)' % r['fout'], r['fout'] <= 2.5, r)

    r = schatting(pg, """
      var m = [punt(0, 0, 0, 10), punt(1, 0, 1000, 10)];
      return gpsSchatting(m, 1000).sigma;""")
    eis('twee metingen 1 s na elkaar zijn niet beter dan één (±%.1f m)' % r, abs(r - 10) < 0.01, r)

    r = schatting(pg, """
      var g = rng(5), m = [];
      for (var i = 0; i <= 120; i++) m.push(punt(normaal(g), normaal(g), i * 1000, 2));
      return gpsSchatting(m, 120000).sigma;""")
    eis('nooit beter dan 3 m (zeer goede GPS: %.1f)' % r, r == 3, r)

    r = schatting(pg, """
      var g = rng(17), m = [];
      for (var i = 0; i <= 120; i++) m.push(punt(9 * normaal(g), 9 * normaal(g), i * 1000, 3));
      var s = gpsSchatting(m, 120000);
      return { sigma: s.sigma, n: s.n, fout: afst(s) };""")
    eis('GPS te gunstig over zichzelf (±3 m opgegeven, ±9 m echt): de echte spreiding telt (±%.1f m, %d van 121 metingen)'
        % (r['sigma'], r['n']), r['sigma'] >= 5 and r['n'] >= 115 and r['sigma'] >= r['fout'], r)

    r = schatting(pg, "return gpsSchatting([punt(0, 0, 0, 10)], 130000);")
    eis('metingen ouder dan 2 minuten tellen niet', r is None, r)
    niv = pg.evaluate("[8, 9, 15, 16].map(gpsNiveau)")
    eis('niveaus: 8 nauwkeurig, 9 en 15 redelijk, 16 grof', niv == ['nauwkeurig', 'redelijk', 'redelijk', 'grof'], niv)
    ctx.close()

    print('\n== B. de app: tellen meteen, de plek wordt beter ==')
    adressen = []; adres_antwoord.clear()
    ctx, pg, fouten = app(b, adres=adressen)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    for i in range(3): pg.evaluate(TIK % i)
    eis('tellen kan vanaf Start, nog zonder positie (3 tikken)',
        pg.evaluate("document.getElementById('grand-total').textContent") == '3')
    import random
    rnd = random.Random(42)
    meet(ctx, pg, 25, -20, 30)                                  # eerste meting: ver weg, grof
    eis('eerste meting: grof, "wordt beter, nog 2:5x"', re.match(r'^±\d+ m · grof · wordt beter, nog 2:5\d$', pg.evaluate(NAUW)),
        pg.evaluate(NAUW))
    eis('GPS-stip zoekt nog', 'searching' in pg.evaluate("document.getElementById('gpsDot').className"))
    for i in range(80):
        meet(ctx, pg, rnd.gauss(0, 7), rnd.gauss(0, 7), 12)
    na80 = pg.evaluate("[gpsLocation.accuracy, gpsLuistert()]")
    eis('na 80 s ±12 m-metingen: beter dan één meting (±%d m), nog aan het luisteren' % na80[0],
        na80[0] < 12 and na80[1], na80)
    pg.clock.run_for(110 * 1000)
    eis('na 3 minuten klaar met luisteren', not pg.evaluate('gpsLuistert()') and pg.evaluate('gpsLocation.klaar'))
    eis('daarna geen "wordt beter" meer', 'wordt beter' not in pg.evaluate(NAUW), pg.evaluate(NAUW))
    g = pg.evaluate("gpsLocation")
    fout_m = math.hypot((g['lon'] - LON) * KX, (g['lat'] - LAT) * KY)
    eis('het gemiddelde ligt binnen %d m van het telpunt (%.1f m)' % (g['accuracy'], fout_m), fout_m <= g['accuracy'], g)
    eis('één adresverzoek; de straat op z\'n Nederlands ("Voorstraat 1, Spijkenisse")',
        len(adressen) == 1 and pg.evaluate(PLEK) == 'Voorstraat 1, Spijkenisse',
        (adressen, pg.evaluate(PLEK)))
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()'); pg.clock.run_for(1000)
    ses, ovz = zip_lees(d)
    eis('_sessie: positie en nauwkeurigheid zijn het gemiddelde',
        ses['lat'] == '%.6f' % g['lat'] and ses['lon'] == '%.6f' % g['lon'] and ses['nauwkeurigheid'] == str(g['accuracy']), (ses, g))
    betr = [x for x in ovz if x.startswith('GPS reliable;')]
    verwacht = 'GPS reliable;Yes (<= 15m)' if g['accuracy'] <= 15 else 'GPS reliable;No (> 15m, best available)'
    eis('overzicht: de echte grens (%s)' % verwacht, betr == [verwacht], betr)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== C. een goede GPS: eerder klaar ==')
    ctx, pg, fouten = app(b)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    rnd = random.Random(1)
    t = 0
    while pg.evaluate('gpsLuistert()') and t < 200:
        meet(ctx, pg, rnd.gauss(0, 2), rnd.gauss(0, 2), 4); t += 1
    eis('±4 m-metingen: klaar na %d s (binnen 2 minuten), ±%d m nauwkeurig' % (t, pg.evaluate('gpsLocation.accuracy')),
        t <= 120 and pg.evaluate('gpsLocation.accuracy') <= 4 and 'nauwkeurig' in pg.evaluate(NAUW), (t, pg.evaluate(NAUW)))
    eis('GPS-stip groen tijdens het tellen', pg.evaluate("document.getElementById('gpsDot').className") == 'gps-dot active')
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== D. een slechte GPS: grof, maar tellen gaat door ==')
    ctx, pg, fouten = app(b)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    rnd = random.Random(9)
    for i in range(185):
        meet(ctx, pg, rnd.gauss(0, 30), rnd.gauss(0, 30), 60)
        if i % 30 == 0: pg.evaluate(TIK % i)
    eis('na 3 minuten met ±60 m: grof (%s)' % pg.evaluate(NAUW),
        not pg.evaluate('gpsLuistert()') and pg.evaluate(NAUW).endswith('grof'), pg.evaluate(NAUW))
    eis('de telling liep gewoon (7 tikken)', pg.evaluate("document.getElementById('grand-total').textContent") == '7')
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()'); pg.clock.run_for(1000)
    ses, ovz = zip_lees(d)
    eis('overzicht: No (> 15m, best available)', 'GPS reliable;No (> 15m, best available)' in ovz,
        [x for x in ovz if x.startswith('GPS reliable')])
    eis('_sessie: nauwkeurigheid > 15', int(ses['nauwkeurigheid']) > 15, ses['nauwkeurigheid'])
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== E. Stop voor de 3 minuten om zijn ==')
    ctx, pg, fouten = app(b)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    rnd = random.Random(4)
    for i in range(40):
        meet(ctx, pg, rnd.gauss(0, 6), rnd.gauss(0, 6), 10)
    pg.evaluate(TIK % 0)
    voor = pg.evaluate('gpsLocation')
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()'); pg.clock.run_for(1000)
    ses, _ = zip_lees(d)
    eis('na 40 s gestopt: luisteren uit, de schatting van dat moment in de ZIP',
        not pg.evaluate('gpsLuistert()') and ses['lat'] == '%.6f' % voor['lat'] and ses['nauwkeurigheid'] == str(voor['accuracy']),
        (ses, voor))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== F. het adres ==')
    adressen = []; adres_antwoord.clear()
    ctx, pg, fouten = app(b, adres=adressen)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    for i in range(10):
        meet(ctx, pg, 0, 0, 40)
    eis('grof en nog geen 30 s: nog geen adres', len(adressen) == 0, adressen)
    for i in range(25):
        meet(ctx, pg, 0, 0, 40)
    eis('na 30 s toch één adres, ook al is het grof', len(adressen) == 1, adressen)
    for i in range(130):
        meet(ctx, pg, 30, 0, 5)                                  # de schatting schuift 30 m op
    eis('30 m verschoven: nog een adres (2)', len(adressen) == 2, adressen)
    ctx.close()
    adressen = []; adres_antwoord['fout'] = True
    ctx, pg, fouten = app(b, adres=adressen)
    pg.evaluate('startSession()'); pg.wait_for_timeout(50)
    for i in range(20):
        meet(ctx, pg, 0, 0, 5)
    eis('Nominatim onbereikbaar: na een mislukt verzoek 30 s pauze (%d verzoeken in 20 s)' % len(adressen),
        len(adressen) == 1, len(adressen))
    for i in range(32):
        meet(ctx, pg, 0, 0, 5)
    eis('daarna nog één keer (%d)' % len(adressen), len(adressen) == 2, len(adressen))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== G. geen toestemming voor GPS ==')
    ctx, pg, fouten = app(b, geo=False)
    pg.evaluate('startSession()'); pg.wait_for_timeout(300)
    pg.clock.run_for(2000)
    for i in range(2): pg.evaluate(TIK % i)
    eis('melding "geen toestemming voor GPS", luisteren uit', pg.evaluate(PLEK) == 'geen toestemming voor GPS'
        and not pg.evaluate('gpsLuistert()'), pg.evaluate(PLEK))
    eis('tellen gaat gewoon (2 tikken)', pg.evaluate("document.getElementById('grand-total').textContent") == '2')
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
