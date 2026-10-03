/* v2.59 regressietest — lege telling laat telreconstructie niet meer vastlopen.

   Achtergrond: een pocket-sessie die is gestart en gestopt zonder tikken en
   zonder GPS-track (gebeurt als Overpass onbereikbaar is) leverde een bbox met
   la0=+Infinity / la1=-Infinity. coveringTiles zette met Math.max beide
   tegelgrenzen op Infinity, en omdat Infinity+1 === Infinity telde de lus nooit
   op: oneindige lus die elke ronde een object pushte.

   De test bouwt zo'n ZIP zelf op, dus hij hangt niet van een upload af.
   Vereist jszip en papaparse.                                                */
const fs = require('fs');
const vm = require('vm');
const JSZip = require('jszip');
const Papa = require('papaparse');

const html = fs.readFileSync('telreconstructie.html', 'utf8');
const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)]
  .map(m => m[1]).join('\n;\n');

function nietsProxy() {
  const f = function () { return nietsProxy(); };
  return new Proxy(f, {
    get(t, p) {
      if (p === Symbol.toPrimitive || p === 'toString') return () => '';
      if (p === 'classList') return { add(){}, remove(){}, toggle(){}, contains(){ return false; } };
      if (p === 'style') return {};
      if (p === 'length') return 0;
      if (p === 'then' || p === Symbol.iterator) return undefined;
      return nietsProxy();
    },
    set() { return true; }, apply() { return nietsProxy(); }, construct() { return nietsProxy(); }
  });
}

function maakCtx(log) {
  const ctx = {
    console, Promise, Date, Math, JSON, Error, setTimeout, clearTimeout, setInterval, clearInterval,
    isFinite, isNaN, parseInt, parseFloat, String, Number, Object, Array, RegExp,
    encodeURIComponent, decodeURIComponent, Map, Set, Blob: class {}, File,
    JSZip, Papa, L: nietsProxy(),
    document: { getElementById: () => nietsProxy(), querySelector: () => nietsProxy(),
                querySelectorAll: () => [], createElement: () => nietsProxy(),
                addEventListener(){}, body: nietsProxy(), documentElement: nietsProxy() },
    navigator: { userAgent: 'node' },
    location: { href: 'https://telonline.org/telreconstructie.html', search: '' },
    localStorage: { getItem(){ return null; }, setItem(){}, removeItem(){} },
    indexedDB: { open(){ const q={}; setTimeout(()=>q.onerror&&q.onerror(),0); return q; } },
    fetch: () => Promise.reject(new Error('geen net in de test')),
    alert(){}, URL: { createObjectURL(){ return 'blob:x'; }, revokeObjectURL(){} }
  };
  ctx.window = ctx; ctx.self = ctx;
  vm.createContext(ctx);
  try { vm.runInContext(scripts, ctx); } catch (e) {}
  vm.runInContext('stap = function(a,b,c,d){ __log.push({fase:a, kop:b, staat:c, detail:d||""}); };',
    Object.assign(ctx, { __log: log }));
  return ctx;
}

async function legeZip() {
  const sid = '20260903_145005_fit_pkt_s';
  const z = new JSZip();
  z.file(sid + '_sessie.csv',
    'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b\n' +
    sid + ';2026-09-03;14:48:33;14:50:05;pocket;ped;0;simpel;;\n');
  z.file(sid + '_telregels.csv',
    'sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat;conf;conf_level;gps_stab;gps_level;richting;snelheid\n');
  z.file(sid + '_snap_trace.csv',
    'sessie_id;seq;tijdstip;event;lat;lon;accuracy;anchor_before;snap_path;chosen_way;d_anchor;d_chosen;alternatives;anchor_after;tap_nr;conf;conf_level;gps_stab;gps_level\n' +
    sid + ';18;2026-09-03T12:48:43;fetch_fail;51.8902253;4.0403522;;;fid:1|ep:0|attempt:0|err:504;;;;;;;;none;0.92;green\n');
  const buf = await z.generateAsync({ type: 'nodebuffer' });
  buf.name = sid + '.zip';
  return buf;
}

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

(async function () {
  console.log('== coveringTiles kan niet meer eeuwig lussen ==');
  {
    const ctx = maakCtx([]);
    const gevallen = [
      ['lege bbox (Infinity/-Infinity)', '{la0:Infinity,la1:-Infinity,lo0:NaN,lo1:NaN}'],
      ['null', 'null'],
      ['NaN-grenzen', '{la0:NaN,la1:NaN,lo0:NaN,lo1:NaN}'],
      ['half oneindig', '{la0:51.8,la1:Infinity,lo0:4.0,lo1:4.1}']
    ];
    gevallen.forEach(function (g) {
      const t = Date.now();
      let r;
      try { r = vm.runInContext('coveringTiles(' + g[1] + ').length', ctx, { timeout: 3000 }); }
      catch (e) { r = 'EXCEPTIE: ' + e.message; }
      eis(g[0] + ' -> lege lijst, binnen 3s', r === 0, { resultaat: r, ms: Date.now() - t });
    });
    let plafond;
    try { plafond = vm.runInContext('coveringTiles({la0:40,la1:60,lo0:0,lo1:20}).length', ctx, { timeout: 3000 }); }
    catch (e) { plafond = e.message; }
    eis('absurd groot gebied -> luide fout i.p.v. geheugen opeten',
      typeof plafond === 'string' && /te groot/.test(plafond), plafond);
    const goed = vm.runInContext('coveringTiles({la0:51.89,la1:51.91,lo0:4.03,lo1:4.06}).length', ctx);
    eis('normale route -> gewoon tegels', goed > 0 && goed < 20, goed);
  }

  console.log('\n== trailBbox geeft null i.p.v. een omgekeerde rechthoek ==');
  {
    const ctx = maakCtx([]);
    vm.runInContext('S.gps = [];', ctx);
    eis('nul posities -> null', vm.runInContext('trailBbox() === null', ctx));
    vm.runInContext("S.gps = [{lat:'51.89',lon:'4.04'},{lat:'51.90',lon:'4.05'}];", ctx);
    const b = vm.runInContext('JSON.stringify(trailBbox())', ctx);
    eis('echte posities -> eindige bbox', /"wM":\d/.test(b) && !/null/.test(b), b);
  }

  console.log('\n== de lege ZIP wordt geweigerd, niet doorgerekend ==');
  {
    const log = [];
    const ctx = maakCtx(log);
    ctx.__f = await legeZip();
    const t0 = Date.now();
    vm.runInContext('laadZip(__f)', ctx);
    await new Promise(r => setTimeout(r, 800));
    const duur = Date.now() - t0;
    const laatste = log[log.length - 1] || {};
    eis('binnen 800 ms klaar (geen vastloper)', duur < 1500, duur);
    eis('eindigt op een fail-stap', laatste.staat === 'fail', laatste);
    eis('kop is begrijpelijk, niet "Fout"', laatste.kop === 'Niets te reconstrueren', laatste.kop);
    eis('melding legt de oorzaak uit', /0 tikken en geen GPS-track/.test(laatste.detail || ''), laatste.detail);
    eis('geen stack-regel in de melding voor de gebruiker',
      !/\[.*at .*\]/.test(laatste.detail || ''), laatste.detail);
    eis('geen fetch-knop aangeboden (bbox nooit gezet)',
      vm.runInContext('!S.bbox', ctx));
    eis('geen NaN-bbox in de meldingen',
      !log.some(function (l) { return /NaN|Infinity/.test(l.detail || ''); }),
      log.map(function (l) { return l.detail; }));
  }

  console.log('\n== cacheGefetchteRoute weigert een gebiedloze bbox ==');
  {
    const ctx = maakCtx([]);
    let uitkomst = null;
    vm.runInContext('cacheGefetchteRoute(null, function(){}).then(function(){__r("gelukt");},function(e){__r("afgewezen: "+e.message);})',
      Object.assign(ctx, { __r: v => { uitkomst = v; } }));
    await new Promise(r => setTimeout(r, 200));
    eis('null-bbox -> afgewezen met uitleg',
      /afgewezen: Geen bruikbaar route-gebied/.test(uitkomst || ''), uitkomst);
  }

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
