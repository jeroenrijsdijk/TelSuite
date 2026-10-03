// vtest.js — headless Viterbi-toets op een pocket-ZIP.
// Spiegelt loadPocketZip + viterbiWaysForSession + reassignTaps uit telrapport_viterbi.html.
// Gebruik: node vtest.js <pad/naar/sessie.zip>   [hardWays=130419432,136079346,130418057]
'use strict';
const fs = require('fs');
const cp = require('child_process');
const Viterbi = require('./viterbi_engine.js');

// ── faithful parsers (header, ';'-delimiter, skip empty) ──
function parseCSV(txt){
  const lines = txt.replace(/\r/g,'').split('\n').filter(l => l.trim().length);
  if(!lines.length) return [];
  const hdr = lines[0].split(';').map(h => h.trim());
  return lines.slice(1).map(line => {
    const c = line.split(';'); const o = {};
    hdr.forEach((h,i) => o[h] = (c[i] !== undefined ? c[i] : '').trim());
    return o;
  });
}
function parseWKT(wkt){
  if(!wkt) return null;
  return wkt.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'')
    .split(',').map(p => { const [lo,la] = p.trim().split(/\s+/).map(Number); return [la,lo]; });
}
function readZip(zipPath){
  const tmp = fs.mkdtempSync('/tmp/vtest_');
  cp.execSync(`unzip -o -q ${JSON.stringify(zipPath)} -d ${tmp}`);
  const find = n => { const h = cp.execSync(`find ${tmp} -iname ${JSON.stringify('*'+n)} | head -1`).toString().trim();
                      return h ? fs.readFileSync(h,'utf8') : null; };
  return { gps:find('gps.csv'), tel:find('telregels.csv'), net:find('netwerk.csv'), ses:find('sessie.csv') };
}

// ── build engine inputs exactly as loadPocketZip does ──
function buildInputs(z){
  const fixes = z.gps ? parseCSV(z.gps).map(r => ({
      lat:+r.lat, lon:+r.lon, acc:parseFloat(r.nauwkeurigheid)||0,
      t: r.tijdstip ? new Date(r.tijdstip).getTime() : null,
      origWay:(r.osm_way_id||'').trim()||null
    })).filter(f => !isNaN(f.lat) && !isNaN(f.lon)) : [];

  const taps = z.tel ? parseCSV(z.tel)
      .filter(r => !isNaN(parseFloat(r.lat)) && !isNaN(parseFloat(r.lon)))
      .map(r => ({ lat:parseFloat(r.lat), lon:parseFloat(r.lon),
                   t: r.tijdstip ? new Date(r.tijdstip).getTime() : null,
                   origWay:(r.osm_way_id||'').trim()||null, straat:r.straat||'' })) : [];

  // wayData per (wayId,segIdx) → reassemble per wayId (viterbiWaysForSession)
  const wd = {};
  if(z.net) parseCSV(z.net).forEach(r => {
    const wid=(r.osm_way_id||'').trim(); if(!wid) return;
    const geom=parseWKT(r.geometrie_wkt); if(!geom||geom.length<2) return;
    const segIdx=+(r.segment_index||0)||0; const k=wid+':'+segIdx;
    if(!wd[k]) wd[k]={geometry:geom, wayId:wid, segIdx:segIdx};
  });
  const bySeg={};
  Object.values(wd).forEach(w => { (bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w); });
  const ways=[];
  Object.keys(bySeg).forEach(wid => {
    const segs=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx); const g=[];
    segs.forEach(s => s.geometry.forEach((pt,idx) => {
      if(g.length && idx===0 && g[g.length-1][0]===pt[0] && g[g.length-1][1]===pt[1]) return;
      g.push(pt);
    }));
    if(g.length>=2) ways.push({wayId:wid, geometry:g});
  });
  return { fixes, taps, ways };
}

// ── link each tap to the path's wayId via nearest fix in time (reassignTaps logic) ──
function nearestFixIdx(tapT, fixes){
  let best=-1, bd=Infinity;
  for(let i=0;i<fixes.length;i++){ const ft=fixes[i].t; if(ft==null) continue;
    const d=Math.abs(ft-tapT); if(d<bd){bd=d;best=i;} }
  return best;
}

function run(zipPath, hardWays){
  const z = readZip(zipPath);
  const present = ['gps','tel','net','ses'].filter(k=>z[k]).map(k=>k+'.csv');
  console.log('ZIP:', zipPath);
  console.log('bestanden gevonden:', present.join(', ') || '(geen)');
  const { fixes, taps, ways } = buildInputs(z);
  console.log(`fixes=${fixes.length}  taps=${taps.length}  ways=${ways.length}`);
  if(!fixes.length || !ways.length){ console.log('!! onvoldoende data voor matchTopo'); return; }

  const opts = {searchRadius:40, sigmaMin:5, hop1:4, hop2:12, gamma:0.02, junctionWeight:0.08};
  const res = Viterbi.matchTopo(fixes, ways, opts);
  const path = res.path;

  // path continuity
  let nSwitch=0, nNull=0;
  for(let i=0;i<path.length;i++){ if(!path[i]) nNull++;
    if(i && path[i] && path[i-1] && path[i]!==path[i-1]) nSwitch++; }
  // emission quality = mean projected distance of fixes onto their matched way
  const geomById={}; ways.forEach(w=>geomById[w.wayId]=w.geometry);
  let dsum=0, dn=0;
  for(let i=0;i<fixes.length;i++){ const wid=path[i]; if(!wid||!geomById[wid]) continue;
    const pr=Viterbi.projectFull(fixes[i].lat,fixes[i].lon,geomById[wid]); dsum+=pr.dist; dn++; }
  console.log('\n── trajectorie ──');
  console.log(`way-wissels langs pad: ${nSwitch}   (lager = continuer)`);
  console.log(`fixes zonder match: ${nNull}/${path.length}`);
  console.log(`gem. snap-afstand fix→toegewezen way: ${dn?(dsum/dn).toFixed(2):'n/a'} m`);

  // tap reassignment: field-snap (origWay) vs Viterbi
  const haveTimes = fixes.some(f=>f.t!=null) && taps.some(t=>t.t!=null);
  let changed=0, same=0, lost=0; const flowOrig={}, flowNew={};
  const splitByOrig={}; // origWay → { assignedWay → count }
  taps.forEach(tp => {
    let wid=null;
    if(haveTimes && tp.t!=null){ const fi=nearestFixIdx(tp.t,fixes); if(fi>=0) wid=path[fi]; }
    if(wid==null){ // fallback: nearest way by projection
      let bd=Infinity; ways.forEach(w=>{const pr=Viterbi.projectFull(tp.lat,tp.lon,w.geometry); if(pr.dist<bd){bd=pr.dist;wid=w.wayId;}});
    }
    flowOrig[tp.origWay||'∅']=(flowOrig[tp.origWay||'∅']||0)+1;
    flowNew[wid||'∅']=(flowNew[wid||'∅']||0)+1;
    if(wid==null) lost++; else if(wid===tp.origWay) same++; else changed++;
    const ok=tp.origWay||'∅'; (splitByOrig[ok]=splitByOrig[ok]||{}); splitByOrig[ok][wid||'∅']=(splitByOrig[ok][wid||'∅']||0)+1;
  });
  console.log('\n── tik-hertoekenning ──');
  console.log(`tijdkoppeling beschikbaar: ${haveTimes?'ja':'nee (projectie-fallback)'}`);
  console.log(`onveranderd=${same}  verplaatst=${changed}  zonder match=${lost}  (van ${taps.length})`);

  // convergent-way focus
  if(hardWays && hardWays.length){
    console.log('\n── convergente ways (de irreducibele rest) ──');
    hardWays.forEach(w => {
      const asOrig = flowOrig[w]||0, asNew = flowNew[w]||0;
      const split = splitByOrig[w];
      console.log(`way ${w}: field-snap=${asOrig} tikken → Viterbi verdeelt als ${split?JSON.stringify(split):'—'} ; Viterbi-totaal op deze way=${asNew}`);
    });
    console.log('\nInterpretatie: als field-snap-tikken van één hard-way bij Viterbi op ÉÉN doel-way landen');
    console.log('(i.p.v. gesplitst), dan lost de trajectorie-continuïteit de sub-meter-ambiguïteit op.');
  }
}

const zip = process.argv[2];
const hard = (process.argv[3]||'130419432,136079346,130418057').split(',').map(s=>s.trim()).filter(Boolean);
if(!zip){ console.log('gebruik: node vtest.js <sessie.zip> [hardWays]'); process.exit(1); }
run(zip, hard);
