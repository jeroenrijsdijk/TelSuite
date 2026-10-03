/* v2.61 test — clusterbol als taartdiagram.
   Draait de echte clusterBolHtml / clusterPunten / conicAchtergrond headless.  */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('telrapport.html', 'utf8');
function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j + (inc ? b.length : 0));
}
const BLOK = knip('/* ── Clusterbol (v2.61)',
  "  var gat = Math.max(14, Math.round(size * 0.52));", false)
  + knip("  var gat = Math.max(14, Math.round(size * 0.52));",
         "+ cijfer + '\">' + total + '</div></div>';\n}", true);
// APP_CONFIG uit het bestand, zodat de test de echte kleuren en volgordes gebruikt
const CFG = knip('const APP_CONFIG = {', '\n};', true);

const ctx = { console, Math, Object, Array, String, Number };
vm.createContext(ctx);
vm.runInContext(CFG + '\n' + BLOK, ctx);

const bol = (counts, total, appType, opts) =>
  vm.runInContext('clusterBolHtml(' + JSON.stringify(counts) + ',' + total
    + ', APP_CONFIG["' + appType + '"], ' + JSON.stringify(opts || {}) + ')', ctx);
const punten = (counts, appType) =>
  vm.runInContext('clusterPunten(' + JSON.stringify(counts) + ', APP_CONFIG["' + appType + '"])', ctx);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

console.log('== vaste puntvolgorde ==');
{
  // 'leeg' heeft het grootste aantal maar staat in APP_CONFIG.auto achter goed/fout
  const p = punten({ leeg: 30, goed: 5, fout: 2 }, 'auto');
  eis('volgt APP_CONFIG.types, niet het aantal',
    p.map(x => x.type).join(',') === 'goed,fout,leeg', p.map(x => x.type));
  eis('kleuren komen uit de config',
    p[0].kleur === '#22c55e' && p[2].kleur === '#94a3b8', p.map(x => x.kleur));
  eis('types met nul komen er niet in', punten({ goed: 3, spec: 0 }, 'auto').length === 1);
  const onb = punten({ goed: 1, gekkigheid: 2 }, 'auto');
  eis('onbekend type komt achteraan met een neutrale kleur',
    onb[onb.length - 1].type === 'gekkigheid' && onb[onb.length - 1].kleur === '#777777', onb);
}

console.log('== taart vs vlakke bol ==');
{
  const groot = bol({ goed: 6, leeg: 4 }, 10, 'auto', { size: 40, fontSize: 13 });
  eis('grote bol met twee typen -> conic-gradient', /conic-gradient\(/.test(groot));
  eis('en een donutgat met het totaal',
    /border-radius:50%;background:#1a1c1e;/.test(groot) && groot.indexOf('>10</div>') > 0, groot.slice(-160));

  const klein = bol({ goed: 6, leeg: 4 }, 10, 'auto', { size: 20, fontSize: 13 });
  eis('kleine bol blijft vlak (punten zouden mush zijn)', !/conic-gradient/.test(klein));
  eis('en houdt het cijfer er gewoon op', /<span style=.*>10<\/span>/.test(klein), klein.slice(-120));

  const een = bol({ goed: 9 }, 9, 'auto', { size: 40, fontSize: 13 });
  eis('één type -> geen taart maar de eigen kleur',
    !/conic-gradient/.test(een) && /background:#22c55e/.test(een), een.slice(0, 120));
}

console.log('== de punten kloppen ==');
{
  const h = bol({ goed: 1, fout: 1, leeg: 2 }, 4, 'auto', { size: 40, fontSize: 13 });
  const m = h.match(/conic-gradient\(([^)]*)\)/);
  eis('drie punten', m && m[1].split(',').length === 3, m && m[1]);
  eis('eerste punt begint op 0%', /#22c55e 0\.000% 25\.000%/.test(m[1]), m[1]);
  eis('tweede punt sluit aan', /#eab308 25\.000% 50\.000%/.test(m[1]), m[1]);
  const eind = a => parseFloat(a.split(',').pop().trim().split(/\s+/).pop());
  eis('laatste punt sluit exact op 100% (geen haarlijn)', eind(m[1]) === 100, m[1]);
}
{
  // afronding: 1/3 elk
  const h = bol({ goed: 1, fout: 1, leeg: 1 }, 3, 'auto', { size: 40, fontSize: 13 });
  const m = h.match(/conic-gradient\(([^)]*)\)/);
  const eind3 = parseFloat(m[1].split(',').pop().trim().split(/\s+/).pop());
  eis('derden: laatste punt eindigt op precies 100, niet op 99.999', eind3 === 100, m[1]);
}

console.log('== bgStyle wint (gecombineerd cluster van twee sessies) ==');
{
  const h = bol({ goed: 3, leeg: 3 }, 6, 'auto',
    { size: 40, fontSize: 13, bgStyle: 'background:linear-gradient(135deg,#aaa 50%,#bbb 50%)' });
  eis('geen taart', !/conic-gradient/.test(h));
  eis('wel de meegegeven tweekleur', /linear-gradient\(135deg/.test(h));
  eis('en dan ook geen donutgat', !/background:#1a1c1e/.test(h), h.slice(-140));
}

console.log('== werkt voor alle telsoorten ==');
['fiets', 'auto', 'pocket', 'transect'].forEach(t => {
  const types = vm.runInContext('APP_CONFIG["' + t + '"].types', ctx);
  const counts = {}; types.slice(0, 3).forEach((x, i) => counts[x] = i + 1);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const h = bol(counts, total, t, { size: 44, fontSize: 11 });
  eis(t + ': taart met ' + Object.keys(counts).length + ' punten',
    /conic-gradient/.test(h) && h.indexOf('>' + total + '</div>') > 0);
});

console.log('== randgevallen ==');
eis('leeg counts-object klapt niet', typeof bol({}, 0, 'auto', { size: 40, fontSize: 13 }) === 'string');
eis('onbekend appType valt terug op neutraal',
  /background:#777777/.test(vm.runInContext('clusterBolHtml({x:1},1,undefined,{size:40,fontSize:13})', ctx)));
eis('donutgat wordt nooit kleiner dan 14px',
  /width:14px;height:14px;border-radius:50%;background:#1a1c1e/.test(
    bol({ goed: 1, leeg: 1 }, 2, 'auto', { size: 26, fontSize: 13 })));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
