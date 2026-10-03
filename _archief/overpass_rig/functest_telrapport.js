/* v2.50 functionele test — telrapport.html: haalWayGeometrie op het gedeelde
   transport. Controleert ontdubbeling, mirror-fallback (die er op twee van de
   drie plekken helemaal niet was), rate-limit-gedrag en de faaltak.           */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 40));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 40));
  return html.slice(i, j + (inc ? b.length : 0));
}

const blokVers = knip('/* ---- Verse-data-garantie', '\nvar SNAP_OVERPASS', false);
const blokOvp = knip('/* ---- Overpass-antwoord classificeren (v2.49)',
  'function ovpBackoffMs(n) { return Math.min(500 * Math.pow(2, Math.max(0, n - 1)), 8000); }', true);
const blokTransport = knip('/* ---- overpassFetch: gedeeld transport (v2.50)', '  tryOnce();\n}', true);
const blokHelper = knip('/* Geometrie ophalen voor een lijst way-IDs', '\n  }, function (reden) { if (onFail) onFail(reden); });\n}', true);

function maakCtx(antwoorden) {
  const log = { urls: [], queries: [] };
  let n = 0;
  const ctx = {
    console, Promise, Date, Math, JSON, Error, setTimeout, clearTimeout,
    isNaN, String, Object, Array, encodeURIComponent, decodeURIComponent, RegExp,
    _log: log,
    fetch(url) {
      log.urls.push(url);
      log.queries.push(decodeURIComponent(url.split('?data=')[1] || ''));
      const a = antwoorden[Math.min(n, antwoorden.length - 1)];
      n++;
      return a();
    }
  };
  vm.createContext(ctx);
  vm.runInContext([blokVers,
    "var SNAP_OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];",
    blokOvp, blokTransport, blokHelper].join('\n'), ctx);
  return ctx;
}

const nu = new Date().toISOString();
const rOk = () => Promise.resolve({
  ok: true, json: () => Promise.resolve({
    osm3s: { timestamp_osm_base: nu },
    elements: [
      { type: 'way', id: 111, geometry: [{ lat: 51.85, lon: 4.33 }, { lat: 51.851, lon: 4.331 }] },
      { type: 'node', id: 222, lat: 51.8, lon: 4.3 }
    ]
  })
});
const rStuk = () => Promise.reject(new TypeError('network down'));
const r429 = () => Promise.resolve({ ok: false, status: 429, json: () => Promise.resolve({}) });
const rLeeg = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: nu }, elements: [] }) });

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const wacht = ms => new Promise(r => setTimeout(r, ms));

function roep(ctx, ids) {
  return new Promise(res => {
    ctx.__onOk = m => res({ ok: true, map: m });
    ctx.__onFail = r => res({ ok: false, reden: r });
    vm.runInContext('haalWayGeometrie(' + JSON.stringify(ids) + ', __onOk, __onFail)', ctx);
  });
}

(async function () {
  console.log('== haalWayGeometrie: normale gang ==');
  {
    const c = maakCtx([rOk]);
    const r = await roep(c, [111, 999]);
    eis('1 verzoek', c._log.urls.length === 1, c._log.urls.length);
    eis('geomMap op wayId', r.ok && r.map['111'] && r.map['111'].length === 2, r);
    eis('lat/lon-paren', r.ok && r.map['111'][0][0] === 51.85 && r.map['111'][0][1] === 4.33, r.ok && r.map['111'][0]);
    eis('nodes worden genegeerd', r.ok && !r.map['222'], r.ok && Object.keys(r.map));
  }

  console.log('\n== ontdubbeling van IDs ==');
  {
    const c = maakCtx([rOk]);
    await roep(c, [111, 111, 222, 111, '222']);
    const q = c._log.queries[0];
    eis('query bevat elk ID één keer', /way\(id:111,222\);/.test(q), q);
  }

  console.log('\n== lege lijst kost geen verzoek ==');
  {
    const c = maakCtx([rOk]);
    const r = await roep(c, []);
    eis('0 verzoeken', c._log.urls.length === 0, c._log.urls.length);
    eis('onOk met lege map', r.ok && Object.keys(r.map).length === 0, r);
  }

  console.log('\n== mirror-fallback (bestond op 2 van de 3 plekken niet) ==');
  {
    const c = maakCtx([rStuk, rOk]);
    const r = await roep(c, [111]);
    await wacht(50);
    eis('valt terug op de tweede mirror', c._log.urls.length === 2, c._log.urls.length);
    eis('tweede poging gaat naar private.coffee',
      (c._log.urls[1] || '').indexOf('private.coffee') > 0, c._log.urls[1]);
    eis('resultaat komt alsnog binnen', r.ok && !!r.map['111'], r);
  }

  console.log('\n== alles stuk -> onFail, geen oneindige lus ==');
  {
    const c = maakCtx([rStuk]);
    const r = await roep(c, [111]);
    eis('geeft op na endpoints x 2', c._log.urls.length === 4, c._log.urls.length);
    eis('onFail aangeroepen', r.ok === false, r);
  }

  console.log('\n== rate-limit: geen mirror-hop, wachten ==');
  {
    const c = maakCtx([r429]);
    let klaar = false;
    roep(c, [111]).then(() => { klaar = true; });
    await wacht(600);
    eis('1 verzoek, daarna stil (geen hop naar de tweede mirror)', c._log.urls.length === 1, c._log.urls.length);
    eis('nog niet opgegeven, wacht op het slot', klaar === false);
  }

  console.log('\n== leeg antwoord is geldig ==');
  {
    const c = maakCtx([rLeeg]);
    const r = await roep(c, [111]);
    eis('1 verzoek, geen retry', c._log.urls.length === 1, c._log.urls.length);
    eis('onOk met lege map', r.ok && Object.keys(r.map).length === 0, r);
  }

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
