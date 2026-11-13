#!/usr/bin/env python3
"""v3.47 — De stippen in telrapport na het tijdfilter en de typeknopjes.

Jay: "In de laatste geopackage zit alleen teltype alles, terwijl het een mix
was van heel veel soorten tellingen." Het tijdfilter zette de stippen aan en
uit met de typeknopjes van fietsparkeren en parkeren (dotVisible). Pocket-types
hebben zo'n knopje niet: hun stippen gingen weg en kwamen na het uitzetten niet
terug. Een eigen soort die bij Start is ingetypt ("Alles") stond niet in de
lijst en bleef juist altijd staan, ook buiten het venster. De GeoPackage neemt
mee wat op de kaart staat, dus daar zat alleen "Alles" in. Sinds v3.47 regelt
zetStippen het op één plek.

  A. Vijf tellingen met de veld-apps: parkeertelling, pocket parkeren,
     winkelstraat, simpel (auto) en simpel met een eigen soort ("Alles").
  B. In telrapport: alle stippen op de kaart.
  C. Tijdfilter aan, met "Alles" zes uur later gezet: de vier in het venster
     houden al hun stippen, "Alles" heeft er geen.
  D. Tijdfilter weer uit: alle stippen terug, en in de GeoPackage
     (waarnemingen) elke soort met het goede aantal.
  E. Typeknopje "leeg" van parkeren: alleen de lege plekken van de
     parkeertelling gaan uit, niet de lege vakken van pocket. Weer aan: terug.
  F. Sessielijst: Winkelstraat uit en aan, zoals altijd.

Hulp (veld-apps, server, CDN-omleiding, sql.js, export) uit gpkgtest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/tijdfiltertest.py
"""
import os, sqlite3, sys
HIER = os.path.dirname(os.path.abspath(__file__))
_gsrc = open(os.path.join(HIER, 'gpkgtest.py'), encoding='utf-8').read()
exec(_gsrc.split('\nwith sync_playwright() as p:\n')[0].replace(
    "HIER = os.path.dirname(os.path.abspath(__file__))", "HIER = %r" % HIER))
UIT = '/tmp/tijdfiltertest'; os.makedirs(UIT, exist_ok=True)

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))

# Stippen op de kaart en in dotLayers, per soort telling en type: { soort: { type: n } }.
# De soort: car (parkeertelling) of de laatste letters van een pocket-sessie-id
# (pkt_p, pkt_w, pkt_s), en ":Alles" voor de eigen soort.
STIPPEN = r"""(() => {
  const soort = sid => (sessions[sid].appType === 'auto' ? 'car' : (sid.match(/_(pkt_[a-z])$/) || [, sid])[1])
                       + (sessions[sid].meta.type === 'Alles' ? ':Alles' : '');
  const kaart = {}, alle = {};
  Object.keys(dotLayers).forEach(sid => Object.keys(dotLayers[sid] || {}).forEach(t => (dotLayers[sid][t] || []).forEach(m => {
    const s = soort(sid);
    (alle[s] = alle[s] || {})[t] = (alle[s][t] || 0) + 1;
    if (map.hasLayer(m)) (kaart[s] = kaart[s] || {})[t] = (kaart[s][t] || 0) + 1;
  })));
  return { kaart, alle };
})()"""

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
         lambda i: "adjustWinkel('%s',1)" % ['tegemoet', 'stilstaand'][i % 2], 'stopTelling()'),
        ('pocket_count.html', "startTelling('car', '\\u{1F697}', 'Auto')", lambda i: 'doTap()', 'stopTelling()'),
        ('pocket_count.html', "startTelling('other', '\\u2753', 'Alles')", lambda i: 'doTap()', 'stopTelling()')]:
        z, f = maak_zip(b, app, start, tik, stop, n=8)
        zips.append(z); jsfout += f
        eis('%s -> %s' % (app, os.path.basename(z)), z.endswith('.zip'))
    eis('geen JS-fouten in de veld-apps', not jsfout, jsfout)

    print('\n== B. Telrapport: alles geladen ==')
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}, accept_downloads=True)
    ctx.route('**/*', route_gpkg)
    ctx.add_init_script(OPSLAAN_STUB)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:160]))
    pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(800)
    pg.set_input_files('#file-input', zips); pg.wait_for_timeout(4000)
    st = pg.evaluate(STIPPEN)
    alle = st['alle']
    print('  stippen: %s' % alle)
    eis('vijf tellingen geladen', pg.evaluate('Object.keys(sessions).length') == 5)
    eis('elke soort telling heeft stippen', set(alle) == {'car', 'pkt_p', 'pkt_w', 'pkt_s', 'pkt_s:Alles'}, sorted(alle))
    eis('pocket: auto, lege en bezette vakken, tegemoet en stilstaand, "Alles"',
        set(alle.get('pkt_s', {})) == {'car'} and set(alle.get('pkt_p', {})) == {'leeg', 'bezet'}
        and set(alle.get('pkt_w', {})) == {'tegemoet', 'stilstaand'} and set(alle.get('pkt_s:Alles', {})) == {'Alles'}, alle)
    eis('alle stippen staan op de kaart', st['kaart'] == alle, st['kaart'])

    print('\n== C. Tijdfilter aan, "Alles" zes uur later ==')
    uur = pg.evaluate("""(() => {
      const sids = Object.keys(sessions), h = sessionHour(sids[0]);
      const alles = sids.filter(s => sessions[s].meta.type === 'Alles')[0];
      sessions[alles].meta.start_tijd = String((h + 6) % 24).padStart(2, '0') + ':00:00';
      document.getElementById('time-slider').value = h;
      document.getElementById('time-toggle').click();
      return h;
    })()""")
    pg.wait_for_timeout(300)
    st = pg.evaluate(STIPPEN)
    zonder = {k: v for k, v in alle.items() if k != 'pkt_s:Alles'}
    eis('tijdfilter op %02d uur: de vier in het venster houden al hun stippen' % uur,
        {k: v for k, v in st['kaart'].items() if k != 'pkt_s:Alles'} == zonder, st['kaart'])
    eis('"Alles" valt buiten het venster: geen stippen', 'pkt_s:Alles' not in st['kaart'], st['kaart'])
    pg.evaluate("const s = document.getElementById('time-slider'); s.value = %d; s.dispatchEvent(new Event('input'))" % ((uur + 12) % 24))
    st = pg.evaluate(STIPPEN)
    eis('een uur waar niets valt: geen enkele stip', st['kaart'] == {}, st['kaart'])

    print('\n== D. Tijdfilter uit: alles terug, ook in de GeoPackage ==')
    pg.evaluate("document.getElementById('time-toggle').click()"); pg.wait_for_timeout(300)
    st = pg.evaluate(STIPPEN)
    eis('alle stippen weer op de kaart', st['kaart'] == alle, st['kaart'])
    pad, _ = exporteer(pg, 'tijdfilter.gpkg')
    db = sqlite3.connect(pad)
    rijen = db.execute('select app_type, type, count(*) from waarnemingen group by 1, 2').fetchall()
    db.close()
    verwacht = {}
    for s, typen in alle.items():
        for t, n in typen.items():
            k = ('auto' if s == 'car' else 'pocket', t)
            verwacht[k] = verwacht.get(k, 0) + n
    eis('waarnemingen: elke soort met het goede aantal (%d stippen)' % sum(verwacht.values()),
        {(a, t): n for a, t, n in rijen} == verwacht, (rijen, verwacht))

    print('\n== E. Typeknopje "leeg" van parkeren ==')
    pg.evaluate("""document.querySelector('.dot-btn[data-type="leeg"]').click()""")
    st = pg.evaluate(STIPPEN)
    eis('parkeertelling: de lege plekken zijn uit, de rest staat er',
        'leeg' not in st['kaart'].get('car', {}) and all(st['kaart'].get('car', {}).get(t) == n
                                                         for t, n in alle['car'].items() if t != 'leeg'), st['kaart'].get('car'))
    eis('pocket parkeren: de lege vakken blijven staan', st['kaart'].get('pkt_p') == alle['pkt_p'], st['kaart'].get('pkt_p'))
    pg.evaluate("""document.querySelector('.dot-btn[data-type="leeg"]').click()""")
    st = pg.evaluate(STIPPEN)
    eis('weer aan: alle stippen terug', st['kaart'] == alle, st['kaart'])

    print('\n== F. Sessielijst ==')
    pg.evaluate("toggleGroupVisibility('pocket:winkelstraat')")
    st = pg.evaluate(STIPPEN)
    eis('Winkelstraat uit: zijn stippen weg, de rest staat er', 'pkt_w' not in st['kaart']
        and {k: v for k, v in st['kaart'].items()} == {k: v for k, v in alle.items() if k != 'pkt_w'}, st['kaart'])
    pg.evaluate("toggleGroupVisibility('pocket:winkelstraat')")
    st = pg.evaluate(STIPPEN)
    eis('en weer aan: alles terug', st['kaart'] == alle, st['kaart'])
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
