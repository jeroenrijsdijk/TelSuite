/* v3.17 functionele test — het bbox-filter van telrapport, ook voor verzamelingen.
   Knipt probeBbox en zijn hulpfuncties uit telrapport.html en voert ze met
   echte ZIP's (gemaakt met JSZip).

   Gecontroleerd:
     A. een tel-ZIP: bbox uit _netwerk.csv, anders uit _gps.csv, anders null;
     B. een verzameling (verzameling.json + tel-ZIP's): de bbox van al haar
        tellingen samen; tot v3.17 gaf probeBbox daar null en liet het filter
        haar altijd door;
     C. een verzameling met een telling zonder bbox, of met een kapot manifest:
        null (meenemen, net als een los bestand); een lid dat in het manifest
        staat maar ontbreekt, telt niet mee;
     D. het filter zelf: een verzameling ver buiten beeld valt weg, een die
        deels in beeld ligt niet.
   Draaien vanuit de suite-root (jszip en papaparse via NODE_PATH):
     node _archief/overpass_rig/functest_bbox.js                               */
const fs = require('fs');
const vm = require('vm');
const JSZip = require('jszip');
const Papa = require('papaparse');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j);
}
const code = [
  "const parseCSV = txt => Papa.parse(txt.trim(), { header:true, delimiter:';', skipEmptyLines:true }).data;",
  "const parseStandStillCsv = () => null;",
  "const VERZAMELING_MANIFEST = 'verzameling.json';",
  knip('// ── bbox-filter: alleen tellingen binnen het huidige kaartbeeld laden', '// Laadt de aangeleverde bestanden')
].join('\n');
const ctx = { Papa, JSZip, JSON, Math, Array, Object, String, isFinite, Infinity, console };
vm.createContext(ctx);
vm.runInContext(code + '\nthis.probeBbox = probeBbox; this.bboxesOverlap = bboxesOverlap;', ctx);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const bijna = (a, b) => Math.abs(a - b) < 1e-9;

// Een tel-ZIP als bytes. net: [[lon,lat],...] of null; gps: [[lat,lon],...] of null
async function telZip(sid, net, gps) {
  const z = new JSZip();
  z.file(sid + '_sessie.csv', 'sessie_id;app_type\n' + sid + ';pocket\n');
  if (net) z.file(sid + '_netwerk.csv', 'osm_way_id;segment_index;segment_count;highway;geometrie_wkt\n' +
    '1;0;1;residential;LINESTRING (' + net.map(p => p[0] + ' ' + p[1]).join(', ') + ')\n');
  if (gps) z.file(sid + '_gps.csv', 'sessie_id;tijdstip;lat;lon\n' + gps.map(p => sid + ';x;' + p[0] + ';' + p[1]).join('\n') + '\n');
  return z.generateAsync({ type: 'uint8array' });
}
async function verzameling(leden, manifest) {
  const z = new JSZip();
  for (const [naam, bytes] of leden) z.file(naam, bytes);
  z.file('verzameling.json', manifest !== undefined ? manifest : JSON.stringify({
    formaat: 'telonline-verzameling', versie: 1, tellingen: leden.map(([naam]) => ({ bestand: naam }))
  }));
  return z.generateAsync({ type: 'uint8array' });
}
// JSZip leest in Node geen Blob/File; de bytes met een naam erbij gedragen zich voor
// probeBbox als een bestand (hij gebruikt alleen .name en JSZip.loadAsync).
const alsBestand = (bytes, naam) => Object.assign(bytes, { name: naam });

(async () => {
  console.log('\n== A. een tel-ZIP ==');
  const rd = await telZip('a', [[4.30, 51.85], [4.31, 51.86]], [[51.80, 4.20]]);
  let bb = await ctx.probeBbox(alsBestand(rd, 'a.zip'));
  eis('uit _netwerk.csv (niet uit _gps.csv)', bb && bijna(bb.minLat, 51.85) && bijna(bb.maxLat, 51.86) && bijna(bb.minLon, 4.30) && bijna(bb.maxLon, 4.31), bb);
  bb = await ctx.probeBbox(alsBestand(await telZip('b', null, [[51.70, 4.10], [51.71, 4.12]]), 'b.zip'));
  eis('zonder netwerk: uit _gps.csv', bb && bijna(bb.minLat, 51.70) && bijna(bb.maxLon, 4.12), bb);
  bb = await ctx.probeBbox(alsBestand(await telZip('c', null, null), 'c.zip'));
  eis('zonder netwerk en spoor: null', bb === null, bb);
  bb = await ctx.probeBbox(alsBestand(new Uint8Array([1, 2, 3]), 'kapot.zip'));
  eis('geen ZIP: null', bb === null, bb);

  console.log('\n== B. een verzameling ==');
  const dichtbij = await telZip('d1', [[4.30, 51.85], [4.301, 51.851]], null);
  const ver = await telZip('d2', [[5.10, 52.10], [5.11, 52.11]], null);
  const vz = await verzameling([['d1.zip', dichtbij], ['d2.zip', ver]]);
  bb = await ctx.probeBbox(alsBestand(vz, 'TelVerzameling_20261018.zip'));
  eis('bbox van alle tellingen samen', bb && bijna(bb.minLat, 51.85) && bijna(bb.maxLat, 52.11) &&
    bijna(bb.minLon, 4.30) && bijna(bb.maxLon, 5.11), bb);

  console.log('\n== C. randgevallen ==');
  bb = await ctx.probeBbox(alsBestand(await verzameling([['d1.zip', dichtbij], ['leeg.zip', await telZip('e', null, null)]]), 'v2.zip'));
  eis('een telling zonder bbox: null (hele verzameling meenemen)', bb === null, bb);
  bb = await ctx.probeBbox(alsBestand(await verzameling([['d1.zip', dichtbij]], '{kapot'), 'v3.zip'));
  eis('kapot manifest: null', bb === null, bb);
  const metGat = await verzameling([['d1.zip', dichtbij]], JSON.stringify({ versie: 1, tellingen: [{ bestand: 'd1.zip' }, { bestand: 'weg.zip' }] }));
  bb = await ctx.probeBbox(alsBestand(metGat, 'v4.zip'));
  eis('een ontbrekend lid telt niet mee', bb && bijna(bb.maxLat, 51.851), bb);
  bb = await ctx.probeBbox(alsBestand(await verzameling([], JSON.stringify({ versie: 1, tellingen: [] })), 'v5.zip'));
  eis('lege verzameling: null', bb === null, bb);

  console.log('\n== D. het filter ==');
  const beeldVer = { minLat: 53.0, maxLat: 53.1, minLon: 6.5, maxLon: 6.6 };     // Groningen
  const beeldDeels = { minLat: 52.05, maxLat: 52.2, minLon: 5.0, maxLon: 5.2 };  // raakt alleen d2
  bb = await ctx.probeBbox(alsBestand(vz, 'TelVerzameling_20261018.zip'));
  eis('verzameling ver buiten beeld: overgeslagen', !ctx.bboxesOverlap(bb, beeldVer));
  eis('verzameling deels in beeld: geladen', ctx.bboxesOverlap(bb, beeldDeels));

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
  process.exit(fout ? 1 : 0);
})().catch(e => { console.log('FOUT ' + e.stack); process.exit(1); });
