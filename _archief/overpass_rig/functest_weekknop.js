/* v2.59 test — de weekprofiel-knop staat bovenaan het detailpaneel.

   Het paneel scrollt binnen 340 px. Stond de knop onder de sessietabel, dan zakte
   hij bij veel geladen tellingen uit beeld en was er geen weg meer naar het
   weekprofiel. Deze test controleert de volgorde in de opgebouwde HTML.        */
const fs = require('fs');

const html = fs.readFileSync('telrapport.html', 'utf8');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

console.log('== opbouw van het detailpaneel ==');

// De regel die de knop plaatst
const regel = html.split('\n').find(l => l.indexOf('Toon weekprofiel') >= 0);
eis('knopregel gevonden', !!regel, regel);
eis('knop wordt vóór de tabel gezet, niet erachter',
  !!regel && /\+ html;\s*$/.test(regel.trim()) && !/html \+=/.test(regel), regel && regel.trim().slice(0, 60));
eis('knop zit in de plakkerige houder',
  !!regel && regel.indexOf('class="hm-btn-top"') >= 0);

console.log('\n== CSS ==');
const css = html.slice(0, html.indexOf('</style>'));
eis('.hm-btn-top bestaat', css.indexOf('.hm-btn-top {') >= 0);
eis('position: sticky', /\.hm-btn-top \{[^}]*position: sticky/.test(css));
eis('ondoorzichtige achtergrond (anders schuift de tabel erdoorheen)',
  /\.hm-btn-top \{[^}]*background: var\(--bg\)/.test(css));
eis('boven de tabelinhoud (z-index)', /\.hm-btn-top \{[^}]*z-index: 2/.test(css));
eis('marge van de knop zelf genuld in de houder',
  /\.hm-btn-top \.hm-btn \{ margin-top: 0; \}/.test(css));

const panel = css.match(/#detail-panel \{[^}]*\}/);
eis('paneel scrollt nog steeds (anders is plakkerig zinloos)',
  !!panel && /overflow-y: auto/.test(panel[0]) && /max-height/.test(panel[0]), panel && panel[0]);

console.log('\n== volgorde in de echte functie ==');
const fn = html.slice(html.indexOf('function showWegvakDetail'),
                      html.indexOf("document.getElementById('detail-body').innerHTML=html;"));
const posTabel = fn.indexOf('cmp-table');
const posKnop  = fn.indexOf('Toon weekprofiel');
eis('de tabel wordt eerder in de code opgebouwd dan de knop', posTabel > 0 && posKnop > posTabel,
  { posTabel, posKnop });
eis('maar de knop wordt vooraan geplakt (html = knop + html)',
  /html = `<div class="hm-btn-top">[\s\S]*?` \+ html;/.test(fn));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
