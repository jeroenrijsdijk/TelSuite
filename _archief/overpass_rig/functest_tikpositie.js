/* v2.51 functionele test — tikPositie() en de clustergroepering.
   Controleert dat rauwe ZIP's ongemoeid blijven en dat een gereconstrueerde
   parkeertelling links en rechts uit elkaar houdt.                           */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 40));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 40));
  return html.slice(i, j + (inc ? b.length : 0));
}
const blokHelper = knip('/* Welke coördinaat tekenen we voor een pocket-tik? (v2.51)',
  '  return [parseFloat(r.lat), parseFloat(r.lon)];\n}', true);

const ctx = { console, Math, parseFloat, isNaN, Number };
vm.createContext(ctx);
vm.runInContext(blokHelper, ctx);
const pos = r => vm.runInContext('tikPositie(' + JSON.stringify(r) + ')', ctx);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const gelijk = (a, b) => JSON.stringify(a) === JSON.stringify(b);

console.log('== tikPositie: keuze tussen GPS- en wegpositie ==');
eis('rauwe pocket-rij (geen markerkolom) -> lat/lon',
  gelijk(pos({ lat: '51.85', lon: '4.33' }), [51.85, 4.33]), pos({ lat: '51.85', lon: '4.33' }));
eis('gereconstrueerde rij -> lat_marker/lon_marker',
  gelijk(pos({ lat: '51.85', lon: '4.33', lat_marker: '51.8501', lon_marker: '4.3301' }), [51.8501, 4.3301]));
eis('lege markerkolom -> terugval op lat/lon',
  gelijk(pos({ lat: '51.85', lon: '4.33', lat_marker: '', lon_marker: '' }), [51.85, 4.33]));
eis('halve markerkolom -> terugval (geen mengsel)',
  gelijk(pos({ lat: '51.85', lon: '4.33', lat_marker: '51.8501', lon_marker: '' }), [51.85, 4.33]));
eis('wandelprofiel (transect, geen marker) -> lat/lon',
  gelijk(pos({ lat: '51.9', lon: '4.4', richting: 'a' }), [51.9, 4.4]));
const nan = pos({ lat: '', lon: '' });
eis('rij zonder enige coördinaat -> NaN (lader slaat hem over)',
  Number.isNaN(nan[0]) && Number.isNaN(nan[1]), nan);

console.log('\n== clustergroepering: links en rechts blijven gescheiden ==');
// Nabootsing van de groepssleutel uit drawClusters: `${wayId|segIdx}|${zijde}`
function groepen(rijen) {
  const g = {};
  rijen.forEach(r => {
    const k = r.osm_way_id + '_' + (r.segment_index || 0) + '|' + (r.zijde || 'X');
    (g[k] = g[k] || []).push(r);
  });
  return Object.keys(g);
}
const recon = [
  { osm_way_id: '12', segment_index: 0, zijde: 'L' },
  { osm_way_id: '12', segment_index: 0, zijde: 'L' },
  { osm_way_id: '12', segment_index: 0, zijde: 'R' }
];
eis('gereconstrueerde parkeerrij -> twee groepen (L en R)', groepen(recon).length === 2, groepen(recon));
const zonder = recon.map(r => ({ osm_way_id: r.osm_way_id, segment_index: r.segment_index }));
eis('zonder zijde zouden het er één zijn (dit is wat v2.51 voorkomt)',
  groepen(zonder).length === 1, groepen(zonder));
const wandel = [{ osm_way_id: '12', segment_index: 0 }, { osm_way_id: '12', segment_index: 1 }];
eis('wandelprofiel zonder zijde: groepering blijft op segment', groepen(wandel).length === 2, groepen(wandel));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
