'use strict';
const fs=require('fs'),cp=require('child_process');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
const LATM=111320,lonM=l=>LATM*Math.cos(l*Math.PI/180);
function dM(a,b){const dy=(a[0]-b[0])*LATM,dx=(a[1]-b[1])*lonM((a[0]+b[0])/2);return Math.hypot(dx,dy);}
process.argv.slice(2).forEach(zip=>{
  const name=zip.split('/').pop().replace('.zip','').replace('20260616_','').replace('_pkt','');
  const T=fs.mkdtempSync('/tmp/vsp_');cp.execSync(`unzip -o -q ${JSON.stringify(zip)} -d ${T}`);
  const g=cp.execSync(`find ${T} -iname '*gps.csv'|head -1`).toString().trim();
  const pts=pCSV(fs.readFileSync(g,'utf8')).map(r=>[+r.lat,+r.lon]).filter(p=>!isNaN(p[0]));
  let path=0;for(let i=1;i<pts.length;i++)path+=dM(pts[i-1],pts[i]);
  const las=pts.map(p=>p[0]),los=pts.map(p=>p[1]);
  const diag=dM([Math.min(...las),Math.min(...los)],[Math.max(...las),Math.max(...los)]);
  console.log(`${name.padEnd(8)} fixes=${String(pts.length).padStart(3)}  bbox-diagonaal=${diag.toFixed(0).padStart(4)} m  padlengte=${path.toFixed(0).padStart(4)} m  → ${diag<25?'≈ STILSTAAND':'bewoog'}`);
});
