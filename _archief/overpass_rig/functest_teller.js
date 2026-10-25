/* v3.37 functionele test — het blok "teller" van de vijf veld-apps, los van de browser.
   Bij het opslaan van een ZIP: één vingerafdruk (SHA-256 van "telonline.org teller "
   + de naam zonder .zip) naar /teller/. Geen verbinding of "later": wachten in
   localStorage. Niet als het toestel is uitgezet, alleen via http(s). Global
   Privacy Control telt niet (Jay: "GPC eruit, de knop blijft"). */
const fs = require('fs');
const vm = require('vm');
const nodeCrypto = require('crypto');
const APPS = ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html', 'pocket_count.html', 'traffic_counter.html'];
function blok(f) {
  const s = fs.readFileSync(f, 'utf8'), a = '/* ── Teller (v3.37)', z = '/* ── einde gedeeld blok teller ── */';
  const i = s.indexOf(a), j = s.indexOf(z);
  if (i < 0 || j < 0) throw new Error('blok teller niet gevonden in ' + f);
  return s.slice(i, j + z.length);
}
const BLOK = blok(APPS[0]);

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };
const sha = t => nodeCrypto.createHash('sha256').update(t, 'utf8').digest('hex');

// Een nagebootste browser: fetch onthoudt elk verzoek en antwoordt met wat de test kiest.
function omgeving(opties) {
  opties = opties || {};
  const opslag = Object.assign({}, opties.opslag || {});
  const verzoeken = [];
  const ctx = {
    location: { protocol: opties.protocol || 'https:' },
    navigator: opties.gpc ? { globalPrivacyControl: true } : {},
    localStorage: { getItem: k => (k in opslag ? opslag[k] : null), setItem: (k, v) => { opslag[k] = String(v); }, removeItem: k => { delete opslag[k]; } },
    crypto: nodeCrypto.webcrypto, TextEncoder, URLSearchParams, setTimeout: () => 0, Promise, JSON, Array, String, Error,
    fetch: (url, init) => {
      verzoeken.push({ url, methode: init.method, h: new URLSearchParams(init.body).get('h') });
      const a = typeof opties.antwoord === 'function' ? opties.antwoord(verzoeken.length) : (opties.antwoord || 200);
      return a === 'net' ? Promise.reject(new TypeError('Failed to fetch')) : Promise.resolve({ status: a, ok: a >= 200 && a < 300 });
    }
  };
  ctx.window = ctx; ctx.window.addEventListener = () => {};
  vm.createContext(ctx);
  vm.runInContext(BLOK, ctx);
  return { ctx, opslag, verzoeken, wacht: () => JSON.parse(opslag.telsuite_teller_wacht || '[]') };
}

(async () => {
  console.log('== de vingerafdruk ==');
  let o = omgeving();
  const h = await o.ctx.telTelling('20261025_143000_abc_pkt_w.zip');
  eis('SHA-256 van "telonline.org teller " + de naam zonder .zip', h === sha('telonline.org teller 20261025_143000_abc_pkt_w'), h);
  eis('één POST naar /teller/ met h = die vingerafdruk', o.verzoeken.length === 1 && o.verzoeken[0].url === '/teller/' && o.verzoeken[0].methode === 'POST' && o.verzoeken[0].h === h, o.verzoeken);
  eis('met of zonder .zip: dezelfde vingerafdruk (dezelfde telling)', (await o.ctx.telTelling('20261025_143000_abc_pkt_w')) === h);
  eis('64 kleine hexadecimale tekens', /^[0-9a-f]{64}$/.test(h));
  eis('een andere telling: een andere vingerafdruk', (await o.ctx.telTelling('20261025_143001_abc_pkt_w.zip')) !== h);
  eis('een geslaagd verzoek laat niets wachten', o.wacht().length === 0 && !('telsuite_teller_wacht' in o.opslag));

  console.log('\n== geen verbinding, of later ==');
  for (const [a, naam] of [['net', 'geen verbinding'], [429, '429 (rem)'], [503, '503'], [502, '502'], [504, '504']]) {
    o = omgeving({ antwoord: a });
    const x = await o.ctx.telTelling('a_car.zip');
    eis(naam + ': de vingerafdruk wacht in localStorage', JSON.stringify(o.wacht()) === JSON.stringify([x]), o.wacht());
  }
  for (const a of [400, 404, 405, 501]) {
    o = omgeving({ antwoord: a });
    await o.ctx.telTelling('a_car.zip');
    eis(a + ': een antwoord is genoeg, er wacht niets (ook niet bij een server zonder teller)', o.wacht().length === 0, o.wacht());
  }
  o = omgeving({ antwoord: 'net' });
  await o.ctx.telTelling('a_car.zip'); await o.ctx.telTelling('a_car.zip');
  eis('dezelfde vingerafdruk wacht maar één keer', o.wacht().length === 1);
  const vol = Array.from({ length: 60 }, (_, i) => sha('x' + i));
  o = omgeving({ antwoord: 'net', opslag: { telsuite_teller_wacht: JSON.stringify(vol) } });
  await o.ctx.telTelling('b_car.zip');
  eis('hooguit 50 wachten (de nieuwste)', o.wacht().length === 50 && o.wacht()[49] === sha('telonline.org teller b_car'), o.wacht().length);

  console.log('\n== inhalen bij het openen ==');
  const wachtend = Array.from({ length: 7 }, (_, i) => sha('w' + i));
  o = omgeving({ antwoord: 200, opslag: { telsuite_teller_wacht: JSON.stringify(wachtend) } });
  o.ctx.tellerInhalen(); await new Promise(r => setTimeout(r, 20));
  eis('hooguit 5 per keer; die zijn daarna weg, 2 wachten nog', o.verzoeken.length === 5 && JSON.stringify(o.wacht()) === JSON.stringify(wachtend.slice(5)), [o.verzoeken.length, o.wacht().length]);
  o = omgeving({ antwoord: 'net', opslag: { telsuite_teller_wacht: JSON.stringify(wachtend.slice(0, 2)) } });
  o.ctx.tellerInhalen(); await new Promise(r => setTimeout(r, 20));
  eis('nog steeds geen verbinding: ze blijven wachten', o.wacht().length === 2);

  console.log('\n== niet versturen ==');
  o = omgeving({ opslag: { telsuite_niet_tellen: '1' } });
  eis('dit toestel uitgezet (privacyverklaring): niets', (await o.ctx.telTelling('c_car.zip')) === null && o.verzoeken.length === 0);
  o = omgeving({ protocol: 'file:' });
  eis('een bestand van schijf (file:): niets', (await o.ctx.telTelling('c_car.zip')) === null && o.verzoeken.length === 0);
  o = omgeving({ opslag: { telsuite_niet_tellen: '1', telsuite_teller_wacht: JSON.stringify([sha('z')]) } });
  o.ctx.tellerInhalen();
  eis('ook inhalen niet, als het niet mag', o.verzoeken.length === 0);
  o = omgeving({ gpc: true, antwoord: 200 });
  eis('Global Privacy Control telt niet (Jay: "GPC eruit, de knop blijft"): wel verstuurd',
      (await o.ctx.telTelling('c_car.zip')) === sha('telonline.org teller c_car') && o.verzoeken.length === 1);

  console.log('\n== hetzelfde blok in de vijf veld-apps ==');
  eis('byte-identiek in ' + APPS.join(', '), APPS.every(f => blok(f) === BLOK));
  const haken = { 'parkeertelling.html': 'telTelling(zipName);', 'fietsparkeren.html': 'telTelling(zipName);', 'capaciteitstelling.html': 'telTelling(zipName);',
                  'traffic_counter.html': 'telTelling(zipName);', 'pocket_count.html': 'if (lastZipName) telTelling(lastZipName);' };
  eis('elke app meldt de telling waar hij de ZIP aanbiedt (bewaarZip, of het voorbeeldscherm van pocket)',
      Object.entries(haken).every(([f, t]) => fs.readFileSync(f, 'utf8').split(t).length === 2));

  console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : ok + ' ok, ' + fout + ' FOUT'));
  process.exit(fout ? 1 : 0);
})();
