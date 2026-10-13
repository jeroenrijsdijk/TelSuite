/* v3.7 functionele test — de tabel "Tellingen op dit segment" in het weekprofiel
   van telrapport. Knipt renderSegmentSessionTable() uit telrapport.html en voert
   hem met nagebootste sessies en bezoeken (visits).

   Gecontroleerd:
     - nieuwste bovenaan, ook over maanden en jaren heen (vóór v3.7 werd op de
       datumtekst "dd-mm-jjjj" gesorteerd, dus op dag van de maand);
     - twee tellingen op één dag: de latere bovenaan;
     - weekdag vóór de datum, zoals in het dag×uur-diagram (ma … zo);
     - aanwezigheid altijd in seconden, ook boven de minuut en in de ∑-rij;
     - alleen bezoeken aan dit segment en alleen zichtbare sessies tellen.     */
process.env.TZ = 'Europe/Amsterdam';
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 40));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 40));
  return html.slice(i, j + b.length);
}
const fn = knip('function renderSegmentSessionTable(', "  html += '</table>';\n  return html;\n}");
const fmt = knip('function fmtDatum(d, t) {', '\n}');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

// Een bezoek aan way 136079339, segment 0, op een lokale datum en tijd
const bezoek = (j, mnd, d, u, m, sec, tel, wid, seg) => ({
  wid: wid || '136079339', segIdx: seg || 0,
  tStart: new Date(j, mnd - 1, d, u, m, 0), tEnd: new Date(j, mnd - 1, d, u, m, sec),
  durSec: sec, nTel: tel
});
const visitData = {
  a: [bezoek(2026, 7, 1, 14, 5, 36, 28)],                        // wo 01-07-2026
  b: [bezoek(2026, 8, 1, 10, 0, 20, 13)],                        // za 01-08-2026
  c: [bezoek(2026, 10, 3, 15, 10, 40, 30), bezoek(2026, 10, 3, 15, 30, 32, 19)],  // za 03-10, 2 bezoeken, 72 s
  d: [bezoek(2026, 5, 20, 9, 0, 23, 2)],                         // wo 20-05 's ochtends
  e: [bezoek(2026, 5, 20, 16, 45, 30, 17)],                      // wo 20-05 's middags
  f: [bezoek(2025, 12, 31, 23, 50, 25, 9)],                      // wo 31-12-2025: vorig jaar
  g: [bezoek(2026, 9, 1, 12, 0, 50, 99, '999')],                 // ander segment: telt niet
  h: [bezoek(2026, 9, 2, 12, 0, 50, 99)]                         // verborgen sessie: telt niet
};
const sessions = {};
Object.keys(visitData).forEach(sid => { sessions[sid] = { meta: { datum: '', start_tijd: '' } }; });

const ctx = {
  String, Math, Date, Object, visitData, sessions,
  pocketZichtbaar: sid => sid !== 'h',
  intensityClass: v => ({ kleur: '#fff', label: v >= 60 ? 'Zeer druk' : 'Druk' })
};
vm.createContext(ctx);
vm.runInContext(fmt + '\n' + fn, ctx);
const uit = vm.runInContext("renderSegmentSessionTable({}, '136079339', 0, 45)", ctx);

const rijen = [...uit.matchAll(/<tr(?: class="([^"]*)")?>(.*?)<\/tr>/gs)]
  .map(m => ({ klasse: m[1] || '', cellen: [...m[2].matchAll(/<td[^>]*>(.*?)<\/td>/g)].map(c => c[1]) }))
  .filter(r => r.cellen.length);
const data = rijen.filter(r => r.klasse !== 'sum-row');
const som = rijen.find(r => r.klasse === 'sum-row');

console.log('== volgorde: nieuwste bovenaan ==');
const datums = data.map(r => r.cellen[0]);
eis('zes tellingen (ander segment en verborgen sessie niet)', data.length === 6, datums);
eis('volgorde op tijd, nieuwste eerst', JSON.stringify(datums) === JSON.stringify([
  'za 03-10-2026', 'za 01-08-2026', 'wo 01-07-2026', 'wo 20-05-2026', 'wo 20-05-2026', 'wo 31-12-2025']), datums);
eis('twee tellingen op 20-05: de middag (17 tikken) boven de ochtend (2 tikken)',
  data[3].cellen[3] === '17' && data[4].cellen[3] === '2', [data[3].cellen[3], data[4].cellen[3]]);

console.log('\n== weekdag ==');
eis('03-10-2026 is een zaterdag', datums[0].startsWith('za '));
eis('31-12-2025 is een woensdag', datums[5].startsWith('wo '));

console.log('\n== aanwezigheid in seconden ==');
eis('twee bezoeken van 40 + 32 s: "72 s", niet "1.2 min"', data[0].cellen[2] === '72 s', data[0].cellen[2]);
eis('nergens nog minuten', !/min/.test(uit));
eis('∑-rij in seconden: 36+20+72+23+30+25 = 206 s', som && som.cellen[2] === '206 s', som && som.cellen[2]);
eis('∑-rij telt de tikken op: 28+13+49+2+17+9 = 118', som && som.cellen[3] === '118', som && som.cellen[3]);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
process.exit(fout ? 1 : 0);
