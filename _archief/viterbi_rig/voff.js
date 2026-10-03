'use strict';
const fs=require('fs'),cp=require('child_process'),V=require('./viterbi_engine.js');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function pWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
function ways_of(rd){const wd={};pCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=pWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0,k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});const bySeg={};Object.values(wd).forEach(w=>{(bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w);});const ways=[];Object.keys(bySeg).forEach(wid=>{const s=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];s.forEach(x=>x.geometry.forEach((pt,i)=>{if(g.length&&i===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});return ways;}
process.argv.slice(2).forEach(zip=>{
  const name=zip.split('/').pop().replace('.zip','').replace('20260616_','').replace('_pkt','');
  const T=fs.mkdtempSync('/tmp/vo_');cp.execSync(`unzip -o -q ${JSON.stringify(zip)} -d ${T}`);
  const rd=n=>{const h=cp.execSync(`find ${T} -iname ${JSON.stringify('*'+n)}|head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
  const fixes=pCSV(rd('gps.csv')).map(r=>({lat:+r.lat,lon:+r.lon})).filter(f=>!isNaN(f.lat));
  const ways=ways_of(rd);
  const nd=fixes.map(f=>{let b=Infinity;for(const w of ways){const pr=V.projectFull(f.lat,f.lon,w.geometry);if(pr.dist<b)b=pr.dist;}return b;});
  const within40=nd.filter(d=>d<=40).length, off=nd.filter(d=>d>40).length;
  const s=[...nd].sort((a,b)=>a-b),q=p=>s[Math.floor(p*(s.length-1))];
  console.log(`${name.padEnd(8)}  fixes=${String(fixes.length).padStart(3)}  binnen40m=${String(within40).padStart(3)}  OFF-NETWERK(>40m)=${String(off).padStart(3)}  | dichtstbij-way: med ${q(.5).toFixed(0)}m  p90 ${q(.9).toFixed(0)}m  max ${q(1).toFixed(0)}m`);
});
