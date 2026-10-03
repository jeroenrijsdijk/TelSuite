/* v2.61 test — shift-klik op een clusterbol isoleert die telling.
   Draait de echte soloSessies / clusterShiftSolo / clusterTip headless.       */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('telrapport.html', 'utf8');
function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j + (inc ? b.length : 0));
}
const BLOK = knip('/* Solo-modus: alleen deze telling(en) zichtbaar.',
  '  if (e && e.originalEvent && e.originalEvent.shiftKey) L.DomEvent.stop(e.originalEvent);\n}', true);

function maakCtx(sids, zichtbaar) {
  const log = { applied: [], recolor: 0, stats: 0, groups: 0, emphasis: 0, render: 0, stopped: 0 };
  const sessions = {};
  sids.forEach((k, i) => { sessions[k] = { visible: zichtbaar ? zichtbaar[i] : true }; });
  const ctx = {
    console, Object, Array, String,
    sessions, _log: log,
    applySessionVisibility: k => log.applied.push(k),
    recolorAll: () => log.recolor++,
    updateStats: () => log.stats++,
    syncGroupHeads: () => log.groups++,
    setSessionEmphasis: () => log.emphasis++,
    renderSessions: () => log.render++,
    L: { DomEvent: { stop: () => log.stopped++ } }
  };
  vm.createContext(ctx);
  vm.runInContext(BLOK, ctx);
  return ctx;
}

const zichtbaar = ctx => Object.keys(ctx.sessions).filter(k => ctx.sessions[k].visible);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

const A = 'ses_a', B = 'ses_b', C = 'ses_c';

console.log('== soloSessies ==');
{
  const c = maakCtx([A, B, C]);
  vm.runInContext('soloSessies(["' + B + '"])', c);
  eis('alleen de gekozen telling blijft aan', zichtbaar(c).join() === B, zichtbaar(c));
  eis('alle sessies zijn bijgewerkt op de kaart', c._log.applied.length === 3, c._log.applied);
  eis('kleuren, statistiek en lijst lopen mee',
    c._log.recolor === 1 && c._log.stats === 1 && c._log.render === 1);
}
{
  const c = maakCtx([A, B, C]);
  vm.runInContext('soloSessies(["' + B + '"])', c);
  vm.runInContext('soloSessies(["' + B + '"])', c);
  eis('nogmaals solo op dezelfde selectie zet alles weer aan',
    zichtbaar(c).length === 3, zichtbaar(c));
}
{
  const c = maakCtx([A, B, C]);
  vm.runInContext('soloSessies(["' + A + '","' + C + '"])', c);
  eis('een groep isoleren kan ook (gecombineerd cluster)',
    zichtbaar(c).sort().join() === [A, C].join(), zichtbaar(c));
  vm.runInContext('soloSessies(["' + A + '","' + C + '"])', c);
  eis('en die groep schakelt ook weer terug', zichtbaar(c).length === 3, zichtbaar(c));
}
{
  const c = maakCtx([A, B, C]);
  vm.runInContext('soloSessies(["' + B + '"])', c);
  vm.runInContext('soloSessies(["' + C + '"])', c);
  eis('solo op een ándere telling wisselt, niet terugzetten',
    zichtbaar(c).join() === C, zichtbaar(c));
}
{
  const c = maakCtx([A, B]);
  vm.runInContext('soloSessies(["bestaat_niet"])', c);
  eis('onbekende sid doet niets', zichtbaar(c).length === 2 && c._log.applied.length === 0);
  vm.runInContext('soloSessies([])', c);
  eis('lege lijst doet niets', zichtbaar(c).length === 2);
}

console.log('== clusterShiftSolo ==');
{
  const c = maakCtx([A, B, C]);
  const zonder = vm.runInContext('clusterShiftSolo({originalEvent:{shiftKey:false}}, ["' + A + '"])', c);
  eis('zonder shift: niet afgehandeld, klik gaat door naar het detailpaneel', zonder === false);
  eis('en niets geschakeld', zichtbaar(c).length === 3);

  const met = vm.runInContext('clusterShiftSolo({originalEvent:{shiftKey:true}}, ["' + A + '"])', c);
  eis('met shift: afgehandeld', met === true);
  eis('en geïsoleerd', zichtbaar(c).join() === A, zichtbaar(c));
  eis('box-zoom van Leaflet tegengehouden', c._log.stopped === 1, c._log.stopped);
}
{
  const c = maakCtx([A, B]);
  eis('event zonder originalEvent klapt niet',
    vm.runInContext('clusterShiftSolo({}, ["' + A + '"])', c) === false);
  eis('helemaal geen event ook niet',
    vm.runInContext('clusterShiftSolo(null, ["' + A + '"])', c) === false);
}

console.log('== box-zoom-blokkade op mousedown ==');
{
  const c = maakCtx([A, B]);
  vm.runInContext('shiftBoxZoomBlokkeren({originalEvent:{shiftKey:true}})', c);
  eis('shift+mousedown wordt gestopt (anders start het zoomkader al)', c._log.stopped === 1);
  vm.runInContext('shiftBoxZoomBlokkeren({originalEvent:{shiftKey:false}})', c);
  eis('gewone mousedown blijft ongemoeid (slepen blijft werken)', c._log.stopped === 1);
}

console.log('== hint in de tooltip ==');
{
  const een = maakCtx([A]);
  eis('bij één geladen telling geen hint',
    vm.runInContext('clusterTip("goed: 4")', een) === 'goed: 4');
  const twee = maakCtx([A, B]);
  eis('vanaf twee tellingen wél',
    /shift-klik: alleen deze telling/.test(vm.runInContext('clusterTip("goed: 4")', twee)));
  eis('de inhoud blijft voorop staan',
    vm.runInContext('clusterTip("goed: 4")', twee).indexOf('goed: 4') === 0);
}

console.log('== bedrading in de drie clusterpaden ==');
eis('gecombineerd cluster', /clusterShiftSolo\(e, Object\.keys\(sessionCounts\)\)/.test(html));
eis('gap-pad', /clusterShiftSolo\(e, \[sid\]\)/.test(html));
eis('segment-pad', (html.match(/clusterShiftSolo\(e, \[sid\]\)/g) || []).length === 2);
eis('alle drie hebben de mousedown-blokkade',
  (html.match(/\.on\('mousedown', shiftBoxZoomBlokkeren\)/g) || []).length === 3);
eis('de sessielijst gebruikt dezelfde schakelaar', /soloSessies\(\[sid\]\);/.test(html));
eis('en heeft geen eigen kopie meer van de solo-logica',
  !/const isSolo = sessions\[sid\]\.visible/.test(html));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
