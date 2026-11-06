/* v3.43 functionele test — de dagcurve in passanten.html, los van de browser.
   v3.44: de dagcurve van gekozen stukken (Jay: "linkjes kunnen selecteren om
   daarvan dagcurves te zien"; "kiezen per klik plus hele straat is goed"), en
   heleStraat: welke stukken bij een straat horen.

   Jay: "zou je uit een grote set winkelstraat tellingen ook algemenere
   dagcurves kunnen maken? wat basisdata om factoren uit te halen."
   Het model: verwachte tegemoetkomers = venster/3600 · A[stuk|richting] ·
   F[dagtype:uur] · D[weekdag], geschat met iterative proportional fitting.
   De test knipt het rekendeel uit de pagina en draait het in Node op gemaakte
   tellingen waarvan de echte factoren bekend zijn.

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_dagcurve.js */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('passanten.html', 'utf8');
const a = html.indexOf('/* ── Dagcurve (v3.43)'), z = html.indexOf('function dcGrafiek(');
if (a < 0 || z < 0) throw new Error('blok Dagcurve niet gevonden');
const csv = ['function dcCsvGetal(', 'function dagcurveCsv(', 'function passagesCsv(', 'function straatNaam(', 'function heleStraat('].map(n => {
  const i = html.indexOf(n); let j = html.indexOf('{', i), diep = 0;
  for (; j < html.length; j++) { if (html[j] === '{') diep++; else if (html[j] === '}' && --diep === 0) return html.slice(i, j + 1); }
});
const ctx = { console };
vm.createContext(ctx);
vm.runInContext([
  'var SESSIES = {}, KEUZE = {};',
  "var PASSANTEN = { V_VOET: 1.1, dagIndex: function (d) { var t = new Date(d + 'T12:00:00Z'); return isNaN(t) ? null : (t.getUTCDay() + 6) % 7; } };",
  "var DAGKORT = ['ma','di','wo','do','vr','za','zo'], DAGNAAM = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'];",
  html.slice(a, z), csv.join('\n'), /var STRAAT_GAT = [^;]+;/.exec(html)[0],
  'this.f = { dcSchat, dcNormeer, dcGroepen, dcWaarnemingen, dagcurve, dagcurveVan, dagcurveKeuze, dagcurveCsv, passagesCsv, heleStraat, ' +
  'zet: function (s) { SESSIES = s; DAGCURVE = null; DCKEUZE = null; }, kies: function (k) { KEUZE = k; }, ' +
  'DC_REF: DC_REF, DC_TREKKINGEN: DC_TREKKINGEN };'
].join('\n'), ctx);
const F = ctx.f;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const bijna = (x, y, tol) => Math.abs(x - y) <= tol * Math.abs(y);

// Een maandag tot zondag: 2 t/m 8 november 2026.
const DATUM = ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-07', '2026-11-08'];
// passage: [weekdag, uur, stuk, richting, venster in s, tegemoetkomers]; het venster zit in L/1,1 + t met t = 0
function sessies(lijst) {
  const S = {};
  lijst.forEach((ps, i) => {
    const id = 'S' + String(i).padStart(3, '0');
    S[id] = { s: { id, visits: ps.map(([d, h, stuk, r, w, m], j) => ({
      key: stuk + '/0', way: stuk, seg: 0, straat: 'straat ' + stuk, L: w * 1.1, t: 0,
      t0: h * 3600 + 60 * j, t1: h * 3600 + 60 * j + 30, datum: DATUM[d], richting: r, teg: m, stil: 0 })) } };
  });
  return S;
}
const obsVan = S => { F.zet(S); const per = F.dcWaarnemingen(); return [].concat(...Object.keys(per).map(k => per[k])); };
// schatten en schalen: alle werkdagen samen gemiddeld 1, index 100 = de werkdaguren 11–15 die er zijn
function schat(obs) {
  const s0 = F.dcSchat(obs), dagen = [0, 1, 2, 3, 4].filter(d => s0.dagOk[d]);
  let refK = [11, 12, 13, 14, 15].map(h => 'werkdag:' + h).filter(k => s0.F[k] > 0);
  if (!refK.length) refK = Object.keys(s0.F);
  return Object.assign(F.dcNormeer(s0, dagen, refK), { s0 });
}

console.log('== precies: verwachte aantallen geven de factoren terug ==');
// echte factoren: A per stuk, F per dagtype:uur, D per werkdag
const A = { 11: 900, 12: 300, 13: 1500, 14: 600 };
const FW = { 11: 0.8, 12: 1.1, 13: 1.2, 14: 1.0, 15: 0.9 }, FZ = { 12: 1.4, 13: 1.6, 14: 1.5 };
const D = [0.9, 1.0, 1.1, 1.05, 0.95];
const verwacht = (d, h, stuk, w) => w / 3600 * A[stuk] * (d < 5 ? FW[h] * D[d] : FZ[h]);
const plan = [];
[[0, [11, 12, 13]], [1, [12, 13, 14]], [2, [13, 14, 15]], [3, [11, 14, 15]], [4, [12, 15]], [5, [12, 13]], [5, [13, 14]], [1, [11, 15]],
 [0, [14, 15]], [2, [11, 12]], [3, [12, 13]]].forEach(([d, uren], i) => {
  plan.push(uren.map(h => [11, 12, 13, 14].filter((s, j) => (i + j + h) % 3 !== 0).map(s => [d, h, s, 'A', 60, verwacht(d, h, s, 60)])).flat());
});
let s = schat(obsVan(sessies(plan)));
const refW = (FW[11] + FW[12] + FW[13] + FW[14] + FW[15]) / 5;
eis('werkdag 11–15: index = 100 · F ÷ gemiddelde (11 tot 16 uur)', [11, 12, 13, 14, 15].every(h => bijna(s.idx['werkdag:' + h], 100 * FW[h] / refW, 1e-6)), s.idx);
eis('zaterdag 12–14 op dezelfde schaal', [12, 13, 14].every(h => bijna(s.idx['zaterdag:' + h], 100 * FZ[h] / refW, 1e-6)), s.idx);
const gemD = D.reduce((x, y) => x + y) / 5;
eis('weekdagfactoren terug, samen gemiddeld 1', D.every((v, d) => bijna(s.dag[d], v / gemD, 1e-6)) && bijna(s.dag.reduce((x, y) => x + y) / 5, 1, 1e-9), s.dag);
eis('index 100 is het gemiddelde werkdaguur van 11 tot 16', bijna([11, 12, 13, 14, 15].reduce((x, h) => x + s.idx['werkdag:' + h], 0) / 5, 100, 1e-9));
eis('het convergeert (onder 3000 rondes)', s.s0.iteraties < 3000, s.s0.iteraties);
F.zet(sessies(plan));
let dc = F.dagcurve();
const gem4 = (D[0] + D[1] + D[2] + D[3]) / 4;
eis('in de pagina: vrijdag heeft één telling, dus de andere vier (elk twee) zijn samen gemiddeld 1', dc.dagen.every((x, d) => bijna(x.factor, D[d] / gem4, 1e-6)) &&
    !dc.dagen[4].genoeg && !dc.dagen[4].inNorm && dc.dagen.slice(0, 4).every(x => x.inNorm), dc.dagen.map(x => [x.factor, x.n, x.inNorm]));
eis('en index 100 = de werkdaguren 11–15 met genoeg metingen', dc.ref === 'kern' && dc.refK.join() === 'werkdag:11,werkdag:12,werkdag:13,werkdag:14,werkdag:15' &&
    bijna(dc.cel['werkdag:13'].index, 100 * FW[13] / refW, 1e-6), [dc.ref, dc.refK]);

console.log('\n== de straat en het uur niet verwarren ==');
// Stuk 13 (druk) alleen op zaterdag om 13 uur, stuk 12 (rustig) alleen op werkdagen; één stuk (11) op beide.
const plan2 = [
  [[5, 13, 13, 'A', 60, verwacht(5, 13, 13, 60)], [5, 13, 11, 'A', 60, verwacht(5, 13, 11, 60)]],
  [[1, 13, 12, 'A', 60, verwacht(1, 13, 12, 60)], [1, 13, 11, 'A', 60, verwacht(1, 13, 11, 60)]]
];
s = schat(obsVan(sessies(plan2)));
const naief = (verwacht(5, 13, 13, 60) + verwacht(5, 13, 11, 60)) / (verwacht(1, 13, 12, 60) + verwacht(1, 13, 11, 60));
eis('zaterdag ÷ werkdag om 13 uur = de echte 1,6 ÷ (1,2 · 1,0), niet het gewone gemiddelde (' + naief.toFixed(2) + ')',
    bijna(s.idx['zaterdag:13'] / s.idx['werkdag:13'], FZ[13] / (FW[13] * D[1]), 1e-6) && !bijna(naief, FZ[13] / (FW[13] * D[1]), 0.1), [s.idx, naief]);

console.log('\n== wat niet te scheiden is, staat er niet in ==');
// een losse groep: stuk 99 alleen op zondag 11, door niemand anders gedeeld
const plan3 = plan.concat([[[6, 11, 99, 'A', 60, 3]]]);
s = schat(obsVan(sessies(plan3)));
eis('een stuk dat met niets samenhangt (zondag 11): geen index', !('zondag:11' in s.idx) && 'werkdag:12' in s.idx, Object.keys(s.idx));
F.zet(sessies(plan3)); dc = F.dagcurve();
eis('in de pagina: los, zonder index en zonder marge, met zijn eigen telling erbij', dc.cel['zondag:11'].los && dc.cel['zondag:11'].index === null &&
    dc.cel['zondag:11'].onder === null && dc.cel['zondag:11'].n === 1 && !dc.cel['zondag:11'].genoeg, dc.cel['zondag:11']);
eis('en de rest is precies als zonder', [11, 12, 13, 14, 15].every(h => bijna(s.idx['werkdag:' + h], 100 * FW[h] / refW, 1e-6)));
// werkdagen die uren niet delen: ma alleen om 9, di alleen om 10, met hetzelfde stuk
const plan4 = [[[0, 9, 11, 'A', 60, 5], [1, 10, 11, 'A', 60, 6]], [[0, 9, 11, 'B', 60, 4]]];
s = schat(obsVan(sessies(plan4)));
const g = F.dcGroepen(obsVan(sessies(plan4)));
eis('ma 9 en di 10 met hetzelfde stuk: uur en dag niet te scheiden, één ervan valt weg',
    [g.dag(0), g.dag(1)].filter(Boolean).length === 1 && Object.keys(s.idx).length === 1 && s.dag.filter(v => v !== null).length === 1, [s.idx, s.dag]);

console.log('\n== op toevalsgetallen: 100 tellingen ==');
let zaad = 7;
const rnd = () => { zaad = (zaad * 1103515245 + 12345) % 2147483648; return zaad / 2147483648; };
const poisson = mu => { let L = Math.exp(-mu), k = 0, p = 1; do { k++; p *= rnd(); } while (p > L); return k - 1; };
const FW2 = { 9: 0.45, 10: 0.7, 11: 0.9, 12: 1.1, 13: 1.15, 14: 1.05, 15: 1.0, 16: 0.85, 17: 0.6 };
const FZ2 = { 10: 0.9, 11: 1.3, 12: 1.6, 13: 1.7, 14: 1.6, 15: 1.4, 16: 1.1 };
const D2 = [0.85, 0.95, 1.05, 1.1, 1.05];
const A2 = {}; for (let st = 1; st <= 40; st++) A2[st] = 200 + 1800 * rnd();
const plan5 = [];
for (let i = 0; i < 100; i++) {
  const d = i < 80 ? Math.floor(rnd() * 5) : 5, uren = d < 5 ? Object.keys(FW2).map(Number) : Object.keys(FZ2).map(Number);
  const h0 = uren[Math.floor(rnd() * (uren.length - 1))], ps = [];
  [h0, h0 + 1].filter(h => uren.includes(h)).forEach(h => {
    for (let j = 0; j < 12; j++) {
      const st = 1 + Math.floor(rnd() * 40), r = rnd() < 0.5 ? 'A' : 'B', w = 40 + 50 * rnd();
      ps.push([d, h, st, r, w, poisson(w / 3600 * A2[st] * (d < 5 ? FW2[h] * D2[d] : FZ2[h]))]);
    }
  });
  plan5.push(ps);
}
F.zet(sessies(plan5));
let t = Date.now();
dc = F.dagcurve();
const duur = Date.now() - t;
const refW2 = (FW2[11] + FW2[12] + FW2[13] + FW2[14] + FW2[15]) / 5;
const echt = k => { const [ty, h] = k.split(':'); return 100 * (ty === 'werkdag' ? FW2[h] : FZ2[h]) / refW2; };
const genoeg = Object.keys(dc.cel).filter(k => dc.cel[k].genoeg && dc.cel[k].onder !== null);
const binnen = genoeg.filter(k => dc.cel[k].onder <= echt(k) && echt(k) <= dc.cel[k].boven);
eis('100 tellingen met ' + F.DC_TREKKINGEN + ' trekkingen in ' + duur + ' ms (onder 5 s), allemaal bruikbaar', duur < 5000 && dc.trekkingen === F.DC_TREKKINGEN, [duur, dc.trekkingen]);
eis('de marge (95%) bevat de echte index in ' + binnen.length + ' van de ' + genoeg.length + ' uren (minstens 85%)', genoeg.length >= 12 && binnen.length >= 0.85 * genoeg.length,
    genoeg.map(k => [k, Math.round(dc.cel[k].onder), Math.round(echt(k)), Math.round(dc.cel[k].boven)]));
const fouten = genoeg.map(k => Math.abs(dc.cel[k].index / echt(k) - 1));
eis('de index ligt gemiddeld binnen 10% van de echte (' + (100 * fouten.reduce((x, y) => x + y) / fouten.length).toFixed(1) + '%)', fouten.reduce((x, y) => x + y) / fouten.length < 0.10);
const dagBinnen = dc.dagen.filter(x => x.genoeg && x.onder <= D2[x.dag] / (D2.reduce((p, q) => p + q) / 5) && D2[x.dag] / (D2.reduce((p, q) => p + q) / 5) <= x.boven);
eis('de weekdagfactoren: ' + dagBinnen.length + ' van de 5 binnen hun marge (minstens 4)', dagBinnen.length >= 4, dc.dagen.map(x => [x.dag, x.onder, x.factor, x.boven]));
F.zet(sessies(plan5));
const dc2 = F.dagcurve();
eis('herhaalbaar: dezelfde trekkingen geven dezelfde marges', Object.keys(dc.cel).every(k => dc.cel[k].onder === dc2.cel[k].onder && dc.cel[k].boven === dc2.cel[k].boven));
eis('zondag niet gemeten: geen cel', !Object.keys(dc.cel).some(k => k.indexOf('zondag') === 0));
eis('de dekking telt tellingen per weekdag:uur', Object.keys(dc.dekking).every(k => Object.keys(dc.dekking[k]).length >= 1) &&
    Object.keys(dc.dekking).reduce((n, k) => n + Object.keys(dc.dekking[k]).length, 0) === plan5.reduce((n, ps) => n + new Set(ps.map(p => p[0] + ':' + p[1])).size, 0));

console.log('\n== drempels ==');
F.zet(sessies([[[5, 16, 1, 'A', 60, 3], [5, 15, 1, 'A', 60, 30]]]));
const klein = F.dagcurve();
eis('één telling: geen marge, en niets "genoeg"', Object.keys(klein.cel).every(k => klein.cel[k].onder === null && !klein.cel[k].genoeg));

console.log('\n== de CSV-bestanden ==');
F.zet(sessies(plan5)); F.dagcurve();
let regels = F.dagcurveCsv().trim().split('\n');
eis('dagcurve.csv: de kolommen', regels[0] === 'soort;dag;uur;index;onder;boven;tellingen;tegemoet;genoeg', regels[0]);
eis('een rij per uur en dagtype, en per werkdag', regels.filter(r => r.startsWith('uur;')).length === Object.keys(dc.cel).length && regels.filter(r => r.startsWith('weekdag;')).length === 5, regels.length);
const r12 = regels.find(r => r.startsWith('uur;werkdag;12;')).split(';');
eis('werkdag 12: index met één decimaal, punt als decimaalteken, genoeg = ja', /^\d+\.\d$/.test(r12[3]) && r12[8] === 'ja' && Math.abs(+r12[3] - dc.cel['werkdag:12'].index) < 0.051, r12);
const wd = regels.filter(r => r.startsWith('weekdag;')).map(r => +r.split(';')[3]);
eis('de weekdagrijen ×100, samen gemiddeld 100', Math.abs(wd.reduce((x, y) => x + y) / 5 - 100) < 0.1, wd);
regels = F.passagesCsv().trim().split('\n');
eis('passages.csv: de kolommen', regels[0] === 'sessie_id;datum;weekdag;uur;osm_way_id;segment_index;straat;richting;lengte_m;tijd_s;venster_s;tegemoet;stilstaand', regels[0]);
eis('één rij per passage', regels.length - 1 === plan5.reduce((n, ps) => n + ps.length, 0));
const p1 = regels[1].split(';');
eis('een rij: sessie, datum, weekdag, uur, stuk, venster = lengte ÷ 1,1 + tijd', p1[0] === 'S000' && /^2026-11-0\d$/.test(p1[1]) && Math.abs(+p1[10] - (+p1[8] / 1.1 + +p1[9])) < 0.06, p1);

console.log('\n== v3.44: de dagcurve van gekozen stukken ==');
// Twee groepen straten met een eigen verloop: X (21–23) piekt om 12 uur, Y (31–33) om 15 uur.
const FX = { 11: 0.9, 12: 1.4, 13: 1.1, 14: 0.8, 15: 0.7 }, FY = { 11: 0.6, 12: 0.8, 13: 1.0, 14: 1.2, 15: 1.5 };
const AXY = { 21: 800, 22: 500, 23: 1200, 31: 700, 32: 400, 33: 900 }, DXY = [0.95, 1.1];
const plan6 = [];
for (let h = 11; h <= 15; h++) for (let d = 0; d < 2; d++)
  plan6.push([21, 22, 23, 31, 32, 33].map(st => [d, h, st, 'A', 60, 60 / 3600 * AXY[st] * (st < 30 ? FX[h] : FY[h]) * DXY[d]]));
F.zet(sessies(plan6));
const X = { '21/0': true, '22/0': true, '23/0': true };
const dx = F.dagcurveVan(X), da = F.dagcurve();
const gemX = (FX[11] + FX[12] + FX[13] + FX[14] + FX[15]) / 5;
eis('alleen de stukken van X: hun eigen verloop terug (piek om 12 uur)', [11, 12, 13, 14, 15].every(h => bijna(dx.cel['werkdag:' + h].index, 100 * FX[h] / gemX, 1e-6)),
    [11, 12, 13, 14, 15].map(h => dx.cel['werkdag:' + h].index));
eis('en hun eigen aantallen: 2 tellingen per uur, alleen hun passages', dx.cel['werkdag:12'].n === 2 && dx.passages === 30 && da.passages === 60, [dx.cel['werkdag:12'].n, dx.passages, da.passages]);
eis('de weekdagfactoren van X: maandag en dinsdag zoals ze erin gingen', bijna(dx.dagen[1].factor / dx.dagen[0].factor, DXY[1] / DXY[0], 1e-6), dx.dagen.map(x => x.factor));
eis('alle stukken samen: daartussenin (om 12 uur lager dan X, om 15 uur hoger)', da.cel['werkdag:12'].index < dx.cel['werkdag:12'].index && da.cel['werkdag:15'].index > dx.cel['werkdag:15'].index);
F.kies({}); eis('zonder keuze: geen dagcurve van de keuze', F.dagcurveKeuze() === null);
F.kies(Object.assign({}, X));
const k1 = F.dagcurveKeuze();
eis('met keuze: de dagcurve van de keuze, en één keer gerekend (hetzelfde antwoord)', k1 && k1 === F.dagcurveKeuze() && bijna(k1.cel['werkdag:12'].index, dx.cel['werkdag:12'].index, 1e-12));
F.kies({ '31/0': true });
eis('een andere keuze: opnieuw gerekend', F.dagcurveKeuze() !== k1 && F.dagcurveKeuze().passages === 10);
let rk = F.passagesCsv(X).trim().split('\n');
eis('passages_keuze.csv: dezelfde kolommen, alleen de gekozen stukken', rk[0].startsWith('sessie_id;datum;') && rk.length - 1 === 30 && rk.slice(1).every(r => ['21', '22', '23'].includes(r.split(';')[4])), rk.length);
rk = F.dagcurveCsv(dx).trim().split('\n');
eis('dagcurve_keuze.csv: dezelfde kolommen, de cijfers van de keuze', rk[0] === 'soort;dag;uur;index;onder;boven;tellingen;tegemoet;genoeg' &&
    Math.abs(+rk.find(r => r.startsWith('uur;werkdag;12;')).split(';')[3] - dx.cel['werkdag:12'].index) < 0.051, rk.slice(0, 3));

console.log('\n== v3.44: hele straat ==');
// rechte stukken naar het oosten: [lon, lat], 1 m oost ≈ 1/(111320·cos 51,85°) graad
const MO = 1 / (111320 * Math.cos(51.85 * Math.PI / 180)), LAT = 51.85;
const stk = (key, straat, x0, x1, dy = 0) => ({ key, straat, geom: [[4.3 + x0 * MO, LAT + dy / 111320], [4.3 + x1 * MO, LAT + dy / 111320]] });
const SEG = {};
[stk('1/0', 'Hoofdstraat', 0, 40), stk('1/1', 'Hoofdstraat', 40, 80), stk('2/0', 'hoofdstraat', 80, 120),       // aaneen (ook met een kleine letter)
 stk('3/0', 'Hoofdstraat', 160, 200),                                                                             // 40 m verder: een ongelopen stuk ertussen
 stk('4/0', 'Hoofdstraat', 300, 340),                                                                             // 100 m verder: niet meer
 stk('5/0', 'Hoofdstraat', 0, 40, 5000),                                                                          // 5 km verderop, een ander dorp
 stk('6/0', 'Kerkstraat', 120, 160), stk('7/0', '(naamloos)', 200, 240)].forEach(x => { SEG[x.key] = x; });
const hs = F.heleStraat(SEG['1/1'], SEG);
eis('vanaf een stuk in het midden: de stukken die aaneen liggen, beide kanten op, ook over een gat van 40 m', hs[0] === '1/1' && hs.slice().sort().join() === '1/0,1/1,2/0,3/0', hs);
eis('niet: 100 m verder, een Hoofdstraat in een ander dorp, of een andere straat ertussen', !hs.includes('4/0') && !hs.includes('5/0') && !hs.includes('6/0'));
eis('een stuk zonder naam: alleen dat stuk', F.heleStraat(SEG['7/0'], SEG).join() === '7/0');

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
