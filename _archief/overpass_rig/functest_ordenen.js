/* v3.31 functionele test — de indeling van Ordenen (telarchief.html), los van de browser.
   v3.32: de naam van het logboek, met datum en tijd.
   v3.33: de catalogus (wanneer, waar, dubbel, zonder reconstructie) en catalogus.csv.
   ORDENEN.plan krijgt een lijst bestanden en geeft per bestand: blijven, verplaatsen
   (waarheen en waarom), overslaan of een naamconflict. */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('telarchief.html', 'utf8');
const i = html.indexOf('var ORDENEN = (function () {'), j = html.indexOf('/* ── einde ORDENEN ── */');
if (i < 0 || j < 0) throw new Error('blok ORDENEN niet gevonden');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(html.slice(i, j) + '\nthis.ORDENEN = ORDENEN;', ctx);
const O = ctx.ORDENEN;

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const ses = (app_type, sessie_id, extra) => Object.assign({ app_type, sessie_id }, extra || {});
const item = (pad, sessie, extra) => Object.assign({ pad, naam: pad.split('/').pop(), sha: 'sha:' + pad, sessie }, extra || {});
const naar = (acties, pad) => { const a = acties.find(x => x.van === pad); return a ? [a.status, a.naar, a.reden] : null; };

console.log('== soort: eerst de naam, dan _sessie.csv ==');
const S = (naam, sessie, v) => O.soort({ naam, sessie, verzameling: v });
eis('_car -> auto', S('20261001_100000_abc_car.zip') === 'auto');
eis('_fts -> fiets', S('20261001_100000_abc_fts.zip') === 'fiets');
eis('_cap -> capaciteit', S('20261001_100000_abc_cap.zip') === 'capaciteit');
eis('_pkt_p, _pkt_s, _pkt_t, _pkt_w -> de vier pocket-modi',
  ['p', 's', 't', 'w'].map(l => S('20261001_100000_abc_pkt_' + l + '.zip')).join() === 'pocket:parkeren,pocket:simpel,pocket:transect,pocket:winkelstraat');
eis('pocket-reconstructie: _pkt_w_recon -> winkelstraat', S('20261001_100000_abc_pkt_w_recon.zip') === 'pocket:winkelstraat');
eis('dubbele download: _car (1).zip -> auto', S('20261001_100000_abc_car (1).zip') === 'auto');
eis('Static: _sta -> standstill', S('20261001_100000_abc_sta.zip') === 'standstill');
eis('auto-reconstructie zonder merkteken: uit _sessie.csv', S('20261001_100000_abc_recon.zip', ses('auto', '20261001_100000_abc')) === 'auto');
eis('pocket zonder merkteken: modus uit _sessie.csv', S('x.zip', ses('pocket', 'x', { modus: 'transect' })) === 'pocket:transect');
eis('pocket zonder modus: letter uit de sessie-id', S('x.zip', ses('pocket', '20261001_100000_abc_pkt_s')) === 'pocket:simpel');
eis('de naam gaat voor de inhoud', S('20261001_100000_abc_fts.zip', ses('auto', '20261001_100000_abc')) === 'fiets');
eis('verzameling: aan de naam of aan verzameling.json',
  S('TelVerzameling_20261020.zip') === 'verzameling' && S('mijn kaart.zip', null, true) === 'verzameling');
eis('het oude _trn-formaat en onbekende ZIPs: geen soort', S('20260514_113917_ard_trn.zip', ses('transect', 'x')) === null && S('foto.zip', null) === null);

console.log('\n== indeling ==');
const A = [
  item('20261001_100000_abc_car.zip', ses('auto', '20261001_100000_abc')),
  item('20261001_100000_abc_recon.zip', ses('auto', '20261001_100000_abc', { reconstructie: 'v3.30' })),
  item('20261002_100000_def_car.zip', ses('auto', '20261002_100000_def')),
  item('sub/20261003_100000_ghi_pkt_w.zip', ses('pocket', '20261003_100000_ghi_pkt_w', { modus: 'winkelstraat' })),
  item('Pocket simpel/20261004_100000_jkl_pkt_s.zip', ses('pocket', '20261004_100000_jkl_pkt_s', { modus: 'simpel' })),
  item('TelVerzameling_20261020.zip', null, { verzameling: true }),
  item('foto.zip', null),
  item('kapot_car.zip', null, { fout: 'Corrupted zip' }),
  item('20261005_100000_mno_sta.zip', ses('standstill', '20261005_100000_mno_sta'))
];
const P = O.plan(A);
eis('origineel met een reconstructie -> Autoparkeren/originelen',
  JSON.stringify(naar(P, '20261001_100000_abc_car.zip').slice(0, 2)) === JSON.stringify(['verplaatsen', 'Autoparkeren/originelen/20261001_100000_abc_car.zip']),
  naar(P, '20261001_100000_abc_car.zip'));
eis('de reconstructie -> Autoparkeren',
  naar(P, '20261001_100000_abc_recon.zip')[1] === 'Autoparkeren/20261001_100000_abc_recon.zip' && /reconstructie/.test(naar(P, '20261001_100000_abc_recon.zip')[2]));
eis('een origineel zonder reconstructie -> Autoparkeren', naar(P, '20261002_100000_def_car.zip')[1] === 'Autoparkeren/20261002_100000_def_car.zip');
eis('ook uit een submap -> Winkelstraat', naar(P, 'sub/20261003_100000_ghi_pkt_w.zip')[1] === 'Winkelstraat/20261003_100000_ghi_pkt_w.zip');
eis('wat al goed staat: blijft', naar(P, 'Pocket simpel/20261004_100000_jkl_pkt_s.zip')[0] === 'goed');
eis('verzameling -> Verzamelingen', naar(P, 'TelVerzameling_20261020.zip')[1] === 'Verzamelingen/TelVerzameling_20261020.zip');
eis('Static -> Stilstaand', naar(P, '20261005_100000_mno_sta.zip')[1] === 'Stilstaand/20261005_100000_mno_sta.zip');
eis('een andere ZIP blijft liggen', naar(P, 'foto.zip')[0] === 'overslaan' && /geen telling/.test(naar(P, 'foto.zip')[2]));
eis('een onleesbare ZIP blijft liggen, met de reden', naar(P, 'kapot_car.zip')[0] === 'overslaan' && /niet te lezen/.test(naar(P, 'kapot_car.zip')[2]));

console.log('\n== een origineel komt terug als de reconstructie weg is ==');
const B = O.plan([item('Autoparkeren/originelen/20261001_100000_abc_car.zip', ses('auto', '20261001_100000_abc'))]);
eis('Autoparkeren/originelen -> Autoparkeren', B[0].naar === 'Autoparkeren/20261001_100000_abc_car.zip' && B[0].status === 'verplaatsen');
const B2 = O.plan([item('20261003_100000_ghi_pkt_w.zip', ses('pocket', '20261003_100000_ghi_pkt_w', { modus: 'winkelstraat' })),
                   item('x/20261003_100000_ghi_pkt_w_recon.zip', ses('pocket', '20261003_100000_ghi_pkt_w', { modus: 'winkelstraat', reconstructie: 'v3.30' }))]);
eis('pocket: origineel en reconstructie op de sessie-id (met _pkt_w erin)',
  B2[0].naar === 'Winkelstraat/originelen/20261003_100000_ghi_pkt_w.zip' && B2[1].naar === 'Winkelstraat/20261003_100000_ghi_pkt_w_recon.zip', B2.map(a => a.naar));

console.log('\n== dubbelen ==');
const C = O.plan([
  item('20261002_100000_def_car (1).zip', ses('auto', '20261002_100000_def'), { sha: 'zelfde' }),
  item('20261002_100000_def_car.zip', ses('auto', '20261002_100000_def'), { sha: 'zelfde' }),
  item('Autoparkeren/20261002_100000_def_car (2).zip', ses('auto', '20261002_100000_def'), { sha: 'zelfde' }),
  item('20261006_100000_pqr_car (1).zip', ses('auto', '20261006_100000_pqr'), { sha: 'een' }),
  item('20261006_100000_pqr_car.zip', ses('auto', '20261006_100000_pqr'), { sha: 'twee' })
]);
const blijft = C.filter(a => !a.dubbel && a.item.sha === 'zelfde');
eis('van drie gelijke blijft er één: die al goed staat', blijft.length === 1 && blijft[0].van === 'Autoparkeren/20261002_100000_def_car (2).zip' && blijft[0].status === 'goed', blijft.map(a => a.van));
eis('de andere twee -> dubbel, met de reden', C.filter(a => a.dubbel).length === 2 &&
  C.filter(a => a.dubbel).every(a => a.naar.startsWith('dubbel/') && /dubbel van Autoparkeren\//.test(a.reden)));
eis('andere inhoud onder bijna dezelfde naam: beide naar Autoparkeren, geen dubbel',
  naar(C, '20261006_100000_pqr_car (1).zip')[1] === 'Autoparkeren/20261006_100000_pqr_car (1).zip' &&
  naar(C, '20261006_100000_pqr_car.zip')[1] === 'Autoparkeren/20261006_100000_pqr_car.zip');
const C2 = O.plan([item('a/x_car.zip', ses('auto', 'x'), { sha: 's' }), item('b/x_car.zip', ses('auto', 'x'), { sha: 's' }),
                   item('dubbel/x_car.zip', ses('auto', 'x'), { sha: 's' })]);
eis('in dubbel/ krijgt een tweede dezelfde naam een volgnummer',
  C2.filter(a => a.dubbel).map(a => a.naar).sort().join() === 'dubbel/x_car (2).zip,dubbel/x_car.zip', C2.map(a => [a.van, a.status, a.naar]));

console.log('\n== naamconflicten: nooit overschrijven ==');
const D = O.plan([item('Autoparkeren/x_car.zip', ses('auto', 'y'), { sha: '1' }),
                  item('x_car.zip', ses('auto', 'x'), { sha: '2' }),
                  item('a/z_fts.zip', ses('fiets', 'z'), { sha: '3' }), item('b/z_fts.zip', ses('fiets', 'z2'), { sha: '4' })]);
eis('doel bezet door een ander bestand: conflict, blijft liggen', naar(D, 'x_car.zip')[0] === 'conflict' && /staat al een ander bestand/.test(naar(D, 'x_car.zip')[2]));
eis('twee verschillende bestanden naar hetzelfde doel: de eerste gaat, de tweede is een conflict',
  naar(D, 'a/z_fts.zip')[0] === 'verplaatsen' && naar(D, 'b/z_fts.zip')[0] === 'conflict');
eis('hoofdletters tellen niet (Windows): AUTOPARKEREN/x_car.zip bezet Autoparkeren/x_car.zip',
  O.plan([item('AUTOPARKEREN/X_CAR.zip', null, { fout: 'x' }), item('X_CAR.zip', ses('auto', 'q'))]).find(a => a.van === 'X_CAR.zip').status === 'conflict');

eis('een map met andere hoofdletters telt als goed (autoparkeren/ is Autoparkeren/)',
  O.plan([item('autoparkeren/x_car.zip', ses('auto', 'x'))])[0].status === 'goed');

console.log('\n== het logboek: datum en tijd in de naam (v3.32) ==');
eis('ordenen_logboek_jjjjmmdd_uummss.csv, zoals een sessie-id',
  O.logboekNaam(new Date(2026, 9, 24, 8, 10, 12)) === 'ordenen_logboek_20261024_081012.csv', O.logboekNaam(new Date(2026, 9, 24, 8, 10, 12)));
eis('met voorloopnullen (2 januari, 03:04:05)', O.logboekNaam(new Date(2026, 0, 2, 3, 4, 5)) === 'ordenen_logboek_20260102_030405.csv');
eis('naam bezet: _2, _3; k = 1 geeft geen nummer',
  O.logboekNaam(new Date(2026, 0, 2, 3, 4, 5), 2) === 'ordenen_logboek_20260102_030405_2.csv' &&
  O.logboekNaam(new Date(2026, 0, 2, 3, 4, 5), 1) === O.logboekNaam(new Date(2026, 0, 2, 3, 4, 5)));

console.log('\n== catalogus (v3.33): wanneer, waar, dubbel, zonder reconstructie ==');
const thuis = [52.0, 4.0], hier = [51.85, 4.30];
const pl = O.plek([thuis, thuis, thuis, [51.8501, 4.3001], [51.8502, 4.2999], hier, hier, hier, hier, hier]);
eis('plek: de mediaan ligt in het telgebied (binnen 20 m), ook als de opname thuis begint (3 van de 10 punten)',
  Math.abs(pl.lat - 51.85) < 0.0002 && Math.abs(pl.lon - 4.3) < 0.0003, pl);
eis('plek: lege, nul- en kapotte waarden tellen niet mee; niets bruikbaars geeft null',
  JSON.stringify(O.plek([['', ''], ['0', '0'], ['x', '4'], ['51.9', '4.5']])) === JSON.stringify({ lat: 51.9, lon: 4.5 }) && O.plek([['', '']]) === null && O.plek([]) === null);
eis('weekdag: za 24 oktober 2026, ma 19 oktober 2026, leeg zonder datum',
  O.weekdag('2026-10-24') === 'za' && O.weekdag('2026-10-19') === 'ma' && O.weekdag('') === '');
const P_ = (lat, lon) => ({ plek: { lat, lon } });
const K = O.catalogus([
  item('20261001_100000_abc_car.zip', ses('auto', '20261001_100000_abc', { datum: '2026-10-01', start_tijd: '10:00:00', eind_tijd: '10:30:00', n_waarnemingen: '120' }), Object.assign({ sha: 'A', grootte: 1234, gewijzigd: '2026-10-01 10:31:00' }, P_(51.85, 4.3))),
  item('20261001_100000_abc_car (1).zip', ses('auto', '20261001_100000_abc', { datum: '2026-10-01', start_tijd: '10:00:00' }), Object.assign({ sha: 'A' }, P_(51.85, 4.3))),
  item('Autoparkeren/20261001_100000_abc_recon.zip', ses('auto', '20261001_100000_abc', { datum: '2026-10-01', start_tijd: '10:00:00', reconstructie: 'v3.30' }), P_(51.85, 4.3)),
  item('20261002_090000_def_car.zip', ses('auto', '20261002_090000_def', { datum: '2026-10-02', start_tijd: '09:00:00' }), P_(51.86, 4.31)),
  item('veld/20261003_110000_ghi_pkt_w.zip', ses('pocket', '20261003_110000_ghi_pkt_w', { modus: 'winkelstraat', datum: '2026-10-03', start_tijd: '11:00:00' }), P_(51.84, 4.32)),
  item('20261004_120000_jkl_sta.zip', ses('standstill', '20261004_120000_jkl_sta', { datum: '2026-10-04', start_tijd: '12:00:00' }), P_(51.83, 4.33)),
  item('20261005_130000_mno_cap.zip', ses('capaciteit', '20261005_130000_mno', { datum: '2026-10-05', start_tijd: '13:00:00' }), P_(51.82, 4.34)),
  item('TelVerzameling_20261020.zip', null, { verzameling: true }),
  item('a/20261006_140000_xyz_fts.zip', ses('fiets', '20261006_140000_xyz', { datum: '2026-10-06', start_tijd: '14:00:00' }), { sha: 'X1' }),
  item('b/20261006_140000_xyz_fts.zip', ses('fiets', '20261006_140000_xyz', { datum: '2026-10-06', start_tijd: '14:00:00' }), { sha: 'X2' }),
  item('foto.zip', null),
  item('20261001_080000_vro_car.zip', ses('auto', '20261001_080000_vro; met puntkomma', { datum: '2026-10-01', start_tijd: '08:00:00' }), {})
]);
const rij = pad => K.find(r => r.pad === pad) || {};
eis('een regel per telling of verzameling, niet voor foto.zip', K.length === 11 && !K.some(r => r.pad === 'foto.zip'), K.map(r => r.pad));
eis('recon: ja (er is een reconstructie), zelf, nee (nog niet)',
  rij('20261001_100000_abc_car.zip').recon === 'ja' && rij('Autoparkeren/20261001_100000_abc_recon.zip').recon === 'zelf' &&
  rij('20261002_090000_def_car.zip').recon === 'nee' && rij('veld/20261003_110000_ghi_pkt_w.zip').recon === 'nee');
eis('recon: n.v.t. voor Static, capaciteit en een verzameling',
  ['20261004_120000_jkl_sta.zip', '20261005_130000_mno_cap.zip', 'TelVerzameling_20261020.zip'].every(p => rij(p).recon === 'n.v.t.'));
eis('dubbel_van: de kopie wijst naar het bestand dat blijft; dat weet dat het een dubbel heeft',
  rij('20261001_100000_abc_car (1).zip').dubbel_van === '20261001_100000_abc_car.zip' && rij('20261001_100000_abc_car.zip').heeftDubbel &&
  rij('20261001_100000_abc_car.zip').dubbel_van === '' && !rij('20261002_090000_def_car.zip').heeftDubbel);
eis('zelfde telling, andere inhoud: twee fietstellingen met dezelfde sessie-id en een andere vingerafdruk',
  rij('a/20261006_140000_xyz_fts.zip').zelfde === 2 && rij('b/20261006_140000_xyz_fts.zip').zelfde === 2 &&
  !rij('20261001_100000_abc_car.zip').zelfde && !rij('Autoparkeren/20261001_100000_abc_recon.zip').zelfde);
eis('een verzameling: datum uit de naam (di 20 oktober), soort Verzamelingen, zonder plek',
  rij('TelVerzameling_20261020.zip').datum === '2026-10-20' && rij('TelVerzameling_20261020.zip').weekdag === 'di' &&
  rij('TelVerzameling_20261020.zip').soort === 'Verzamelingen' && rij('TelVerzameling_20261020.zip').lat === null);
eis('op datum en dan begintijd: 08:00 voor 10:00 op 1 oktober, de verzameling achteraan',
  K[0].pad === '20261001_080000_vro_car.zip' && K[1].start_tijd === '10:00:00' && K[K.length - 1].pad === 'TelVerzameling_20261020.zip', K.map(r => r.pad));
const csv = O.csvTekst(K), regels = csv.split('\n');
eis('csv: de kop zoals afgesproken', regels[0] === 'sessie_id;soort;datum;weekdag;start_tijd;eind_tijd;n_waarnemingen;recon;dubbel_van;lat;lon;pad;bytes;gewijzigd;sha256', regels[0]);
eis('csv: een regel per telling, en een slotregel', regels.length === K.length + 2 && regels[regels.length - 1] === '' && csv.endsWith('\n'));
eis('csv: een volledige regel (lat/lon met zes decimalen)',
  regels.includes('20261001_100000_abc;Autoparkeren;2026-10-01;do;10:00:00;10:30:00;120;ja;;51.850000;4.300000;20261001_100000_abc_car.zip;1234;2026-10-01 10:31:00;A'),
  regels.filter(x => x.startsWith('20261001_100000_abc;Autoparkeren')));
eis('csv: een puntkomma in een waarde wordt een komma; zonder plek blijven lat en lon leeg',
  regels.some(x => x.startsWith('20261001_080000_vro, met puntkomma;Autoparkeren;') && x.split(';').length === 15 && x.split(';')[9] === '' && x.split(';')[10] === ''));
eis('csv: elke regel 15 velden', regels.slice(0, -1).every(x => x.split(';').length === 15));

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
