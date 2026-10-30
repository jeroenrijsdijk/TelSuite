/* v3.41 functionele test — _bezocht.csv uit de gereconstrueerde route
   (herbouwBezocht in telreconstructie.html), los van de browser.

   Jay: "een stukje van 15 meter zijn eigen passage - dat wil ik graag".
   Een reeks gps-punten die de drempels (5 s, 3 punten) niet haalt, blijft toch
   een passage als je erdoorheen liep (de reeks ervoor en erna op verschillende
   wegen, en geen van beide op de weg van dit stuk), het stuk hooguit 20 m is,
   en er minstens 2 punten zijn (anders duur 0, en KNIME deelt door duur_sec).

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_bezocht.js */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telreconstructie.html', 'utf8');

// Een functie uit de pagina knippen, op haar naam, tot de bijbehorende sluitaccolade.
function functie(naam) {
  const i = html.indexOf('function ' + naam + '(');
  if (i < 0) throw new Error('functie niet gevonden: ' + naam);
  let j = html.indexOf('{', i), diep = 0;
  for (; j < html.length; j++) {
    if (html[j] === '{') diep++;
    else if (html[j] === '}' && --diep === 0) return html.slice(i, j + 1);
  }
  throw new Error('geen einde voor ' + naam);
}
const regel = re => { const m = re.exec(html); if (!m) throw new Error('niet gevonden: ' + re); return m[0]; };
const ctx = { S: null };
vm.createContext(ctx);
vm.runInContext([
  regel(/var SEGMENT_TARGET_M = [^;]+;/), regel(/var SEGMENT_MIN_M = [^;]+;/), regel(/var RECON_VERSIE = [^;]+;/),
  functie('_normPt'), functie('splitWayIntoSegments'), functie('tsec'), functie('hhmmss'), functie('herbouwBezocht')
].join('\n') + '\nthis.herbouwBezocht = herbouwBezocht; this.split = splitWayIntoSegments; this.RECON_VERSIE = RECON_VERSIE;', ctx);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

// Rechte wegen naar het noorden: 1 m = 1/111320 graad breedte (de knip rekent zo).
const M = 1 / 111320;
const weg = (y0, lengte, x = 0) => ({ geometry: [[y0 * M, x * M], [(y0 + lengte) * M, x * M]] });
const NET = {
  A: weg(0, 120),        // 120 m: 3 stukken van 40 m
  X: weg(120, 15),       // 15 m: één stuk, kort
  B: weg(135, 80),       // 80 m: 2 stukken van 40 m
  Y: weg(120, 30, 50),   // 30 m: één stuk, maar langer dan 20 m
  Z: weg(80, 15, 30)     // 15 m: een zijstraatje
};
const segCount = (w, g) => ctx.split(g).length;
const ts = s => '2026-10-26T12:' + String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
// route: [[weg, stuk, [seconden van de punten]], ...]
function maak(route, tikken) {
  const events = [];
  route.forEach(([w, s, tijden]) => tijden.forEach(t => events.push({ kind: 'gps', t: 43200 + t, ts: ts(t), _match: { wayId: w, segIdx: s } })));
  ctx.S = { sid: 's', sessieRow: { datum: '2026-10-26' }, gps: [], telregels: [],
            taps: (tikken || []).map(([w, s, t]) => ({ wayId: w, segIdx: s, status: 'ok', src: { tijdstip: ts(t) } })) };
  return ctx.herbouwBezocht(events, NET, segCount);
}
const sleutels = rijen => rijen.map(r => r.osm_way_id + '/' + r.segment_index).join(' ');

console.log('== de knip ==');
eis('A is 3 stukken van 40 m, X één stuk van 15 m, Y één stuk van 30 m',
    ctx.split(NET.A.geometry).length === 3 && ctx.split(NET.X.geometry).length === 1 && ctx.split(NET.Y.geometry).length === 1);
eis('versiestempel van de reconstructor: v3.41', ctx.RECON_VERSIE === 'v3.41');

console.log('\n== zoals altijd ==');
let r = maak([['A', 0, [0, 4, 8, 12]], ['A', 1, [16, 20, 24, 28, 32]], ['A', 2, [36, 40, 44, 48]]]);
eis('drie gewone passages over weg A', sleutels(r) === 'A/0 A/1 A/2' && r[1].duur_sec === 16 && r[1].n_gps === 5, r);
eis('begin en eind zijn de tijden van het eerste en laatste punt', r[1].start_tijd === '12:00:16' && r[1].eind_tijd === '12:00:32');

console.log('\n== korte stukjes (v3.41) ==');
r = maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [16, 19]], ['B', 0, [23, 27, 31, 35]]], [['X', 0, 17], ['X', 0, 30]]);
eis('A → X (15 m, 2 punten, 3 s) → B: X is een eigen passage', sleutels(r) === 'A/2 X/0 B/0', sleutels(r));
const x = r[1];
eis('met de tijden van zijn punten (12:00:16–12:00:19, 3 s, 2 punten)', x.start_tijd === '12:00:16' && x.eind_tijd === '12:00:19' && x.duur_sec === 3 && x.n_gps === 2, x);
eis('en de tikken in dat venster (1, niet die van 12:00:30)', x.n_tellingen === 1, x.n_tellingen);
r = maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [17]], ['B', 0, [22, 26, 30, 34]]]);
eis('één punt is niet genoeg: dat zou duur 0 geven (KNIME deelt door duur_sec)', sleutels(r) === 'A/2 B/0', sleutels(r));
eis('nergens een duur van 0 in de uitvoer', [maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [16, 19]], ['B', 0, [23, 27, 31, 35]]]),
    maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [17]], ['B', 0, [22, 26, 30, 34]]])].every(rr => rr.every(x => x.duur_sec > 0)));
r = maak([['A', 2, [0, 4, 8, 12]], ['Y', 0, [16, 19]], ['B', 0, [23, 27, 31, 35]]]);
eis('een stuk van 30 m met een kort bezoek: geen passage (een afgesneden hoek)', sleutels(r) === 'A/2 B/0', sleutels(r));
r = maak([['A', 1, [0, 4, 8, 12]], ['Z', 0, [16]], ['A', 1, [20, 24, 28, 32]]]);
eis('A → Z → A: een uitstapje of gps-ruis, geen passage', sleutels(r) === 'A/1 A/1', sleutels(r));
r = maak([['A', 1, [0, 4, 8, 12]], ['Z', 0, [16, 18]], ['A', 2, [22, 26, 30, 34]]]);
eis('A → Z → A verderop: ook geen passage', sleutels(r) === 'A/1 A/2', sleutels(r));
r = maak([['A', 0, [0, 4, 8, 12]], ['A', 1, [16, 19]], ['B', 0, [23, 27, 31, 35]]]);
eis('een kort bezoek aan een stuk van een lange weg (A/1, 40 m): geen passage', sleutels(r) === 'A/0 B/0', sleutels(r));
r = maak([['X', 0, [0, 3]], ['B', 0, [7, 11, 15, 19]]]);
eis('aan het begin van de route (niets ervoor): geen passage', sleutels(r) === 'B/0', sleutels(r));
r = maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [16, 19]]]);
eis('aan het eind (niets erna): geen passage', sleutels(r) === 'A/2', sleutels(r));
r = maak([['A', 2, [0, 4, 8, 12]], ['X', 0, [16, 19]], ['Z', 0, [22, 24]], ['B', 0, [28, 32, 36, 40]]]);
eis('twee korte stukjes achter elkaar (A → X → Z → B): allebei een passage', sleutels(r) === 'A/2 X/0 Z/0 B/0', sleutels(r));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
