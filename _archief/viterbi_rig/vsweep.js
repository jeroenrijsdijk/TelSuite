'use strict';
const fs=require('fs'),cp=require('child_process'),Viterbi=require('./viterbi_engine.js');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function pWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
const tmp=fs.mkdtempSync('/tmp/vs_');cp.execSync(`unzip -o -q ${JSON.stringify(process.argv[2])} -d ${tmp}`);
const rd=n=>{const h=cp.execSync(`find ${tmp} -iname ${JSON.stringify('*'+n)}|head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
const fixes=pCSV(rd('gps.csv')).map(r=>({lat:+r.lat,lon:+r.lon,acc:parseFloat(r.nauwkeurigheid)||0,t:r.tijdstip?new Date(r.tijdstip).getTime():null})).filter(f=>!isNaN(f.lat));
const wd={};pCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=pWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0,k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});
const bySeg={};Object.values(wd).forEach(w=>{(bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w);});
const ways=[];Object.keys(bySeg).forEach(wid=>{const s=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];s.forEach(x=>x.geometry.forEach((pt,i)=>{if(g.length&&i===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});
console.log(`fixes=${fixes.length} ways=${ways.length}\n`);
function stats(name,res){let m=0,sw=0;for(let i=0;i<res.path.length;i++){if(res.path[i])m++;if(i&&res.path[i]&&res.path[i-1]&&res.path[i]!==res.path[i-1])sw++;}
  console.log(`${name.padEnd(34)} gematcht=${m}/${fixes.length}  null=${fixes.length-m}  wissels=${sw}`);}
stats('topo reassignTaps (jw=0.08)',Viterbi.matchTopo(fixes,ways,{searchRadius:40,sigmaMin:5,hop1:4,hop2:12,gamma:0.02,junctionWeight:0.08}));
stats('topo runViterbi (adjTol=2.0)',Viterbi.matchTopo(fixes,ways,{searchRadius:40,sigmaMin:5,hop1:4,hop2:12,gamma:0.02,adjTol:2.0}));
stats('topo wijd (R=60,hop6/20)',Viterbi.matchTopo(fixes,ways,{searchRadius:60,sigmaMin:5,hop1:6,hop2:20,gamma:0.02,junctionWeight:0.08}));
stats('topo R=40 hop8/24',Viterbi.matchTopo(fixes,ways,{searchRadius:40,sigmaMin:5,hop1:8,hop2:24,gamma:0.02,junctionWeight:0.08}));
try{stats('plain match (beta=10)',Viterbi.match(fixes,ways,{searchRadius:40,sigmaMin:5,beta:10,maxRouteDist:250}));}catch(e){console.log('plain match: ERR '+e.message);}
