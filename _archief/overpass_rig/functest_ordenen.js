/* v3.31 functionele test — de indeling van Ordenen (telarchief.html), los van de browser.
   v3.32: de naam van het logboek, met datum en tijd.
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

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
