/* v3.7 functionele test — het weekprofiel van een segment in telrapport: de
   tabel "Tellingen op dit segment" en de cellen van het dag×uur-diagram.
   Knipt de functies uit telrapport.html en voert ze met nagebootste sessies.

   Gecontroleerd:
     A. tabel: nieuwste bovenaan (vóór v3.7 werd op de datumtekst "dd-mm-jjjj"
        gesorteerd, dus op dag van de maand), weekdag + datum + tijd, aanwezigheid
        altijd in seconden (met "· n×" bij meer bezoeken), ∑-rij;
     B. 95%-marge (exact Poisson-interval), getoetst aan bekende waarden;
     C. 'onzeker': minder dan 5 tikken én de marge over een klassegrens;
     D. koppeling: elke rij weet in welke cellen (dag-uur) hij meetelt, elke
        gemeten cel heeft een data-cel;
     E. alleen bezoeken aan dit segment en alleen zichtbare sessies tellen.      */
process.env.TZ = 'Europe/Amsterdam';
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 40));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 40));
  return html.slice(i, j + b.length);
}
const code = [
  knip('const INTENSITEIT = [', '];'),
  knip('function intensityClass(pmu) {', '\n}'),
  knip('function fmtDatum(d, t) {', '\n}'),
  knip('// ── Betrouwbaarheid van een p/m·u (v3.7)', "function margeTekst(m) {"),
  "return m ? `95%-marge ${fmtPmh(m.lo)}–${fmtPmh(m.hi)} p/m·u` : ''; }",
  knip('function splitVisitIntoHourBuckets(v) {', '\n  return buckets;\n}'),
  knip('function renderWeeklyHeatmap(hm) {', '\n  return html + legHtml;\n}'),
  knip('function renderSegmentSessionTable(', "  return html;\n}")
].join('\n');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const bijna = (a, b, tol) => Math.abs(a - b) <= tol;

// Een bezoek aan way 136079339, segment 0, op een lokale datum en tijd
const bezoek = (j, mnd, d, u, m, sec, tel, wid) => ({
  wid: wid || '136079339', segIdx: 0,
  tStart: new Date(j, mnd - 1, d, u, m, 0), tEnd: new Date(j, mnd - 1, d, u, m, sec),
  durSec: sec, nTel: tel
});
const visitData = {
  a: [bezoek(2026, 7, 1, 14, 5, 36, 28)],                        // wo 01-07-2026 14:05
  b: [bezoek(2026, 8, 1, 10, 0, 20, 13)],                        // za 01-08-2026
  c: [bezoek(2026, 10, 3, 15, 10, 40, 30), bezoek(2026, 10, 3, 15, 30, 32, 19)],  // za 03-10, 2 bezoeken
  d: [bezoek(2026, 5, 20, 9, 0, 23, 2)],                         // wo 20-05 's ochtends: 2 tikken
  e: [bezoek(2026, 5, 20, 16, 45, 30, 17)],                      // wo 20-05 's middags
  f: [bezoek(2025, 12, 31, 23, 50, 25, 9)],                      // wo 31-12-2025: vorig jaar
  g: [bezoek(2026, 9, 1, 12, 0, 50, 99, '999')],                 // ander segment: telt niet
  h: [bezoek(2026, 9, 2, 12, 0, 50, 99)],                        // verborgen sessie: telt niet
  i: [bezoek(2026, 6, 1, 8, 59, 120, 1)]                         // ma 01-06 08:59, 2 min over de uurgrens
};
const sessions = {};
Object.keys(visitData).forEach(sid => { sessions[sid] = { meta: { datum: '', start_tijd: '' } }; });

const ctx = { String, Math, Date, Object, Array, Set, visitData, sessions, pocketZichtbaar: sid => sid !== 'h' };
vm.createContext(ctx);
vm.runInContext(code, ctx);
const LEN = 45;
const uit = vm.runInContext("renderSegmentSessionTable({}, '136079339', 0, " + LEN + ")", ctx);

const rijen = [...uit.matchAll(/<tr([^>]*)>(.*?)<\/tr>/gs)]
  .map(m => ({ attr: m[1], cellen: [...m[2].matchAll(/<td([^>]*)>(.*?)<\/td>/g)].map(c => ({ attr: c[1], tekst: c[2] })) }))
  .filter(r => r.cellen.length);
const data = rijen.filter(r => !/sum-row/.test(r.attr));
const som = rijen.find(r => /sum-row/.test(r.attr));
const kol = (r, i) => r.cellen[i].tekst;          // 0 datum, 1 aanwezig, 2 tikken, 3 p/m·u, 4 klasse

console.log('== A. tabel ==');
const datums = data.map(r => kol(r, 0));
eis('zeven tellingen (ander segment en verborgen sessie niet)', data.length === 7, datums);
eis('nieuwste bovenaan, met weekdag en tijd', JSON.stringify(datums) === JSON.stringify([
  'za 03-10-2026 15:10', 'za 01-08-2026 10:00', 'wo 01-07-2026 14:05', 'ma 01-06-2026 08:59',
  'wo 20-05-2026 16:45', 'wo 20-05-2026 09:00', 'wo 31-12-2025 23:50']), datums);
eis('kolommen: datum, aanwezig, tikken, p/m·u, klasse (visits zit in aanwezig)',
  /<th>datum<\/th><th>aanwezig<\/th><th>tikken<\/th><th>p\/m·u<\/th><th>klasse<\/th>/.test(uit));
eis('twee bezoeken van 40 + 32 s: "72 s · 2×"', kol(data[0], 1) === '72 s · 2×', kol(data[0], 1));
eis('één bezoek: alleen seconden, "120 s" (niet "2.0 min")', kol(data[3], 1) === '120 s', kol(data[3], 1));
eis('nergens nog minuten', !/\bmin\b/.test(uit));
eis('∑-rij: 72+20+36+120+30+23+25 = 326 s, 8 bezoeken', som && kol(som, 1) === '326 s · 8×', som && kol(som, 1));
eis('∑-rij telt de tikken op: 49+13+28+1+17+2+9 = 119', som && kol(som, 2) === '119', som && kol(som, 2));

console.log('\n== B. 95%-marge (exact Poisson) ==');
const marge = k => vm.runInContext('poissonMarge(' + k + ')', ctx);
// Referentie: chi2.ppf(0.025, 2k)/2 en chi2.ppf(0.975, 2k+2)/2 (scipy)
[[0, 0, 3.6889], [1, 0.0253, 5.5716], [2, 0.2422, 7.2247], [5, 1.6235, 11.6683],
 [50, 37.1110, 65.9188], [1000, 938.9730, 1063.9521]].forEach(([k, lo, hi]) => {
  const [a, b] = marge(k);
  eis(`k=${k}: ${lo}–${hi}`, bijna(a, lo, 0.002) && bijna(b, hi, 0.002), [a, b]);
});
const titelPmh = r => (r.cellen[3].attr.match(/title="([^"]*)"/) || [])[1];
eis('tooltip op p/m·u: 2 tikken in 23 s op 45 m → 0.8–25 p/m·u',
  titelPmh(data[5]) === '95%-marge 0.8–25 p/m·u', titelPmh(data[5]));

console.log('\n== C. onzeker ==');
eis('2 tikken: onzeker (lichter)', /class="onzeker"/.test(data[5].attr));
eis('1 tik in 120 s: marge 0–3.7 p/m·u valt helemaal in Rustig → niet onzeker',
  !/onzeker/.test(data[3].attr), [data[3].attr, titelPmh(data[3])]);
eis('17 tikken: niet onzeker', !/onzeker/.test(data[4].attr));

console.log('\n== D. koppeling met het diagram ==');
const cellenVan = r => (r.attr.match(/data-cellen="([^"]*)"/) || [])[1];
eis('za 03-10 15:10 en 15:30 → cel za-15 ("5-15")', cellenVan(data[0]) === '5-15', cellenVan(data[0]));
eis('ma 08:59 + 120 s gaat over de uurgrens → "0-8 0-9"', cellenVan(data[3]) === '0-8 0-9', cellenVan(data[3]));
// Diagram: maak de cellen zoals buildWeeklyHeatmap ze maakt
const hm = vm.runInContext(`(() => {
  const cells = Array.from({length: 7}, () => Array.from({length: 24}, () => ({ secs: 0, taps: 0 })));
  Object.keys(visitData).filter(pocketZichtbaar).forEach(sid => visitData[sid]
    .filter(v => v.wid === '136079339').forEach(v => splitVisitIntoHourBuckets(v).forEach(b => {
      cells[b.dow][b.hour].secs += b.secs; cells[b.dow][b.hour].taps += b.taps; })));
  cells.forEach(r => r.forEach(c => { c.value = c.secs > 0 ? c.taps / (${LEN} * c.secs / 3600) : null; }));
  return { cells: cells, lenM: ${LEN} };
})()`, ctx);
const diag = vm.runInContext('renderWeeklyHeatmap', ctx)(hm);
const gemeten = hm.cells.flat().filter(c => c.value !== null).length;
eis('elke gemeten cel heeft een data-cel (' + gemeten + ')', (diag.match(/data-cel="/g) || []).length === gemeten);
eis('cel wo-9 (2 tikken) is lichter', /data-cel="2-9" class="hm-onzeker"/.test(diag));
eis('tooltip van een cel in seconden, met marge', /za 15:00 · [\d.]+ p\/m·u · \w[^"]*\(49 tikken in 72 s\) · 95%-marge/.test(diag));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
process.exit(fout ? 1 : 0);
