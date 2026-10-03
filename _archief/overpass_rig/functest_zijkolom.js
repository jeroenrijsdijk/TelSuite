/* v2.59 test — de sessielijst krijgt gegarandeerde ruimte in de zijkolom.

   #sidebar is een flexkolom waarin alles flex-shrink:0 was behalve
   #sessions-list. Die kreeg dus enkel de rest, met min-height:60px als bodem —
   nog geen anderhalve sessierij. Een open #detail-panel (max 340px, niet
   krimpbaar) drukte de lijst daar altijd naartoe.                            */
const fs = require('fs');
const html = fs.readFileSync('telrapport.html', 'utf8');
const css = html.slice(0, html.indexOf('</style>'));

function regel(sel) {
  const re = new RegExp('(^|\\n)\\s*' + sel.replace(/[.#]/g, '\\$&') + '\\s*\\{[^}]*\\}');
  const m = css.match(re);
  return m ? m[0].replace(/\s+/g, ' ').trim() : null;
}

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

console.log('== sessielijst wint de onderhandeling ==');
const lijst = regel('#sessions-list');
eis('#sessions-list gevonden', !!lijst, lijst);
eis('groeit nog steeds mee (flex: 1)', /flex: 1/.test(lijst || ''));
eis('gegarandeerde bodem opgetrokken van 60px', !/min-height: 60px/.test(lijst || ''), lijst);
eis('bodem is proportioneel geplafonneerd', /min-height: min\(170px, 24vh\)/.test(lijst || ''), lijst);
eis('scrollt zelf', /overflow-y: auto/.test(lijst || ''));

console.log('\n== detailpaneel geeft ruimte terug ==');
const det = regel('#detail-panel');
eis('#detail-panel gevonden', !!det, det);
eis('mag krimpen (was flex-shrink: 0)', /flex: 0 1 auto/.test(det || '') && !/flex-shrink: 0/.test(det || ''), det);
eis('pakt hoogstens 40% van de kolom', /max-height: min\(340px, 40vh\)/.test(det || ''), det);
eis('houdt een leesbare bodem', /min-height: 84px/.test(det || ''), det);
eis('scrollt zelf, dus krimpen verbergt niets', /overflow-y: auto/.test(det || ''));

console.log('\n== compacte dropzone na het laden ==');
eis('.compact-regels bestaan', css.indexOf('#dropzone.compact {') >= 0);
eis('icoon verdwijnt', /#dropzone\.compact \.dz-icon \{ display: none; \}/.test(css));
eis('tweede regel verdwijnt', /#dropzone\.compact \.dz-sub \{ display: none; \}/.test(css));
eis('maar komt terug bij hover (map kiezen blijft bereikbaar)',
  /#dropzone\.compact:hover \.dz-sub \{ display: block; \}/.test(css));
eis('krappere marges elders in de kolom',
  /\.sidebar-compact #bbox-filter/.test(css) && /\.sidebar-compact #statsbar/.test(css));

console.log('\n== aan- en uitzetten hangt aan hasAny ==');
const js = html.slice(html.indexOf('function updateUI()'), html.indexOf('function updateUI()') + 1800);
eis('dropzone krijgt .compact zodra er tellingen zijn',
  /dropzone'\)\.classList\.toggle\('compact', hasAny\)/.test(js), js.slice(0, 40));
eis('zijkolom krijgt .sidebar-compact',
  /sidebar'\)\.classList\.toggle\('sidebar-compact', hasAny\)/.test(js));
eis('naast de bestaande statsbar-schakelaar (zelfde moment)',
  js.indexOf("statsbar") < js.indexOf("classList.toggle('compact'"), 'volgorde');

console.log('\n== de tekstnode blijft intact (voortgangsmeldingen) ==');
eis('compact verbergt .dz-text niet', !/#dropzone\.compact \.dz-text \{[^}]*display: none/.test(css));
eis('dzText verwijst nog naar .dz-text', /dz\.querySelector\('\.dz-text'\)/.test(html));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
