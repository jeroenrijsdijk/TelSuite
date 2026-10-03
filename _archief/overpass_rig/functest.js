/* v2.49 functionele test — draait de echte blokken uit parkeertelling.html in
   een nagebouwde omgeving: eigen IndexedDB, eigen Overpass. Telt verzoeken.   */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('parkeertelling.html', 'utf8');

function knip(start, eind, incl) {
  const i = html.indexOf(start);
  if (i < 0) throw new Error('niet gevonden: ' + start.slice(0, 40));
  const j = html.indexOf(eind, i);
  if (j < 0) throw new Error('eind niet gevonden: ' + eind.slice(0, 40));
  return html.slice(i, j + (incl ? eind.length : 0));
}

const blokOvp = knip('/* ---- Overpass-antwoord classificeren (v2.49)',
  'function ovpBackoffMs(n) { return Math.min(500 * Math.pow(2, Math.max(0, n - 1)), 8000); }', true);
const blokTegelDb = knip('var TILE_DEG_SHARED = 0.01', 'var _tileCov = {};', false);
const blokCache = knip('function cacheWaysInTiles(elements, lat, lon, radiusM) {',
  '  } catch (e) { /* cache is best-effort: nooit het tellen verstoren */ }\n}', true);
const blokLees = knip('/* ---- Tegel-cache LEZEN (v2.49)', '  });\n}', true);
const blokFetch = knip('/* Fetch road geometries from Overpass, try endpoints in order + retry */',
  '\n// Verwerk een netwerk', false);
const blokPas = knip('// Verwerk een netwerk', '\n/* Kies de beste OSM-richting', false);
const blokVers = knip('var OSM_MAX_LAG_DAGEN = 7;', '\nvar OVERPASS_ENDPOINTS', false);

// ---- nagebouwde IndexedDB (alleen wat de code gebruikt) --------------------
function maakIDB() {
  const tabel = {};
  const db = {
    objectStoreNames: { contains: () => true },
    transaction() {
      return {
        objectStore() {
          return {
            get(k) {
              const r = { result: tabel[k] };
              setImmediate(() => r.onsuccess && r.onsuccess());
              return r;
            },
            put(rec) { tabel[rec.key] = rec; return {}; }
          };
        }
      };
    }
  };
  return {
    tabel,
    indexedDB: {
      open() {
        const q = {};
        setImmediate(() => q.onsuccess && q.onsuccess({ target: { result: db } }));
        return q;
      }
    }
  };
}

// ---- omgeving -------------------------------------------------------------
function maakCtx(overpass) {
  const idb = maakIDB();
  const log = { fetches: [], badges: [], opgeslagen: [] };
  const ctx = {
    console, Promise, Date, Math, JSON, Error, setTimeout, clearTimeout, setImmediate,
    isNaN, parseInt, parseFloat, String, Object, Array, encodeURIComponent, RegExp,
    indexedDB: idb.indexedDB,
    _tabel: idb.tabel,
    _log: log,
    AbortController: function () { this.signal = {}; this.abort = function () {}; },
    localStorage: { setItem(k) { log.opgeslagen.push(k); }, getItem() { return null; } },
    LS_KEY: 'test',
    sessionActive: true,   // v2.76: fetchen gebeurt tijdens een sessie; pasNetwerkToe kijkt ernaar
    HIGHWAY_RE: 'residential|service',
    ROAD_FETCH_RADIUS: 300,
    SNAP_SEGS_RADIUS: 480,
    snap: { status: 'none', cacheLat: null, cacheLon: null, segs: [], networkElements: [], fetchTimer: null },
    setSnapBadge() { log.badges.push(ctx.snap.status); },
    drawMiniMap() {},
    elementsNear() { return ctx.snap.networkElements; },
    buildSegments(els) { return els.map(e => ({ wayId: e.id })); },
    fetch(url) {
      log.fetches.push(url);
      return overpass(url, log.fetches.length);
    }
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  vm.runInContext([blokVers, blokOvp, blokTegelDb, 'var _tileCov = {}; var _TILE_N = 8;',
    blokCache, blokLees,
    "var OVERPASS_ENDPOINTS = ['https://a/api/interpreter','https://b/api/interpreter'];",
    blokFetch, blokPas].join('\n'), ctx);
  return ctx;
}

const nu = new Date().toISOString();
const antwoordOk = () => Promise.resolve({
  ok: true, json: () => Promise.resolve({
    osm3s: { timestamp_osm_base: nu },
    elements: [{ type: 'way', id: 1, nodes: [7, 8], geometry: [{ lat: 51.85, lon: 4.33 }, { lat: 51.851, lon: 4.331 }], tags: { highway: 'residential', name: 'Teststraat' } }]
  })
});
const antwoordLeeg = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: nu }, elements: [] }) });
const antwoordLimietBody = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: nu }, remark: 'runtime error: Query run out of memory ... rate_limited. Please check /api/status' }) });
const antwoord429 = () => Promise.resolve({ ok: false, status: 429, json: () => Promise.resolve({}) });
const antwoordOud = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: '2020-01-01T00:00:00Z' }, elements: [{ type: 'way', id: 2, geometry: [{ lat: 51.85, lon: 4.33 }, { lat: 51.86, lon: 4.34 }], tags: {} }] }) });

// ---------------------------------------------------------------- testkader
let ok = 0, fout = 0;
function eis(naam, voorwaarde, extra) {
  if (voorwaarde) { ok++; console.log('  OK   ' + naam); }
  else { fout++; console.log('  FOUT ' + naam + (extra !== undefined ? '  -> ' + JSON.stringify(extra) : '')); }
}
const wacht = ms => new Promise(r => setTimeout(r, ms));

(async function () {
  console.log('== ovpKeur: classificatie ==');
  {
    const c = maakCtx(antwoordOk);
    const K = q => vm.runInContext(q, c);
    eis('normaal antwoord -> ok', K(`ovpKeur({osm3s:{timestamp_osm_base:'${nu}'},elements:[1]})`) === 'ok');
    eis('lege elements -> leeg', K(`ovpKeur({osm3s:{timestamp_osm_base:'${nu}'},elements:[]})`) === 'leeg');
    eis('rate-limit in body (200) -> limiet',
      K(`ovpKeur({osm3s:{timestamp_osm_base:'${nu}'},remark:'rate_limited. Please check /api/status'})`) === 'limiet');
    eis('runtime error in body -> fout',
      K(`ovpKeur({osm3s:{timestamp_osm_base:'${nu}'},remark:'runtime error: Query timed out'})`) === 'fout');
    eis('verouderde mirror -> oud', K(`ovpKeur({osm3s:{timestamp_osm_base:'2020-01-01T00:00:00Z'},elements:[1]})`) === 'oud');
    eis('null -> fout', K('ovpKeur(null)') === 'fout');
    eis('HTTP 429 -> limiet', K('ovpStatusUitHttp(429)') === 'limiet');
    eis('HTTP 504 -> limiet', K('ovpStatusUitHttp(504)') === 'limiet');
    eis('HTTP 500 -> fout', K('ovpStatusUitHttp(500)') === 'fout');
    eis('backoff 1..6 = 500,1k,2k,4k,8k,8k',
      JSON.stringify([1, 2, 3, 4, 5, 6].map(n => K('ovpBackoffMs(' + n + ')'))) === '[500,1000,2000,4000,8000,8000]',
      [1, 2, 3, 4, 5, 6].map(n => K('ovpBackoffMs(' + n + ')')));
  }

  console.log('\n== leesTegels: alles-of-niets, verval, schema, ontdubbelen ==');
  {
    const c = maakCtx(antwoordOk);
    const nuMs = Date.now();
    const w = id => ({ id, type: 'way', nodes: [], geometry: [{ lat: 51.85, lon: 4.33 }], tags: { highway: 'residential', name: 'X' } });
    // cirkel r=300 rond 51.855/4.335 raakt de tegels t_5185_433 .. t_5185_433(+1)
    const keys = vm.runInContext(`(function(){var lat=51.855,lon=4.335,r=300;
      var mLat=111320,mLon=111320*Math.cos(lat*Math.PI/180);
      var dLat=r/mLat,dLon=r/mLon,out=[];
      for(var ty=Math.floor((lat-dLat)/TILE_DEG_SHARED);ty<=Math.floor((lat+dLat)/TILE_DEG_SHARED);ty++)
        for(var tx=Math.floor((lon-dLon)/TILE_DEG_SHARED);tx<=Math.floor((lon+dLon)/TILE_DEG_SHARED);tx++)
          out.push('t_'+ty+'_'+tx);
      return out;})()`, c);
    // alle tegels vers + schema 2, met een way die in twee tegels staat
    keys.forEach(k => { c._tabel[k] = { key: k, ts: nuMs, v: 2, ways: [w(1), w(2)] }; });
    let r = await vm.runInContext('leesTegels(51.855,4.335,300)', c);
    eis('volledige dekking -> lijst', Array.isArray(r), r);
    eis('ways ontdubbeld over tegels', r && r.length === 2, r && r.length);

    delete c._tabel[keys[0]];
    r = await vm.runInContext('leesTegels(51.855,4.335,300)', c);
    eis('één tegel ontbreekt -> null (geen deelresultaat)', r === null, r);

    keys.forEach(k => { c._tabel[k] = { key: k, ts: nuMs, v: 2, ways: [w(1)] }; });
    c._tabel[keys[0]].ts = nuMs - 20 * 24 * 3600 * 1000;
    r = await vm.runInContext('leesTegels(51.855,4.335,300)', c);
    eis('tegel ouder dan 14 dagen -> null', r === null, r);

    keys.forEach(k => { c._tabel[k] = { key: k, ts: nuMs, v: 2, ways: [w(1)] }; });
    delete c._tabel[keys[0]].v;              // tegel van vóór v2.49
    r = await vm.runInContext('leesTegels(51.855,4.335,300)', c);
    eis('tegel zonder schemaversie -> null (geneest zichzelf)', r === null, r);

    keys.forEach(k => { c._tabel[k] = { key: k, ts: nuMs, v: 2, ways: [] }; });
    r = await vm.runInContext('leesTegels(51.855,4.335,300)', c);
    eis('gedekt maar wegenloos -> lege lijst (geen null)', Array.isArray(r) && r.length === 0, r);
  }

  console.log('\n== tegelrecord draagt naam + schema ==');
  {
    const c = maakCtx(antwoordOk);
    // 8x8-raster vullen met één grote fetch over een kleine tegelgrootte is niet
    // haalbaar; we controleren het record dat cacheWaysInTiles zou bouwen.
    vm.runInContext(`_tileCov['t_1_1']={cells:{},n:64,ways:{}};`, c);
    vm.runInContext(`cacheWaysInTiles([{type:'way',id:9,nodes:[1,2],geometry:[{lat:0.015,lon:0.015},{lat:0.016,lon:0.016}],tags:{highway:'service',name:'Kade'}}],0.015,0.015,300)`, c);
    await wacht(30);
    const recs = Object.values(c._tabel);
    const metNaam = recs.filter(r => (r.ways || []).some(w => w.tags && w.tags.name === 'Kade'));
    eis('weggeschreven tegel bevat straatnaam', metNaam.length > 0, recs.map(r => r.key));
    eis('weggeschreven tegel draagt v=2', recs.every(r => r.v === 2), recs.map(r => r.v));
  }

  console.log('\n== fetchRoads: gebied zonder wegen (de storm van vóór v2.49) ==');
  {
    const c = maakCtx(antwoordLeeg);
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(400);
    eis('leeg gebied kost precies 1 verzoek (was tot 10)', c._log.fetches.length === 1, c._log.fetches.length);
    eis('cacheLat gezet -> afstandspoort zwijgt', c.snap.cacheLat === 51.9, c.snap.cacheLat);
    // tweede aanvraag vanaf dezelfde positie mag niet opnieuw vuren zolang de
    // afstandspoort niet is overschreden; die poort zit buiten dit blok, dus we
    // testen hier alleen dat een herhaalde startRoadFetch niet stapelt.
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(200);
    eis('herhaalde aanvraag zonder cache-hit: hoogstens 2 verzoeken totaal', c._log.fetches.length <= 2, c._log.fetches.length);
  }

  console.log('\n== fetchRoads: rate-limit ==');
  {
    const c = maakCtx(antwoord429);
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(600);
    eis('HTTP 429 -> 1 verzoek, geen mirror-hop', c._log.fetches.length === 1, c._log.fetches);
    eis('afkoeling van 30s gezet', vm.runInContext('_roadFetchCooldownTot - Date.now() > 25000', c));
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(200);
    eis('nieuwe aanvraag tijdens afkoeling wordt geweigerd', c._log.fetches.length === 1, c._log.fetches.length);
  }
  {
    const c = maakCtx(antwoordLimietBody);
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(600);
    eis('rate-limit ín een 200-body -> 1 verzoek (was: als "geen wegen" de storm in)',
      c._log.fetches.length === 1, c._log.fetches.length);
  }

  console.log('\n== fetchRoads: verouderde mirrors ==');
  {
    const c = maakCtx(antwoordOud);
    vm.runInContext('startRoadFetch(51.9,4.4)', c);
    await wacht(800);
    eis('beide mirrors verouderd -> 2 verzoeken, dan stoppen', c._log.fetches.length === 2, c._log.fetches.length);
    eis('lange afkoeling (5 min)', vm.runInContext('_roadFetchCooldownTot - Date.now() > 250000', c));
  }

  console.log('\n== fetchRoads: cache-hit kost nul verzoeken ==');
  {
    const c = maakCtx(antwoordOk);
    const nuMs = Date.now();
    const keys = vm.runInContext(`(function(){var lat=51.855,lon=4.335,r=300;
      var mLat=111320,mLon=111320*Math.cos(lat*Math.PI/180);
      var dLat=r/mLat,dLon=r/mLon,out=[];
      for(var ty=Math.floor((lat-dLat)/TILE_DEG_SHARED);ty<=Math.floor((lat+dLat)/TILE_DEG_SHARED);ty++)
        for(var tx=Math.floor((lon-dLon)/TILE_DEG_SHARED);tx<=Math.floor((lon+dLon)/TILE_DEG_SHARED);tx++)
          out.push('t_'+ty+'_'+tx);
      return out;})()`, c);
    keys.forEach(k => {
      c._tabel[k] = { key: k, ts: nuMs, v: 2, ways: [{ id: 5, type: 'way', nodes: [], geometry: [{ lat: 51.855, lon: 4.335 }], tags: { highway: 'residential', name: 'Cachestraat' } }] };
    });
    vm.runInContext('startRoadFetch(51.855,4.335)', c);
    await wacht(300);
    eis('cache-hit -> 0 Overpass-verzoeken', c._log.fetches.length === 0, c._log.fetches.length);
    eis('netwerk toch gevuld', c.snap.networkElements.length === 1, c.snap.networkElements.length);
    eis('straatnaam overleeft de cache',
      c.snap.networkElements[0].tags.name === 'Cachestraat', c.snap.networkElements[0].tags);
    eis('status ok', c.snap.status === 'ok', c.snap.status);
  }

  console.log('\n== fetchRoads: normale gang blijft werken ==');
  {
    const c = maakCtx(antwoordOk);
    vm.runInContext('startRoadFetch(51.855,4.335)', c);
    await wacht(300);
    eis('1 verzoek', c._log.fetches.length === 1, c._log.fetches.length);
    eis('netwerk cumulatief gevuld', c.snap.networkElements.length === 1);
    eis('teller teruggezet na succes', vm.runInContext('_roadFetchFailStreak===0 && _roadFetchInFlight===false', c));
  }

  console.log('\n== pasNetwerkToe: wegennet alleen wegschrijven tijdens een sessie (v2.76) ==');
  {
    const c = maakCtx(antwoordOk);
    vm.runInContext("pasNetwerkToe([{id:7,type:'way',nodes:[],geometry:[{lat:51.85,lon:4.3}],tags:{highway:'residential'}}],51.85,4.3)", c);
    eis('tijdens de sessie: weggeschreven naar de noodopslag', c._log.opgeslagen.indexOf('test_netwerk') >= 0, c._log.opgeslagen);
    c._log.opgeslagen.length = 0; c.sessionActive = false;
    vm.runInContext("pasNetwerkToe([{id:8,type:'way',nodes:[],geometry:[{lat:51.85,lon:4.3}],tags:{highway:'residential'}}],51.85,4.3)", c);
    eis('na Stop: niet weggeschreven', c._log.opgeslagen.length === 0, c._log.opgeslagen);
    eis('na Stop: in het geheugen wel bijgewerkt (voor de export)', c.snap.networkElements.length === 2, c.snap.networkElements.length);
  }

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
