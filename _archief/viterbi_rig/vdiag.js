// vdiag.js — diepere diagnose op de matchTopo-output.
'use strict';
const fs=require('fs'), cp=require('child_process');
const Viterbi=require('./viterbi_engine.js');
function parseCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];
  const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function parseWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
const tmp=fs.mkdtempSync('/tmp/vd_');
cp.execSync(`unzip -o -q ${JSON.stringify(process.argv[2])} -d ${tmp}`);
const rd=n=>{const h=cp.execSync(`find ${tmp} -iname ${JSON.stringify('*'+n)} | head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
const fixes=parseCSV(rd('gps.csv')).map(r=>({lat:+r.lat,lon:+r.lon,acc:parseFloat(r.nauwkeurigheid)||0,t:r.tijdstip?new Date(r.tijdstip).getTime():null,origWay:(r.osm_way_id||'').trim()||null})).filter(f=>!isNaN(f.lat));
const taps=parseCSV(rd('telregels.csv')).filter(r=>!isNaN(parseFloat(r.lat))).map(r=>({lat:parseFloat(r.lat),lon:parseFloat(r.lon),t:r.tijdstip?new Date(r.tijdstip).getTime():null,origWay:(r.osm_way_id||'').trim()||null}));
const wd={};parseCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=parseWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0;const k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});
const bySeg={};Object.values(wd).forEach(w=>{(bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w);});
const ways=[];Object.keys(bySeg).forEach(wid=>{const segs=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];segs.forEach(s=>s.geometry.forEach((pt,idx)=>{if(g.length&&idx===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});

const SR=40;
// per-fix kandidaten binnen searchRadius
const cand=fixes.map(f=>{let n=0,best=Infinity;for(const w of ways){const pr=Viterbi.projectFull(f.lat,f.lon,w.geometry);if(pr.dist<=SR)n++;if(pr.dist<best)best=pr.dist;}return{n,best};});
const res=Viterbi.matchTopo(fixes,ways,{searchRadius:40,sigmaMin:5,hop1:4,hop2:12,gamma:0.02,junctionWeight:0.08});
const path=res.path;

let null0=0,nullHad=0,matched=0;
for(let i=0;i<fixes.length;i++){if(path[i]){matched++;continue;}if(cand[i].n===0)null0++;else nullHad++;}
console.log('── fix-diagnose ──');
console.log(`gematcht=${matched}  null=${fixes.length-matched}/${fixes.length}`);
console.log(`  ↳ null met 0 kandidaat-ways binnen ${SR}m (OFF-NETWERK): ${null0}`);
console.log(`  ↳ null mét kandidaten (HMM liet vallen):              ${nullHad}`);
// histogram dichtstbijzijnde-way-afstand voor de off-netwerk-nulls
const offDists=[];for(let i=0;i<fixes.length;i++)if(!path[i]&&cand[i].n===0)offDists.push(cand[i].best);
if(offDists.length){offDists.sort((a,b)=>a-b);const q=p=>offDists[Math.floor(p*(offDists.length-1))];
  console.log(`  ↳ afstand off-netwerk-fix → dichtstbijzijnde way: min ${q(0).toFixed(0)}  mediaan ${q(.5).toFixed(0)}  max ${q(1).toFixed(0)} m`);}

// eerlijke tik-vergelijking: alleen tikken waarvan de naaste fix ECHT gematcht is
function nf(t){let b=-1,bd=Infinity;for(let i=0;i<fixes.length;i++){if(fixes[i].t==null)continue;const d=Math.abs(fixes[i].t-t);if(d<bd){bd=d;b=i;}}return b;}
let realSame=0,realMoved=0,fb=0;const moves=[];
taps.forEach(tp=>{const fi=tp.t!=null?nf(tp.t):-1;const wid=fi>=0?path[fi]:null;
  if(wid==null){fb++;return;} // naaste fix ongematcht → telt niet als Viterbi-oordeel
  if(wid===tp.origWay)realSame++;else{realMoved++;moves.push({from:tp.origWay,to:wid});}});
console.log('\n── eerlijke tik-vergelijking (alleen tikken met gematchte naaste fix) ──');
console.log(`Viterbi-beoordeeld: ${realSame+realMoved} tikken  (onveranderd=${realSame}  verplaatst=${realMoved})`);
console.log(`fallback/onbeoordeeld (naaste fix off-netwerk): ${fb} tikken`);
if(moves.length){const agg={};moves.forEach(m=>{const k=m.from+' → '+m.to;agg[k]=(agg[k]||0)+1;});
  console.log('verplaatsingen:');Object.keys(agg).sort((a,b)=>agg[b]-agg[a]).forEach(k=>console.log(`   ${k}: ${agg[k]}`));}
