/* v2.59 functionele test — telrapport kiest bij een paar de _recon-versie.

   De sessie_id is in beide ZIP's identiek; alleen de bestandsnaam verschilt.
   Zonder deze logica won het origineel, omdat `_car` alfabetisch vóór `_recon`
   komt en loadZip een tweede ZIP met dezelfde sid stil overslaat.            */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('telrapport.html', 'utf8');
function knip(a, b, inc) {
  const i = html.indexOf(a); if (i < 0) throw new Error('mist: ' + a.slice(0, 50));
  const j = html.indexOf(b, i); if (j < 0) throw new Error('mist eind: ' + b.slice(0, 50));
  return html.slice(i, j + (inc ? b.length : 0));
}
const BLOK = knip('/* ── origineel versus reconstructie (v2.59)',
  '  return { lijst:houden, weg };\n}', true);
// de sorteervergelijker zoals ingestFiles hem gebruikt
const SORT = `function sorteer(files){ return files.slice().sort((a,b)=>{
  const ra=reconBasis(a.name||''), rb=reconBasis(b.name||'');
  if(ra.basis===rb.basis && ra.recon!==rb.recon) return ra.recon?-1:1;
  return (a.name||'').localeCompare(b.name||'');
}); }`;

const ctx = { console, String, Object, Array, RegExp };
vm.createContext(ctx);
vm.runInContext(BLOK + '\n' + SORT, ctx);

const F = namen => namen.map(n => ({ name: n }));
const namenVan = lijst => lijst.map(f => f.name);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const kies = namen => vm.runInContext('kiesReconstructies(' + JSON.stringify(F(namen)) + ')', ctx);
const sorteer = namen => namenVan(vm.runInContext('sorteer(' + JSON.stringify(F(namen)) + ')', ctx));
const basis = naam => vm.runInContext('reconBasis(' + JSON.stringify(naam) + ')', ctx);

console.log('== reconBasis: paren herkennen ==');
eis('auto-origineel', basis('20260514_100500_qah_car.zip').basis === '20260514_100500_qah', basis('20260514_100500_qah_car.zip'));
eis('auto-reconstructie', basis('20260514_100500_qah_recon.zip').basis === '20260514_100500_qah', basis('20260514_100500_qah_recon.zip'));
eis('recon-vlag gezet', basis('20260514_100500_qah_recon.zip').recon === true);
eis('origineel niet als recon gemarkeerd', basis('20260514_100500_qah_car.zip').recon === false);
eis('fiets', basis('a_fts.zip').basis === 'a' && basis('a_recon.zip').basis === 'a');
eis('capaciteit', basis('b_cap.zip').basis === 'b');
eis('transect', basis('c_trn.zip').basis === 'c');
eis('pocket heeft geen achtervoegsel',
  basis('20260903_145005_fit_pkt_s.zip').basis === '20260903_145005_fit_pkt_s');
eis('pocket-reconstructie matcht het origineel',
  basis('20260903_145005_fit_pkt_s_recon.zip').basis === basis('20260903_145005_fit_pkt_s.zip').basis);
eis('"(1)"-kopie van een tweede download telt mee',
  basis('x_recon (1).zip').basis === 'x' && basis('x_recon (1).zip').recon === true);
eis('hoofdletters maken niet uit', basis('X_RECON.ZIP').basis === 'x' && basis('X_RECON.ZIP').recon === true);

console.log('\n== kiesReconstructies ==');
{
  const r = kies(['20260514_100500_qah_car.zip', '20260514_100500_qah_recon.zip']);
  eis('paar -> alleen de reconstructie', namenVan(r.lijst).join() === '20260514_100500_qah_recon.zip', namenVan(r.lijst));
  eis('overgeslagen origineel gemeld', r.weg.join() === '20260514_100500_qah_car.zip', r.weg);
}
{
  const r = kies(['a_car.zip', 'b_fts.zip', 'c_pkt_s.zip']);
  eis('geen reconstructies -> niets weggelaten', r.lijst.length === 3 && r.weg.length === 0, r.weg);
}
{
  const r = kies(['a_recon.zip', 'b_recon.zip']);
  eis('alleen reconstructies -> alles blijft', r.lijst.length === 2 && r.weg.length === 0);
}
{
  const r = kies(['a_car.zip', 'a_recon.zip', 'b_fts.zip', 'c_pkt_s.zip', 'c_pkt_s_recon.zip', 'd_cap.zip']);
  eis('gemengde lijst -> twee originelen weg',
    namenVan(r.lijst).sort().join() === ['a_recon.zip','b_fts.zip','c_pkt_s_recon.zip','d_cap.zip'].join(),
    namenVan(r.lijst));
  eis('en ze worden allebei gemeld', r.weg.sort().join() === 'a_car.zip,c_pkt_s.zip', r.weg);
}
{
  const r = kies(['losse_telling.csv', 'a_car.zip', 'a_recon.zip']);
  eis('een los CSV wordt nooit als paar gezien',
    r.lijst.some(f => f.name === 'losse_telling.csv'), namenVan(r.lijst));
}
{
  // verschillende tellingen die toevallig op elkaar lijken
  const r = kies(['20260514_100500_qah_car.zip', '20260514_100501_qah_car.zip']);
  eis('twee losse tellingen blijven beide', r.lijst.length === 2 && r.weg.length === 0, r.weg);
}

console.log('\n== sorteervolgorde: vangnet voor hernoemde bestanden ==');
{
  const s = sorteer(['20260514_100500_qah_car.zip', '20260514_100500_qah_recon.zip']);
  eis('reconstructie laadt eerst bij dezelfde telling', s[0].endsWith('_recon.zip'), s);
}
{
  const s = sorteer(['b_recon.zip', 'a_car.zip', 'c_pkt_s.zip']);
  eis('verder gewoon op naam', s.join() === 'a_car.zip,b_recon.zip,c_pkt_s.zip', s);
}
{
  const s = sorteer(['z_car.zip', 'a_recon.zip']);
  eis('losse tellingen niet omgegooid', s.join() === 'a_recon.zip,z_car.zip', s);
}

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
process.exit(fout ? 1 : 0);
