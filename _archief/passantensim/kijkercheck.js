/* Simkijker: zijn de kopieën in simkijker.html nog gelijk aan het origineel?
   simkijker.html is één zelfstandige pagina (ook als artifact), dus hij draagt
   een kopie van sim_kern.js en van het blok PASSANTEN uit passanten.html.

   Draaien vanuit de repo-root:
     node _archief/passantensim/kijkercheck.js              controleren
     node _archief/passantensim/kijkercheck.js --bijwerken  de kopieën vervangen */
const fs = require('fs');
const path = require('path');
const KIJKER = path.join(__dirname, 'simkijker.html');

function tussen(tekst, a, z, metEind) {
  const i = tekst.indexOf(a), j = tekst.indexOf(z, i);
  if (i < 0 || j < 0) throw new Error('niet gevonden: ' + a);
  return tekst.slice(i, metEind ? j + z.length : j);
}
const pas = fs.readFileSync('passanten.html', 'utf8');
const BRONNEN = [
  { naam: 'sim_kern.js',
    begin: '/* ==== kopie van _archief/passantensim/sim_kern.js (node _archief/passantensim/kijkercheck.js) ==== */\n',
    eind: '/* ==== einde kopie sim_kern.js ==== */',
    tekst: fs.readFileSync(path.join(__dirname, 'sim_kern.js'), 'utf8') },
  { naam: 'blok PASSANTEN',
    begin: '/* ==== kopie van het blok PASSANTEN uit passanten.html (node _archief/passantensim/kijkercheck.js) ==== */\n',
    eind: '/* ==== einde kopie PASSANTEN ==== */',
    tekst: tussen(pas, '/* ── Passanten per uur: de rekenkern (v3.34)', '/* ── einde gedeeld blok passanten ── */', true) + '\n' }
];
let html = fs.readFileSync(KIJKER, 'utf8'), anders = 0;
BRONNEN.forEach(b => {
  const i = html.indexOf(b.begin), j = html.indexOf(b.eind, i);
  if (i < 0 || j < 0) throw new Error('markering niet gevonden in simkijker.html: ' + b.naam);
  const nu = html.slice(i + b.begin.length, j);
  if (nu === b.tekst) { console.log('  OK   ' + b.naam); return; }
  anders++;
  console.log('  ANDERS ' + b.naam);
  html = html.slice(0, i + b.begin.length) + b.tekst + html.slice(j);
});
if (anders && process.argv.includes('--bijwerken')) { fs.writeFileSync(KIJKER, html); console.log('bijgewerkt'); }
else if (anders) { console.log('draai met --bijwerken om de kopieën te vervangen'); process.exit(1); }
