/* v2.49 functionele test — pocket_count.html snap-fetch.
   Doel: de oneindige retry bij 'geen wegen' is weg, de cache wordt geraadpleegd,
   en de v2.17/v2.18-garanties (volgorde-guard, in-flight guard) staan nog. */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('pocket_count.html', 'utf8');

function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 40));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 40));
  return html.slice(i, j + (inc ? b.length : 0));
}

const blokVers = knip('var OSM_MAX_LAG_DAGEN = 7;', '\nvar SNAP_OVERPASS', false);
const blokOvp = knip('/* ---- Overpass-antwoord classificeren (v2.49)',
  'function ovpBackoffMs(n) { return Math.min(500 * Math.pow(2, Math.max(0, n - 1)), 8000); }', true);
const blokTegelDb = knip('var TILE_DEG_SHARED = 0.01', 'var _tileCov = {};', false);
const blokCache = knip('function cacheWaysInTiles(elements, lat, lon, radiusM) {',
  '  } catch (e) { /* cache is best-effort: nooit het tellen verstoren */ }\n}', true);
const blokLees = knip('/* ---- Tegel-cache LEZEN (v2.49)', '  });\n}', true);
const blokFetch = knip('// v2.49: een verse aanvraag begint hier',
  'function snapBackoffMs(n) {\n  return ovpBackoffMs(n);\n}', true);

function maakCtx(overpass) {
  const tabel = {};
  const db = {
    objectStoreNames: { contains: () => true },
    transaction() {
      return {
        objectStore() {
          return {
            get(k) { const r = { result: tabel[k] }; setImmediate(() => r.onsuccess && r.onsuccess()); return r; },
            put(rec) { tabel[rec.key] = rec; return {}; }
          };
        }
      };
    }
  };
  const log = { fetches: [] };
  const ctx = {
    console, Promise, Date, Math, JSON, Error, setTimeout, clearTimeout, setImmediate,
    isNaN, String, Object, Array, encodeURIComponent, RegExp,
    indexedDB: { open() { const q = {}; setImmediate(() => q.onsuccess && q.onsuccess({ target: { result: db } })); return q; } },
    _tabel: tabel, _log: log,
    HIGHWAY_RE: 'residential|service',
    SNAP_ROAD_FETCH_RADIUS: 250,
    snap: {
      segs: [], cacheLat: null, cacheLon: null, elements: {}, ready: false,
      pendingQueue: [], nodeToWays: {}, adjacency: {}, anchorWayId: null, anchorSegIdx: 0,
      fetchSeq: 0, fetchApplied: 0, fetchInFlight: false, fetchCooldownUntil: 0,
      fetchFailStreak: 0, trace: [], traceSeq: 0,
      confScore: null, confLevel: 'none', gpsStabScore: null, gpsStabLevel: 'none'
    },
    snapRegisterWay() {},
    snapElementsNear() { return Object.keys(ctx.snap.elements).map(k => ctx.snap.elements[k]); },
    snapBuildSegs(els) { return els.map(e => ({ wayId: 1 })); },
    snapNearestAny() { return null; },
    traceWrite() {},
    fetch(url) { log.fetches.push(url); return overpass(url, log.fetches.length); }
  };
  vm.createContext(ctx);
  vm.runInContext([blokVers, blokOvp, blokTegelDb, 'var _tileCov={};var _TILE_N=8;',
    blokCache, blokLees,
    "var SNAP_OVERPASS=['https://a/api/interpreter','https://b/api/interpreter'];",
    // traceFetchEvent is een dunne logger in de echte app; hier een stub met
    // dezelfde handtekening zodat de event-namen zichtbaar blijven.
    'function traceFetchEvent(e,la,lo,d){ snap.trace.push({event:e, snap_path:d}); }',
    blokFetch].join('\n'), ctx);
  return ctx;
}

const nu = new Date().toISOString();
const rOk = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: nu }, elements: [{ type: 'way', id: 1, nodes: [1, 2], geometry: [{ lat: 51.85, lon: 4.33 }, { lat: 51.851, lon: 4.331 }], tags: { highway: 'residential', name: 'Teststraat' } }] }) });
const rLeeg = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ osm3s: { timestamp_osm_base: nu }, elements: [] }) });
const r429 = () => Promise.resolve({ ok: false, status: 429, json: () => Promise.resolve({}) });

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const wacht = ms => new Promise(r => setTimeout(r, ms));

(async function () {
  console.log('== pocket: gebied zonder wegen ==');
  {
    const c = maakCtx(rLeeg);
    vm.runInContext('snapStartFetch(51.9,4.4)', c);
    await wacht(2500);   // ruim langer dan de oude backoff-cyclus
    eis('leeg gebied kost 1 verzoek (was: eindeloos doorvragen)', c._log.fetches.length === 1, c._log.fetches.length);
    eis('cacheLat gezet, dus geen fataal-tak meer', c.snap.cacheLat === 51.9, c.snap.cacheLat);
    eis('snap.ready gezet (tik krijgt eerlijk geen kandidaat i.p.v. wachtrij)', c.snap.ready === true);
    eis('in-flight guard vrijgegeven', c.snap.fetchInFlight === false);
    eis('trace meldt fetch_leeg', c.snap.trace.some(t => t.event === 'fetch_leeg'), c.snap.trace.map(t => t.event));
  }

  console.log('\n== pocket: cache-hit ==');
  {
    const c = maakCtx(rOk);
    const keys = vm.runInContext(`(function(){var lat=51.855,lon=4.335,r=250;
      var mLat=111320,mLon=111320*Math.cos(lat*Math.PI/180);
      var dLat=r/mLat,dLon=r/mLon,out=[];
      for(var ty=Math.floor((lat-dLat)/TILE_DEG_SHARED);ty<=Math.floor((lat+dLat)/TILE_DEG_SHARED);ty++)
        for(var tx=Math.floor((lon-dLon)/TILE_DEG_SHARED);tx<=Math.floor((lon+dLon)/TILE_DEG_SHARED);tx++)
          out.push('t_'+ty+'_'+tx);
      return out;})()`, c);
    keys.forEach(k => {
      c._tabel[k] = { key: k, ts: Date.now(), v: 2, ways: [{ id: 77, type: 'way', nodes: [3, 4], geometry: [{ lat: 51.855, lon: 4.335 }, { lat: 51.856, lon: 4.336 }], tags: { highway: 'residential', name: 'Cachestraat' } }] };
    });
    vm.runInContext('snapStartFetch(51.855,4.335)', c);
    await wacht(300);
    eis('cache-hit -> 0 Overpass-verzoeken', c._log.fetches.length === 0, c._log.fetches.length);
    eis('snap.elements gevuld uit cache', Object.keys(c.snap.elements).length === 1, c.snap.elements);
    eis('osmName overleeft de cache', c.snap.elements['77'] && c.snap.elements['77'].osmName === 'Cachestraat', c.snap.elements['77']);
    eis('trace meldt bron:tegel', c.snap.trace.some(t => (t.snap_path || '').indexOf('bron:tegel') === 0), c.snap.trace.map(t => t.snap_path));
    eis('snap.ready gezet', c.snap.ready === true);
  }

  console.log('\n== pocket: rate-limit ==');
  {
    const c = maakCtx(r429);
    vm.runInContext('snapStartFetch(51.9,4.4)', c);
    await wacht(800);
    eis('HTTP 429 -> 1 verzoek, geen mirror-hop', c._log.fetches.length === 1, c._log.fetches.length);
    eis('cooldown van 30s gezet', c.snap.fetchCooldownUntil - Date.now() > 25000);
    vm.runInContext('snapStartFetch(51.9,4.4)', c);
    await wacht(200);
    eis('aanvraag tijdens cooldown geweigerd', c._log.fetches.length === 1, c._log.fetches.length);
  }

  console.log('\n== pocket: normale gang + volgorde-guard ==');
  {
    const c = maakCtx(rOk);
    vm.runInContext('snapStartFetch(51.855,4.335)', c);
    await wacht(300);
    eis('1 verzoek', c._log.fetches.length === 1, c._log.fetches.length);
    eis('netwerk toegepast', Object.keys(c.snap.elements).length === 1);
    eis('fetchApplied bijgewerkt', c.snap.fetchApplied === 1, c.snap.fetchApplied);
    // een oudere respons mag niet meer landen
    c.snap.fetchApplied = 99;
    vm.runInContext('snapVerwerkNetwerk([],51.0,4.0,5,"fetch")', c);
    eis('volgorde-guard blokkeert verouderde respons', c.snap.cacheLat === 51.855, c.snap.cacheLat);
    eis('guard wel vrijgegeven', c.snap.fetchInFlight === false);
  }

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
