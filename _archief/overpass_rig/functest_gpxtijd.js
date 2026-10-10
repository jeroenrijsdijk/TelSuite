/* v3.4 functionele test — tijden in het GPX-bestand van de drie parkeer-apps.
   Tot v3.3 stond daar de lokale tijd met een 'Z' (UTC) erachter: één of twee
   uur mis. Nu: echte UTC. Gedraaid in de tijdzone Europe/Amsterdam, dus met
   zomer- en wintertijd. Knipt timestamp(), het gedeelde blok GPX-tijd en
   buildGpxString() uit elk bestand en draait ze met nagebootste routepunten.  */
process.env.TZ = 'Europe/Amsterdam';
const fs = require('fs');
const vm = require('vm');

let ok = 0, fout = 0;
const eis = (n, v, x) => { if (v) { ok++; console.log('  OK   ' + n); } else { fout++; console.log('  FOUT ' + n + (x !== undefined ? ' -> ' + JSON.stringify(x) : '')); } };

const APPS = ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'];
const blokken = {};

for (const f of APPS) {
  const html = fs.readFileSync(f, 'utf8');
  const knip = (a, b) => {
    const i = html.indexOf(a); if (i < 0) throw new Error(f + ' mist: ' + a.slice(0, 40));
    const j = html.indexOf(b, i); if (j < 0) throw new Error(f + ' mist eind: ' + b.slice(0, 40));
    return html.slice(i, j + b.length);
  };
  const pad = 'function pad(n) { return String(n).padStart(2,\'0\'); }\n';
  const ts = knip('function timestamp(d) {', '\n}\n');
  const blok = knip('/* ── GPX-tijd (v3.4) ── */', '/* ── einde gedeeld blok GPX-tijd ── */');
  const gpx = knip('function buildGpxString() {', "  return lines.join('\\n');\n}");
  blokken[f] = blok;

  const ctx = { String, Date, isNaN, entries: [], trackPoints: [] };
  vm.createContext(ctx);
  vm.runInContext(pad + ts + blok + gpx, ctx);

  console.log('\n== ' + f + ' ==');
  // Zomertijd (UTC+2) en wintertijd (UTC+1): nieuw routepunt zoals onPosition het maakt.
  const zomer = new Date(Date.UTC(2026, 9, 10, 7, 54, 12));   // 09:54:12 lokaal
  const winter = new Date(Date.UTC(2026, 11, 3, 13, 5, 0));   // 14:05:00 lokaal
  const maak = d => vm.runInContext('({ts: timestamp(D), utc: utcTijd(D)})', Object.assign(ctx, { D: d }));
  const pz = maak(zomer), pw = maak(winter);
  eis('zomertijd: ts lokaal 09:54:12', pz.ts === '2026-10-10 09:54:12', pz.ts);
  eis('zomertijd: utc 07:54:12Z', pz.utc === '2026-10-10T07:54:12Z', pz.utc);
  eis('wintertijd: ts lokaal 14:05:00', pw.ts === '2026-12-03 14:05:00', pw.ts);
  eis('wintertijd: utc 13:05:00Z', pw.utc === '2026-12-03T13:05:00Z', pw.utc);

  // GPX met een nieuw punt, een punt uit een oude noodkopie (alleen ts) en een kapot punt.
  ctx.trackPoints = [
    { ts: pz.ts, utc: pz.utc, lat: '51.850000', lon: '4.330000' },
    { ts: '2026-07-01 12:00:00', lat: '51.850100', lon: '4.330100' },
    { ts: 'onzin', lat: '51.850200', lon: '4.330200' }
  ];
  const gpxTekst = vm.runInContext('buildGpxString()', ctx);
  const tijden = [...gpxTekst.matchAll(/<trkpt[^>]*>\s*(?:<time>([^<]*)<\/time>)?\s*<\/trkpt>/g)].map(m => m[1] || null);
  eis('drie routepunten in de GPX', tijden.length === 3, tijden);
  eis('nieuw punt: de vastgelegde UTC-tijd', tijden[0] === '2026-10-10T07:54:12Z', tijden[0]);
  eis('oud punt (alleen lokale tijd): omgerekend naar UTC', tijden[1] === '2026-07-01T10:00:00Z', tijden[1]);
  eis('onleesbare tijd: punt zonder <time>, geen fout', tijden[2] === null, tijden[2]);
  eis('nergens nog lokale tijd met Z', !/T09:54:12Z|T12:00:00Z/.test(gpxTekst));
  eis('kopregel: metadata-tijd is UTC (toISOString)', /<metadata>[\s\S]*<time>\d{4}-\d\d-\d\dT[\d:.]+Z<\/time>/.test(gpxTekst));
}

console.log('\n== gedeeld blok GPX-tijd ==');
const uniek = new Set(Object.values(blokken));
eis('byte-identiek in de drie apps', uniek.size === 1);

console.log('\n' + (fout === 0 ? 'ALLE ' + ok + ' TESTS OK' : fout + ' FOUT, ' + ok + ' OK'));
process.exit(fout ? 1 : 0);
