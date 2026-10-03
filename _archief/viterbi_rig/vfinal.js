'use strict';
const fs=require('fs'),cp=require('child_process'),V=require('./viterbi_engine.js');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function pWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
const tmp=fs.mkdtempSync('/tmp/vf_');cp.execSync(`unzip -o -q ${JSON.stringify(process.argv[2])} -d ${tmp}`);
const rd=n=>{const h=cp.execSync(`find ${tmp} -iname ${JSON.stringify('*'+n)}|head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
const fixes=pCSV(rd('gps.csv')).map(r=>({lat:+r.lat,lon:+r.lon,acc:parseFloat(r.nauwkeurigheid)||0,t:r.tijdstip?new Date(r.tijdstip).getTime():null})).filter(f=>!isNaN(f.lat));
const taps=pCSV(rd('telregels.csv')).filter(r=>!isNaN(parseFloat(r.lat))).map(r=>({lat:parseFloat(r.lat),lon:parseFloat(r.lon),t:r.tijdstip?new Date(r.tijdstip).getTime():null,origWay:(r.osm_way_id||'').trim()||null}));
const wd={};pCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=pWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0,k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});
const bySeg={};Object.values(wd).forEach(w=>{(bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w);});
const ways=[];Object.keys(bySeg).forEach(wid=>{const s=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];s.forEach(x=>x.geometry.forEach((pt,i)=>{if(g.length&&i===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});
const res=V.matchTopo(fixes,ways,{searchRadius:60,sigmaMin:5,hop1:6,hop2:20,gamma:0.02,junctionWeight:0.08});
const path=res.path;let m=0;for(const w of path)if(w)m++;
console.log(`[R=60]  gematcht=${m}/${fixes.length}`);
function nf(t){let b=-1,bd=Infinity;for(let i=0;i<fixes.length;i++){if(fixes[i].t==null)continue;const d=Math.abs(fixes[i].t-t);if(d<bd){bd=d;b=i;}}return b;}
let same=0,moved=0,fb=0;const mv={},trio={'130419432':{},'136079346':{},'130418057':{}};
taps.forEach(tp=>{const fi=tp.t!=null?nf(tp.t):-1;const wid=fi>=0?path[fi]:null;
  if(wid==null){fb++;return;}
  if(wid===tp.origWay)same++;else{moved++;const k=tp.origWay+' → '+wid;mv[k]=(mv[k]||0)+1;}
  if(trio[tp.origWay])trio[tp.origWay][wid]=(trio[tp.origWay][wid]||0)+1;});
console.log(`eerlijke tik-vergelijking: beoordeeld=${same+moved}  onveranderd=${same}  verplaatst=${moved}  fallback=${fb}`);
console.log('verplaatsingen:');Object.keys(mv).sort((a,b)=>mv[b]-mv[a]).forEach(k=>console.log('   '+k+': '+mv[k]));
console.log('convergente trio (field-snap-way → waar Viterbi de tikken legt):');
Object.keys(trio).forEach(w=>console.log(`   ${w}: ${JSON.stringify(trio[w])}`));
