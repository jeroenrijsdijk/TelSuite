/* Passantensimulatie — de batch (Monte Carlo) die de tabellen maakt.
   Rekent met het échte blok PASSANTEN en de échte Garwood-marge uit
   passanten.html, ongewijzigd, via vm (zoals functest_passanten.js).

   Draaien vanuit de repo-root:
     node _archief/passantensim/batch.js            (1000 runs per regel)
     node _archief/passantensim/batch.js 3000       (meer runs)
   Uitvoer: Markdown-tabellen op stdout. Niets wordt weggeschreven.          */
const fs = require('fs');
const vm = require('vm');
const path = require('path');

function stuk(html, a, z, metEind) {
  const i = html.indexOf(a), j = html.indexOf(z, i);
  if (i < 0 || j < 0) throw new Error('blok niet gevonden: ' + a);
  return html.slice(i, metEind ? j + z.length : j);
}
const html = fs.readFileSync('passanten.html', 'utf8');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(
  stuk(html, '/* ── Passanten per uur: de rekenkern (v3.34)', '/* ── einde gedeeld blok passanten ── */', true) + '\n' +
  stuk(html, '/* ── Marge (Garwood)', '/* ── Passanten per uur (v3.34)', false) + '\n' +
  fs.readFileSync(path.join(__dirname, 'sim_kern.js'), 'utf8') +
  '\nthis.P = PASSANTEN; this.marge = poissonMarge; this.S = SIMKERN;', ctx);
const { P, marge, S } = ctx;
const OPHOGEN = 2;                      // passanten.html: één richting gemeten → × 2 (ρ kan hier niet)

const RUNS = parseInt(process.argv[2], 10) || 1000;

/* ---------- één run door Passanten halen ---------------------------------- */
function analyse(param, zaad) {
  const R = S.run(param, zaad);
  const ses = P.sessie(R.invoer, 'sim.zip');
  const segs = {};
  P.voegToe(segs, ses);
  P.bereken(segs, P.V_VOET);
  const vakken = [];
  R.W.segs.forEach(s => {
    const g = segs['1/' + s.k];
    const waar = s.qPlus + s.qMin, tegen = R.T.dir > 0 ? s.qMin : s.qPlus;
    if (!g) { vakken.push({ k: s.k, waar, tegen, gemist: true }); return; }
    const c = g.cells[Object.keys(g.cells)[0]];
    const st = ['A', 'B', '?'].filter(r => c.stromen[r].n);
    const f = c.compleet || st.length !== 1 ? 1 : OPHOGEN;
    const w = st.reduce((a, r) => a + c.stromen[r].w, 0);
    const waard = c.m > 0 ? c.q / c.m : 3600 * st.length / w;
    const gw = marge(c.m);
    vakken.push({ k: s.k, waar, tegen, m: c.m, w, q: c.q, schat: c.q * f,
      lo: gw[0] * waard * f, hi: gw[1] * waard * f, stil: c.stil, L: g.L,
      sta: s.staGeteld, staWaar: s.staPlus + s.staMin, gemist: false });
  });
  // vingerafdruk, zoals in de analyse van Jay's vijf tellingen
  const vis = ses.visits;
  let gat = 0;
  for (let i = 1; i < vis.length; i++) gat += Math.max(0, vis[i].t0 - vis[i - 1].t1);
  const duur = vis.length ? vis[vis.length - 1].t1 - vis[0].t0 : 0;
  const gelopen = vis.reduce((a, v) => a + v.L, 0);
  // tussenpozen tussen tegemoet-tikken binnen dezelfde passage
  const teg = R.invoer.telregels.filter(t => t.type === 'tegemoet')
    .map(t => ({ k: t.osm_way_id + '/' + t.segment_index, s: sec(t.tijdstip) }));
  const tus = [];
  vis.forEach(v => {
    const s = teg.filter(t => t.k === v.key && t.s >= v.t0 && t.s <= v.t1).map(t => t.s).sort((a, b) => a - b);
    for (let i = 1; i < s.length; i++) tus.push(s[i] - s[i - 1]);
  });
  return { R, vakken, vis, ses,
    afdruk: { tegPerPas: vis.length ? vis.reduce((a, v) => a + v.teg, 0) / vis.length : 0,
      tempo: duur > 0 ? gelopen / duur : 0, gat: duur > 0 ? gat / duur : 0,
      wees: ses.nTel ? ses.nWees / ses.nTel : 0, tus,
      stil100: gelopen ? 100 * vis.reduce((a, v) => a + v.stil, 0) / gelopen : 0, n: vis.length } };
}
function sec(iso) { const p = iso.split('T')[1].split(':').map(Number); return p[0] * 3600 + p[1] * 60 + p[2]; }

/* ---------- statistiek -------------------------------------------------- */
const som = a => a.reduce((s, x) => s + x, 0);
const gem = a => a.length ? som(a) / a.length : NaN;
function kwantiel(a, p) { if (!a.length) return NaN; const b = a.slice().sort((x, y) => x - y); const i = (b.length - 1) * p, l = Math.floor(i); return b[l] + (b[Math.min(l + 1, b.length - 1)] - b[l]) * (i - l); }
const k2 = (x, d = 2) => isFinite(x) ? x.toFixed(d).replace('.', ',') : '–';
const pct = x => isFinite(x) ? Math.round(100 * x) + '%' : '–';

function draai(param, runs, zaadBasis) {
  const uit = [];
  for (let i = 0; i < runs; i++) uit.push(analyse(param, (zaadBasis || 1) * 100003 + i));
  return uit;
}
function samenvat(runs, Fextern, breed) {
  breed = breed || 1;
  const v = runs.flatMap(x => x.vakken);
  const ok = v.filter(x => !x.gemist);
  const F = som(ok.map(x => x.waar)) / som(ok.map(x => x.schat));
  const F1 = som(ok.map(x => x.tegen)) / som(ok.map(x => x.q));
  const ratio = ok.map(x => x.schat / x.waar);
  const lnr = ok.filter(x => x.schat > 0).map(x => Math.log(x.schat / x.waar));
  // dekking van de 95%-marge, op de stroom die je tegemoet komt (zonder het × 2-effect)
  const dek1 = gem(ok.map(x => (x.tegen >= x.lo / 2 && x.tegen <= x.hi / 2) ? 1 : 0));
  const Fc = Fextern || F1;
  const lo = x => Fc * (x.schat - breed * (x.schat - x.lo)) / 2, hi = x => Fc * (x.schat + breed * (x.hi - x.schat)) / 2;
  const dek1F = gem(ok.map(x => (x.tegen >= lo(x) && x.tegen <= hi(x)) ? 1 : 0));
  const dekTot = gem(ok.map(x => (x.waar >= F * x.lo && x.waar <= F * x.hi) ? 1 : 0));
  // overdispersie: (m − μ)² / μ, met μ = verwacht aantal tikken uit de waarheid en F1
  const phi = gem(ok.map(x => { const mu = x.tegen * x.w / 3600 / F1; return mu > 0 ? (x.m - mu) ** 2 / mu : 0; }));
  return { n: ok.length, gemist: (v.length - ok.length) / v.length, F, F1,
    med: kwantiel(ratio, 0.5), p10: kwantiel(ratio, 0.1), p90: kwantiel(ratio, 0.9),
    sdLog: Math.sqrt(gem(lnr.map(x => (x - gem(lnr)) ** 2))), dek1, dek1F, dekTot, phi };
}

/* ---------- de scenario's: foutbronnen één voor één erbij ------------------ */
const IDEAAL = { pEind: 1, vGem: 1.1, vSd: 0, pSlenter: 0, pStop: 0, stilDicht: 0, groep: [1], salvo: 0,
  pZelf: 1, pOver: 1, pGroep: 1, qZicht: Infinity, vertraging: 0, vertragingSd: 0, minTussen: 0,
  idealGps: true, scheef: [0.5, 0.5] };
const ST = S.STANDAARD;
const stappen = [
  ['ideaal: geen winkels, iedereen 1,1 m/s, alles gezien, exacte bezoeken (controle)', {}],
  ['+ winkeldeuren: de stroom verandert langs de straat', { pEind: ST.pEind }],
  ['+ echte loopsnelheden (gem. 1,25 ± 0,25; 15% slenteraars 0,7)', { vGem: ST.vGem, vSd: ST.vSd, pSlenter: ST.pSlenter }],
  ['+ even stilstaan (25%, ~1 min) en vaste stilstaanders', { pStop: ST.pStop, stilDicht: ST.stilDicht }],
  ['+ groepjes (1–4, gem. 1,65)', { groep: ST.groep }],
  ['+ tikken: 0,8 ± 0,8 s vertraging, salvo\'s van 3 s, 0,35 s ertussen', { vertraging: ST.vertraging, vertragingSd: ST.vertragingSd, minTussen: ST.minTussen, salvo: ST.salvo }],
  ['+ gps en bezoeken zoals Pocket (gaten, wezen)', { idealGps: false }],
  ['+ scheve straten (tot 75/25 bij de einden)', { scheef: [0.5, 0.75] }]
];
const ALLES = Object.assign({}, IDEAAL, ...stappen.map(s => s[1]));       // alles behalve gemiste tikken
const tref = [
  ['alles gezien', {}],
  ['optimistisch: 98% / 90% overkant / 95% groep / zicht 8000', { pZelf: 0.98, pOver: 0.90, pGroep: 0.95, qZicht: 8000 }],
  ['standaard: 95% / 75% overkant / 85% groep / zicht 4000', { pZelf: ST.pZelf, pOver: ST.pOver, pGroep: ST.pGroep, qZicht: ST.qZicht }],
  ['pessimistisch: 90% / 60% overkant / 70% groep / zicht 2500', { pZelf: 0.90, pOver: 0.60, pGroep: 0.70, qZicht: 2500 }]
];

const t0 = Date.now();
let param = Object.assign({}, IDEAAL);
const rijen = [];
stappen.forEach(([naam, extra], i) => {
  Object.assign(param, extra);
  rijen.push([naam, samenvat(draai(Object.assign({}, param), RUNS, i + 1))]);
});
const trefRijen = [];
let standaard = null;
tref.forEach(([naam, extra], i) => {
  const runs = draai(Object.assign({}, ALLES, extra), RUNS, 50 + i);
  const p = som(runs.map(x => som(x.R.bedoeld.filter(b => b.soort === 'tegemoet').map(() => 1)))) /
            som(runs.map(x => x.R.ontmoet.tegemoet));
  trefRijen.push([naam, samenvat(runs), p]);
  if (i === 2) standaard = runs;
});

console.log(`# Passantensimulatie — ${RUNS} rondes per regel, ${Math.round((Date.now() - t0) / 1000)} s\n`);
console.log('Waarheid: de doorsnedestroom in het midden van het vak, beide richtingen samen.');
console.log('F = Σ waarheid / Σ Passanten: de factor waarmee Passanten vermenigvuldigd moet worden.');
console.log('F₁ = hetzelfde voor de ene gemeten stroom (zonder het effect van × 2).\n');
console.log('## 1a. Waar zit de fout? Foutbronnen één voor één erbij, nog alles gezien\n');
const kop = '| | F | F₁ | per vak: mediaan schat/waar | 10–90% | spreiding (sd ln) | dispersie φ | 95%-marge raakt waarheid | na F | vak zonder bezoek |';
const streep = '|---|---|---|---|---|---|---|---|---|---|';
const regel = (naam, s) => `| ${naam} | ${k2(s.F)} | ${k2(s.F1)} | ${k2(s.med)} | ${k2(s.p10)}–${k2(s.p90)} | ${k2(s.sdLog)} | ${k2(s.phi, 1)} | ${pct(s.dek1)} | ${pct(s.dek1F)} | ${pct(s.gemist)} |`;
console.log(kop); console.log(streep);
rijen.forEach(([naam, s]) => console.log(regel(naam, s)));

console.log('\n## 1b. Gemiste tikken bovenop 1a (de trefkans is niet uit de data te halen)\n');
console.log('p̄ = getikte / echte tegemoet-ontmoetingen. F · p̄ hoort ongeveer gelijk te blijven.\n');
console.log('| trefkans | p̄ | F | F · p̄ | spreiding (sd ln) | dispersie φ | 95%-marge raakt waarheid | na F |');
console.log('|---|---|---|---|---|---|---|---|');
trefRijen.forEach(([naam, s, p]) => console.log(`| ${naam} | ${pct(p)} | ${k2(s.F)} | ${k2(s.F * p)} | ${k2(s.sdLog)} | ${k2(s.phi, 1)} | ${pct(s.dek1)} | ${pct(s.dek1F)} |`));

/* ---------- vingerafdruk: lijkt de simulatie op de echte tellingen? -------- */
const af = standaard.map(x => x.afdruk).filter(a => a.n >= 3);
const tus = af.flatMap(a => a.tus);
const kort = gem(tus.map(g => g <= 1 ? 1 : 0));
console.log('\n## 2. Vingerafdruk van "standaard" tegen Jay\'s vijf tellingen\n');
console.log('| | simulatie (mediaan, 10–90%) | echt (5 tellingen) |');
console.log('|---|---|---|');
const rij = (n, f, echt, d = 1) => console.log(`| ${n} | ${k2(kwantiel(af.map(f), 0.5), d)} (${k2(kwantiel(af.map(f), 0.1), d)}–${k2(kwantiel(af.map(f), 0.9), d)}) | ${echt} |`);
rij('tegemoet per passage', a => a.tegPerPas, '2,7–14,8 (mediaan 4,5)');
rij('eigen tempo (m/s)', a => a.tempo, '0,9–1,5 (meestal 1,4)', 2);
rij('gaten tussen bezoeken (%)', a => 100 * a.gat, '18', 0);
rij('weestikken (%)', a => 100 * a.wees, '10', 0);
rij('stilstaand per 100 m', a => a.stil100, '1,4–6,8');
console.log(`| tussenpozen tegemoet ≤ 1 s (binnen een passage) | ${pct(kort)} | 67% (47% bij toeval) |`);

/* ---------- F naar drukte en tempo: wat je in een telling kunt zien -------- */
console.log('\n## 3. Hangt F af van wat je in de telling ziet? ("standaard")\n');
function perKlasse(titel, f, grenzen) {
  console.log(`| ${titel} | rondes | F | F₁ |`);
  console.log('|---|---|---|---|');
  for (let i = 0; i < grenzen.length - 1; i++) {
    const sel = standaard.filter(x => { const a = f(x); return a >= grenzen[i] && a < grenzen[i + 1]; });
    if (sel.length < 20) continue;
    const s = samenvat(sel);
    console.log(`| ${k2(grenzen[i], 1)}–${isFinite(grenzen[i + 1]) ? k2(grenzen[i + 1], 1) : '…'} | ${sel.length} | ${k2(s.F)} | ${k2(s.F1)} |`);
  }
  console.log('');
}
perKlasse('tegemoet per passage', x => x.afdruk.tegPerPas, [0, 3, 5, 8, 12, Infinity]);
perKlasse('eigen tempo (m/s)', x => x.afdruk.tempo, [0, 1.0, 1.2, 1.35, 1.5, Infinity]);

/* ---------- ijken met een vaste teller ------------------------------------ */
// Per ronde staat Static midden in één vak en telt tijdens de ronde (97% trefkans).
// F̂ = Σ Static per uur / Σ Passanten, over k rondes. Hoe dicht zit F̂ bij de echte F?
console.log('## 4. IJken met Static: hoeveel rondes? ("standaard")\n');
const Fstd = trefRijen[2][1].F;
const ijk = standaard.map((x, i) => {
  const ok = x.vakken.filter(v => !v.gemist);
  if (!ok.length) return null;
  const v = ok[(i * 7919) % ok.length];
  const uur = 3600 / (x.R.T.T1 - x.R.T.T0);
  return { sta: v.sta * uur, vak: v.schat, straat: gem(ok.map(o => o.schat)) };
}).filter(Boolean);
console.log(`Echte F: ${k2(Fstd)}. Tabel: F̂ / F over groepjes van k rondes (mediaan en 10–90%).\n`);
console.log('| rondes k | vergeleken met het vak van Static | met het gemiddelde van de hele ronde |');
console.log('|---|---|---|');
[1, 3, 5, 10, 20, 40].forEach(k => {
  const a = [], b = [];
  for (let s = 0; s + k <= ijk.length; s += k) {
    const g = ijk.slice(s, s + k);
    a.push(som(g.map(x => x.sta)) / som(g.map(x => x.vak)) / Fstd);
    b.push(som(g.map(x => x.sta)) / som(g.map(x => x.straat)) / Fstd);
  }
  const f = r => `${k2(kwantiel(r, 0.5))} (${k2(kwantiel(r, 0.1))}–${k2(kwantiel(r, 0.9))})`;
  console.log(`| ${k} | ${f(a)} | ${f(b)} |`);
});

/* ---------- marges: groepjes of salvo's? --------------------------------- */
// De tikken komen in het echt sterker geclusterd dan bij toeval. Twee verklaringen
// geven dezelfde tussenpozen, maar niet dezelfde spreiding: groepjes wel, salvo's niet.
console.log('\n## 5. Marges: hoe breed moeten ze zijn?\n');
console.log('Twee verklaringen voor de clustering in het echt (67% van de tussenpozen ≤ 1 s).\n');
console.log('| verklaring | tussenpozen ≤ 1 s | dispersie φ | 95%-marge na F | na F en × √φ |');
console.log('|---|---|---|---|---|');
const STD = Object.assign({}, ALLES, tref[2][1]);
[['standaard: groepjes (gem. 1,65) + salvo\'s van 3 s', {}],
 ['alleen grotere groepjes (gem. 2,1), geen salvo\'s', { groep: [0.40, 0.30, 0.15, 0.15], salvo: 0 }],
 ['alleen salvo\'s van 4 s, iedereen alleen', { groep: [1], salvo: 4 }]].forEach(([naam, extra], i) => {
  const runs = i === 0 ? standaard : draai(Object.assign({}, STD, extra), RUNS, 80 + i);
  const s0 = samenvat(runs), s1 = samenvat(runs, null, Math.sqrt(s0.phi));
  const t = runs.map(x => x.afdruk).filter(a => a.n >= 3).flatMap(a => a.tus);
  console.log(`| ${naam} | ${pct(gem(t.map(g => g <= 1 ? 1 : 0)))} | ${k2(s0.phi, 1)} | ${pct(s0.dek1F)} | ${pct(s1.dek1F)} |`);
});
console.log(`\nKlaar in ${Math.round((Date.now() - t0) / 1000)} s.`);
