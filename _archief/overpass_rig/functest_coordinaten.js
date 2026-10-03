/* v2.60 test — welk coordinaat op de telrapport-kaart belandt.

   Dit is een broncodetest: hij controleert de vijf regels die we in v2.60 hebben
   vastgelegd, niet een gerenderde kaart. Dat is precies wat je wilt bewaken,
   want dit zijn stuk voor stuk plekken waar een "kleine opschoning" later stil
   de positie van een marker kan verschuiven.                                  */
const fs = require('fs');
const html = fs.readFileSync('telrapport.html', 'utf8');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

function fn(naam) {
  const i = html.indexOf('function ' + naam);
  if (i < 0) return '';
  return html.slice(i, i + 14000);
}

console.log('== A. gap-clusterbol op het zwaartepunt ==');
const dc = fn('drawClusters');
eis('bol staat niet meer op de eerste tik', dc.indexOf('[group[0].lat, group[0].lon]') < 0);
eis('zwaartepunt wordt berekend', /var gLat = group\.reduce/.test(dc) && /var gLon = group\.reduce/.test(dc));
eis('en gebruikt in de marker', /L\.marker\(\[gLat, gLon\]/.test(dc));
eis('het segmentpad middelt nog steeds ook', /const centLat=group\.reduce/.test(dc));

console.log('\n== A. tik-type komt van de marker, niet uit de tooltip ==');
eis('tooltip wordt niet meer uitgeplozen voor het type',
  dc.indexOf("tip.getContent().split(' ')") < 0);
eis('_tikType wordt gelezen', /dot\._tikType/.test(dc));
eis('pocket zet _tikType', /m\._tikType = rowType;/.test(fn('loadPocketZip')));
eis('transect zet _tikType', /m\._tikType = type;/.test(fn('loadTransectZip')));

console.log('\n== B. capaciteitslabel op het polygoon-zwaartepunt ==');
const cap = fn('loadCapaciteitZip');
eis('geen bbox-midden meer', !/bounds\.getNorth\(\)\+bounds\.getSouth\(\)/.test(cap));
eis('getCenter() gebruikt', /const mid = poly\.getCenter\(\);/.test(cap));
eis('en dat punt gaat in de marker', /L\.marker\(\[mid\.lat, mid\.lng\]/.test(cap));

console.log('\n== C. geen marker op een verzonnen positie ==');
eis('spreidingsoffset verdwenen', cap.indexOf('centLat+(i*0.00005)') < 0);
eis('Noordzee-fallback verdwenen', !/:\s*52\.0;/.test(cap) && !/:\s*4\.5;/.test(cap));
eis('groep zonder geometrie wordt geregistreerd', /zonderGeom\.push\(/.test(cap));
eis('en gemeld in de console', /console\.warn\('Capaciteit /.test(cap));
eis('en op de sessie gezet', /sessions\[sid\]\.zonderGeom = zonderGeom;/.test(cap));
eis('de sessierij toont het', /s\.zonderGeom && s\.zonderGeom\.length/.test(html));
eis('met de waarschuwingsopmaak die al bestond', /zonder geometrie<\/div>/.test(html)
  && /session-dekking incompleet/.test(html));

console.log('\n== D. standstill-pin: de bestaande afscherming staat er nog ==');
// Deze bleek bij de v2.60-analyse al aanwezig; v2.60 heeft hier niets toegevoegd.
// De test staat er wel, want het is de enige plek waar een telsoort met één
// coordinaat binnenkomt en een NaN het laden zou laten klappen.
// v2.73: de logica staat nu in toonStandStill(); loadStandStillCsv() en de
// ZIP-route leveren daar alleen de tekst aan.
const ss = fn('toonStandStill');
eis('GPS-controle staat aan het begin van de functie',
  ss.indexOf('isNaN(data.lat) || isNaN(data.lon)') >= 0);
eis('en vóór alles wat state aanmaakt',
  ss.indexOf('isNaN(data.lat) || isNaN(data.lon)') < ss.indexOf('const sid = vasteSid || ssBuildSid') &&
  ss.indexOf('isNaN(data.lat) || isNaN(data.lon)') < ss.indexOf('originalFile[sid] = bron') &&
  ss.indexOf('isNaN(data.lat) || isNaN(data.lon)') < ss.indexOf('getSessionColor(sid)'));
eis('geen tweede, overbodige controle bijgebouwd',
  (ss.match(/isFinite\(data\.lat\)/g) || []).length === 0);

console.log('\n== E. dode transect-tak weg ==');
eis('tweede transect-tak bestaat niet meer',
  html.indexOf("if (appType === 'transect' && telCSV)") < 0);
eis('het levende pad wordt precies één keer aangeroepen',
  (html.match(/(?<!function )loadTransectZip\(sid, sm, telCSV/g) || []).length === 1);
eis('en de functie zelf ook', (html.match(/function loadTransectZip/g) || []).length === 1);

console.log('\n== de coordinaatbronnen per telsoort, zoals vastgelegd ==');
eis('auto/fiets: lat_marker', /const la=\+r\.lat_marker, lo=\+r\.lon_marker;/.test(html));
eis('pocket: via tikPositie()', /const pos = tikPositie\(r\);/.test(fn('loadPocketZip')));
eis('transect: rauwe lat/lon (dit profiel krijgt geen markerkolom)',
  /const la = parseFloat\(r\.lat\), lo = parseFloat\(r\.lon\);/.test(fn('loadTransectZip')));
eis('capaciteit losse vakken: lat_marker', /parseFloat\(r\.lat_marker\)/.test(fn('showCapDetail')));
eis('standstill: GPS uit de metakop', /parseFloat\(meta\['GPS latitude'\]\)/.test(html));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
