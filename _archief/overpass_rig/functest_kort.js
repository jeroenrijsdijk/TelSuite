/* v3.42 functionele test — "te kort gemeten" in telrapport (pocket, p/m·u),
   los van de browser.

   Jay: "Nu de korte linkjes op de kaart staan verstoren het beeld van het
   resultaat. 1 tik op een korte link is al gauw enorm druk. Zie link 136445442".
   Een pocket-segment krijgt pas een kleur als lengte × aanwezigheid, alle
   zichtbare tellingen samen, minstens PMU_MIN_MS (300) meter·seconde is.

   Draaien vanuit de suite-root:  node _archief/overpass_rig/functest_kort.js */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telrapport.html', 'utf8');

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
const blok = (a, z) => { const i = html.indexOf(a), j = html.indexOf(z, i); if (i < 0 || j < 0) throw new Error('blok: ' + a); return html.slice(i, j + z.length); };

const ctx = { wayData: {}, wayLayers: {}, visitData: {}, sessions: {}, maxFietsTotaal: 1 };
vm.createContext(ctx);
vm.runInContext([
  'var wayData = this.wayData, wayLayers = this.wayLayers, visitData = this.visitData, sessions = this.sessions, maxFietsTotaal = 1;',
  'function pocketZichtbaar(sid) { return !!(sessions[sid] && sessions[sid].visible); }',
  'function getSessionColor() { return "#123456"; }',
  regel(/const PMU_MIN_MS = [^;]+;/), regel(/const KORT_KLEUR = [^;]+;/),
  blok('const INTENSITEIT = [', '];'),
  functie('intensityClass'), functie('parseKey'), functie('segmentLengthM'), functie('heatColor'),
  functie('pmuForKey'), functie('pmuMeting'), functie('kortTekst'), functie('wayHeat'), functie('recolorOne')
].join('\n') + '\nthis.f = { pmuForKey, pmuMeting, kortTekst, wayHeat, recolorOne, PMU_MIN_MS, KORT_KLEUR };', ctx);
const F = ctx.f;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

// Een segment van L meter (noord), met bezoeken [{ sid, sec, tikken }].
const M = 1 / 111320;
function zet(key, L, bezoeken) {
  const [wid, seg] = key.split(':');
  Object.keys(ctx.visitData).forEach(sid => { ctx.visitData[sid] = ctx.visitData[sid].filter(v => !(v.wid === wid && v.segIdx === +seg)); });
  ctx.wayData[key] = { geometry: [[52, 5], [52 + L * M, 5]], sessions: [], wayId: wid, segIdx: +seg };
  bezoeken.forEach(b => {
    ctx.sessions[b.sid] = ctx.sessions[b.sid] || { visible: true, appType: 'pocket' };
    (ctx.visitData[b.sid] = ctx.visitData[b.sid] || []).push({ wid, segIdx: +seg, durSec: b.sec, nTel: b.tikken });
    ctx.wayData[key].sessions.push({ sid: b.sid, appType: 'pocket', totaal: b.tikken, zeroVisited: b.tikken === 0 });
  });
}
const lijn = () => { const l = { stijl: null, setStyle(s) { this.stijl = s; } }; return l; };

console.log('== de drempel ==');
eis('PMU_MIN_MS = 300 meter·seconde', F.PMU_MIN_MS === 300);

console.log('\n== een gewoon segment ==');
zet('258377242:0', 43.3, [{ sid: 'a', sec: 19, tikken: 14 }]);
let m = F.pmuMeting('258377242:0');
eis('43,3 m × 19 s, 14 tikken: 61 p/m·u, niet te kort (823 m·s)', Math.abs(m.pmu - 14 / (43.3 * 19 / 3600)) < 0.01 && !m.kort && Math.round(m.ms) === 823, m);
eis('pmuForKey geeft de waarde, wayHeat een kleur (Zeer druk)', Math.abs(F.pmuForKey('258377242:0') - m.pmu) < 1e-9 && F.wayHeat('258377242:0').label === 'Zeer druk', F.wayHeat('258377242:0'));
let l = lijn(); ctx.wayLayers['258377242:0'] = l; F.recolorOne('258377242:0');
eis('op de kaart: in de kleur van de klasse, doorgetrokken', l.stijl.dashArray === null && l.stijl.color === F.wayHeat('258377242:0').kleur, l.stijl);

console.log('\n== het korte stukje van Jay (136445442) ==');
zet('136445442:0', 6.6, [{ sid: 'a', sec: 2, tikken: 1 }]);
m = F.pmuMeting('136445442:0');
eis('6,6 m × 2 s met 1 tik: 273 p/m·u (Extreem druk), maar te kort gemeten (13 m·s)', Math.abs(m.pmu - 1 / (6.6 * 2 / 3600)) < 0.01 && m.kort && Math.round(m.ms) === 13, m);
eis('geen waarde voor de kaart (pmuForKey null) en geen kleur (wayHeat null)', F.pmuForKey('136445442:0') === null && F.wayHeat('136445442:0') === null);
l = lijn(); ctx.wayLayers['136445442:0'] = l; F.recolorOne('136445442:0');
eis('op de kaart: dun grijs gestreept', l.stijl.color === F.KORT_KLEUR && l.stijl.dashArray === '2 5' && l.stijl.weight < 4, l.stijl);
eis('de tekst noemt de meting en de drempel', /te kort gemeten: 13 meter·seconde .*vanaf 300/.test(F.kortTekst(m)), F.kortTekst(m));

console.log('\n== vaker gelopen: het telt op ==');
zet('136445442:0', 6.6, [{ sid: 'a', sec: 2, tikken: 1 }, { sid: 'b', sec: 50, tikken: 1 }]);
m = F.pmuMeting('136445442:0');
eis('twee tellingen samen: 6,6 m × 52 s = 343 m·s, dus wel een kleur (2 tikken: 21 p/m·u, Matig)',
    !m.kort && Math.round(m.ms) === 343 && F.wayHeat('136445442:0') && F.wayHeat('136445442:0').label === 'Matig', [m, F.wayHeat('136445442:0')]);
ctx.sessions.b.visible = false;
eis('verberg de tweede telling: weer te kort', F.pmuMeting('136445442:0').kort && F.pmuForKey('136445442:0') === null);
ctx.sessions.b.visible = true;

console.log('\n== zonder tikken: zoals altijd ==');
zet('305452946:1', 6.6, [{ sid: 'c', sec: 3, tikken: 0 }]);
eis('een kort stukje zonder tikken is geen "te kort gemeten" maar "bezocht, geen waarnemingen"', F.pmuMeting('305452946:1') === null);
l = lijn(); ctx.wayLayers['305452946:1'] = l; F.recolorOne('305452946:1');
eis('op de kaart: gestreept in de kleur van de telling', l.stijl.color === '#123456' && l.stijl.dashArray === '6 4', l.stijl);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
