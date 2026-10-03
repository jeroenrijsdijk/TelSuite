/* v2.55 functionele test — verzamel-ZIP in telrapport.html.
   Draait de echte exportVerzameling/loadVerzameling in een nagebouwde omgeving:
   echte JSZip, nagemaakte Leaflet-kaart, DOM-stubs. Controleert de round-trip.

   Vereist jszip:  npm install jszip                                          */
const fs = require('fs');
const vm = require('vm');
const JSZip = require('jszip');

/* Node kent File en Blob, maar geen FileReader. JSZip ziet het File-object dan
   als blob, slaat het inlezen over en weigert het met "Can't read the data".
   In de browser bestaat FileReader gewoon; dit vult alleen het gat in Node.
   Contract zoals JSZip het gebruikt (lib/utils.js, prepareContent):
   onload(e) met e.target.result, onerror(e) met e.target.error.             */
if (typeof globalThis.FileReader === 'undefined') {
  globalThis.FileReader = class {
    readAsArrayBuffer(blob) {
      blob.arrayBuffer().then(
        r => { this.result = r; if (this.onload) this.onload({ target: this }); },
        e => { this.error = e; if (this.onerror) this.onerror({ target: this }); });
    }
  };
}

const html = fs.readFileSync('telrapport.html', 'utf8');
function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j + (inc ? b.length : 0));
}
const BLOK = knip('/* ═══ VERZAMEL-ZIP (v2.55)', '  // Onbekend type: stil overslaan (multi-select kan andere bestanden bevatten)\n}', true);

// ─────────────────────────────────────────────────────────── omgeving
function maakCtx(opts) {
  opts = opts || {};
  const log = { geladen: [], setView: null, basemap: [], toggles: [] };
  const knoppen = {};
  function knop(id, actief) {
    const cl = new Set(actief ? ['active'] : []);
    return {
      id: id,
      classList: {
        contains: c => cl.has(c),
        toggle: (c, v) => { const n = v === undefined ? !cl.has(c) : !!v; n ? cl.add(c) : cl.delete(c); return n; },
        add: c => cl.add(c), remove: c => cl.delete(c)
      },
      click: () => { log.toggles.push(id); }
    };
  }
  knoppen['capnetwerk-toggle'] = knop('capnetwerk-toggle', !!opts.capAan);
  knoppen['cluster-toggle'] = knop('cluster-toggle', true);

  const ctx = {
    console, Promise, Date, Math, JSON, Error, setTimeout, isFinite, isNaN,
    String, Object, Array, parseInt, parseFloat, URL: { createObjectURL: () => 'blob:x', revokeObjectURL(){} },
    JSZip, File,
    _log: log,
    sessions: opts.sessions || {},
    originalFile: opts.originalFile || {},
    allTelregels: opts.allTelregels || {},
    dotLayers: opts.dotLayers || {},
    dotVisible: opts.dotVisible || { fiets:true, wrak:true, brommer:true, breed:true, goed:true, fout:true, leeg:true, spec:true },
    clustersVisible: true,
    currentBasemap: opts.basemap || 'osm',
    dzText: { innerHTML: '' },
    map: {
      getCenter: () => ({ lat: opts.lat != null ? opts.lat : 51.85, lng: opts.lon != null ? opts.lon : 4.33 }),
      getZoom: () => opts.zoom != null ? opts.zoom : 15,
      setView: (c, z) => { log.setView = { c: c, z: z }; }
    },
    countCorrections: sid => (opts.correcties && opts.correcties[sid]) || 0,
    buildTelregelsCsv: sid => 'sessie_id;nr\nGECORRIGEERD_' + sid + ';1',
    buildStratenCsv: (sid, orig) => 'sessie_id;naam\nSTRATEN_' + sid + ';X|orig:' + (orig ? 'ja' : 'nee'),
    setBasemap: k => { log.basemap.push(k); ctx.currentBasemap = k; },
    toggleCapNetwerk: btn => { btn.classList.toggle('active'); log.toggles.push('cap'); },
    showHideDots: () => {},
    applySessionVisibility: () => {},
    renderSessions: () => {},
    loadStandStillCsv: () => {},
    loadZip: async (file) => { log.geladen.push(file.name); },
    document: {
      getElementById: id => knoppen[id] || null,
      querySelector: () => null,
      body: { appendChild(){}, removeChild(){} },
      createElement: () => ({ click(){}, style:{} })
    }
  };
  vm.createContext(ctx);
  vm.runInContext(BLOK, ctx);
  return ctx;
}

// ─────────────────────────────────────────────────────────── testkader
let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

async function bronZip(sid, opts) {
  opts = opts || {};
  const z = new JSZip();
  z.file(sid + '_sessie.csv', 'sessie_id;app_type\n' + sid + ';auto');
  z.file(sid + '_telregels.csv', 'sessie_id;nr\n' + sid + ';1');
  z.file(sid + '_straten.csv', 'sessie_id;naam\n' + sid + ';Voorstraat');
  if (opts.kaart !== false) z.file(sid + '_kaart.png', Buffer.from([0x89, 0x50, 0x4e, 0x47, 1, 2, 3]));
  z.file(sid + '.gpx', Buffer.from([0x3c, 0x67, 0x70, 0x78, 0xff, 0xfe, 0x00]));
  const buf = await z.generateAsync({ type: 'nodebuffer' });
  const f = new File([buf], sid + '_car.zip');
  return f;
}

(async function () {
  const sidA = '20260514_100500_qah', sidB = '20260514_140200_bvk';

  console.log('== exportVerzameling: inhoud en volgorde ==');
  const ctx = maakCtx({
    sessions: { [sidA]: { visible:true, appType:'auto' }, [sidB]: { visible:false, appType:'fiets' } },
    originalFile: { [sidA]: await bronZip(sidA), [sidB]: await bronZip(sidB) },
    allTelregels: { [sidA]: [] },
    correcties: { [sidA]: 3 },
    lat: 51.9, lon: 4.4, zoom: 17, basemap: 'positron', capAan: true
  });
  // onderschep de download zodat we de blob te pakken krijgen
  let uitBlob = null;
  ctx.URL.createObjectURL = b => { uitBlob = b; return 'blob:x'; };
  await vm.runInContext('exportVerzameling()', ctx);
  eis('er is een ZIP geproduceerd', !!uitBlob);

  const buf = Buffer.from(await uitBlob.arrayBuffer());
  const verz = await JSZip.loadAsync(buf);
  const namen = Object.keys(verz.files).filter(p => !verz.files[p].dir).sort();
  eis('bevat manifest + twee geneste ZIPs',
    JSON.stringify(namen) === JSON.stringify([sidA + '.zip', sidB + '.zip', 'verzameling.json']), namen);

  const man = JSON.parse(await verz.file('verzameling.json').async('text'));
  eis('manifest: formaat en versie', man.formaat === 'telonline-verzameling' && man.versie === 1, man.versie);
  eis('manifest: laadvolgorde bewaard',
    man.tellingen.map(t => t.sid).join(',') === sidA + ',' + sidB, man.tellingen.map(t => t.sid));
  eis('manifest: correcties geteld per telling',
    man.tellingen[0].correcties === 3 && man.tellingen[1].correcties === 0,
    man.tellingen.map(t => t.correcties));
  eis('manifest: weggelaten kaart.png benoemd',
    man.tellingen[0].weggelaten.length === 1 && /_kaart\.png$/.test(man.tellingen[0].weggelaten[0]),
    man.tellingen[0].weggelaten);

  console.log('\n== leden: kaart eruit, correcties erin, binair intact ==');
  const lidA = await JSZip.loadAsync(await verz.file(sidA + '.zip').async('nodebuffer'));
  const ledenA = Object.keys(lidA.files).filter(p => !lidA.files[p].dir).sort();
  eis('geen _kaart.png meer in het lid', !ledenA.some(n => n.endsWith('_kaart.png')), ledenA);
  eis('overige leden aanwezig', ledenA.length === 4, ledenA);
  eis('telregels vervangen door de gecorrigeerde versie',
    (await lidA.file(sidA + '_telregels.csv').async('text')).indexOf('GECORRIGEERD_') >= 0);
  eis('straten opnieuw geaggregeerd, mét de originele tekst als input',
    (await lidA.file(sidA + '_straten.csv').async('text')).indexOf('orig:ja') >= 0);
  const gpx = await lidA.file(sidA + '.gpx').async('nodebuffer');
  eis('binair lid byte-identiek overgenomen',
    Buffer.compare(gpx, Buffer.from([0x3c, 0x67, 0x70, 0x78, 0xff, 0xfe, 0x00])) === 0, [...gpx]);

  const lidB = await JSZip.loadAsync(await verz.file(sidB + '.zip').async('nodebuffer'));
  eis('telling zonder correcties blijft ongewijzigd',
    (await lidB.file(sidB + '_telregels.csv').async('text')).indexOf('GECORRIGEERD_') < 0);

  console.log('\n== manifest: weergavestaat ==');
  const w = man.weergave;
  eis('midden en zoom', w.midden.lat === 51.9 && w.midden.lon === 4.4 && w.zoom === 17, w);
  eis('basemap', w.basemap === 'positron', w.basemap);
  eis('zichtbaarheid per telling', w.zichtbaar[sidA] === true && w.zichtbaar[sidB] === false, w.zichtbaar);
  eis('stippen-state meegenomen', w.stippen && w.stippen.fiets === true, w.stippen);
  eis('capaciteitscontouren aan', w.capaciteitscontouren === true, w.capaciteitscontouren);

  console.log('\n== loadVerzameling: uitpakken in manifestvolgorde ==');
  const ctx2 = maakCtx({});
  const verz2 = await JSZip.loadAsync(buf);
  await vm.runInContext('loadVerzameling(__z)', Object.assign(ctx2, { __z: verz2 }));
  eis('beide leden door loadZip gestuurd', ctx2._log.geladen.length === 2, ctx2._log.geladen);
  eis('in de volgorde van het manifest',
    ctx2._log.geladen.join(',') === sidA + '.zip,' + sidB + '.zip', ctx2._log.geladen);
  eis('weergave klaargezet voor na het laden',
    vm.runInContext('_verzamelingHerstel !== null', ctx2));

  console.log('\n== pasVerzamelingWeergaveToe ==');
  const ctx3 = maakCtx({
    sessions: { [sidA]: { visible:true }, [sidB]: { visible:true } },
    basemap: 'osm'
  });
  vm.runInContext('pasVerzamelingWeergaveToe(' + JSON.stringify(w) + ')', ctx3);
  eis('kaartbeeld gezet als laatste',
    ctx3._log.setView && ctx3._log.setView.c[0] === 51.9 && ctx3._log.setView.z === 17, ctx3._log.setView);
  eis('basemap teruggezet', ctx3._log.basemap.indexOf('positron') >= 0, ctx3._log.basemap);
  eis('zichtbaarheid toegepast',
    ctx3.sessions[sidA].visible === true && ctx3.sessions[sidB].visible === false,
    [ctx3.sessions[sidA].visible, ctx3.sessions[sidB].visible]);
  eis('capaciteitscontouren aangezet (stond uit)', ctx3._log.toggles.indexOf('cap') >= 0, ctx3._log.toggles);

  console.log('\n== randgevallen ==');
  const ctx4 = maakCtx({ sessions: {}, originalFile: {} });
  let gewaarschuwd = false;
  ctx4.alert = () => { gewaarschuwd = true; };
  vm.runInContext('this.alert = alert;', ctx4);
  await vm.runInContext('exportVerzameling()', ctx4);
  eis('lege kaart: waarschuwt in plaats van een lege ZIP te maken', gewaarschuwd);

  const ctx5 = maakCtx({
    sessions: { [sidA]: { visible:true, appType:'auto' } },
    originalFile: {}            // origineel kwijt
  });
  let gewaarschuwd5 = false;
  ctx5.alert = () => { gewaarschuwd5 = true; };
  await vm.runInContext('exportVerzameling()', ctx5);
  eis('origineel kwijt: waarschuwt, produceert niets', gewaarschuwd5);

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
