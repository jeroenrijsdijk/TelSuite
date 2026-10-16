#!/usr/bin/env python3
"""v3.10 logicatest — het pocket-id bij Start en het kwaliteitsrapport in telrapport.

  A. Pocket-id, in de echte app:
     A1. vast vanaf Start: de noodkopie draagt het id, met de datum en tijd van de
         start en de moduscode;
     A2. de ZIP heet zo, en _sessie.csv draagt hetzelfde id en dezelfde starttijd;
     A3. iPhone, deelvenster geannuleerd, herstel in een nieuw venster, Download:
         dezelfde ZIP-naam als de eerste poging (tot v3.10 een nieuw id, met de
         tijd van de tweede Stop);
     A4. Doortellen houdt het id vast;
     A5. een kopie van vóór v3.10 (zonder id): het id komt uit de starttijd, en
         twee vensters komen op hetzelfde id uit.
  B. Kwaliteitsrapport in telrapport:
     B1. echte ZIP's van pocket en Static: "✓";
     B2. een parkeertelling, ook met een verschoven tik en met een fout aantal:
         "✓" en "⚠ 1"; het teken staat op de eerste regel van de rij en maakt
         de rij niet hoger (v3.11);
     B3. een klik opent het paneel met de juiste controle, en zet de telling niet
         uit; Escape sluit het; "alles wissen" ruimt de rapporten op.

Hulp (server, CDN-omleiding, nep-Overpass) komt uit opruimtest.py en hersteltest.py.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/logicatest.py
"""
import os, sys, io, json, re, tempfile, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_osrc = open(os.path.join(HIER, 'opruimtest.py'), encoding='utf-8').read()
exec(_osrc[:_osrc.index('\nwith sync_playwright() as p:')]
     .replace("HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)))

TMP = tempfile.mkdtemp(prefix='logicatest_')
KNOP = ("(f)=>{var b=[...document.querySelectorAll('button')].find(x=>(x.getAttribute('onclick')||'')"
        ".indexOf(f+'(')===0&&x.offsetParent!==null);if(!b)return false;b.click();return true}")
KOPIE_POCKET = "JSON.parse(localStorage.getItem('pocket_sessie')||'null')"
STARTSTAM = ("(()=>{var d=startTime,p=n=>String(n).padStart(2,'0');return d.getFullYear()+p(d.getMonth()+1)+p(d.getDate())"
             "+'_'+p(d.getHours())+p(d.getMinutes())+p(d.getSeconds())})()")
def zip_bewaar(dl, naam):
    pad = os.path.join(TMP, naam); dl.save_as(pad); return pad
def sessie_uit(pad):
    z = zipfile.ZipFile(pad)
    n = [x for x in z.namelist() if x.endswith('_sessie.csv')][0]
    kop, rij = z.read(n).decode('utf-8').splitlines()[:2]
    return dict(zip(kop.split(';'), rij.split(';')))

with sync_playwright() as p:
    b = p.chromium.launch()

    print('== A. pocket-id vast vanaf Start ==')
    ctx, pg, fouten = open_app(b, 'pocket_count.html')
    pg.evaluate("startTelling('car','x','Auto')"); pg.wait_for_timeout(300)
    stam = pg.evaluate(STARTSTAM)
    pg.wait_for_timeout(1500)                                  # Stop valt duidelijk later dan Start
    loop(ctx, pg, 3, lambda i: 'doTap()')
    k = pg.evaluate(KOPIE_POCKET)
    sid = k and k.get('sessieId')
    eis('A1. de noodkopie draagt het id: datum en tijd van de start, moduscode s',
        bool(sid) and re.fullmatch(re.escape(stam) + r'_[a-z]{3}_pkt_s', sid or ''), (sid, stam))
    eis('A1. de noodkopie gebruikt dat id ook als telling-id (blok noodkopie)', k and k.get('telling') == sid, k and k.get('telling'))
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('stopTelling()')
    pad = zip_bewaar(d.value, 'a2.zip'); pg.wait_for_timeout(500)
    sm = sessie_uit(pad)
    eis('A2. de ZIP heet naar het id', d.value.suggested_filename == sid + '.zip', d.value.suggested_filename)
    eis('A2. _sessie.csv: zelfde id, start_tijd gelijk aan de tijd in het id',
        sm['sessie_id'] == sid and sm['start_tijd'].replace(':', '') == stam.split('_')[1], sm)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()

    # A3: iPhone, deelvenster geannuleerd; herstel in een nieuw venster, dan Download
    ctx, A, fa = open_app(b, 'pocket_count.html', deelblad(['annuleer']), IPHONE)
    A.evaluate('startParkeren()'); A.wait_for_timeout(300)
    loop(ctx, A, 3, lambda i: "adjustParkeer('links_bezet',1)")
    A.evaluate('stopTelling()'); A.wait_for_timeout(1500)
    eerste = A.evaluate('window.__deelBestanden')
    eis('A3. eerste poging: deelvenster geannuleerd, kopie blijft',
        eerste and eerste[0] and A.evaluate(KOPIE_POCKET) is not None, eerste)
    opslag = bevries(A); ctx.close()
    # nieuw venster, ook als iPhone, met alleen de bevroren opslag; nu lukt het deelvenster
    ctx, B, fb = open_app(b, 'pocket_count.html',
                          ("if(!sessionStorage.getItem('z')){sessionStorage.setItem('z','1');var o=%s;"
                           "for(var k in o)localStorage.setItem(k,o[k]);}" % opslag) + deelblad(['ok']), IPHONE)
    B.wait_for_timeout(400)
    B.evaluate('restoreDownload()'); B.wait_for_timeout(1500)
    tweede = B.evaluate('window.__deelBestanden')
    eis('A3. na herstel en Download: dezelfde ZIP-naam als de eerste poging',
        tweede and tweede[0] and tweede[0][0] == eerste[0][0], (eerste, tweede))
    eis('geen JS-fouten', not (fa + fb), fa + fb)
    ctx.close()

    # A4: Doortellen houdt het id vast
    ctx, A, fa = open_app(b, 'pocket_count.html')
    A.evaluate('startTransect()'); A.wait_for_timeout(300)
    loop(ctx, A, 2, lambda i: "adjustTransect('car','a',1)")
    sid_a = A.evaluate(KOPIE_POCKET)['sessieId']
    B = ctx.new_page(); B.on('dialog', lambda d: d.accept())
    B.goto(BASIS + 'pocket_count.html', wait_until='load'); B.wait_for_timeout(900)
    B.evaluate(KNOP, 'hervatTelling'); B.wait_for_timeout(500)
    loop(ctx, B, 2, lambda i: "adjustTransect('car','b',1)")
    eis('A4. na Doortellen in een ander venster: hetzelfde id in de kopie',
        B.evaluate(KOPIE_POCKET)['sessieId'] == sid_a and sid_a.endswith('_pkt_t'), (sid_a, B.evaluate(KOPIE_POCKET)['sessieId']))
    with B.expect_download(timeout=15000) as d:
        B.evaluate('stopTelling()')
    eis('A4. en de ZIP heet zo', d.value.suggested_filename == sid_a + '.zip', d.value.suggested_filename)
    pocket_zip = zip_bewaar(d.value, 'pocket.zip')
    eis('geen JS-fouten', not fa, fa)
    ctx.close()

    # A5: kopie van vóór v3.10, zonder id
    oud = json.loads(opslag)
    kop = json.loads(oud['pocket_sessie'])
    for veld in ('sessieId', 'venster', 'telling'): kop.pop(veld, None)
    kop['startTime'] = '2026-10-16T07:30:15.123Z'               # 09:30:15 in Amsterdam
    legacy = json.dumps({'pocket_sessie': json.dumps(kop)})
    namen = []
    for i in range(2):
        ctx, C, fc = herlaad_met(b, 'pocket_count.html', legacy, geo=True)
        with C.expect_download(timeout=15000) as d:
            C.evaluate('restoreDownload()')
        namen.append(d.value.suggested_filename)
        eis('A5. geen JS-fouten (venster %d)' % (i + 1), not fc, fc)
        ctx.close()
    eis('A5. id uit de starttijd: 20261016_093015_..._pkt_p', re.fullmatch(r'20261016_093015_[a-z]{3}_pkt_p\.zip', namen[0]), namen)
    eis('A5. twee vensters, hetzelfde id', namen[0] == namen[1], namen)

    # Static: een echte ZIP met GPS-fix voor deel B
    ctx, pg, fouten = open_app(b, 'traffic_counter.html')
    pg.evaluate('startSession()'); pg.wait_for_timeout(1500)
    for i in range(4): pg.evaluate(TIK_STATIC % i)
    with pg.expect_download(timeout=15000) as d:
        pg.evaluate('endSession()')
    static_zip = zip_bewaar(d.value, 'static.zip')
    ctx.close()

    print('\n== B. kwaliteitsrapport in telrapport ==')
    def parkeer_zip(naam, sid, verschuif=False, n=4):
        d = 7 / 111320
        net = '%s_netwerk.csv' % sid
        z = zipfile.ZipFile(os.path.join(TMP, naam), 'w')
        z.writestr(sid + '_sessie.csv', 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n'
                   '%s;Jay;2026-10-16;2026-10-16 10:00:00;2026-10-16 10:01:30;auto;%d\n' % (sid, n))
        regels = []
        for i in range(4):
            la = LAT + 2 * i * d + (200 / 111320 if verschuif and i == 2 else 0)
            regels.append('%s;%d;2026-10-16 10:00:%02d;goed;L;Noordstraat 3;%.6f;%.6f;%.6f;%.6f;1;1003;;;;'
                          % (sid, i + 1, i * 20, LAT + 2 * i * d, LON, la, LON))
        z.writestr(sid + '_telregels.csv', 'sessie_id;nr;tijdstip;type;zijde;straat;lat_marker;lon_marker;lat_gps;lon_gps;snapped;'
                   'osm_way_id;hdg_kompas;hdg_gps;hdg_osm;hdg_gebruikt\n' + '\n'.join(regels) + '\n')
        z.writestr(sid + '_gps.csv', 'sessie_id;tijdstip;lat;lon;nauwkeurigheid;hdg_gps;hdg_kompas;hdg_fused;gesnapped;osm_way_id;kompas_bevroren\n' +
                   ''.join('%s;2026-10-16 10:00:%02d;%.6f;%.6f;5;;;;1;1003;0\n' % (sid, i * 10, LAT + i * d, LON) for i in range(9)))
        z.writestr(sid + '_straten.csv', 'sessie_id;naam;osm_way_ids;goed;fout;leeg;spec;bezet;vrij;bezettingsgraad_pct;'
                   'eerste_waarneming;laatste_waarneming\n%s;Noordstraat 3;1003;4;0;0;0;4;0;100;;\n' % sid)
        z.writestr(net, 'osm_way_id;highway;geometrie_wkt\n1003;residential;LINESTRING (%.6f %.6f, %.6f %.6f)\n'
                   % (LON, LAT - 0.004, LON, LAT + 0.008))
        z.close()
        return os.path.join(TMP, naam)
    zips = [pocket_zip, static_zip,
            parkeer_zip('p_goed_car.zip', '20261016_100000_goe'),
            parkeer_zip('p_verschoven_car.zip', '20261016_110000_ver', verschuif=True),
            parkeer_zip('p_aantal_car.zip', '20261016_120000_aan', n=5)]
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}); ctx.route('**/*', route_met_osm)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(600)
    pg.set_input_files('#file-input', zips); pg.wait_for_timeout(4000)
    RIJ = ("(sid)=>{var r=document.querySelector('.session-row[data-sid=\"'+sid+'\"]');"
           "var k=r&&r.querySelector('.session-kwaliteit');return k?k.textContent:null}")
    eis('B1. pocket (echte ZIP, na Doortellen): ✓', pg.evaluate(RIJ, sid_a) == '✓',
        (pg.evaluate(RIJ, sid_a), pg.evaluate('kwaliteit[%r]' % sid_a)))
    sid_s = sessie_uit(static_zip)['sessie_id']
    eis('B1. Static (echte ZIP, met fix): ✓', pg.evaluate(RIJ, sid_s) == '✓',
        (pg.evaluate(RIJ, sid_s), pg.evaluate('kwaliteit[%r]' % sid_s)))
    eis('B2. nette parkeertelling: ✓', pg.evaluate(RIJ, '20261016_100000_goe') == '✓',
        pg.evaluate('kwaliteit["20261016_100000_goe"]'))
    eis('B2. een tik 200 m verschoven: ⚠ 1', pg.evaluate(RIJ, '20261016_110000_ver') == '⚠ 1',
        pg.evaluate(RIJ, '20261016_110000_ver'))
    eis('B2. een fout aantal: ⚠ 1', pg.evaluate(RIJ, '20261016_120000_aan') == '⚠ 1',
        pg.evaluate(RIJ, '20261016_120000_aan'))
    # v3.11: het teken staat op de eerste regel en kost de rij geen hoogte
    plek = pg.evaluate("""(sid)=>{var r=document.querySelector('.session-row[data-sid="'+sid+'"]');
      var k=r.querySelector('.session-kwaliteit'), h=r.getBoundingClientRect().height;
      var opRegel1=!!k.closest('.session-line1'), titel=k.title;
      var kopie=k.cloneNode(true); k.remove(); var h0=r.getBoundingClientRect().height;
      r.querySelector('.session-line1').appendChild(kopie);
      return {opRegel1:opRegel1, h:h, h0:h0, titel:titel}}""", '20261016_110000_ver')
    eis('B2. het teken staat op de eerste regel van de rij, met uitleg in de tooltip',
        plek['opRegel1'] and plek['titel'] == 'kwaliteit: 1 aandachtspunt — klik voor het rapport', plek)
    eis('B2. de rij is met het teken even hoog als zonder (%.0f px)' % plek['h0'], abs(plek['h'] - plek['h0']) < 0.5, plek)
    pg.click('.session-row[data-sid="20261016_110000_ver"] .session-kwaliteit'); pg.wait_for_timeout(300)
    paneel = pg.evaluate("(()=>{var o=document.getElementById('kw-overlay');if(!o)return null;"
                         "return [...o.querySelectorAll('tr')].map(t=>[t.className,t.querySelector('.kw-naam').textContent])})()")
    eis('B3. klik: het paneel, met "Op de route" als aandachtspunt', paneel and ['let', 'Op de route'] in paneel and
        sum(1 for c, _ in paneel if c == 'let') == 1, paneel)
    eis('B3. de klik zet de telling niet uit', pg.evaluate("sessions['20261016_110000_ver'].visible") is True)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    eis('B3. Escape sluit het paneel', pg.evaluate("!document.getElementById('kw-overlay')"))
    pg.evaluate('resetAll()'); pg.wait_for_timeout(500)
    eis('B3. alles wissen ruimt de rapporten op', pg.evaluate('Object.keys(kwaliteit).length') == 0)
    eis('geen JS-fouten', not fouten, fouten)
    ctx.close()
    b.close()
srv.shutdown()
print('\n' + ('ALLE %d TESTS OK' % ok if fout == 0 else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
