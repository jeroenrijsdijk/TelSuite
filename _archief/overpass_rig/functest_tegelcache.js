/* v3.20 functionele test — tegels schrijven tijdens het lopen (cacheWaysInTiles).
   Knipt het gedeelde blok uit parkeertelling.html (byte-gelijkheid met
   fietsparkeren, capaciteitstelling en pocket bewaakt valideer.py) en draait het
   met een nagebouwde IndexedDB. Controleert de drie reparaties van v3.20:
     A. dekking: een cel telt pas als hij helemaal binnen een cirkel ligt. Een
        cirkel die alle celmiddens raakt maar niet alle hoeken, maakt een tegel
        niet meer compleet (tot v3.20 wel: dan ontbrak een weg in die hoeken);
     B. toewijzing: een weg met een lang segment door een tegel, zonder punt in
        die tegel, komt in die tegel (tegelsVanWeg);
     C. knooppunten: een weg zonder nodes maakt een tegel onbruikbaar; hij gaat
        niet de cache in. Weggeschreven tegels dragen schema 3;
     D. na het wegschrijven van een tegel breekt een volgende fetch die hem weer
        raakt niets meer af (tot v3.20 een stille TypeError, en schreef de app
        daarna geen tegels meer).
   Draaien vanuit de suite-root (geen modules nodig):
     node _archief/overpass_rig/functest_tegelcache.js                        */
const fs = require('fs');
const vm = require('vm');

const START = '// Bewaar ways per tegel';
const EIND = '  } catch (e) { /* cache is best-effort: nooit het tellen verstoren */ }\n}';
function knip(bestand) {
  const html = fs.readFileSync(bestand, 'utf8');
  const i = html.indexOf(START); if (i < 0) return null;
  const j = html.indexOf(EIND, i); if (j < 0) return null;
  return html.slice(i, j + EIND.length);
}
const blok = knip('parkeertelling.html');

function maakCtx() {
  const tabel = {};
  const db = { transaction() { return { objectStore() { return { put(r) { tabel[r.key] = r; } }; } }; } };
  const ctx = { Math, Object, Date, Promise, console, tabel,
    TILE_DEG_SHARED: 0.01, TILE_STORE: 'tiles', TEGEL_SCHEMA: 3,
    _tileDb() { return Promise.resolve(db); } };
  vm.createContext(ctx);
  vm.runInContext(blok + '\nthis.cache = cacheWaysInTiles; this.vanWeg = tegelsVanWeg; this.cov = function () { return _tileCov; };', ctx);
  return ctx;
}
const wacht = () => new Promise(r => setTimeout(r, 10));
let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

// Tegel t_5185_430: 51,85–51,86 N, 4,30–4,31 O. Midden 51,855/4,305. Hoeken op
// ~654 m van het midden; het verste celmidden op ~572 m.
const MID = [51.855, 4.305];
const weg = (id, pts, nodes) => ({ type: 'way', id, nodes: nodes === undefined ? pts.map((p, i) => id * 100 + i) : nodes,
  geometry: pts.map(p => ({ lat: p[0], lon: p[1] })), tags: { highway: 'residential', name: 'W' + id } });
const kort = weg(1, [[51.855, 4.305], [51.8555, 4.3055]]);
// van tegel 5184 naar tegel 5186, recht door 5185 heen, zonder punt in 5185
const lang = weg(2, [[51.8495, 4.3050], [51.8605, 4.3051]]);

(async () => {
  console.log('\n== het blok in vier bestanden ==');
  const bestanden = ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html', 'pocket_count.html'];
  const blokken = bestanden.map(knip);
  eis('het blok staat in alle vier', blokken.every(b => b), bestanden.filter((f, i) => !blokken[i]));
  eis('en is overal gelijk', blokken.every(b => b === blok));

  console.log('\n== A. dekking ==');
  let c = maakCtx();
  c.cache([kort, lang], MID[0], MID[1], 600);
  await wacht();
  const t = c.cov()['t_5185_430'];
  eis('r = 600 m: alle celmiddens binnen de cirkel, maar niet alle hoeken: de tegel is niet compleet',
      !c.tabel['t_5185_430'] && t && t.n < 64, t && t.n);
  c = maakCtx();
  c.cache([kort, lang], MID[0], MID[1], 660);
  await wacht();
  eis('r = 660 m: de hele tegel binnen de cirkel: hij gaat de cache in', !!c.tabel['t_5185_430'], Object.keys(c.tabel));
  eis('alleen die tegel (de buren zijn niet helemaal gedekt)', Object.keys(c.tabel).length === 1, Object.keys(c.tabel));

  console.log('\n== B. toewijzing per segment ==');
  const rec = c.tabel['t_5185_430'];
  eis('de lange weg zonder punt in de tegel staat erin', rec && rec.ways.some(w => w.id === 2), rec && rec.ways.map(w => w.id));
  eis('de korte weg ook', rec && rec.ways.some(w => w.id === 1));
  eis('tegelsVanWeg: drie tegels voor het lange segment',
      JSON.stringify(c.vanWeg(lang.geometry).sort()) === JSON.stringify(['t_5184_430', 't_5185_430', 't_5186_430']), c.vanWeg(lang.geometry));
  eis('tegelsVanWeg: een schuin segment over een tegelhoek raakt alle vier',
      c.vanWeg([{ lat: 51.8495, lon: 4.2995 }, { lat: 51.8505, lon: 4.3005 }]).length === 4);

  console.log('\n== C. knooppunten en schema ==');
  eis('weggeschreven tegel: schema 3, wegen met knooppunten', rec && rec.v === 3 && rec.ways.every(w => w.nodes.length >= 2), rec && rec.v);
  c = maakCtx();
  c.cache([kort, weg(3, [[51.856, 4.306], [51.857, 4.307]], [])], MID[0], MID[1], 660);
  await wacht();
  eis('een weg zonder knooppunten: de tegel gaat de cache niet in', !c.tabel['t_5185_430'], Object.keys(c.tabel));

  console.log('\n== D. na het wegschrijven verder ==');
  c = maakCtx();
  c.cache([kort], MID[0], MID[1], 660);                 // tegel 5185_430 compleet en weg
  await wacht();
  const oost = weg(4, [[51.855, 4.315], [51.8555, 4.3155]]);
  c.cache([kort, oost], 51.855, 4.315, 660);             // raakt 5185_430 opnieuw, maakt 5185_431 compleet
  await wacht();
  eis('een volgende fetch die de weggeschreven tegel raakt: de buurtegel gaat gewoon de cache in',
      !!c.tabel['t_5185_431'] && c.tabel['t_5185_431'].ways.some(w => w.id === 4), Object.keys(c.tabel));
  eis('en de weggeschreven tegel wordt niet opnieuw geschreven of leeggemaakt',
      c.tabel['t_5185_430'].ways.length === 1, c.tabel['t_5185_430'].ways.map(w => w.id));

  console.log('\n' + (fout ? fout + ' FOUT, ' + ok + ' OK' : 'ALLE ' + ok + ' TESTS OK'));
  process.exit(fout ? 1 : 0);
})().catch(e => { console.log('FOUT ' + e.stack); process.exit(1); });
