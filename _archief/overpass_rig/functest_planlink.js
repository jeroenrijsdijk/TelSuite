/* v3.14 functionele test — een planning als link (blok planlink).
   Knipt het gedeelde blok uit telplanning.html (byte-gelijkheid met de drie
   veld-apps bewaakt valideer.py) en controleert:
     A. het blok staat in alle vier de bestanden, en is daar gelijk;
     B. heen en terug: een planning in een link en er weer uit, alle velden,
        coördinaten binnen 1 m, ook met lastige tekens en een negatieve lengte;
     C. de polyline zelf: de bekende voorbeeldwaarde van Google;
     D. de link: welke app bij welk teltype, en het '#'-deel (pocket #parkeren&plan=);
     E. kapotte links: afgebroken, onzin, een punt erachter, een nieuwere versie;
     F. de lengte van een wijk van 40 straten (moet ruim onder PLANLINK_LANG blijven).
   Draaien vanuit de suite-root (geen modules nodig; Node 18+):
     node _archief/overpass_rig/functest_planlink.js                          */
const fs = require('fs');
const vm = require('vm');

const START = '/* ── Planning als link (v3.14) ──';
const EIND = '/* ── einde gedeeld blok planlink ── */';
function knip(bestand) {
  const html = fs.readFileSync(bestand, 'utf8');
  const i = html.indexOf(START); if (i < 0) return null;
  const j = html.indexOf(EIND, i); if (j < 0) return null;
  return html.slice(i, j + EIND.length);
}
const blok = knip('telplanning.html');
const ctx = { Math, String, Number, JSON, Array, Object, Promise, Error, Uint8Array, isFinite,
  TextEncoder, TextDecoder, CompressionStream, DecompressionStream, Response, Blob, URL, btoa, atob, console };
vm.createContext(ctx);
vm.runInContext(blok + `
this.P = { planlinkInpakken, planlinkUitpakken, planlinkUitHash, planlinkUrl, planlinkPolyline,
           planlinkPolylineTerug, planlinkWktCoords, PLANLINK_LANG, PLANLINK_APP, PLANLINK_VERSIE };`, ctx);
const P = ctx.P;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const getallen = wkt => (wkt.match(/-?\d+(\.\d+)?/g) || []).map(Number);
const maxVerschil = (a, b) => a.length !== b.length ? Infinity : Math.max(...a.map((v, i) => Math.abs(v - b[i])));

// een kleine wijk, met een weg zonder naam en een weg ten westen van Greenwich
const wegen = [
  { osm_way_id: '123456789', naam: 'Dorpsstraat', highway: 'residential',
    geometrie_wkt: 'LINESTRING (4.321234 51.851234, 4.322345 51.852345, 4.323456 51.852001)' },
  { osm_way_id: '987654321', naam: "Prins Hendrikkade & 't Hof #2 (één)", highway: 'living_street',
    geometrie_wkt: 'LINESTRING (4.330000 51.850000, 4.330100 51.850050)' },
  { osm_way_id: '42', naam: '(service)', highway: 'service',
    geometrie_wkt: 'LINESTRING (-0.127758 51.507351, -0.127000 51.508000, -0.126500 51.507800)' }
];
const planning = { sessie_naam: 'Spijkenisse centrum — ochtend', datum: '2026-10-20', tijdstip: '08:45',
  teller: 'T01', tel_type: 'pocket', aangemaakt: '2026-10-18T09:00:00', n_wegen: 3, wegen };

(async () => {
  console.log('\n== A. het blok in vier bestanden ==');
  const bestanden = ['telplanning.html', 'parkeertelling.html', 'fietsparkeren.html', 'pocket_count.html'];
  const blokken = bestanden.map(knip);
  eis('het blok staat in alle vier', blokken.every(b => b), bestanden.filter((f, i) => !blokken[i]));
  eis('en is overal gelijk', blokken.every(b => b === blok));

  console.log('\n== B. heen en terug ==');
  const waarde = await P.planlinkInpakken(planning);
  eis('vorm: versie, punt, base64url', /^1\.[A-Za-z0-9_-]+$/.test(waarde), waarde.slice(0, 30));
  const terug = await P.planlinkUitpakken(waarde);
  eis('naam, datum, tijdstip, teller, teltype', terug.sessie_naam === planning.sessie_naam &&
    terug.datum === planning.datum && terug.tijdstip === planning.tijdstip &&
    terug.teller === planning.teller && terug.tel_type === 'pocket', terug);
  eis('drie wegen, n_wegen klopt', terug.wegen.length === 3 && terug.n_wegen === 3);
  eis('id, naam (met &, #, \' en é) en highway', terug.wegen.every((w, i) =>
    w.osm_way_id === wegen[i].osm_way_id && w.naam === wegen[i].naam && w.highway === wegen[i].highway),
    terug.wegen.map(w => w.naam));
  const verschil = Math.max(...terug.wegen.map((w, i) => maxVerschil(getallen(w.geometrie_wkt), getallen(wegen[i].geometrie_wkt))));
  eis('coördinaten binnen 0,00001° (~1 m), ook west van Greenwich', verschil <= 0.0000051, verschil);
  eis('geometrie weer als WKT, lon lat, zoals de apps hem lezen',
    /^LINESTRING \(-0\.12776 51\.50735, /.test(terug.wegen[2].geometrie_wkt), terug.wegen[2].geometrie_wkt);
  const leeg = await P.planlinkUitpakken(await P.planlinkInpakken({ wegen: [] }));
  eis('lege planning: teltype auto, geen wegen', leeg.tel_type === 'auto' && leeg.wegen.length === 0 && leeg.teller === '', leeg);

  console.log('\n== C. polyline ==');
  // Voorbeeld uit de documentatie van Google
  const google = [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]];
  eis('codering gelijk aan het voorbeeld van Google', P.planlinkPolyline(google) === '_p~iF~ps|U_ulLnnqC_mqNvxq`@',
    P.planlinkPolyline(google));
  eis('en terug', JSON.stringify(P.planlinkPolylineTerug('_p~iF~ps|U_ulLnnqC_mqNvxq`@')) === JSON.stringify(google));
  eis('WKT lezen: lon lat wordt [lat, lon]', JSON.stringify(P.planlinkWktCoords('LINESTRING (4.3 51.8, 4.4 51.9)')) === '[[51.8,4.3],[51.9,4.4]]');

  console.log('\n== D. de link ==');
  const basis = 'https://telonline.org/telplanning.html';
  eis('auto → parkeertelling, #plan=', P.planlinkUrl(basis, 'auto', '1.abc') === 'https://telonline.org/parkeertelling.html#plan=1.abc');
  eis('fiets → fietsparkeren', P.planlinkUrl(basis, 'fiets', '1.abc') === 'https://telonline.org/fietsparkeren.html#plan=1.abc');
  eis('pocket → pocket_count.html#parkeren&plan=', P.planlinkUrl(basis, 'pocket', '1.abc') === 'https://telonline.org/pocket_count.html#parkeren&plan=1.abc');
  eis('onbekend teltype → parkeertelling', P.planlinkUrl(basis, 'xyz', '1.abc') === 'https://telonline.org/parkeertelling.html#plan=1.abc');
  eis('telplanning in een submap: de app ernaast', P.planlinkUrl('http://localhost:8000/suite/telplanning.html?x=1', 'auto', '1.a') === 'http://localhost:8000/suite/parkeertelling.html#plan=1.a');
  eis('hash #plan=…', P.planlinkUitHash('#plan=1.abc') === '1.abc');
  eis('hash #parkeren&plan=…', P.planlinkUitHash('#parkeren&plan=1.abc') === '1.abc');
  eis('hash #parkeren zonder planning → null', P.planlinkUitHash('#parkeren') === null);
  eis('geen hash → null', P.planlinkUitHash('') === null && P.planlinkUitHash(undefined) === null);
  const echt = P.planlinkUrl(basis, 'pocket', waarde);
  const viaUrl = await P.planlinkUitpakken(P.planlinkUitHash(new URL(echt).hash));
  eis('een echte link via URL en hash terug naar de planning', viaUrl.wegen.length === 3 && viaUrl.sessie_naam === planning.sessie_naam);

  console.log('\n== E. kapotte links ==');
  const melding = async w => { try { await P.planlinkUitpakken(w); return 'geen fout'; } catch (e) { return e.message; } };
  eis('afgebroken link (helft): beschadigd of afgebroken', /beschadigd of afgebroken/.test(await melding(waarde.slice(0, Math.floor(waarde.length / 2)))), await melding(waarde.slice(0, Math.floor(waarde.length / 2))));
  eis('onzin na de versie: beschadigd', /beschadigd/.test(await melding('1.ditisgeenplanning')), await melding('1.ditisgeenplanning'));
  eis('zonder versie: onvolledig', /onvolledig/.test(await melding('abc')), await melding('abc'));
  eis('leeg: onvolledig', /onvolledig/.test(await melding('')), await melding(''));
  eis('versie 2: uit een nieuwere versie', /nieuwere versie/.test(await melding('2.' + waarde.slice(2))), await melding('2.' + waarde.slice(2)));
  const metPunt = await P.planlinkUitpakken(waarde + ').');
  eis('een punt of haakje achter de link (mailprogramma) mag', metPunt.wegen.length === 3);

  console.log('\n== F. lengte van een wijk ==');
  let zaad = 7; const rnd = () => (zaad = (zaad * 16807) % 2147483647) / 2147483647;
  const namen = ['Dorpsstraat', 'Kerkstraat', 'Molenweg', 'Schoolstraat', 'Julianalaan', 'Beatrixstraat', 'Prins Hendrikkade', 'Van der Waalsstraat'];
  const wijk = [];
  for (let i = 0; i < 40; i++) {
    let lat = 51.85 + rnd() * 0.01, lon = 4.32 + rnd() * 0.015; const pts = [];
    for (let j = 0, n = 6 + Math.floor(rnd() * 5); j < n; j++) {
      lat += (rnd() - 0.5) * 0.0008; lon += (rnd() - 0.5) * 0.0012; pts.push(lon.toFixed(6) + ' ' + lat.toFixed(6));
    }
    wijk.push({ osm_way_id: String(100000000 + Math.floor(rnd() * 9e8)), naam: namen[i % 8],
      highway: i % 5 ? 'residential' : 'service', geometrie_wkt: 'LINESTRING (' + pts.join(', ') + ')' });
  }
  const lang = P.planlinkUrl(basis, 'auto', await P.planlinkInpakken({ sessie_naam: 'Wijk', wegen: wijk }));
  console.log('       40 straten, ~320 punten: ' + lang.length + ' tekens');
  eis('40 straten: link ruim onder de grens van ' + P.PLANLINK_LANG + ' tekens', lang.length < P.PLANLINK_LANG / 2, lang.length);

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
  process.exit(fout ? 1 : 0);
})().catch(e => { console.log('FOUT ' + e.stack); process.exit(1); });
