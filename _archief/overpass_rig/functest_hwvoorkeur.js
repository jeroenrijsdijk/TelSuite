/* v2.67 test — de highway-voorkeur van de profielen komt aan bij de matcher.

   Tot v2.67 gaf reconstrueer() de voorkeur als vijfde argument aan
   MATCHER.matchTrajectory, maar die functie had er maar vier. Deze test draait de
   ECHTE matcher en de ECHTE profielen uit telreconstructie.html, in een vm.

   Het scenario is steeds hetzelfde: een rijbaan en een fietspad liggen parallel,
   zonder verbinding. De teller loopt of rijdt op de ene, de GPS ligt een paar
   meter richting de andere.

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_hwvoorkeur.js */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telreconstructie.html', 'utf8');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

function knip(a, b) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j + b.length);
}

// MATCHER, de profielen (met hwPref, RIJBAAN, LANGZAAM) en de log-tekst, zoals ze in de tool staan
const ctx = { S: {} };
vm.createContext(ctx);
vm.runInContext(knip('var MATCHER = (function () {', '\n})();'), ctx);
vm.runInContext(knip('function hwPref(prefer, avoid) {', '\n// leidt een profiel-sleutel af'), ctx);
vm.runInContext(knip('function hwVoorkeurTekst() {', "' / vermijd ' + (tegen.join(',') || '-');\n}"), ctx);
const { MATCHER, PROFIELEN } = ctx;

// ---- netwerkjes -------------------------------------------------------------
const LAT0 = 51.85, LON0 = 4.30, dLat = m => m / 111320;
const lijn = y => [{ lat: LAT0 + dLat(y), lon: LON0 }, { lat: LAT0 + dLat(y), lon: LON0 + 0.0043 }];   // ~300 m
function net(ways) { const n = {}; ways.forEach(([id, y, hw]) => { n[id] = { geometry: lijn(y), highway: hw }; }); return n; }
function adjVan(n) { const a = {}; Object.keys(n).forEach(k => { a[k] = {}; }); return a; }
function spoor(y, n = 20, acc = 5) { const f = []; for (let i = 0; i < n; i++) f.push({ lat: LAT0 + dLat(y), lon: LON0 + i * 0.0002, acc }); return f; }
const seg = () => 1;
function telling(res) { return res.reduce((a, m) => { const k = m ? m.wayId : 'null'; a[k] = (a[k] || 0) + 1; return a; }, {}); }
const auto = PROFIELEN.auto.highwayCost, fiets = PROFIELEN.fiets.highwayCost;

console.log('== de matcher neemt de voorkeur aan ==');
eis('matchTrajectory heeft vijf parameters', MATCHER.matchTrajectory.length === 5, MATCHER.matchTrajectory.length);
eis('reconstrueer() geeft de voorkeur van het profiel mee',
  /MATCHER\.matchTrajectory\(netMatch, adj, events, segCount, S\.profiel\.highwayCost\)/.test(html));

console.log('\n== auto: rijbaan op 0 m, fietspad op 10 m, GPS op 6 m ==');
{
  const n = net([['rijbaan', 0, 'residential'], ['fietspad', 10, 'cycleway']]), a = adjVan(n), f = spoor(6);
  const zonder = telling(MATCHER.matchTrajectory(n, a, f, seg));
  const met = telling(MATCHER.matchTrajectory(n, a, f, seg, auto));
  eis('zonder voorkeur: dichtstbijzijnde wint (fietspad) — het oude gedrag', zonder.fietspad === 20, zonder);
  eis('met auto-voorkeur: de rijbaan', met.rijbaan === 20, met);
}

console.log('\n== fiets: fietspad op 0 m, rijbaan op 10 m, GPS op 6 m ==');
{
  const n = net([['fietspad', 0, 'cycleway'], ['rijbaan', 10, 'residential']]), a = adjVan(n), f = spoor(6);
  const met = telling(MATCHER.matchTrajectory(n, a, f, seg, fiets));
  eis('met fiets-voorkeur: het fietspad', met.fietspad === 20, met);
}

console.log('\n== netjes degraderen ==');
{
  const n = net([['fietspad', 0, 'cycleway']]), a = adjVan(n), f = spoor(3);
  const met = telling(MATCHER.matchTrajectory(n, a, f, seg, auto));
  eis('alleen een fietspad: auto kiest het alsnog (geen null)', met.fietspad === 20, met);
}
{
  const n = net([['rijbaan', 0, ''], ['fietspad', 10, '']]), a = adjVan(n), f = spoor(6);
  const zonder = MATCHER.matchTrajectory(n, a, f, seg);
  const met = MATCHER.matchTrajectory(n, a, f, seg, auto);
  eis('onbekend highway-type: voorkeur telt niet mee', JSON.stringify(zonder) === JSON.stringify(met));
}
{
  const n = net([['rijbaan', 0, 'residential'], ['fietspad', 10, 'cycleway']]), a = adjVan(n), f = spoor(6);
  const zonder = MATCHER.matchTrajectory(n, a, f, seg);
  const leeg = MATCHER.matchTrajectory(n, a, f, seg, () => undefined);
  eis('profiel dat niets teruggeeft (NaN): neutraal', JSON.stringify(zonder) === JSON.stringify(leeg));
}

console.log('\n== bereik: hoe ver trekt de voorkeur? (acc 5 m) ==');
// Emissie = 0.5 (d/5)^2, voorkeur -2, vermijden +4. Staat de teller op 2 m van een
// vermeden weg, dan wint een geprefereerde weg tot ruim 17 m afstand.
{
  const n = net([['rijbaan', 0, 'residential'], ['fietspad', 14, 'cycleway']]), a = adjVan(n), f = spoor(2);
  const met = telling(MATCHER.matchTrajectory(n, a, f, seg, fiets));
  eis('fiets, fietspad 12 m verderop: fietspad wint', met.fietspad === 20, met);
}
{
  const n = net([['rijbaan', 0, 'residential'], ['fietspad', 27, 'cycleway']]), a = adjVan(n), f = spoor(2);
  const met = telling(MATCHER.matchTrajectory(n, a, f, seg, fiets));
  eis('fiets, fietspad 25 m verderop: blijft op de rijbaan', met.rijbaan === 20, met);
}

console.log('\n== wandelprofielen: rekenkundig identiek aan zonder voorkeur ==');
// Rommelig netwerk met gemengde typen, verbindingen en ruis. Deterministisch.
{
  let zaad = 7; const rnd = () => ((zaad = (zaad * 16807) % 2147483647) / 2147483647);
  const typen = ['residential', 'cycleway', 'footway', 'service', 'path', 'tertiary', ''];
  const n = {};
  for (let k = 0; k < 12; k++) {
    const y = (k % 6) * 12 - 30, x0 = LON0 + (k < 6 ? 0 : 0.002);
    n['w' + k] = { geometry: [{ lat: LAT0 + dLat(y), lon: x0 }, { lat: LAT0 + dLat(y + (rnd() - 0.5) * 8), lon: x0 + 0.0025 }], highway: typen[k % typen.length] };
  }
  const a = adjVan(n);
  for (let k = 0; k < 11; k++) { a['w' + k]['w' + (k + 1)] = true; a['w' + (k + 1)]['w' + k] = true; }
  const f = []; for (let i = 0; i < 60; i++) f.push({ lat: LAT0 + dLat((rnd() - 0.5) * 60), lon: LON0 + i * 0.00007, acc: 3 + rnd() * 12 });
  const basis = JSON.stringify(MATCHER.matchTrajectory(n, a, f, seg));
  ['transect', 'winkelstraat', 'simpel', 'pocket-parkeren'].forEach(p => {
    eis(p + ': zelfde pad als zonder voorkeur', JSON.stringify(MATCHER.matchTrajectory(n, a, f, seg, PROFIELEN[p].highwayCost)) === basis);
  });
  eis('auto kiest hier wél anders (de test kan dus iets zien)', JSON.stringify(MATCHER.matchTrajectory(n, a, f, seg, auto)) !== basis);
}

console.log('\n== regel in de reconstructie-log ==');
ctx.S.profiel = PROFIELEN.auto; ctx.S.profielId = 'auto';
const tAuto = ctx.hwVoorkeurTekst();
eis('auto: actief, rijbaan voor, fietspad vermeden',
  /^actief \(auto\) voorkeur residential,.*service \/ vermijd cycleway,footway,pedestrian,path,track$/.test(tAuto), tAuto);
ctx.S.profiel = PROFIELEN.simpel; ctx.S.profielId = 'simpel';
eis('simpel: neutraal', ctx.hwVoorkeurTekst() === 'neutraal', ctx.hwVoorkeurTekst());
eis('de regel staat in de log', /'highway_voorkeur;' \+ hwVoorkeurTekst\(\)/.test(html));

console.log('\n== versiestempel (v2.74) ==');
eis('één RECON_VERSIE-declaratie', (html.match(/^var RECON_VERSIE = 'v\d+\.\d+';$/mg) || []).length === 1);
eis('log gebruikt RECON_VERSIE', /'reconstructie_versie;' \+ RECON_VERSIE/.test(html));
eis('_sessie.csv gebruikt RECON_VERSIE', /r\.richting_b \|\| '', RECON_VERSIE\]\.join/.test(html));
eis('geen bevroren stempels meer', html.indexOf("'v2.24'") < 0 && html.indexOf('reconstructie_versie;v2.18') < 0);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
