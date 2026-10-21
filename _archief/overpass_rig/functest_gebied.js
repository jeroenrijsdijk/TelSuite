/* v3.19 functionele test — het gebied vooraf ophalen (blok 'gebied vooraf').
   Knipt het gedeelde blok uit parkeertelling.html (byte-gelijkheid met
   fietsparkeren en pocket bewaakt valideer.py) en controleert:
     A. het blok staat in alle drie de bestanden, en is daar gelijk;
     B. de tegels: voor elk punt tot GEBIED_MARGE_M naast een geplande straat
        vraagt leesTegels alleen tegels uit de set, ook midden op een lange
        rechte straat (verdichten), en bij een negatieve lengtegraad;
     C. de zoekvraag: per rij aaneengesloten tegels één bbox op de tegelgrenzen,
        met dezelfde filters als fetchRoads in het veld;
     D. de regel in de statusbalk, lang en kort.
   Het ophalen zelf en de tegelcache (IndexedDB) toetst gebiedtest.py in Chromium.
   Draaien vanuit de suite-root (geen modules nodig):
     node _archief/overpass_rig/functest_gebied.js                            */
const fs = require('fs');
const vm = require('vm');

const START = '/* ── Gebied vooraf ophalen (v3.19)';
const EIND = '/* ── einde gedeeld blok gebied vooraf ── */';
function knip(bestand) {
  const html = fs.readFileSync(bestand, 'utf8');
  const i = html.indexOf(START); if (i < 0) return null;
  const j = html.indexOf(EIND, i); if (j < 0) return null;
  return html.slice(i, j + EIND.length);
}
const blok = knip('parkeertelling.html');
const ctx = { Math, String, Number, JSON, Array, Object, Promise, Error, console,
  TILE_DEG_SHARED: 0.01, HIGHWAY_RE: 'residential|footway' };
vm.createContext(ctx);
vm.runInContext(blok + `
this.G = { gebiedTegels, gebiedQuery, gebiedTekst, GEBIED_MARGE_M, GEBIED_STAP_M, GEBIED_MAX_TEGELS };`, ctx);
const G = ctx.G;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

// Precies de sleutels die leesTegels vraagt voor een cirkel (zelfde rekensom)
function leesSleutels(lat, lon, r) {
  const mPerLat = 111320, mPerLon = 111320 * Math.cos(lat * Math.PI / 180) || 1;
  const dLat = r / mPerLat, dLon = r / mPerLon, uit = [];
  const ty0 = Math.floor((lat - dLat) / 0.01), ty1 = Math.floor((lat + dLat) / 0.01);
  const tx0 = Math.floor((lon - dLon) / 0.01), tx1 = Math.floor((lon + dLon) / 0.01);
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) uit.push('t_' + ty + '_' + tx);
  return uit;
}
// Punten langs de lijn, en zijwaarts verschoven tot (marge) meter
function proef(lijn, marge, stap) {
  const pts = [];
  for (let i = 0; i + 1 < lijn.length; i++) {
    const a = lijn[i], b = lijn[i + 1];
    const cos = Math.cos(a[0] * Math.PI / 180);
    const dy = (b[0] - a[0]) * 111320, dx = (b[1] - a[1]) * 111320 * cos;
    const len = Math.sqrt(dx * dx + dy * dy), n = Math.max(1, Math.ceil(len / stap));
    const ny = -dx / len, nx = dy / len;          // loodrecht, in meters
    for (let k = 0; k <= n; k++) {
      const lat = a[0] + (b[0] - a[0]) * k / n, lon = a[1] + (b[1] - a[1]) * k / n;
      for (const s of [-marge, 0, marge]) pts.push([lat + ny * s / 111320, lon + nx * s / (111320 * cos)]);
    }
  }
  return pts;
}
function dekt(lijnen, radius) {
  const set = new Set(G.gebiedTegels(lijnen, radius).map(t => t.key));
  const mist = [];
  lijnen.forEach(l => proef(l, G.GEBIED_MARGE_M, 7).forEach(p => {
    leesSleutels(p[0], p[1], radius).forEach(k => { if (!set.has(k)) mist.push(k); });
  }));
  return { n: set.size, mist: [...new Set(mist)] };
}

console.log('\n== A. het blok in drie bestanden ==');
const bestanden = ['parkeertelling.html', 'fietsparkeren.html', 'pocket_count.html'];
const blokken = bestanden.map(knip);
eis('het blok staat in alle drie', blokken.every(b => b), bestanden.filter((f, i) => !blokken[i]));
eis('en is overal gelijk', blokken.every(b => b === blok));

console.log('\n== B. de tegels ==');
const wijk = [
  [[51.8510, 4.3020], [51.8540, 4.3025], [51.8562, 4.3101]],
  [[51.8495, 4.2990], [51.8499, 4.3060]],
];
let r = dekt(wijk, 300);
eis('een wijk (radius 300): leesTegels vraagt nergens een tegel buiten de set (%d tegels)'.replace('%d', r.n),
    r.mist.length === 0, r.mist);
r = dekt(wijk, 250);
eis('pocket (radius 250): idem', r.mist.length === 0, r.mist);
const lang = [[[51.8000, 4.2000], [51.8000, 4.2600]]];      // 4,1 km rechtdoor, zonder tussenpunten
r = dekt(lang, 300);
eis('een lange rechte straat zonder tussenpunten: ook het midden is gedekt (verdichten)', r.mist.length === 0, r.mist);
const west = [[[51.5074, -0.1300], [51.5090, -0.1240]]];
r = dekt(west, 300);
eis('negatieve lengtegraad (Londen): gedekt', r.mist.length === 0, r.mist);
const grens = [[[51.8500, 4.3000], [51.8500, 4.3000001]]];   // precies op een tegelhoek
r = dekt(grens, 300);
eis('op een tegelhoek: alle vier de buren erbij', r.n >= 4 && r.mist.length === 0, r);
const t1 = G.gebiedTegels(wijk, 300), t2 = G.gebiedTegels(wijk, 300);
eis('geen dubbelen, en gesorteerd op rij en kolom',
    new Set(t1.map(t => t.key)).size === t1.length &&
    t1.every((t, i) => i === 0 || t1[i - 1].ty < t.ty || (t1[i - 1].ty === t.ty && t1[i - 1].tx < t.tx)) &&
    JSON.stringify(t1) === JSON.stringify(t2));
eis('geen straten: geen tegels', G.gebiedTegels([], 300).length === 0);
eis('een wijk past ruim binnen GEBIED_MAX_TEGELS (%d)'.replace('%d', G.GEBIED_MAX_TEGELS), t1.length <= 12, t1.length);

console.log('\n== C. de zoekvraag ==');
const tegels = [{ ty: 5185, tx: 430 }, { ty: 5185, tx: 431 }, { ty: 5185, tx: 432 },
                { ty: 5186, tx: 430 }, { ty: 5186, tx: 432 }];
const q = G.gebiedQuery(tegels);
const bboxen = (q.match(/\((-?[\d.]+,-?[\d.]+,-?[\d.]+,-?[\d.]+)\)/g) || []);
eis('drie rijen-stukken, elk twee keer (wegen en building_passage)', bboxen.length === 6, bboxen);
eis('rij 5185, kolom 430–432 is één bbox op de tegelgrenzen', bboxen[0] === '(51.85,4.30,51.86,4.33)', bboxen[0]);
eis('een gat in de rij geeft twee bboxen', bboxen.indexOf('(51.86,4.30,51.87,4.31)') >= 0 &&
    bboxen.indexOf('(51.86,4.32,51.87,4.33)') >= 0, bboxen);
eis('zelfde filters als in het veld', q.indexOf('way["highway"~"residential|footway"]["area"!="yes"](51.85,4.30,51.86,4.33);') >= 0 &&
    q.indexOf('way["tunnel"="building_passage"](51.85,4.30,51.86,4.33);') >= 0 && /out body geom;$/.test(q), q);
eis('geen around: niets hangt aan je positie', q.indexOf('around') < 0);
const qw = G.gebiedQuery([{ ty: 5150, tx: -13 }]);
eis('negatieve lengtegraad: (51.50,-0.13,51.51,-0.12)', qw.indexOf('(51.50,-0.13,51.51,-0.12)') >= 0, qw);

console.log('\n== D. de regel ==');
eis('bezig', G.gebiedTekst(null) === 'gebied klaarzetten…');
eis('opgehaald', G.gebiedTekst({ tegels: 6, nieuw: 6, kb: 830 }) === 'gebied klaar (6 tegels, 830 kB opgehaald)', G.gebiedTekst({ tegels: 6, nieuw: 6, kb: 830 }));
eis('al bewaard', G.gebiedTekst({ tegels: 1, nieuw: 0, kb: 0 }) === 'gebied klaar (1 tegel, al bewaard)');
eis('te groot', G.gebiedTekst({ tegels: 44, fout: 'te groot' }) === 'gebied te groot om klaar te zetten (44 tegels)');
eis('mislukt, met reden', G.gebiedTekst({ tegels: 6, fout: 'Overpass is overbelast' }) === 'gebied niet klaargezet: Overpass is overbelast');
eis('kort', G.gebiedTekst({ tegels: 6, nieuw: 6, kb: 1 }, true) === 'gebied klaar' &&
    G.gebiedTekst({ tegels: 6, fout: 'x' }, true) === 'gebied niet klaargezet' &&
    G.gebiedTekst(undefined, true) === 'gebied klaarzetten…');

console.log('\n' + (fout ? fout + ' FOUT, ' + ok + ' OK' : 'ALLE ' + ok + ' TESTS OK'));
process.exit(fout ? 1 : 0);
