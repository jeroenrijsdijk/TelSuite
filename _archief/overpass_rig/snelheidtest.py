#!/usr/bin/env python3
"""v3.49 — telrapport snel bij veel tellingen.

Jay: "Het clusteren van punten is het traagste onderdeel van het tekenen van de
kaart. Kun je daar nog wat snelheidswinst vinden?"; "Doe A,B,C en D maar zorg wel
dat er iets van een voortgangsindicatie is / blijft."

Het clusteren zelf was niet traag. Wat eromheen zat wel: per telling alle
wegvakken langs, de tellers per telling, per wegvak alle bezoeken, elke lijn
opnieuw stijlen, en na elke ZIP alles opnieuw. Nu: opzoeklijsten (wegvakkenVan,
bezoekenOp), tellers één keer per actie, zetStijl, en laden in een bundel.

  A. Een set als die van Jay, gemaakt: N winkelstraat- en simpele tellingen,
     elk met een eigen wegennet van 230 wegvakken. Een deel deelt zijn wegvakken
     met een ander, een deel heeft geen telregels (alleen bezocht).
  B. Laden via de dropzone: de voortgang staat er ("⏳ laden… k/n", daarna
     "⏳ kaart tekenen…"), en het laden blijft binnen een ruime grens.
  C. De opzoeklijsten kloppen met alles langs lopen: wegvakkenVan per telling,
     bezoekenOp per wegvak (in laadvolgorde).
  D. Na het laden: de bollen, de tellers en het kwaliteitsrapport kloppen met
     elkaar; met de bollen uit staat "locaties" op 0 (tot v3.49 bleef het oude
     getal staan).
  E. Hover over een wegvak en eraf: de lijn krijgt zijn kleur terug (zetStijl
     onthoudt de stijl; de hover zet hem op null).
  F. De acties binnen ruime grenzen: bollen aan, tijdfilter aan, schuiven en
     uit, een groep uit en aan. Tot v3.49 duurde elk daarvan seconden.

De grenzen zijn ruim (een trage CI-machine), maar te krap voor de oude manier,
die bij 150 tellingen minuten deed over het laden.

Hulp (server, CDN-omleiding) komt uit laadtest.py ernaast.
Draaien vanuit de suite-root:  python3 _archief/overpass_rig/snelheidtest.py
"""
import os, sys, time, zipfile
HIER = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HIER, 'laadtest.py'), encoding='utf-8').read()
exec(_src.split('ok = fout = 0')[0])             # ROOT, NM, route, srv, BASIS
from playwright.sync_api import sync_playwright

ok = fout = 0
def eis(naam, v, x=None):
    global ok, fout
    if v: ok += 1; print('  OK   ' + naam)
    else: fout += 1; print('  FOUT ' + naam + ('' if x is None else ' -> ' + str(x)[:400]))

N = int(os.environ.get('SNELHEID_N', '150'))
UIT = '/tmp/snelheidtest'
GRENS_LADEN_S = 60          # bij 150 tellingen; de oude manier: minuten
GRENS_ACTIE_MS = 3000       # per actie; de oude manier: seconden tot tien seconden

def maak_set(map_, n, gebieden):
    """n pocket-ZIP's; tellingen in hetzelfde gebied delen hun 230 wegvakken."""
    os.makedirs(map_, exist_ok=True)
    for f in os.listdir(map_): os.remove(os.path.join(map_, f))
    for i in range(n):
        g = i % gebieden
        modus = 'winkelstraat' if i % 3 else 'simpel'
        sid = '202610%02d_%02d%02d00_%s_pkt_%s' % (1 + i % 28, 9 + i % 9, i % 60,
              chr(97 + i % 26) + chr(97 + (i // 26) % 26) + chr(97 + (i // 676) % 26), 'w' if modus == 'winkelstraat' else 's')
        ptype = 'winkelstraat' if modus == 'winkelstraat' else ('car' if i % 2 else 'Alles')
        la0, lo0 = 51.80 + (g % 15) * 0.012, 4.20 + (g // 15) * 0.018
        ways, net, wid = [], ['osm_way_id;segment_index;segment_count;highway;geometrie_wkt'], 100000 + g * 1000
        for r in range(12):
            for c in range(10):
                a, b = (lo0 + c * 0.0008, la0 + r * 0.0005), (lo0 + (c + 1) * 0.0008, la0 + r * 0.0005)
                net.append('%d;0;1;residential;LINESTRING (%.6f %.6f, %.6f %.6f)' % (wid, a[0], a[1], b[0], b[1])); ways.append((wid, a, b)); wid += 1
        for c in range(11):
            for r in range(10):
                a, b = (lo0 + c * 0.0008, la0 + r * 0.0005), (lo0 + c * 0.0008, la0 + (r + 1) * 0.0005)
                net.append('%d;0;1;residential;LINESTRING (%.6f %.6f, %.6f %.6f)' % (wid, a[0], a[1], b[0], b[1])); ways.append((wid, a, b)); wid += 1
        h, zonder_tel = 9 + i % 9, (i % 17 == 5)
        tel = ['sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat']
        bez = ['osm_way_id;segment_index;datum;start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen']
        nr = 0
        for w in range(6):
            wid_, a, b = ways[(w * 3 + i) % len(ways)]
            dur = 25 + (i * 7 + w * 5) % 40
            ntik = 0 if zonder_tel else 4 + (i + w) % 9
            bez.append('%d;0;2026-10-%02d;%02d:%02d:00;%02d:%02d:%02d;%d;8;%d' % (wid_, 1 + i % 28, h, w, h, w, dur, dur, ntik))
            for k in range(ntik):
                f = (k + 0.5) / ntik; kant = 0.00002 if k % 2 else -0.00002
                lo = a[0] + (b[0] - a[0]) * f; la = a[1] + (b[1] - a[1]) * f + kant
                t = (['tegemoet', 'tegemoet', 'stilstaand'][k % 3]) if modus == 'winkelstraat' else ptype
                nr += 1
                tel.append('%s;%d;2026-10-%02dT%02d:%02d:%02d;%s;%.6f;%.6f;%d;0;Straat %d' % (sid, nr, 1 + i % 28, h, w, k, t, la, lo, wid_, w))
        sessie = ('sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b\n'
                  '%s;2026-10-%02d;%02d:00:00;%02d:10:00;pocket;%s;%d;%s;;' % (sid, 1 + i % 28, h, h, ptype, nr, modus))
        with zipfile.ZipFile(os.path.join(map_, sid + '.zip'), 'w') as z:
            z.writestr(sid + '_sessie.csv', sessie)
            if not zonder_tel: z.writestr(sid + '_telregels.csv', '\n'.join(tel) + '\n')
            z.writestr(sid + '_gps.csv', '\n'.join(['lat;lon'] + ['%.6f;%.6f' % (w[1][1], w[1][0]) for w in ways[:20]]) + '\n')
            z.writestr(sid + '_netwerk.csv', '\n'.join(net) + '\n')
            z.writestr(sid + '_bezocht.csv', '\n'.join(bez) + '\n')
    return sorted(os.path.join(map_, f) for f in os.listdir(map_))

# De voortgang in de dropzone: elke tekst die er staat, opgevangen.
VOORTGANG = r"""
window.__dz = [];
document.addEventListener('DOMContentLoaded', () => {
  const dz = document.getElementById('dropzone');
  new MutationObserver(() => { const t = dz.innerText.trim(); if (window.__dz[window.__dz.length - 1] !== t) window.__dz.push(t); })
    .observe(dz, { childList: true, subtree: true, characterData: true });
});"""

INDEX = r"""(() => {
  const fouten = [];
  const scan = {};
  Object.keys(wayData).forEach(k => wayData[k].sessions.forEach(e => (scan[e.sid] = scan[e.sid] || new Set()).add(k)));
  const sids = new Set([...Object.keys(scan), ...Object.keys(wegvakkenVan)]);
  sids.forEach(sid => {
    const a = [...(scan[sid] || [])].sort().join(','), b = [...(wegvakkenVan[sid] || [])].sort().join(',');
    if (a !== b) fouten.push('wegvakkenVan ' + sid);
  });
  const per = {};
  Object.keys(visitData).forEach(sid => visitData[sid].forEach(v => (per[wkey(v.wid, v.segIdx || 0)] = per[wkey(v.wid, v.segIdx || 0)] || []).push(sid + '@' + v.tStart)));
  new Set([...Object.keys(per), ...Object.keys(bezoekenOp)]).forEach(k => {
    const a = (per[k] || []).join(','), b = (bezoekenOp[k] || []).map(x => x.sid + '@' + x.v.tStart).join(',');
    if (a !== b) fouten.push('bezoekenOp ' + k);
  });
  return { fouten: fouten.slice(0, 5), nFouten: fouten.length, tellingen: Object.keys(wegvakkenVan).length,
           wegvakken: Object.keys(wayData).length, bezochteStukken: Object.keys(bezoekenOp).length };
})()"""

STAND = r"""(() => {
  let bollen = 0, tikken = 0, dekking = 0;
  Object.keys(clusterLayers).forEach(sid => (clusterLayers[sid] || []).forEach(m => { if (map.hasLayer(m)) { bollen++; if (m._cluster) tikken += m._cluster.total; } }));
  Object.keys(sessions).forEach(sid => { dekking += clusterDekking(sid).geplaatst; });
  return { bollen, tikken, dekking, locaties: +document.getElementById('s-locaties').textContent,
           sessies: +document.getElementById('s-sessies').textContent };
})()"""

def tijd(pg, js):
    return pg.evaluate('(() => { const t = performance.now(); %s; return performance.now() - t; })()' % js)

with sync_playwright() as p:
    print('== A. Een set als die van Jay ==')
    zips = maak_set(UIT, N, gebieden=max(1, N * 5 // 6))
    eis('%d pocket-ZIP\'s gemaakt' % len(zips), len(zips) == N)

    print('\n== B. Laden via de dropzone, met voortgang ==')
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1400, 'height': 900}); ctx.route('**/*', route)
    ctx.add_init_script(VOORTGANG)
    pg = ctx.new_page(); fouten = []
    pg.on('pageerror', lambda e: fouten.append(e.message[:200])); pg.on('dialog', lambda d: d.accept())
    pg.goto(BASIS + 'telrapport.html', wait_until='load'); pg.wait_for_timeout(800)
    t = time.time()
    pg.set_input_files('#file-input', zips)
    pg.wait_for_function('Object.keys(sessions).length === %d && !/laden|tekenen/.test(document.getElementById("dropzone").innerText)' % N,
                         timeout=600000, polling=100)
    laden = time.time() - t
    dz = pg.evaluate('window.__dz')
    eis('%d tellingen geladen in %.1f s (grens %d s)' % (N, laden, GRENS_LADEN_S), laden < GRENS_LADEN_S, laden)
    eis('voortgang tijdens het laden ("⏳ laden… k/%d"), ook halverwege' % N,
        any('laden… 1/%d' % N in x for x in dz) and any('laden… %d/%d' % (N // 2, N) in x for x in dz), dz[:6])
    eis('en daarna "⏳ kaart tekenen…"', any('kaart tekenen' in x for x in dz), dz[-4:])
    eis('na het tekenen weer de gewone dropzone', not any(w in dz[-1] for w in ('laden', 'tekenen')), dz[-1:])

    print('\n== C. De opzoeklijsten kloppen met alles langs lopen ==')
    ix = pg.evaluate(INDEX)
    print('  %d tellingen met wegvakken, %d wegvakken, %d bezochte stukken' % (ix['tellingen'], ix['wegvakken'], ix['bezochteStukken']))
    eis('wegvakkenVan en bezoekenOp = alles langs lopen', ix['nFouten'] == 0, ix['fouten'])

    print('\n== D. Bollen, tellers en kwaliteitsrapport ==')
    st = pg.evaluate(STAND)
    eis('locaties = het aantal bollen op de kaart (%d)' % st['bollen'], st['locaties'] == st['bollen'] and st['bollen'] > 0, st)
    eis('tikken in de bollen = clusterDekking, opgeteld (%d)' % st['tikken'], st['tikken'] == st['dekking'] and st['tikken'] > 0, st)
    eis('sessies = %d' % N, st['sessies'] == N, st)
    ms_uit = tijd(pg, "document.getElementById('cluster-toggle').click()")
    st = pg.evaluate(STAND)
    eis('bollen uit: locaties 0 (bleef tot v3.49 op het oude getal)', st['locaties'] == 0 and st['bollen'] == 0, st)
    ms_aan = tijd(pg, "document.getElementById('cluster-toggle').click()")
    st2 = pg.evaluate(STAND)
    eis('bollen weer aan: hetzelfde als voorheen', st2['bollen'] > 0 and st2['locaties'] == st2['bollen'], st2)

    print('\n== E. Hover over een wegvak: de kleur komt terug ==')
    h = pg.evaluate("""(() => {
      const k = Object.keys(wayLayers).filter(k => wayHeat(k))[0];
      const l = wayLayers[k], voor = [l.options.color, l.options.weight, l.options.opacity];
      wayHitLayers[k].fire('mouseover', { latlng: l.getLatLngs()[0] });
      const tijdens = [l.options.weight, l.options.opacity];
      wayHitLayers[k].fire('mouseout');
      const na = [l.options.color, l.options.weight, l.options.opacity];
      return { voor, tijdens, na };
    })()""")
    eis('tijdens de hover dik (6), daarna weer zoals ervoor', h['tijdens'] == [6, 1] and h['na'] == h['voor'], h)

    print('\n== F. Acties binnen ruime grenzen ==')
    acties = [('bollen uit', ms_uit), ('bollen aan', ms_aan)]
    for naam, js in [
        ('tijdfilter aan', "(() => { document.getElementById('time-slider').value = 12; document.getElementById('time-toggle').click(); })()"),
        ('tijdfilter schuiven', "(() => { const s = document.getElementById('time-slider'); s.value = 14; s.dispatchEvent(new Event('input')); })()"),
        ('tijdfilter uit', "document.getElementById('time-toggle').click()"),
        ('groep Winkelstraat uit', "toggleGroupVisibility('pocket:winkelstraat')"),
        ('groep Winkelstraat aan', "toggleGroupVisibility('pocket:winkelstraat')"),
        ('clusterafstand 15 m', "(() => { const s = document.getElementById('gap-slider'); s.value = 15; s.dispatchEvent(new Event('input')); })()")]:
        acties.append((naam, tijd(pg, js))); pg.wait_for_timeout(100)
    for naam, ms in acties:
        eis('%-24s %6.0f ms (grens %d)' % (naam, ms, GRENS_ACTIE_MS), ms < GRENS_ACTIE_MS)
    st = pg.evaluate(STAND)
    eis('na alles: locaties en kwaliteitsrapport kloppen nog', st['locaties'] == st['bollen'] and st['tikken'] == st['dekking'], st)
    eis('geen JS-fouten in telrapport', not fouten, fouten)
    b.close()

print('\n' + ('ALLE %d TESTS OK' % ok if not fout else '%d ok, %d FOUT' % (ok, fout)))
sys.exit(1 if fout else 0)
