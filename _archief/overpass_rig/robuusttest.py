#!/usr/bin/env python3
"""v3.9 robuusttest — de robuustheids-release, in Chromium.

  A. Volle opslag (vijf veld-apps): lukt het wegschrijven van de noodkopie niet,
     dan staat er een melding bovenin die geen tikken afneemt, en de vorige kopie
     blijft staan. Is er weer ruimte, dan verdwijnt de melding bij de volgende tik.
     Tot v3.9 werd een mislukte setItem stil ingeslikt.
  B. Start en Doortellen vragen de browser de opslag niet op te ruimen
     (navigator.storage.persist).
  C. Pocket vraagt het schermslot terug na een app-wissel, en anders bij de
     eerstvolgende aanraking; na Terug niet meer.
  D. De voorpagina toont tellingen die nog niet als ZIP zijn opgeslagen, nieuwste
     eerst, met een link naar de app; afgesloten, lege en kapotte kopieën niet.
  E. Telplanning, wegen ophalen: de melding op de kaart is zichtbaar en loopt mee;
     een hangende server wordt na de tijdslimiet overgeslagen; een afgebroken
     antwoord (remark) wordt niet stil gebruikt; Opnieuw werkt; een rate-limit,
     verouderde data en een leeg gebied geven elk een eigen melding.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/robuusttest.py
"""
import os, sys, json
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)))

KNOP = ("(f)=>{var b=[...document.querySelectorAll('button')].find(x=>(x.getAttribute('onclick')||'')"
        ".indexOf(f+'(')===0&&x.offsetParent!==null);if(!b)return false;b.click();return true}")
HERVAT = {'parkeertelling.html': 'hervatSessie', 'fietsparkeren.html': 'hervatSessie',
          'capaciteitstelling.html': 'hervatSessie', 'pocket_count.html': 'hervatTelling',
          'traffic_counter.html': 'doortellenStatic'}
TIKKEN = ("(()=>{var k=Object.keys(localStorage).filter(k=>/_sessie$/.test(k))[0];if(!k)return null;"
          "var d=JSON.parse(localStorage.getItem(k));return (d.entries||d.telHistory||d.history||[]).length})()")
# Vul de opslag tot er minder dan 16 tekens bij kan.
VUL = ("(()=>{var i=0,stuk='x'.repeat(262144);for(;;){try{localStorage.setItem('vulsel'+(i++),stuk)}"
       "catch(e){if(stuk.length<=16)break;stuk=stuk.slice(0,Math.max(16,stuk.length>>2))}}return i})()")
LEEGMAAK = "Object.keys(localStorage).filter(k=>k.indexOf('vulsel')===0).forEach(k=>localStorage.removeItem(k))"
VOL = ("(()=>{var e=document.getElementById('kopie-vol');if(!e)return null;"
       "return {tekst:e.textContent,pe:getComputedStyle(e).pointerEvents,h:e.getBoundingClientRect().height}})()")
ZICHT = ("(z)=>{Object.defineProperty(document,'hidden',{value:!z,configurable:true});"
         "Object.defineProperty(document,'visibilityState',{value:z?'visible':'hidden',configurable:true});"
         "document.dispatchEvent(new Event('visibilitychange'))}")

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. volle opslag: melding, vorige kopie blijft, weer ruimte: weg ==')
    for naam, app, start, tik, stop, sluit in APPS:
        ctx, pg, fouten = open_app(b, app)
        pg.evaluate(start); pg.wait_for_timeout(500)
        loop(ctx, pg, 2, tik)
        eis('%s: geen melding zolang er ruimte is' % naam, pg.evaluate(VOL) is None)
        pg.evaluate(VUL)
        loop(ctx, pg, 2, tik)
        vol = pg.evaluate(VOL)
        eis('%s: opslag vol: melding bovenin, neemt geen tikken af' % naam,
            vol is not None and ('Noodopslag vol' in vol['tekst'] or 'storage full' in vol['tekst'])
            and vol['pe'] == 'none' and vol['h'] > 0, vol)
        eis('%s: de vorige kopie (2 tikken) blijft staan' % naam, pg.evaluate(TIKKEN) == 2, pg.evaluate(TIKKEN))
        pg.evaluate(LEEGMAAK)
        loop(ctx, pg, 1, tik)
        eis('%s: weer ruimte: melding weg, kopie bij (5 tikken)' % naam,
            pg.evaluate(VOL) is None and pg.evaluate(TIKKEN) == 5, (pg.evaluate(VOL), pg.evaluate(TIKKEN)))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    print('\n== B. persist bij Start en bij Doortellen ==')
    PERSIST = ("window.__persist=0;if(navigator.storage){navigator.storage.persist="
               "function(){window.__persist++;return Promise.resolve(true)}}")
    for naam, app, start, tik, stop, sluit in APPS:
        ctx, pg, fouten = open_app(b, app, PERSIST)
        eis('%s: niet bij het openen' % naam, pg.evaluate('window.__persist') == 0)
        pg.evaluate(start); pg.wait_for_timeout(400)
        eis('%s: wel bij Start' % naam, pg.evaluate('window.__persist') >= 1, pg.evaluate('window.__persist'))
        loop(ctx, pg, 2, tik)
        if naam in ('parkeertelling', 'pocket simpel', 'Static'):
            B = ctx.new_page(); B.on('dialog', lambda d: d.accept())
            B.goto(BASIS + app, wait_until='load'); B.wait_for_timeout(900)
            eis('%s: herstellen alleen vraagt het niet' % naam, B.evaluate('window.__persist') == 0)
            B.evaluate(KNOP, HERVAT[app]); B.wait_for_timeout(500)
            eis('%s: Doortellen vraagt het' % naam, B.evaluate('window.__persist') >= 1, B.evaluate('window.__persist'))
        eis('%s: geen JS-fouten' % naam, not fouten, fouten)
        ctx.close()

    print('\n== C. pocket: schermslot terug na een app-wissel ==')
    SLOT = """(()=>{window.__slot={aanvragen:0,actief:null,weiger:0};
      Object.defineProperty(navigator,'wakeLock',{configurable:true,value:{request:function(){
        __slot.aanvragen++;
        if(__slot.weiger>0){__slot.weiger--;return Promise.reject(new DOMException('nee','NotAllowedError'));}
        var s={ls:[],weg:false,addEventListener:function(n,f){if(n==='release')this.ls.push(f)},
               release:function(){if(!this.weg){this.weg=true;if(__slot.actief===this)__slot.actief=null;this.ls.forEach(function(f){f()})}return Promise.resolve()}};
        __slot.actief=s;return Promise.resolve(s);}}});})()"""
    WISSEL = "(()=>{if(__slot.actief)__slot.actief.release();})()"   # de browser geeft het slot vrij
    ctx, pg, fouten = open_app(b, 'pocket_count.html', SLOT)
    pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(300)
    eis('Start vraagt het slot', pg.evaluate('__slot.aanvragen') == 1 and pg.evaluate('!!__slot.actief'))
    pg.evaluate(WISSEL); pg.evaluate(ZICHT, False); pg.wait_for_timeout(100); pg.evaluate(ZICHT, True); pg.wait_for_timeout(200)
    eis('na een app-wissel: opnieuw aangevraagd en actief', pg.evaluate('__slot.aanvragen') == 2 and pg.evaluate('!!__slot.actief'),
        pg.evaluate('__slot.aanvragen'))
    pg.evaluate('__slot.weiger=1'); pg.evaluate(WISSEL); pg.evaluate(ZICHT, False); pg.evaluate(ZICHT, True); pg.wait_for_timeout(200)
    eis('geweigerd bij terugkomen: geen slot', pg.evaluate('__slot.aanvragen') == 3 and not pg.evaluate('!!__slot.actief'))
    pg.evaluate("document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); pg.wait_for_timeout(200)
    eis('de eerstvolgende aanraking vraagt het opnieuw', pg.evaluate('__slot.aanvragen') == 4 and pg.evaluate('!!__slot.actief'))
    pg.evaluate("document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); pg.wait_for_timeout(100)
    eis('met een actief slot vraagt een aanraking niets', pg.evaluate('__slot.aanvragen') == 4)
    pg.evaluate('backToChoose()'); pg.wait_for_timeout(200)
    eis('Terug: slot vrijgegeven', not pg.evaluate('!!__slot.actief'))
    pg.evaluate(ZICHT, False); pg.evaluate(ZICHT, True)
    pg.evaluate("document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); pg.wait_for_timeout(200)
    eis('na Terug: geen nieuw verzoek, ook niet bij aanraken', pg.evaluate('__slot.aanvragen') == 4, pg.evaluate('__slot.aanvragen'))
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== D. voorpagina: nog niet opgeslagen tellingen ==')
    KOPIEEN = {
        'parkeertelling_sessie': json.dumps({'entries': [{}, {}, {}], 'sessionId': '20261014_101500_abc',
                                             'telling': '20261014_101500_abc', 'savedAt': '2026-10-14 10:20:00'}),
        'pocket_sessie': json.dumps({'modus': 'parkeren', 'telCount': 7, 'telHistory': [{}] * 7,
                                     'startTime': '2026-10-15T08:00:00.000Z', 'savedAt': '2026-10-15T10:05:00'}),
        'static_sessie': json.dumps({'state': 'ended', 'history': [{}, {}], 'sessieId': '20261013_120000_xyz_sta',
                                     'savedAt': '2026-10-13T12:00:00'}),
        'fietsparkeren_sessie': json.dumps({'entries': [{}], 'telling': 'X1', 'savedAt': '2026-10-15 11:00:00'}),
        'capaciteitstelling_sessie': '{kapot',
        'telsuite_afgesloten': json.dumps(['X1']),
    }
    INJECT = ("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');var o=%s;for(var k in o)localStorage.setItem(k,o[k]);}"
              % json.dumps(KOPIEEN))
    RIJEN = ("(()=>{var s=document.getElementById('open-tellingen');return {zichtbaar:!s.hidden&&s.getBoundingClientRect().height>0,"
             "kop:document.getElementById('open-kop').textContent,"
             "rijen:[...s.querySelectorAll('a')].map(a=>[a.getAttribute('href'),a.textContent])}})()")
    ctx, pg, fouten = open_app(b, 'index.html', INJECT)
    pg.evaluate("document.querySelector('.lang-btn[data-lang=nl]').click()"); pg.wait_for_timeout(100)
    r = pg.evaluate(RIJEN)
    eis('zichtbaar, kop "Nog niet opgeslagen"', r['zichtbaar'] and r['kop'] == 'Nog niet opgeslagen', r)
    eis('drie tellingen; afgesloten, kapot en leeg niet', len(r['rijen']) == 3, r['rijen'])
    eis('nieuwste eerst, met app, aantal en tijd', [x[0] for x in r['rijen']] ==
        ['pocket_count.html#parkeren', 'parkeertelling.html', 'traffic_counter.html'], r['rijen'])
    eis('pocket: "Pocket · parkeren", "7 tikken · do 15-10 10:05"',
        r['rijen'][0][1] == 'Pocket · parkeren7 tikken · do 15-10 10:05', r['rijen'][0][1])
    eis('Static: afgerond', r['rijen'][2][1].endswith('· afgerond'), r['rijen'][2][1])
    pg.evaluate("document.querySelector('.lang-btn[data-lang=en]').click()"); pg.wait_for_timeout(100)
    r = pg.evaluate(RIJEN)
    eis('Engels: "Not saved yet", "3 taps · Wed 14-10 10:20"',
        r['kop'] == 'Not saved yet' and r['rijen'][1][1] == 'Car parking3 taps · Wed 14-10 10:20', r)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    # Echte route: pocket tellen, naar de voorpagina, opslaan, weer naar de voorpagina.
    ctx, pg, fouten = open_app(b, 'pocket_count.html')
    pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(300)
    loop(ctx, pg, 3, lambda i: 'doTap()')
    pg.goto(BASIS + 'index.html', wait_until='load'); pg.wait_for_timeout(300)
    r = pg.evaluate(RIJEN)
    eis('na 3 tikken in pocket staat hij op de voorpagina', r['zichtbaar'] and len(r['rijen']) == 1
        and r['rijen'][0][0] == 'pocket_count.html', r)
    pg.goto(BASIS + 'pocket_count.html', wait_until='load'); pg.wait_for_timeout(800)
    pg.evaluate(KNOP, 'hervatTelling'); pg.wait_for_timeout(500)
    with pg.expect_download(timeout=15000):
        pg.evaluate('stopTelling()')
    pg.wait_for_timeout(900); pg.evaluate('closePreview()'); pg.wait_for_timeout(200)
    pg.goto(BASIS + 'index.html', wait_until='load'); pg.wait_for_timeout(300)
    eis('opgeslagen: de voorpagina toont niets meer', not pg.evaluate(RIJEN)['zichtbaar'])
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    print('\n== E. telplanning: wegen ophalen ==')
    SCEN = {}
    TELLER = {'1': 0, '2': 0}
    HANGT = []
    OSM_REMARK = json.dumps(dict(json.loads(OSM), remark='runtime error: Query timed out in "query" at line 1 after 26 seconds.'))
    OSM_OUD = json.dumps(dict(json.loads(OSM), osm3s={'timestamp_osm_base': '2020-01-01T00:00:00Z'}))
    def overpass(r):
        u = r.request.url
        if 'overpass' not in u:
            return route(r)
        server = '1' if 'overpass-api.de' in u else '2'
        TELLER[server] += 1
        actie = SCEN.get(server, 'ok')
        if actie == 'hang':
            HANGT.append(r); return
        if actie == '429':
            return r.fulfill(status=429, body='rate limited', content_type='text/plain')
        body = {'ok': OSM, 'leeg': json.dumps({'version': 0.6, 'elements': []}),
                'remark': OSM_REMARK, 'oud': OSM_OUD}[actie]
        return r.fulfill(body=body, content_type='application/json')
    d = 0.003
    GEOM = json.dumps({'type': 'Polygon', 'coordinates': [[[LON - d, LAT - d], [LON + d, LAT - d], [LON + d, LAT + d],
                                                            [LON - d, LAT + d], [LON - d, LAT - d]]]})
    MELDING_PL = ("(()=>{var e=document.getElementById('loading'),r=e.getBoundingClientRect(),m=document.getElementById('map').getBoundingClientRect();"
                  "return {zicht:r.width>0&&r.height>0,midden:r.left+r.width/2>m.left&&r.left+r.width/2<m.right,"
                  "klasse:e.className,tekst:e.textContent,wegen:ways.length,status:document.getElementById('status-bar').textContent}})()")

    def planning(scen, timeout=None):
        SCEN.clear(); SCEN.update(scen); TELLER['1'] = TELLER['2'] = 0
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        ctx.route('**/*', overpass)
        pg = ctx.new_page(); f = []
        pg.on('pageerror', lambda e: f.append(e.message[:120]))
        pg.goto(BASIS + 'telplanning.html', wait_until='load'); pg.wait_for_timeout(500)
        if timeout: pg.evaluate('OPHAAL_TIMEOUT_MS=%d' % timeout)
        pg.evaluate('fetchWaysForPolygon(%s)' % GEOM)
        return ctx, pg, f

    print('-- E1. server 1 hangt, server 2 antwoordt --')
    ctx, pg, f = planning({'1': 'hang', '2': 'ok'}, timeout=2500)
    pg.wait_for_timeout(1300)
    m = pg.evaluate(MELDING_PL)
    eis('melding zichtbaar op het midden van de kaart, met verstreken tijd',
        m['zicht'] and m['midden'] and 'Wegen ophalen' in m['tekst'] and '1 s' in m['tekst'], m)
    pg.wait_for_timeout(700)
    eis('de tijd loopt mee', '2 s' in pg.evaluate(MELDING_PL)['tekst'], pg.evaluate(MELDING_PL)['tekst'])
    pg.wait_for_timeout(2000)
    m = pg.evaluate(MELDING_PL)
    eis('na de tijdslimiet: server 2, wegen geladen, melding weg',
        TELLER['2'] == 1 and m['wegen'] > 0 and not m['zicht'], (TELLER, m))
    eis('geen JS-fouten', not f, f)
    for r in HANGT:                       # het verzoek is al afgebroken door de pagina
        try: r.abort()
        except Exception: pass
    ctx.close(); HANGT.clear()

    print('-- E2. afgebroken antwoord (remark) bij beide servers, dan Opnieuw --')
    ctx, pg, f = planning({'1': 'remark', '2': 'remark'})
    pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('foutmelding met reden en advies, niets stil gebruikt',
        m['zicht'] and 'fout' in m['klasse'] and 'brak de zoekvraag af' in m['tekst']
        and 'kleiner gebied' in m['tekst'] and m['wegen'] == 0, m)
    eis('statusregel verwijst naar de melding', 'mislukt' in m['status'], m['status'])
    SCEN.update({'1': 'ok', '2': 'ok'})
    pg.click('#loading button.hoofd'); pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('Opnieuw: wegen geladen, melding weg', m['wegen'] > 0 and not m['zicht'], m)
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('-- E3. rate-limit bij server 1 --')
    ctx, pg, f = planning({'1': '429', '2': 'ok'})
    pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('server 2 springt in, geen foutmelding', m['wegen'] > 0 and not m['zicht'] and TELLER['2'] == 1, (TELLER, m))
    ctx.close()

    print('-- E4. leeg gebied --')
    ctx, pg, f = planning({'1': 'leeg', '2': 'ok'})
    pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('melding "Geen wegen gevonden", server 2 niet gevraagd',
        m['zicht'] and 'Geen wegen gevonden' in m['tekst'] and TELLER['2'] == 0, (TELLER, m))
    pg.click('#loading button'); pg.wait_for_timeout(200)
    eis('Sluiten: melding weg', not pg.evaluate(MELDING_PL)['zicht'])
    eis('geen JS-fouten', not f, f)
    ctx.close()

    print('-- E5. verouderde data, E6. overbelast --')
    ctx, pg, f = planning({'1': 'oud', '2': 'oud'})
    pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('verouderd: foutmelding, wegen niet gebruikt', 'verouderde kaartdata' in m['tekst'] and m['wegen'] == 0, m)
    ctx.close()
    ctx, pg, f = planning({'1': '429', '2': '429'})
    pg.wait_for_timeout(800)
    m = pg.evaluate(MELDING_PL)
    eis('overbelast: advies om even te wachten', 'overbelast' in m['tekst'] and 'halve minuut' in m['tekst'], m)
    eis('geen JS-fouten', not f, f)
    ctx.close()

    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
