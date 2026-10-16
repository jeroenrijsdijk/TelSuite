/* v3.10 functionele test — het kwaliteitsrapport per telling in telrapport.
   Knipt kwTijd, kwAfstand en kwaliteitRapport uit telrapport.html en voert ze met
   nagebootste ZIP-inhoud (de bestanden als tekst, zoals loadZip ze aanlevert).

   Gecontroleerd:
     A. tijden lezen: de vormen van de parkeer-apps, pocket en Static, met zone,
        alleen een kloktijd met de sessiedatum (ook jjjjmmdd);
     B. een nette parkeertelling: zes keer ok;
     C. aantallen: _sessie, _telregels en _straten (parkeertelling en fiets);
     D. tijd: buiten de sessie, zonder tijd, en over middernacht (pocket);
     E. GPS-spoor: stilstaan is geen gat; een gat met een sprong is info, en
        let op zodra er een tik in valt;
     F. positie, nauwkeurigheid en route (een verschoven tik);
     G. Static: onderbrekingen, de ene fix, en n.v.t. waar geen spoor is;
     H. ontbrekende bestanden: n.v.t., geen fout.
   Draaien vanuit de suite-root (papaparse via NODE_PATH):
     node _archief/overpass_rig/functest_kwaliteit.js                          */
process.env.TZ = 'Europe/Amsterdam';
const fs = require('fs');
const vm = require('vm');
const Papa = require('papaparse');
const html = fs.readFileSync('telrapport.html', 'utf8');

function knip(a, b) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j);
}
const code = [
  "const parseCSV = txt => Papa.parse(txt.trim(), { header:true, delimiter:';', skipEmptyLines:true }).data;",
  knip('// ── Kwaliteit van een telling (v3.10)', 'function kwEsc(s)')
].join('\n');
const ctx = { Papa, Math, Date, String, Object, Array, parseInt, parseFloat, isNaN, console };
vm.createContext(ctx);
vm.runInContext(code + '\nthis.kwTijd = kwTijd; this.kwaliteitRapport = kwaliteitRapport; this.KW = KW;', ctx);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const iso = d => d ? [d.getFullYear(), d.getMonth() + 1, d.getDate(), d.getHours(), d.getMinutes(), d.getSeconds()].join(',') : null;
const oordeel = (r, naam) => (r.controles.find(c => c.naam === naam) || {}).oordeel;
const waarde = (r, naam) => (r.controles.find(c => c.naam === naam) || {}).waarde;

// ── nagebootste parkeertelling: lopen langs een straat, een punt per 10 s, 7 m verder
const SID = '20261016_100000_abc';
const LAT0 = 51.85, LON0 = 4.30, DLAT = 7 / 111320;   // 7 m naar het noorden
const p2 = n => String(n).padStart(2, '0');
const klok = (min, sec) => '2026-10-16 10:' + p2(min) + ':' + p2(sec);
function parkeer(opties) {
  const o = Object.assign({ n: 6, tikken: 6, straten: 6, gps: null, verschuif: null, zonderTijd: null, acc: 5 }, opties);
  const gps = o.gps || Array.from({ length: 13 }, (_, i) => [klok(Math.floor(i * 10 / 60), (i * 10) % 60), LAT0 + i * DLAT, LON0, o.acc]);
  const tel = Array.from({ length: o.tikken }, (_, i) => {
    let lat = LAT0 + (2 * i) * DLAT, lon = LON0;                  // op het punt van tik i·20 s
    if (o.verschuif === i) lat += 200 / 111320;                    // 200 m verschoven
    const t = o.zonderTijd === i ? '' : klok(Math.floor(i * 20 / 60), (i * 20) % 60);
    return [SID, i + 1, t, 'goed', 'L', 'Dorpsstraat', lat.toFixed(6), lon.toFixed(6), lat.toFixed(6), lon.toFixed(6), 1, 101, '', '', '', ''].join(';');
  });
  return {
    [SID + '_sessie.csv']: 'sessie_id;teller;datum;start_tijd;eind_tijd;app_type;n_waarnemingen\n' +
      [SID, 'Jay', '2026-10-16', '2026-10-16 10:00:00', '2026-10-16 10:02:00', 'auto', o.n].join(';'),
    [SID + '_telregels.csv']: 'sessie_id;nr;tijdstip;type;zijde;straat;lat_marker;lon_marker;lat_gps;lon_gps;snapped;osm_way_id;hdg_kompas;hdg_gps;hdg_osm;hdg_gebruikt\n' + tel.join('\n'),
    [SID + '_gps.csv']: 'sessie_id;tijdstip;lat;lon;nauwkeurigheid;hdg_gps;hdg_kompas;hdg_fused;gesnapped;osm_way_id;kompas_bevroren\n' +
      gps.map(g => [SID, g[0], g[1].toFixed(6), g[2].toFixed(6), g[3], '', '', '', 1, 101, 0].join(';')).join('\n'),
    [SID + '_straten.csv']: 'sessie_id;naam;osm_way_ids;goed;fout;leeg;spec;bezet;vrij;bezettingsgraad_pct;eerste_waarneming;laatste_waarneming\n' +
      [SID, 'Dorpsstraat', '101', o.straten - 1, 1, 0, 0, o.straten, 0, 100, '', ''].join(';')
  };
}
const sm = F => Papa.parse(F[Object.keys(F).find(k => k.endsWith('_sessie.csv'))], { header: true, delimiter: ';' }).data[0];
const rapport = F => ctx.kwaliteitRapport(F, sm(F));

console.log('== A. tijden lezen ==');
eis('parkeer-apps: "2026-10-16 10:01:20"', iso(ctx.kwTijd('2026-10-16 10:01:20')) === '2026,10,16,10,1,20');
eis('pocket/Static: "2026-10-16T23:58:00" lokaal', iso(ctx.kwTijd('2026-10-16T23:58:00')) === '2026,10,16,23,58,0');
eis('met zone: "2026-10-16T08:00:00.000Z" is 10:00 in Amsterdam', iso(ctx.kwTijd('2026-10-16T08:00:00.000Z')) === '2026,10,16,10,0,0');
eis('kloktijd met sessiedatum', iso(ctx.kwTijd('11:41:10', '2026-10-16')) === '2026,10,16,11,41,10');
eis('kloktijd met datum als jjjjmmdd', iso(ctx.kwTijd('09:05', '20261016')) === '2026,10,16,9,5,0');
eis('leeg of onzin: null', ctx.kwTijd('') === null && ctx.kwTijd('morgen') === null && ctx.kwTijd('10:00') === null);

console.log('\n== B. een nette parkeertelling ==');
let r = rapport(parkeer({}));
eis('zes controles, alle ok, 0 aandachtspunten',
  r.controles.length === 6 && r.controles.every(c => c.oordeel === 'ok') && r.aandacht === 0, r.controles.map(c => c.naam + ':' + c.oordeel));
eis('aantallen: "6 in _sessie, 6 in _telregels, 6 in _straten"', waarde(r, 'Aantallen') === '6 in _sessie, 6 in _telregels, 6 in _straten', waarde(r, 'Aantallen'));

console.log('\n== C. aantallen ==');
r = rapport(parkeer({ n: 7 }));
eis('_sessie zegt 7, er zijn 6 regels: let op', oordeel(r, 'Aantallen') === 'let' && r.aandacht === 1, waarde(r, 'Aantallen'));
r = rapport(parkeer({ straten: 5 }));
eis('_straten telt 5: let op', oordeel(r, 'Aantallen') === 'let', waarde(r, 'Aantallen'));
const fiets = parkeer({});
fiets[SID + '_straten.csv'] = 'sessie_id;naam;osm_way_ids;fiets;brommer;breed;wrak;totaal;eerste_waarneming;laatste_waarneming\n' + [SID, 'x', '101', 4, 1, 1, 0, 6, '', ''].join(';');
eis('fiets: de kolom totaal telt mee (6): ok', oordeel(rapport(fiets), 'Aantallen') === 'ok', waarde(rapport(fiets), 'Aantallen'));

console.log('\n== D. tijd ==');
const laat = parkeer({});
laat[SID + '_telregels.csv'] = laat[SID + '_telregels.csv'].replace('2026-10-16 10:01:40', '2026-10-16 10:05:40');
r = rapport(laat);
eis('een tik 3:40 na het eind: let op', oordeel(r, 'Tijd') === 'let' && /1 tik buiten 10:00:00–10:02:00/.test(waarde(r, 'Tijd')), waarde(r, 'Tijd'));
r = rapport(parkeer({ zonderTijd: 2 }));
eis('een tik zonder tijd: let op', oordeel(r, 'Tijd') === 'let' && /1 tik zonder tijd/.test(waarde(r, 'Tijd')), waarde(r, 'Tijd'));
const binnenMarge = parkeer({});
binnenMarge[SID + '_telregels.csv'] = binnenMarge[SID + '_telregels.csv'].replace('2026-10-16 10:01:40', '2026-10-16 10:02:50');
eis('50 s na het eind valt binnen de marge van 60 s', oordeel(rapport(binnenMarge), 'Tijd') === 'ok');
// pocket over middernacht: start 23:55, eind 00:10 de volgende dag
const PS = '20261016_235500_xyz_pkt_s';
const nacht = {
  [PS + '_sessie.csv']: 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b\n' +
    [PS, '2026-10-16', '23:55:00', '00:10:00', 'pocket', 'car', 2, 'simpel', '', ''].join(';'),
  [PS + '_telregels.csv']: 'sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat;conf;conf_level;gps_stab;gps_level;richting;snelheid\n' +
    [PS, 1, '2026-10-16T23:58:00', 'car', LAT0, LON0, '', '', '', '', '', '', '', '', ''].join(';') + '\n' +
    [PS, 2, '2026-10-17T00:05:00', 'car', LAT0, LON0, '', '', '', '', '', '', '', '', ''].join(';'),
  [PS + '_gps.csv']: 'sessie_id;tijdstip;lat;lon;nauwkeurigheid;osm_way_id;segment_index;straat\n' +
    [PS, '2026-10-16T23:55:00', LAT0, LON0, 6, '', '', ''].join(';')
};
r = rapport(nacht);
eis('pocket over middernacht: tijd ok', oordeel(r, 'Tijd') === 'ok', waarde(r, 'Tijd'));
eis('pocket: stilgestaan met één punt, tikken bij dat punt: spoor en route ok',
  oordeel(r, 'GPS-spoor') === 'ok' && oordeel(r, 'Op de route') === 'ok', [waarde(r, 'GPS-spoor'), waarde(r, 'Op de route')]);

console.log('\n== E. GPS-spoor ==');
// stilstaan: 5 min geen punt, en daarna op dezelfde plek
const stil = parkeer({ gps: [[klok(0, 0), LAT0, LON0, 5], [klok(5, 0), LAT0 + 2 / 111320, LON0, 5]] });
stil[SID + '_sessie.csv'] = stil[SID + '_sessie.csv'].replace('2026-10-16 10:02:00', '2026-10-16 10:06:00');
stil[SID + '_telregels.csv'] = stil[SID + '_telregels.csv'].replace(/;(\d+\.\d+);(\d+\.\d+);(\d+\.\d+);(\d+\.\d+);1;101/g,
  ';' + LAT0.toFixed(6) + ';' + LON0.toFixed(6) + ';' + LAT0.toFixed(6) + ';' + LON0.toFixed(6) + ';1;101');
r = rapport(stil);
eis('5 min stilstaan (2 m verder): geen gat', oordeel(r, 'GPS-spoor') === 'ok', waarde(r, 'GPS-spoor'));
eis('tikken tijdens het stilstaan liggen op de route', oordeel(r, 'Op de route') === 'ok', waarde(r, 'Op de route'));
// gat met sprong, geen tikken erin: punten 0..60 s, dan 4 min later 300 m verder
const gat = parkeer({ tikken: 3, n: 3, straten: 3, gps: [
  [klok(0, 0), LAT0, LON0, 5], [klok(0, 20), LAT0 + 2 * DLAT, LON0, 5], [klok(0, 40), LAT0 + 4 * DLAT, LON0, 5],
  [klok(1, 0), LAT0 + 6 * DLAT, LON0, 5], [klok(5, 0), LAT0 + 300 / 111320, LON0, 5]] });
r = rapport(gat);
eis('gat van 4 min met sprong van 300 m, geen tik erin: info, geen aandachtspunt',
  oordeel(r, 'GPS-spoor') === 'info' && r.aandacht === 0 && /1 gat, langste 4 min/.test(waarde(r, 'GPS-spoor')), waarde(r, 'GPS-spoor'));
const gatTik = parkeer({ tikken: 3, n: 3, straten: 3, gps: [[klok(0, 0), LAT0, LON0, 5], [klok(0, 30), LAT0 + 300 / 111320, LON0, 5]] });
gatTik[SID + '_telregels.csv'] = gatTik[SID + '_telregels.csv'].replace('2026-10-16 10:00:20', '2026-10-16 10:00:10');
r = rapport(gatTik);
eis('korter dan 60 s is geen gat, ook met een sprong', oordeel(r, 'GPS-spoor') === 'ok', waarde(r, 'GPS-spoor'));
const gatMetTik = parkeer({ tikken: 3, n: 3, straten: 3, gps: [[klok(0, 0), LAT0, LON0, 5], [klok(3, 0), LAT0 + 300 / 111320, LON0, 5]] });
r = rapport(gatMetTik);
eis('tikken in een gat met sprong: let op', oordeel(r, 'GPS-spoor') === 'let' && /2 tikken in een gat/.test(waarde(r, 'GPS-spoor')),
  waarde(r, 'GPS-spoor'));
eis('tikken in een gat tellen niet mee in de routecontrole', oordeel(r, 'Op de route') === 'ok', waarde(r, 'Op de route'));

console.log('\n== F. positie, nauwkeurigheid, route ==');
const zonderPos = parkeer({});
zonderPos[SID + '_telregels.csv'] = zonderPos[SID + '_telregels.csv'].replace(/^(.*;3;2026[^\n]*)$/m, l => {
  const v = l.split(';'); v[8] = ''; v[9] = ''; return v.join(';'); });
r = rapport(zonderPos);
eis('een tik zonder GPS-positie (de marker staat er nog wel): let op',
  oordeel(r, 'Positie') === 'let' && waarde(r, 'Positie') === '1 tik zonder GPS-positie', waarde(r, 'Positie'));
r = rapport(parkeer({ acc: 25 }));
eis('mediaan 25 m: let op', oordeel(r, 'Nauwkeurigheid') === 'let' && /mediaan ±25 m/.test(waarde(r, 'Nauwkeurigheid')), waarde(r, 'Nauwkeurigheid'));
const deels = parkeer({});
const g = deels[SID + '_gps.csv'].split('\n');
for (let i = 1; i <= 4; i++) g[i] = g[i].replace(/;5;;;;1;101;0$/, ';30;;;;1;101;0');   // 4 van 13 = 31%
deels[SID + '_gps.csv'] = g.join('\n');
r = rapport(deels);
eis('31% van de punten boven 20 m: let op', oordeel(r, 'Nauwkeurigheid') === 'let' && /31% boven 20 m/.test(waarde(r, 'Nauwkeurigheid')), waarde(r, 'Nauwkeurigheid'));
r = rapport(parkeer({ verschuif: 3 }));
// 200 m naar het noorden; het dichtstbijzijnde spoorpunt ligt 7 m verder noord: 193 m
eis('een tik 200 m verschoven: op de route let op, "verst 193 m"',
  oordeel(r, 'Op de route') === 'let' && /1 tik verder dan 50 m van het spoor \(verst 193 m\)/.test(waarde(r, 'Op de route')), waarde(r, 'Op de route'));
const marker = parkeer({});
marker[SID + '_telregels.csv'] = marker[SID + '_telregels.csv'].replace(/;Dorpsstraat;(\d+\.\d+);/g, (m, a) => ';Dorpsstraat;' + (parseFloat(a) + 0.002).toFixed(6) + ';');
eis('een verschoven marker (correctie, reconstructie) telt niet: de rauwe GPS-kolom wel', oordeel(rapport(marker), 'Op de route') === 'ok');

console.log('\n== G. Static ==');
const SS = '20261016_120000_qrs_sta';
const stat = (lat, acc, onder) => Object.assign({
  [SS + '_sessie.csv']: 'sessie_id;datum;start_tijd;eind_tijd;app_type;type;n_waarnemingen;modus;richting_a;richting_b;lat;lon;nauwkeurigheid;straat;plaats;notities;actieve_duur_s;uurfactor\n' +
    [SS, '2026-10-16', '12:00:00', '12:30:00', 'standstill', 'verkeer', 2, 'standstill', 'West', 'Oost', lat, lat ? LON0 : '', acc, '', '', '', 1500, 2.4].join(';'),
  [SS + '_telregels.csv']: 'sessie_id;nr;tijdstip;type;richting;lat;lon;nauwkeurigheid\n' +
    [SS, 1, '2026-10-16T12:05:00', 'car', 'a', '', '', ''].join(';') + '\n' + [SS, 2, '2026-10-16T12:25:00', 'bike', 'b', '', '', ''].join(';')
}, onder ? { [SS + '_onderbrekingen.csv']: 'sessie_id;nr;van;tot;duur_s\n' + [SS, 1, '2026-10-16T12:10:00', '2026-10-16T12:15:00', 300].join(';') } : {});
r = rapport(stat(LAT0, 8, true));
eis('Static met fix ±8 m en een onderbreking: 0 aandachtspunten, onderbreking als info',
  r.aandacht === 0 && oordeel(r, 'Onderbrekingen') === 'info' && waarde(r, 'Onderbrekingen') === '1 onderbreking, samen 5 min', r.controles);
eis('Static: positie en route n.v.t.', oordeel(r, 'Positie') === 'nvt' && oordeel(r, 'Op de route') === 'nvt');
eis('Static zonder onderbreking: ok', oordeel(rapport(stat(LAT0, 8, false)), 'Onderbrekingen') === 'ok');
eis('Static met fix ±35 m: let op', oordeel(rapport(stat(LAT0, 35, false)), 'Nauwkeurigheid') === 'let');
eis('Static zonder fix: let op "geen GPS-fix"', waarde(rapport(stat('', '', false)), 'Nauwkeurigheid') === 'geen GPS-fix');

console.log('\n== H. ontbrekende bestanden ==');
let foutje = null;
try {
  const leeg = { [SID + '_sessie.csv']: parkeer({})[SID + '_sessie.csv'] };
  r = rapport(leeg);
} catch (e) { foutje = e.message; }
eis('alleen _sessie.csv: geen fout, alles n.v.t. of ok, geen aandachtspunt', !foutje && r.aandacht === 0 &&
  r.controles.every(c => c.oordeel === 'nvt'), foutje || r.controles.map(c => c.naam + ':' + c.oordeel));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
process.exit(fout ? 1 : 0);
