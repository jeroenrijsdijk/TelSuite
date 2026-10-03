'use strict';
const fs=require('fs'),cp=require('child_process'),V=require('./viterbi_engine.js');
function pCSV(t){const L=t.replace(/\r/g,'').split('\n').filter(l=>l.trim().length);if(!L.length)return[];const h=L[0].split(';').map(s=>s.trim());return L.slice(1).map(l=>{const c=l.split(';'),o={};h.forEach((k,i)=>o[k]=(c[i]||'').trim());return o;});}
function pWKT(w){if(!w)return null;return w.replace(/^LINESTRING\s*\(/i,'').replace(/\)$/,'').split(',').map(p=>{const[lo,la]=p.trim().split(/\s+/).map(Number);return[la,lo];});}
function load(zip){const T=fs.mkdtempSync('/tmp/vb_');cp.execSync(`unzip -o -q ${JSON.stringify(zip)} -d ${T}`);
  const rd=n=>{const h=cp.execSync(`find ${T} -iname ${JSON.stringify('*'+n)}|head -1`).toString().trim();return h?fs.readFileSync(h,'utf8'):null;};
  const ses=pCSV(rd('sessie.csv'))[0]||{};
  const rows=pCSV(rd('telregels.csv'));
  const fixes=pCSV(rd('gps.csv')).map(r=>({lat:+r.lat,lon:+r.lon,acc:parseFloat(r.nauwkeurigheid)||0,t:r.tijdstip?new Date(r.tijdstip).getTime():null})).filter(f=>!isNaN(f.lat));
  const wd={};pCSV(rd('netwerk.csv')).forEach(r=>{const wid=(r.osm_way_id||'').trim();if(!wid)return;const g=pWKT(r.geometrie_wkt);if(!g||g.length<2)return;const si=+(r.segment_index||0)||0,k=wid+':'+si;if(!wd[k])wd[k]={geometry:g,wayId:wid,segIdx:si};});
  const bySeg={};Object.values(wd).forEach(w=>{(bySeg[w.wayId]=bySeg[w.wayId]||[]).push(w);});
  const ways=[];Object.keys(bySeg).forEach(wid=>{const s=bySeg[wid].sort((a,b)=>a.segIdx-b.segIdx),g=[];s.forEach(x=>x.geometry.forEach((pt,i)=>{if(g.length&&i===0&&g[g.length-1][0]===pt[0]&&g[g.length-1][1]===pt[1])return;g.push(pt);}));if(g.length>=2)ways.push({wayId:wid,geometry:g});});
  return {ses,rows,fixes,ways};
}
function cov(fixes,ways,R,h1,h2){if(!fixes.length||!ways.length)return{m:0,sw:0,n:fixes.length};const res=V.matchTopo(fixes,ways,{searchRadius:R,sigmaMin:5,hop1:h1,hop2:h2,gamma:0.02,junctionWeight:0.08});let m=0,sw=0;for(let i=0;i<res.path.length;i++){if(res.path[i])m++;if(i&&res.path[i]&&res.path[i-1]&&res.path[i]!==res.path[i-1])sw++;}return{m,sw,n:fixes.length};}
const TYPES=['car','truck','moto','bike','ped','tegemoet','stilstaand','other'];
process.argv.slice(2).forEach(zip=>{
  const name=zip.split('/').pop().replace('.zip','');
  const {ses,rows,fixes,ways}=load(zip);
  const dur=ses.start_tijd&&ses.eind_tijd?((new Date('2026-01-01T'+ses.eind_tijd)-new Date('2026-01-01T'+ses.start_tijd))/60000).toFixed(1):'?';
  console.log(`\n════ ${name} · ${ses.modus||ses.type} · ${dur} min · ${rows.length} tikken · fixes=${fixes.length} ways=${ways.length}`);
  // telling
  if((ses.modus||ses.type)==='winkelstraat'){
    const c={};const sp=[];rows.forEach(r=>{c[r.type]=(c[r.type]||0)+1;const s=parseFloat(r.snelheid);if(!isNaN(s))sp.push(s);});
    console.log('  telling: '+Object.keys(c).map(k=>`${k}=${c[k]}`).join('  '));
    if(sp.length){sp.sort((a,b)=>a-b);console.log(`  waarnemersnelheid (m/s): min ${sp[0].toFixed(2)}  mediaan ${sp[Math.floor(sp.length/2)].toFixed(2)}  max ${sp[sp.length-1].toFixed(2)}`);}
  } else {
    // transect/simpel: type × richting
    const m={};rows.forEach(r=>{const t=r.type||'?',d=r.richting||'-';m[t]=m[t]||{a:0,b:0,'-':0};m[t][d]=(m[t][d]||0)+1;});
    const la=ses.richting_a||'A',lb=ses.richting_b||'B';
    console.log(`  telling (type × richting):   A = ${la}   B = ${lb}`);
    TYPES.forEach(t=>{if(m[t]){const r=m[t];console.log(`    ${t.padEnd(10)} A=${r.a||0}  B=${r.b||0}${r['-']?'  (zonder richting='+r['-']+')':''}`);}});
  }
  // snap coverage
  const c40=cov(fixes,ways,40,4,12), c60=cov(fixes,ways,60,6,20);
  console.log(`  snap: R40 ${c40.m}/${c40.n} gematcht · R60 ${c60.m}/${c60.n} gematcht · R60-wissels ${c60.sw}`);
});
