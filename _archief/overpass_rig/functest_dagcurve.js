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

   v3.51: de dagcurve 3 keer zo snel (Jay: "is er in passanten.html ook nog iets
   te versnellen?"; "die mag je maken"). Samenhang en schatting rekenen op vaste
   nummers per waarneming in plaats van op tekst. De test zet de oude versie
   (union-find op tekst, zoals tot v3.50) ernaast en eist dezelfde uitkomst, tot
   op de laatste decimaal.

   v3.52: de stippen, een per telling per uur (Jay: "Het gaat om het aangeven
   van de spreiding - aangeven dat het gemiddelde niet als waarheid moeten worden
   gezien"). Zonder ruis vallen ze op de curve; met ruis is hun gemiddelde,
   gewogen met wat het model verwacht, precies de index van het vakje.

   v3.53: Wanneer tellen? per stuk en uur (Jay: "kun je dan doorrekenen wanneer
   er geteld moet worden op die link?"; "Doe het gewoon op uurbasis"). Zonder
   ruis volgt elk stuk de curve; met verschillen tussen dagen meet dcSpreiding
   die, en zonder die spreiding in de marge zou een stuk ten onrechte afwijken;
   een stuk met een eigen ritme wijkt wel af.

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_dagcurve.js */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('passanten.html', 'utf8');
const a = html.indexOf('/* ── Dagcurve (v3.43)'), z = html.indexOf('function dcGrafiek(');
if (a < 0 || z < 0) throw new Error('blok Dagcurve niet gevonden');
const csv = ['function dcCsvGetal(', 'function dagcurveCsv(', 'function passagesCsv(', 'function straatNaam(', 'function heleStraat(',
             'function poissonCdf(', 'function poissonMarge('].map(n => {
  const i = html.indexOf(n); let j = html.indexOf('{', i), diep = 0;
  for (; j < html.length; j++) { if (html[j] === '{') diep++; else if (html[j] === '}' && --diep === 0) return html.slice(i, j + 1); }
});
const ctx = { console };
vm.createContext(ctx);
vm.runInContext([
  'var SESSIES = {}, KEUZE = {};',
  "var PASSANTEN = { V_VOET: 1.1, dagIndex: function (d) { var t = new Date(d + 'T12:00:00Z'); return isNaN(t) ? null : (t.getUTCDay() + 6) % 7; } };",
  "var DAGKORT = ['ma','di','wo','do','vr','za','zo'], DAGNAAM = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'];",
  html.slice(a, z), csv.join('\n'), /var STRAAT_GAT = [^;]+;/.exec(html)[0], /var MARGE_BREED = [^;]+;/.exec(html)[0],
  'this.f = { dcSchat, dcNormeer, dcGroepen, dcWaarnemingen, dagcurve, dagcurveVan, dagcurveKeuze, dagcurveCsv, passagesCsv, heleStraat, ' +
  'dcPlan, dcSpreiding, dcKernAlle, ' +
  'zet: function (s) { SESSIES = s; DAGCURVE = null; DCKEUZE = null; DCKERN = null; }, kies: function (k) { KEUZE = k; }, ' +
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

console.log('\n== v3.51: dezelfde uitkomst als de oude versie (union-find op tekst) ==');
// De oude dcGroepen en de oude nummering in dcSchat, zoals tot v3.50.
const OUD_GROEPEN = `function dcGroepen(obs) {
  function vereniging() {
    var ouder = {};
    function wortel(x) { if (!(x in ouder)) ouder[x] = x; while (ouder[x] !== x) { ouder[x] = ouder[ouder[x]]; x = ouder[x]; } return x; }
    return { wortel: wortel, bind: function (a, b) { ouder[wortel(a)] = wortel(b); } };
  }
  function grootste(lijst, van) {
    var n = {}, best = null;
    lijst.forEach(function (o) { var r = van(o); n[r] = (n[r] || 0) + 1; if (best === null || n[r] > n[best]) best = r; });
    return best;
  }
  var g1 = vereniging();
  obs.forEach(function (o) { g1.bind('u' + o.u, 'm' + o.d + ':' + o.h); });
  var r1 = grootste(obs, function (o) { return g1.wortel('u' + o.u); });
  var mee = obs.filter(function (o) { return g1.wortel('u' + o.u) === r1; });
  var g2 = vereniging(), werk = mee.filter(function (o) { return o.d < 5; });
  werk.forEach(function (o) { g2.bind('d' + o.d, 'h' + o.h); });
  var r2 = grootste(werk, function (o) { return g2.wortel('d' + o.d); });
  return { obs: mee,
           dag: function (d) { return r2 !== null && g2.wortel('d' + d) === r2; },
           cel: function (k) { var t = k.split(':'); return t[0] !== 'werkdag' || (r2 !== null && g2.wortel('h' + t[1]) === r2); } };
}`;
const OUD_NUMMERS = `  var uNr = {}, kNr = {}, K = [], nU = 0;
  var ou = new Int32Array(n), ok = new Int32Array(n), od = new Int32Array(n), ow = new Float64Array(n), om = new Float64Array(n);
  obs.forEach(function (o, i) {
    if (!(o.u in uNr)) uNr[o.u] = nU++;
    if (!(o.k in kNr)) { kNr[o.k] = K.length; K.push(o.k); }
    ou[i] = uNr[o.u]; ok[i] = kNr[o.k]; od[i] = o.d; ow[i] = o.w; om[i] = o.m;
  });`;
function functieTekst(tekst, naam) {
  const i = tekst.indexOf(naam); let j = tekst.indexOf('{', i), diep = 0;
  for (; j < tekst.length; j++) { if (tekst[j] === '{') diep++; else if (tekst[j] === '}' && --diep === 0) return tekst.slice(i, j + 1); }
}
let blokOud = html.slice(a, z);
const nieuwGroepen = functieTekst(blokOud, 'function dcGroepen(obs) {');
const nieuwNummers = /  var uNr = new Int32Array[^\n]*\n(?:.*\n){5}  \}\);/.exec(blokOud);
eis('de nieuwe dcGroepen en de nieuwe nummering gevonden', !!nieuwGroepen && !!nieuwNummers && nieuwGroepen.indexOf('dcVereniging') > 0);
blokOud = blokOud.replace(nieuwGroepen, OUD_GROEPEN).replace(nieuwNummers[0], OUD_NUMMERS);
// v3.52: de oude nummering gaat op o.u in plaats van o.ui; dcStippen leest hem zo ook mee
const stipNummer = 's0.A[s0.uNr[o.ui]]';
eis('de nummering in dcStippen gevonden', blokOud.split(stipNummer).length === 2);
blokOud = blokOud.replace(stipNummer, 's0.A[s0.uNr[o.u]]');
const ctxOud = { console };
vm.createContext(ctxOud);
vm.runInContext([
  'var SESSIES = {}, KEUZE = {};',
  "var PASSANTEN = { V_VOET: 1.1, dagIndex: function (d) { var t = new Date(d + 'T12:00:00Z'); return isNaN(t) ? null : (t.getUTCDay() + 6) % 7; } };",
  "var DAGKORT = ['ma','di','wo','do','vr','za','zo'], DAGNAAM = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'];",
  blokOud, csv.join('\n'), /var STRAAT_GAT = [^;]+;/.exec(html)[0],
  'this.f = { dagcurve, dagcurveKeuze, dagcurveCsv, zet: function (s) { SESSIES = s; DAGCURVE = null; DCKEUZE = null; }, kies: function (k) { KEUZE = k; } };'
].join('\n'), ctxOud);
const O = ctxOud.f;
// Twee keer dezelfde gegevens: de 100 tellingen van hierboven, en een tweede set met
// zaterdag, zondag en een losse straat (wat niet te scheiden is, valt weg).
const planB = plan5.slice(0, 60).concat(plan5.slice(80)).concat([[[6, 13, 41, 'A', 60, 9], [6, 14, 41, 'B', 60, 11]], [[2, 9, 42, 'A', 50, 2]]]);
[['100 tellingen', plan5], ['met zondag en een losse straat', planB]].forEach(([naam, plan]) => {
  F.zet(sessies(plan)); O.zet(sessies(plan));
  let t0 = Date.now(); const nw = F.dagcurve(); const tNieuw = Date.now() - t0;
  t0 = Date.now(); const ou = O.dagcurve(); const tOud = Date.now() - t0;
  eis(naam + ': dagcurve gelijk tot op de laatste decimaal (nieuw ' + tNieuw + ' ms, oud ' + tOud + ' ms)', JSON.stringify(nw) === JSON.stringify(ou));
  F.kies({ '1/0': true, '2/0': true, '3/0': true, '17/0': true }); O.kies({ '1/0': true, '2/0': true, '3/0': true, '17/0': true });
  eis(naam + ': ook de dagcurve van een keuze', JSON.stringify(F.dagcurveKeuze()) === JSON.stringify(O.dagcurveKeuze()));
  eis(naam + ': en dagcurve.csv', F.dagcurveCsv() === O.dagcurveCsv());
  F.kies({}); O.kies({});
});

console.log('\n== v3.52: de stippen, een per telling per uur ==');
// zonder ruis (de verwachte aantallen van het eerste plan): elke stip ligt op de curve
F.zet(sessies(plan)); dc = F.dagcurve();
eis('zonder ruis: ' + dc.stippen.length + ' stippen, elk precies op de index van zijn vakje',
    dc.stippen.length === plan.reduce((n, ps) => n + new Set(ps.map(p => p[1])).size, 0) && dc.stippen.every(p => bijna(p.index, dc.cel[p.k].index, 1e-6)),
    dc.stippen.filter(p => !bijna(p.index, dc.cel[p.k].index, 1e-6)).map(p => [p.sid, p.k, p.index, dc.cel[p.k].index]));
// met ruis: de 100 tellingen
F.zet(sessies(plan5)); dc = F.dagcurve();
const perVak = {};
dc.stippen.forEach(p => (perVak[p.k] = perVak[p.k] || []).push(p));
const vakken = Object.keys(dc.cel).filter(k => !dc.cel[k].los);
eis('één stip per telling en uur (' + dc.stippen.length + '), alleen in vakjes die te scheiden zijn',
    dc.stippen.length === plan5.reduce((n, ps) => n + new Set(ps.filter(p => !dc.cel[(p[0] < 5 ? 'werkdag' : p[0] === 5 ? 'zaterdag' : 'zondag') + ':' + p[1]].los).map(p => p[1])).size, 0) &&
    dc.stippen.every(p => !dc.cel[p.k].los) && new Set(dc.stippen.map(p => p.sid + '|' + p.k)).size === dc.stippen.length);
eis('per vakje: het gemiddelde van de stippen, gewogen met wat het model verwacht, is precies de index',
    vakken.every(k => bijna(perVak[k].reduce((a, p) => a + p.gewicht * p.index, 0) / perVak[k].reduce((a, p) => a + p.gewicht, 0), dc.cel[k].index, 1e-6)),
    vakken.map(k => [k, dc.cel[k].index, perVak[k].reduce((a, p) => a + p.gewicht * p.index, 0) / perVak[k].reduce((a, p) => a + p.gewicht, 0)]));
eis('per vakje: de tegemoetkomers van de stippen samen zijn die van het vakje', vakken.every(k => perVak[k].reduce((a, p) => a + p.tikken, 0) === dc.cel[k].tikken));
const w12 = perVak['werkdag:12'].map(p => p.index);
eis('en ze liggen niet op de curve: werkdag 12 van ' + Math.round(Math.min(...w12)) + ' tot ' + Math.round(Math.max(...w12)) + ' (index ' + Math.round(dc.cel['werkdag:12'].index) + ')',
    Math.min(...w12) < 0.95 * dc.cel['werkdag:12'].index && Math.max(...w12) > 1.05 * dc.cel['werkdag:12'].index);   // alleen Poisson-ruis: geen grote spreiding
// de keuze: alleen stippen van de gekozen stukken
F.kies({ '1/0': true, '2/0': true, '3/0': true });
const kz = F.dagcurveKeuze(), metStuk = new Set(plan5.map((ps, i) => ps.some(p => p[2] <= 3) ? 'S' + String(i).padStart(3, '0') : null).filter(Boolean));
eis('de keuze: alleen tellingen die de gekozen stukken liepen (' + new Set(kz.stippen.map(p => p.sid)).size + ' van ' + metStuk.size + ')',
    kz.stippen.length > 0 && kz.stippen.every(p => metStuk.has(p.sid)));
F.kies({});

console.log('\n== v3.53: wanneer tellen, per stuk en uur ==');
const typeVan = d => d < 5 ? 'werkdag' : d === 5 ? 'zaterdag' : 'zondag';
// zonder ruis: elk stuk volgt de curve precies, en er is geen spreiding tussen tellingen
F.zet(sessies(plan)); dc = F.dagcurve();
let pl = F.dcPlan('12/0');
const metV = pl.cellen.filter(c => c.verhouding !== null);
eis('zonder ruis: spreiding 0, en op elk uur met een verwachting precies 1 keer de curve (' + metV.length + ' uren)',
    pl.spreiding === 0 && metV.length >= 5 && metV.every(c => bijna(c.verhouding, 1, 1e-6)) && pl.cellen.every(c => c.stand !== 'hoger' && c.stand !== 'lager'),
    metV.map(c => [c.k, c.verhouding]));
// de aantallen: zoals in het plan
const telPlan = (pp, stuk) => { const r = {}; pp.forEach((ps, i) => ps.forEach(([d, h, st, , , m]) => { if (st !== stuk) return;
  const k = typeVan(d) + ':' + h, x = r[k] = r[k] || { t: new Set(), m: 0 }; x.t.add(i); x.m += m; })); return r; };
let tp = telPlan(plan, 12);
eis('per uur het aantal tellingen en tegemoetkomers van dit stuk, zoals in het plan',
    pl.cellen.every(c => c.n === (tp[c.k] ? tp[c.k].t.size : 0) && bijna(c.tikken + 1, (tp[c.k] ? tp[c.k].m : 0) + 1, 1e-9)) &&
    Object.keys(tp).every(k => pl.cellen.some(c => c.k === k)));
eis('nooit (het gebied heeft er genoeg) en leeg (het gebied niet) waar het stuk niet geteld is',
    pl.cellen.filter(c => !c.n).every(c => c.stand === (dc.cel[c.k] && dc.cel[c.k].genoeg ? 'nooit' : 'leeg')) && pl.cellen.some(c => c.stand === 'leeg'),
    pl.cellen.filter(c => !c.n).map(c => [c.k, c.stand]));
const nooit = pl.cellen.filter(c => c.stand === 'nooit');
eis('het advies: eerst de uren waar het nooit geteld is, zonder spreiding het drukste eerst, hooguit 3',
    pl.advies.length === Math.min(3, pl.cellen.filter(c => c.stand !== 'volgt' && c.stand !== 'gezien').length) &&
    pl.advies.slice(0, nooit.length).every(c => c.stand === 'nooit') && pl.advies.every((c, i) => !i || c.stand !== 'nooit' || pl.advies[i - 1].drukte >= c.drukte),
    pl.advies.map(c => [c.k, c.stand, c.drukte]));
// alleen toeval (Poisson): geen spreiding, en bijna nooit hoger of lager
F.zet(sessies(plan5));
const afwijkend = () => { let t = 0, a = 0; for (let st = 1; st <= 40; st++) F.dcPlan(st + '/0').cellen.forEach(c => {
  if (c.stand === 'volgt' || c.stand === 'hoger' || c.stand === 'lager') { t++; if (c.stand !== 'volgt') a++; } }); return [a, t]; };
let [af, ge] = afwijkend();
eis('alleen toeval: spreiding ' + F.dcSpreiding(F.dcKernAlle()).toFixed(3) + ' (onder 0,1), en ' + af + ' van de ' + ge + ' uren hoger of lager (hooguit 5%)',
    F.dcSpreiding(F.dcKernAlle()) < 0.1 && ge >= 100 && af <= 0.05 * ge);
// dagen verschillen: elke telling × een eigen factor (lognormaal, σ 0,4), geen stuk met een eigen ritme
const normaal = () => Math.sqrt(-2 * Math.log(1 - rnd())) * Math.cos(2 * Math.PI * rnd());
const plan7 = plan5.map(ps => { const f = Math.exp(0.4 * normaal() - 0.08);
  return ps.map(([d, h, st, r, w]) => [d, h, st, r, w, poisson(f * w / 3600 * A2[st] * (d < 5 ? FW2[h] * D2[d] : FZ2[h]))]); });
F.zet(sessies(plan7));
const sp7 = F.dcSpreiding(F.dcKernAlle()), echtSp = Math.sqrt(Math.exp(0.16) - 1);
[af, ge] = afwijkend();
eis('dagen verschillen: spreiding ' + sp7.toFixed(2) + ' (echt ' + echtSp.toFixed(2) + ', binnen 30%), en ' + af + ' van de ' + ge + ' uren hoger of lager (hooguit 5%)',
    Math.abs(sp7 / echtSp - 1) < 0.3 && ge >= 100 && af <= 0.05 * ge);
F.dcKernAlle().spreiding = 0;
const [af0, ge0] = afwijkend();
eis('zonder die spreiding in de marge zouden er veel meer afwijken: ' + af0 + ' van de ' + ge0, af0 > 2 * af && af0 > 0.08 * ge0);
// een stuk met een eigen ritme: stuk 7 op werkdagen om 16 en 17 uur drie keer zo druk
const plan8 = plan7.map(ps => ps.map(([d, h, st, r, w, m]) => st === 7 && d < 5 && (h === 16 || h === 17) ? [d, h, st, r, w, 3 * m + poisson(0.5)] : [d, h, st, r, w, m]));
F.zet(sessies(plan8));
pl = F.dcPlan('7/0');
const laat = pl.cellen.filter(c => c.k === 'werkdag:16' || c.k === 'werkdag:17');
eis('een stuk met een eigen ritme: stuk 7 op werkdag 16 en 17 uur hoger waar het twee keer of vaker geteld is (' + laat.map(c => c.k + ' ' + c.n + ' tellingen ' + (c.verhouding || 0).toFixed(1) + ' ' + c.stand).join(', ') + ')',
    laat.filter(c => c.n >= 2).length >= 1 && laat.filter(c => c.n >= 2).every(c => c.stand === 'hoger') && laat.every(c => c.n >= 2 || c.stand !== 'hoger'), laat);
// met spreiding: een uur dat het gebied goed kent gaat voor een drukker uur dat het gebied nauwelijks kent
const nooit8 = pl.cellen.filter(c => c.stand === 'nooit' && c.perKeer > 5), paren = [];
nooit8.forEach(x => nooit8.forEach(y => { if (x.gebied > 2 * y.gebied && y.perKeer > x.perKeer) paren.push([x, y]); }));
eis('met spreiding: eerst waar het gebied het uur goed kent, ook als het elders drukker is (' +
    paren.map(([x, y]) => x.k + ' (' + x.gebied + ' tellingen, ≈' + x.perKeer.toFixed(0) + ' per keer) voor ' + y.k + ' (' + y.gebied + ', ≈' + y.perKeer.toFixed(0) + ')').join('; ') + ')',
    paren.length > 0 && paren.every(([x, y]) => x.onzeker < y.onzeker) &&
    pl.advies.every((c, i) => !i || c.stand !== pl.advies[i - 1].stand || c.stand === 'dun' || pl.advies[i - 1].onzeker <= c.onzeker),
    nooit8.map(c => [c.k, c.gebied, +c.perKeer.toFixed(1), +c.onzeker.toFixed(3)]));
eis('per keer langs verwacht: wat de schatting per passage geeft (alleen waar het gebied een curve heeft)',
    pl.cellen.every(c => c.perKeer === null || (c.perKeer > 0 && c.drukte > 0)) && pl.cellen.some(c => c.perKeer > 0));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
