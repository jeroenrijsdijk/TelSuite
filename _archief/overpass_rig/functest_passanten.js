/* v3.34 functionele test — de rekenkern van Passanten per uur (gedeeld blok
   PASSANTEN in passanten.html en winkelstraat_rekenrig.html), los van de browser.
   q = 3600 · Σm / Σ(L/v + t), per looprichting gepoold en dan opgeteld; v = 1,1 m/s.
   v3.40: gaatjes tussen passages in het midden gedeeld (hooguit 5 s per kant). */
const fs = require('fs');
const vm = require('vm');
function blok(bestand) {
  const html = fs.readFileSync(bestand, 'utf8');
  const a = '/* ── Passanten per uur: de rekenkern (v3.34)', z = '/* ── einde gedeeld blok passanten ── */';
  const i = html.indexOf(a), j = html.indexOf(z);
  if (i < 0 || j < 0) throw new Error('blok PASSANTEN niet gevonden in ' + bestand);
  return html.slice(i, j + z.length);
}
const tekst = blok('passanten.html');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(tekst + '\nthis.P = PASSANTEN;', ctx);
const P = ctx.P;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const bijna = (a, b) => Math.abs(a - b) < 1e-9;

// Een rechte straat langs de evenaar: 0,001° lengte = 111,195 m (haversine, R = 6371 km).
const GRAAD = 2 * Math.PI * 6371000 / 360;
const L40 = 40 / GRAAD;                       // 40 m in graden
const net = (way, n) => Array.from({ length: n }, (_, s) => ({ osm_way_id: String(way), segment_index: String(s),
  geometrie_wkt: 'LINESTRING (' + (s * L40) + ' 0, ' + ((s + 1) * L40) + ' 0)' }));
const bez = (datum, way, seg, van, tot) => ({ datum, osm_way_id: String(way), segment_index: String(seg), straat: 'Teststraat',
  start_tijd: van, eind_tijd: tot, duur_sec: String(sec(tot) - sec(van)) });
const tik = (datum, way, seg, tijd, type) => ({ osm_way_id: String(way), segment_index: String(seg), tijdstip: datum + 'T' + tijd, type });
function sec(h) { const p = h.split(':').map(Number); return p[0] * 3600 + p[1] * 60 + (p[2] || 0); }
function tel(datum, way, seg, van, n, type) {   // n tikken vanaf van, om de seconde
  return Array.from({ length: n }, (_, i) => { const s = sec(van) + 1 + i; return tik(datum, way, seg, [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60].map(x => String(x).padStart(2, '0')).join(':'), type); });
}
function reken(sessies, v) {
  const segs = {};
  sessies.forEach(d => P.voegToe(segs, P.sessie(d, 'x.zip')));
  return P.bereken(segs, v);
}

console.log('== de formule ==');
eis('standaard loopsnelheid 1,1 m/s (Jay, v3.34)', P.V_VOET === 1.1);
eis('de lengte uit de WKT: 40 m', bijna(P.polyLengte(P.wktPunten('LINESTRING (0 0, ' + L40 + ' 0)')), 40));
let d = { sessie: [{ sessie_id: 's1', datum: '2026-10-24' }], netwerk: net(1, 1), gps: [],
  bezocht: [bez('2026-10-24', 1, 0, '13:00:00', '13:00:30')], telregels: tel('2026-10-24', 1, 0, '13:00:00', 10, 'tegemoet') };
let c = reken([d])['1/0'].cells['5:13'];
eis('één passage van 30 s over 40 m met 10 tegenliggers: 3600 · 10 / (40/1,1 + 30)', bijna(c.q, 3600 * 10 / (40 / 1.1 + 30)), c.q);
eis('een andere loopsnelheid geeft een andere waarde (1,3 m/s)', bijna(reken([d], 1.3)['1/0'].cells['5:13'].q, 3600 * 10 / (40 / 1.3 + 30)));
eis('cel = weekdag:uur, zaterdag = 5, uur 13', Object.keys(reken([d])['1/0'].cells).join() === '5:13');

console.log('\n== poolen: eerst optellen, dan delen ==');
const d2 = { sessie: [{ sessie_id: 's2', datum: '2026-10-17' }], netwerk: net(1, 1), gps: [],
  bezocht: [bez('2026-10-17', 1, 0, '13:10:00', '13:12:00')], telregels: tel('2026-10-17', 1, 0, '13:10:00', 20, 'tegemoet') };
c = reken([d, d2])['1/0'].cells['5:13'];
const w1 = 40 / 1.1 + 30, w2 = 40 / 1.1 + 120;
eis('twee zaterdagen (17 en 24 okt) worden één cel, met beide datums', c.n === 2 && c.datums.join() === '2026-10-17,2026-10-24', c.datums);
eis('ratio of sums: 3600 · (10 + 20) / (venster1 + venster2)', bijna(c.q, 3600 * 30 / (w1 + w2)), c.q);
eis('en dus niet het gemiddelde van de twee losse waarden', Math.abs(c.q - (3600 * 10 / w1 + 3600 * 20 / w2) / 2) > 10);

console.log('\n== looprichting ==');
const heenTerug = { sessie: [{ sessie_id: 's3', datum: '2026-10-22' }], netwerk: net(2, 2), gps: [],
  bezocht: [bez('2026-10-22', 2, 0, '11:00:00', '11:00:40'), bez('2026-10-22', 2, 1, '11:00:41', '11:01:20'),
            bez('2026-10-22', 2, 1, '11:01:21', '11:02:00'), bez('2026-10-22', 2, 0, '11:02:01', '11:02:40')],
  telregels: tel('2026-10-22', 2, 0, '11:00:00', 4, 'tegemoet').concat(tel('2026-10-22', 2, 0, '11:02:01', 6, 'tegemoet')) };
const s3 = P.sessie(heenTerug, 'x.zip');
eis('richting uit de volgorde: 0→1 is A, 1→0 is B', s3.visits.map(v => v.richting).join('') === 'AABB', s3.visits.map(v => v.richting + ':' + v.richtingBron));
c = reken([heenTerug])['2/0'].cells['3:11'];
// v3.40: tussen de passages zit steeds 1 s; elke kant krijgt een halve seconde erbij
eis('heen en terug: twee stromen opgeteld, compleet', c.compleet && bijna(c.q, 3600 * 4 / (40 / 1.1 + 40.5) + 3600 * 6 / (40 / 1.1 + 39.5)) && c.labels.join() === 'B→A,A→B', [c.q, c.labels]);
const enkel = (gps) => ({ sessie: [{ sessie_id: 's4', datum: '2026-10-22' }], netwerk: net(3, 1), gps,
  bezocht: [bez('2026-10-22', 3, 0, '11:00:00', '11:00:40')], telregels: tel('2026-10-22', 3, 0, '11:00:00', 3, 'tegemoet') });
const fix = (t, x) => ({ tijdstip: '2026-10-22T' + t, lat: '0', lon: String(x / GRAAD) });
let v = P.sessie(enkel([fix('11:00:01', 2), fix('11:00:39', 38)]), 'x').visits[0];
eis('één passage op een weg: richting uit de GPS (+36 m is A)', v.richting === 'A' && /^gps \+36 m$/.test(v.richtingBron), v.richtingBron);
v = P.sessie(enkel([fix('11:00:01', 38), fix('11:00:39', 2)]), 'x').visits[0];
eis('en terug (−36 m is B)', v.richting === 'B', v.richtingBron);
v = P.sessie(enkel([fix('11:00:01', 20), fix('11:00:39', 25)]), 'x').visits[0];
eis('minder dan 8 m verschil: richting onbekend', v.richting === null && /te klein/.test(v.richtingBron), v.richtingBron);
c = reken([enkel([fix('11:00:01', 20), fix('11:00:39', 25)])])['3/0'].cells['3:11'];
eis('onbekende richting telt mee, maar de cel is niet compleet', !c.compleet && c.labels.join() === '?' && bijna(c.q, 3600 * 3 / (40 / 1.1 + 40)), c.labels);

console.log('\n== stilstaanders, wezen, randen ==');
const stil = { sessie: [{ sessie_id: 's5', datum: '2026-10-24' }], netwerk: net(4, 1), gps: [],
  bezocht: [bez('2026-10-24', 4, 0, '13:00:00', '13:00:30')],
  telregels: tel('2026-10-24', 4, 0, '13:00:00', 3, 'stilstaand').concat([tik('2026-10-24', 4, 0, '13:05:00', 'tegemoet')]) };
const s5 = P.sessie(stil, 'x');
c = reken([stil])['4/0'].cells['5:13'];
eis('stilstaanders: per 100 m, zonder snelheid (3 op 40 m = 7,5)', bijna(c.kStil, 7.5) && c.m === 0 && c.q === 0, c.kStil);
eis('een tik buiten elke passage telt niet mee (een wees)', s5.nWees === 1 && s5.nGekoppeld === 3, [s5.nWees, s5.nGekoppeld]);
const middag = { sessie: [{ sessie_id: 's6', datum: '2026-10-24' }], netwerk: net(5, 1), gps: [],
  bezocht: [bez('2026-10-24', 5, 0, '12:59:40', '13:00:40')], telregels: [] };
eis('het uur van het midden van de passage: 12:59:40–13:00:40 is uur 13', Object.keys(reken([middag])['5/0'].cells).join() === '5:13');
const leeg = { sessie: [{ sessie_id: 's7', datum: '2026-10-24' }], netwerk: [], gps: [],
  bezocht: [bez('2026-10-24', 6, 0, '13:00:00', '13:00:30')], telregels: [] };
eis('een passage zonder geometrie (L = 0) valt weg', P.sessie(leeg, 'x').visits.length === 0);

console.log('\n== gaatjes tussen passages (v3.40) ==');
eis('hooguit 5 s per kant', P.GAT_MAX === 5);
const gat = (tussen, tikken) => ({ sessie: [{ sessie_id: 's8', datum: '2026-10-24' }], netwerk: net(7, 2), gps: [],
  bezocht: [bez('2026-10-24', 7, 0, '13:00:00', '13:00:30'), bez('2026-10-24', 7, 1, tussen, '13:01:30')],
  telregels: tikken.map(([tijd, seg, type]) => tik('2026-10-24', 7, seg, tijd, type || 'tegemoet')) });
let s8 = P.sessie(gat('13:00:34', [['13:00:31', 1], ['13:00:33', 1], ['13:00:32', 0, 'stilstaand']]), 'x');
eis('een gaatje van 4 s: elke passage krijgt 2 s erbij (t 32 en 58), de GPS-tijden blijven',
    s8.visits[0].t === 32 && s8.visits[1].t === 58 && s8.visits[0].tot === sec('13:00:32') && s8.visits[1].van === sec('13:00:32')
    && s8.visits[0].t1 === sec('13:00:30') && s8.visits[1].t0 === sec('13:00:34'), s8.visits.map(v => [v.t, v.van, v.tot]));
eis('de tikken in het gaatje tellen mee, op tijd: 13:00:31 bij de eerste (ook al zette de reconstructie hem bij het buurstuk), 13:00:33 bij de tweede',
    s8.visits[0].teg === 1 && s8.visits[1].teg === 1 && s8.nWees === 0, s8.visits.map(v => v.teg));
eis('op de grens (13:00:32, het midden) telt een tik bij de eerste passage', s8.visits[0].stil === 1 && s8.visits[1].stil === 0);
s8 = P.sessie(gat('13:01:00', [['13:00:34', 0], ['13:00:45', 1], ['13:00:56', 1]]), 'x');
eis('een gat van 30 s: 5 s per kant (t 35 en 35); het midden blijft leeg, een tik daar is een wees',
    s8.visits[0].t === 35 && s8.visits[1].t === 35 && s8.visits[0].teg === 1 && s8.visits[1].teg === 1 && s8.nWees === 1,
    [s8.visits.map(v => [v.t, v.teg]), s8.nWees]);
c = reken([gat('13:00:34', [['13:00:31', 1], ['13:00:33', 1]])])['7/0'].cells['5:13'];
eis('en dat zit in de formule: 3600 · 1 / (40/1,1 + 32)', bijna(c.q, 3600 * 1 / (40 / 1.1 + 32)), c.q);
eis('het uur volgt de GPS-tijden: een passage van 12:59:50 tot 13:00:30 met een gaatje ervoor blijft uur 13',
    Object.keys(reken([{ sessie: [{ sessie_id: 's9', datum: '2026-10-24' }], netwerk: net(8, 2), gps: [],
      bezocht: [bez('2026-10-24', 8, 0, '12:59:00', '12:59:30'), bez('2026-10-24', 8, 1, '12:59:50', '13:00:30')], telregels: [] }])['8/1'].cells).join() === '5:13');

console.log('\n== hetzelfde blok in het rekenrig ==');
eis('winkelstraat_rekenrig.html heeft precies dezelfde rekenkern', blok('winkelstraat_rekenrig.html') === tekst);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
