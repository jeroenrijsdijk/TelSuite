/* v3.41 functionele test — _bezocht.csv uit de gereconstrueerde route
   (herbouwBezocht in telreconstructie.html), los van de browser.

   Jay: "een stukje van 15 meter zijn eigen passage - dat wil ik graag".
   Een reeks gps-punten die de drempels (5 s, 3 punten) niet haalt, blijft toch
   een passage als je erdoorheen liep (de reeks ervoor en erna op verschillende
   wegen, en geen van beide op de weg van dit stuk), het stuk hooguit 20 m is,
   en er minstens 2 punten zijn (anders duur 0, en KNIME deelt door duur_sec).

   v3.45: erdoorheen. Jay, over een autorit: "Waarom zijn er heel veel linkjes
   die niet als bezocht zijn gemarkeerd?" Een reeks telt ook als je minstens de
   helft van het stuk zag (de punten, en het midden van het gaatje naar de buren
   als dat hooguit 5 s is, op het stuk gelegd), en de duur minstens 1 s.
   En nooit duur 0: twee punten kunnen in dezelfde seconde vallen.

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
eis('versiestempel van de reconstructor: v3.45', ctx.RECON_VERSIE === 'v3.45');

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

console.log('\n== erdoorheen (v3.45) ==');
// punten met een plek: [weg, stuk, seconde, meter langs de weg naar het noorden, meter naar het oosten]
function rijd(punten, tikken) {
  const events = punten.map(([w, st, t, y, x = 0]) => ({ kind: 'gps', t: 43200 + t, ts: ts(t), lat: y * M, lon: x * M, _match: w ? { wayId: w, segIdx: st } : null }));
  ctx.S = { sid: 's', sessieRow: { datum: '2026-10-31' }, gps: [], telregels: [],
            taps: (tikken || []).map(([w, st, t]) => ({ wayId: w, segIdx: st, status: 'ok', src: { tijdstip: ts(t) } })) };
  return ctx.herbouwBezocht(events, NET, segCount);
}
// de auto over weg A (3 stukken van 40 m) en B, 10 m/s, elke seconde een punt
const auto = []; for (let t = 0; t <= 20; t++) { const y = 10 * t; auto.push(y < 120 ? ['A', Math.floor(y / 40), t, y] : y < 135 ? ['X', 0, t, y] : ['B', Math.floor((y - 135) / 40), t, y]); }
r = rijd(auto, [['A', 1, 5]]);
eis('auto, 10 m/s: elk stuk van 40 m 3-4 s en 4 punten, toch bezocht (A/0, A/1, A/2, B/0)', ['A/0', 'A/1', 'A/2', 'B/0'].every(k => sleutels(r).split(' ').includes(k)), sleutels(r));
const a1 = r.find(x => x.osm_way_id === 'A' && x.segment_index === 1);
eis('met de tijden van de punten (12:00:04-12:00:07, 3 s) en de tik', a1 && a1.start_tijd === '12:00:04' && a1.eind_tijd === '12:00:07' && a1.duur_sec === 3 && a1.n_gps === 4 && a1.n_tellingen === 1, a1);
eis('het korte stukje X ertussen (15 m, 2 punten, 1 s): ook bezocht', sleutels(r).includes('X/0') && r.find(x => x.osm_way_id === 'X').duur_sec === 1, sleutels(r));
r = rijd([['A', 1, 0, 50], ['A', 1, 1, 51], ['A', 1, 2, 52], ['A', 1, 3, 53], ['A', 1, 4, 54], ['A', 1, 5, 55], ['A', 1, 6, 56],
          ['Y', 0, 7, 120, 50], ['Y', 0, 8, 121, 50], ['A', 1, 9, 57], ['A', 1, 10, 58], ['A', 1, 11, 59], ['A', 1, 12, 60], ['A', 1, 13, 61], ['A', 1, 14, 62]]);
eis('een gps-sprong opzij (2 punten op Y, 1 m van de 30 m, een sprong van 80 m erheen): niet bezocht', sleutels(r) === 'A/1 A/1', sleutels(r));
r = rijd([['A', 1, 0, 50], ['A', 1, 1, 60], ['A', 1, 2, 70], ['A', 1, 3, 78], ['Y', 0, 4, 121, 50], ['Y', 0, 5, 123, 50], ['B', 0, 6, 140], ['B', 0, 7, 150], ['B', 0, 8, 160]]);
eis('de hoek van Y afgesneden (2 punten, 2 m van de 30 m, eraf naar B): niet bezocht', !sleutels(r).includes('Y/0'), sleutels(r));
r = rijd([['A', 1, 0, 42], ['A', 1, 1, 43], ['A', 1, 2, 44], ['A', 1, 3, 45], ['A', 1, 4, 46], ['A', 1, 5, 47],
          ['A', 2, 6, 81], ['A', 2, 7, 82],
          ['B', 0, 30, 140], ['B', 0, 31, 141], ['B', 0, 32, 142], ['B', 0, 33, 143], ['B', 0, 34, 144], ['B', 0, 35, 145]]);
eis('een gaatje van meer dan 5 s telt niet mee: A/2 met 1 m afgelegd en een sprong van 23 s erna, niet bezocht', !sleutels(r).includes('A/2'), sleutels(r));
r = rijd([['A', 2, 0, 81], ['A', 2, 1, 86], ['A', 2, 2, 91], ['A', 2, 3, 96], ['A', 2, 4, 101], ['A', 2, 5, 106],
          ['X', 0, 6, 122], ['X', 0, 6, 126],
          ['B', 0, 7, 140], ['B', 0, 8, 145], ['B', 0, 9, 150], ['B', 0, 10, 155], ['B', 0, 11, 160], ['B', 0, 12, 165]]);
eis('twee punten in dezelfde seconde op X (15 m, een doorgang): geen bezoek meer (v3.41 gaf duur 0)', !sleutels(r).includes('X/0') && r.every(x => x.duur_sec > 0), r.map(x => [sleutels([x]), x.duur_sec]));
r = rijd([['A', 0, 0, 0], ['A', 0, 4, 5], ['A', 0, 8, 10], ['A', 0, 12, 15], ['A', 0, 16, 20], ['A', 0, 20, 25], ['A', 0, 24, 30], ['A', 0, 28, 35],
          ['A', 1, 32, 40], ['A', 1, 36, 45], ['A', 1, 40, 50]]);
eis('lopend zoals altijd: een reeks van 5 s en 3 punten', sleutels(r) === 'A/0 A/1', sleutels(r));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
