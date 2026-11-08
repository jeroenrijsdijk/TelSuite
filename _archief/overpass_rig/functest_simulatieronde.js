/* v3.46 functionele test — simulatieronde.html, de simulatie achter de ijking.

   Jay: "Verwijzen naar simulatieronde.html [...] om het systeem van winkelstraat
   telling naar passanten te begrijpen", en de ijkfactor "Naar 1,03".
   De pagina draagt een kopie van _archief/passantensim/sim_kern.js en van het
   blok PASSANTEN uit passanten.html, en zijn eigen IJK. Deze test bewaakt dat
   die drie gelijk blijven aan het origineel, en draait de kopieën uit de pagina
   zelf: de simulatie, door Passanten, op een week aan drukte.

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_simulatieronde.js */
const fs = require('fs');
const vm = require('vm');
const pagina = fs.readFileSync('simulatieronde.html', 'utf8');
const pas = fs.readFileSync('passanten.html', 'utf8');
const kern = fs.readFileSync('_archief/passantensim/sim_kern.js', 'utf8');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
function tussen(t, a, z) { const i = t.indexOf(a), j = t.indexOf(z, i); if (i < 0 || j < 0) throw new Error('niet gevonden: ' + a); return t.slice(i + a.length, j); }

console.log('== de kopieën ==');
const kopKern = tussen(pagina, '/* ==== kopie van _archief/passantensim/sim_kern.js (node _archief/passantensim/kijkercheck.js) ==== */\n', '/* ==== einde kopie sim_kern.js ==== */');
const kopPas = tussen(pagina, '/* ==== kopie van het blok PASSANTEN uit passanten.html (node _archief/passantensim/kijkercheck.js) ==== */\n', '/* ==== einde kopie PASSANTEN ==== */');
const blok = pas.slice(pas.indexOf('/* ── Passanten per uur: de rekenkern (v3.34)'), pas.indexOf('/* ── einde gedeeld blok passanten ── */') + '/* ── einde gedeeld blok passanten ── */'.length) + '\n';
eis('sim_kern.js in de pagina is gelijk aan _archief/passantensim/sim_kern.js', kopKern === kern, [kopKern.length, kern.length]);
eis('het blok PASSANTEN in de pagina is gelijk aan dat in passanten.html', kopPas === blok, [kopPas.length, blok.length]);
const ijkPagina = +/var IJK = ([0-9.]+);/.exec(pagina)[1], ijkPas = +/var IJKFACTOR = ([0-9.]+);/.exec(pas)[1];
eis('de ijkfactor van de pagina is die van passanten.html (' + ijkPas + ')', ijkPagina === ijkPas && ijkPas === 1.03, [ijkPagina, ijkPas]);

console.log('\n== de pagina ==');
eis('geen verzoeken naar buiten: de lettertypen uit fonts/, geen Google', pagina.includes('href="fonts/fonts.css"') && !/fonts\.googleapis|fonts\.gstatic/.test(pagina));
eis('een gewone pagina van de suite: doctype, lang="nl", canonical', /^<!DOCTYPE html>\n<html lang="nl">/.test(pagina) && pagina.includes('<link rel="canonical" href="https://telonline.org/simulatieronde.html">'));
eis('de handleiding en Passanten verwijzen ernaar', fs.readFileSync('traffic_counter_help.html', 'utf8').includes('href="simulatieronde.html"') && pas.includes('href="simulatieronde.html"'));
eis('en hij staat in de sitemap', fs.readFileSync('sitemap.xml', 'utf8').includes('<loc>https://telonline.org/simulatieronde.html</loc>'));

console.log('\n== de kopieën draaien: een week aan drukte ==');
const c = {}; vm.createContext(c);
vm.runInContext(kopPas + kopKern + '\nthis.P = PASSANTEN; this.S = SIMKERN;', c);
const WEEK = JSON.parse(JSON.stringify(eval('(' + /week:\s+\{ q: (\{[^}]*\})/.exec(pagina)[1].replace(/(\w+):/g, '"$1":') + ')')));
eis('de drukte "een week": 50–3.000, mediaan 600, spreiding 0,75, teller niet onder 0,8 m/s',
    WEEK.qMin === 50 && WEEK.qMax === 3000 && WEEK.qMediaan === 600 && WEEK.qSpreiding === 0.75 && WEEK.tempoMin === 0.8, WEEK);
const PARAM = Object.assign({ pZelf: 0.95, pOver: 0.95, pGroep: 1, qZicht: Infinity }, WEEK);
const qs = [], u = []; let sw = 0, ss = 0;
for (let z = 1; z <= 300; z++) {
  const R = c.S.run(PARAM, z), ses = c.P.sessie(R.invoer, 's'), segs = {};
  c.P.voegToe(segs, ses); c.P.bereken(segs, c.P.V_VOET);
  qs.push(R.W.qTot); u.push(R.T.uBasis);
  R.W.segs.forEach(g => { const x = segs['1/' + g.k]; if (!x) return; const cl = x.cells[Object.keys(x.cells)[0]];
    const n = ['A', 'B', '?'].filter(r => cl.stromen[r].n).length; sw += g.qPlus + g.qMin; ss += cl.q * (!cl.compleet && n === 1 ? 2 : 1); });
}
qs.sort((a, b) => a - b);
eis('300 rondes: drukte binnen 50–3.000, mediaan rond 600 (' + Math.round(qs[150]) + ')', qs[0] >= 50 && qs[299] <= 3000 && qs[150] > 500 && qs[150] < 720, [qs[0], qs[150], qs[299]]);
eis('de teller loopt nooit langzamer dan 0,8 m/s', Math.min(...u) >= 0.8 - 1e-9, Math.min(...u));
const F = sw / ss;
eis('F over 300 rondes rond de ijkfactor (' + F.toFixed(3) + ', 0,97–1,09)', F > 0.97 && F < 1.09, F);
const R1 = c.S.run(PARAM, 68), R2 = c.S.run(PARAM, 68);
eis('herhaalbaar: hetzelfde zaadje geeft dezelfde ronde, met de voetgangers en ontmoetingen voor het diagram',
    JSON.stringify(R1.invoer) === JSON.stringify(R2.invoer) && R1.V.length > 0 && R1.ontmoetingen.some(o => o.soort === 'tegemoet' && 'worp' in o), R1.V.length);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
