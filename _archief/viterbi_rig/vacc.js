'use strict';
const fs=require('fs'),cp=require('child_process'),V=require('./viterbi_engine.js');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function pWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
function ways_of(rd){const wd={};pCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=pWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0,k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});const bs={};Object.values(wd).forEach(w=>{(bs[w.wayId]=bs[w.wayId]||[]).push(w);});const ways=[];Object.keys(bs).forEach(wid=>{const s=bs[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];s.forEach(x=>x.geometry.forEach((pt,i)=>{if(g.length&&i===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});return ways;}
const med=a=>{const s=[...a].sort((x,y)=>x-y);return s.length?s[Math.floor(s.length/2)]:NaN;};
process.argv.slice(2).forEach(zip=>{
  const name=zip.split('/').pop().replace('.zip','').replace('20260616_','').replace('_pkt','');
  const T=fs.mkdtempSync('/tmp/va_');cp.execSync(`unzip -o -q ${JSON.stringify(zip)} -d ${T}`);
  const rd=n=>{const h=cp.execSync(`find ${T} -iname ${JSON.stringify('*'+n)}|head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
  const rows=pCSV(rd('gps.csv'));
  const ways=ways_of(rd);
  const f=rows.map(r=>({lat:+r.lat,lon:+r.lon,acc:parseFloat(r.nauwkeurigheid)||0,t:r.tijdstip?new Date(r.tijdstip).getTime():null})).filter(x=>!isNaN(x.lat));
  f.forEach((x,i)=>{let b=Infinity;for(const w of ways){const pr=V.projectFull(x.lat,x.lon,w.geometry);if(pr.dist<b)b=pr.dist;}x.dist=b;x.dt=i&&x.t&&f[i-1].t?(x.t-f[i-1].t)/1000:null;});
  const off=f.filter(x=>x.dist>40), on=f.filter(x=>x.dist<=40);
  const dts=f.map(x=>x.dt).filter(x=>x!=null);
  console.log(`\n════ ${name} ════  fixes=${f.length}`);
  console.log(`  ON-netwerk (≤40m):  n=${on.length}  med nauwkeurigheid=${med(on.map(x=>x.acc)).toFixed(0)}m`);
  console.log(`  OFF-netwerk (>40m): n=${off.length}  med nauwkeurigheid=${med(off.map(x=>x.acc)).toFixed(0)}m`);
  console.log(`  tijdgaten tussen fixes: med ${med(dts).toFixed(0)}s  max ${Math.max(...dts).toFixed(0)}s`);
  console.log(`  per-fix (dt s | nauwk m | dichtstbij-way m):`);
  console.log('   '+f.map(x=>`${x.dt==null?'  -':String(Math.round(x.dt)).padStart(3)}|${String(Math.round(x.acc)).padStart(4)}|${String(Math.round(x.dist)).padStart(3)}${x.dist>40?'*':' '}`).join('  '));
});
