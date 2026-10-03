var Viterbi = (function () {
  'use strict';
  var LAT_M = 111320;
  function lonM(lat){ return LAT_M * Math.cos(lat*Math.PI/180); }
  function haversineM(la1,lo1,la2,lo2){ var lm=lonM((la1+la2)/2); return Math.hypot((lo2-lo1)*lm,(la2-la1)*LAT_M); }

  // Volledige projectie: afstand + welke edge (seg) + fractie t + snap-punt.
  function projectFull(plat, plon, geometry){
    var lm=lonM(geometry[0][0]); var px=plon*lm, py=plat*LAT_M;
    var best=Infinity,bestSeg=0,bestT=0,bestLat=geometry[0][0],bestLon=geometry[0][1];
    for (var i=0;i<geometry.length-1;i++){
      var ax=geometry[i][1]*lm, ay=geometry[i][0]*LAT_M;
      var bx=geometry[i+1][1]*lm, by=geometry[i+1][0]*LAT_M;
      var dx=bx-ax, dy=by-ay, len2=dx*dx+dy*dy;
      var t=(len2===0)?0:Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/len2));
      var cx=ax+t*dx, cy=ay+t*dy, d=Math.hypot(px-cx,py-cy);
      if (d<best){ best=d; bestSeg=i; bestT=t; bestLat=cy/LAT_M; bestLon=cx/lm; }
    }
    return { dist:best, seg:bestSeg, t:bestT, lat:bestLat, lon:bestLon };
  }

  // Vertex-graaf uit way-geometrieën; gedeelde eindpunten (binnen nodeTol m)
  // worden dezelfde knoop -> ways die een OSM-knoop delen raken verbonden.
  function buildGraph(ways, nodeTol){
    nodeTol=nodeTol||1.5;
    var nodes=[], adj=[], grid={}, cell=Math.max(nodeTol,0.5);
    function getNode(lat,lon){
      var gy=Math.round(lat*LAT_M/cell), gx=Math.round(lon*lonM(lat)/cell);
      for (var dy=-1;dy<=1;dy++) for (var dx=-1;dx<=1;dx++){
        var b=grid[(gx+dx)+','+(gy+dy)]; if(!b) continue;
        for (var i=0;i<b.length;i++){ var n=nodes[b[i]]; if(haversineM(lat,lon,n.lat,n.lon)<=nodeTol) return b[i]; }
      }
      var id=nodes.length; nodes.push({lat:lat,lon:lon}); adj.push([]);
      var k=gx+','+gy; (grid[k]=grid[k]||[]).push(id); return id;
    }
    function addEdge(a,b,w){ if(a===b) return; adj[a].push({to:b,w:w}); adj[b].push({to:a,w:w}); }
    var wayNodeIds={};
    ways.forEach(function(way){
      var g=way.geometry, prev=getNode(g[0][0],g[0][1]), ids=[prev];
      for (var i=1;i<g.length;i++){ var cur=getNode(g[i][0],g[i][1]);
        addEdge(prev,cur,haversineM(g[i-1][0],g[i-1][1],g[i][0],g[i][1])); ids.push(cur); prev=cur; }
      wayNodeIds[way.wayId]=ids;
    });
    return { nodes:nodes, adj:adj, wayNodeIds:wayNodeIds };
  }

  function dijkstraFrom(graph, src, maxDist){
    var dist=new Float64Array(graph.nodes.length); dist.fill(Infinity); dist[src]=0;
    var heap=[{n:src,d:0}];
    function push(x){ heap.push(x); var i=heap.length-1; while(i>0){var p=(i-1)>>1; if(heap[p].d<=heap[i].d)break; var t=heap[p];heap[p]=heap[i];heap[i]=t;i=p;} }
    function pop(){ var top=heap[0],last=heap.pop(); if(heap.length){heap[0]=last;var i=0,n=heap.length; for(;;){var l=2*i+1,r=l+1,s=i; if(l<n&&heap[l].d<heap[s].d)s=l; if(r<n&&heap[r].d<heap[s].d)s=r; if(s===i)break; var t=heap[s];heap[s]=heap[i];heap[i]=t;i=s;}} return top; }
    while(heap.length){ var cur=pop(); if(cur.d>dist[cur.n])continue; if(cur.d>maxDist)continue;
      var E=graph.adj[cur.n]; for(var e=0;e<E.length;e++){ var nd=cur.d+E[e].w; if(nd<dist[E[e].to]){dist[E[e].to]=nd; push({n:E[e].to,d:nd});} } }
    return dist;
  }

  // Route-afstand tussen twee snap-punten (elk op edge `seg`, fractie t).
  function snapToSnapDist(graph, prev, cur, distFromNode){
    var sIds=graph.wayNodeIds[prev.wayId], dIds=graph.wayNodeIds[cur.wayId];
    if(!sIds||!dIds) return Infinity;
    var sA=sIds[prev.seg], sB=sIds[prev.seg+1], dA=dIds[cur.seg], dB=dIds[cur.seg+1];
    var sLen=haversineM(graph.nodes[sA].lat,graph.nodes[sA].lon,graph.nodes[sB].lat,graph.nodes[sB].lon);
    var dLen=haversineM(graph.nodes[dA].lat,graph.nodes[dA].lon,graph.nodes[dB].lat,graph.nodes[dB].lon);
    if(sA===dA&&sB===dB) return Math.abs(cur.t-prev.t)*sLen;
    var sToA=prev.t*sLen, sToB=(1-prev.t)*sLen, dToA=cur.t*dLen, dToB=(1-cur.t)*dLen;
    var dFromA=distFromNode[sA], dFromB=distFromNode[sB], best=Infinity;
    best=Math.min(best, sToA+dFromA[dA]+dToA);
    best=Math.min(best, sToA+dFromA[dB]+dToB);
    best=Math.min(best, sToB+dFromB[dA]+dToA);
    best=Math.min(best, sToB+dFromB[dB]+dToB);
    return best;
  }

  // Way-niveau adjacency op EXACTE gedeelde knopen. Een gedeelde OSM-knoop
  // verschijnt als identieke coordinaat (6 decimalen) in beide ways — Overpass
  // schrijft de knoop één keer en beide ways verwijzen ernaar. Dus een exacte
  // string-match op afgeronde coordinaten is functioneel gelijk aan node-ID-
  // matching: zuiverder dan een afstandstolerantie (geen false merges van ways
  // die toevallig dicht langs elkaar lopen). Dit brengt telrapport op het
  // kennisniveau van pocket, dat de echte node-ID's gebruikt.
  // Retourneert { adj, junctions } waarbij junctions["A|B"] de gedeelde
  // knoop-coordinaten bevat (voor junction-aware transitiekosten).
  function buildWayAdjacency(ways){
    function key(lat,lon){ return lat.toFixed(6)+','+lon.toFixed(6); }
    var vToWays={};
    ways.forEach(function(w){
      var seen={};
      w.geometry.forEach(function(p){
        var k=key(p[0],p[1]);
        if(!seen[k]){ seen[k]=1; (vToWays[k]=vToWays[k]||[]).push(w.wayId); }
      });
    });
    var adj={}; ways.forEach(function(w){ adj[w.wayId]={}; });
    var junctions={};
    Object.keys(vToWays).forEach(function(k){
      var arr=vToWays[k]; if(arr.length<2) return;
      var parts=k.split(','), J=[parseFloat(parts[0]), parseFloat(parts[1])];
      for (var i=0;i<arr.length;i++) for (var j=i+1;j<arr.length;j++){
        adj[arr[i]][arr[j]]=true; adj[arr[j]][arr[i]]=true;
        (junctions[arr[i]+'|'+arr[j]]=junctions[arr[i]+'|'+arr[j]]||[]).push(J);
        (junctions[arr[j]+'|'+arr[i]]=junctions[arr[j]+'|'+arr[i]]||[]).push(J);
      }
    });
    return { adj:adj, junctions:junctions };
  }

  // Hop-klasse tussen twee ways: 0 = zelfde, 1 = gedeelde knoop, 2 = twee sprongen,
  // Infinity = verder/niet verbonden. De eerste check (gedeelde knoop) is de
  // beslissende in stedelijk gebied.
  function hopClass(adj, a, b){
    if(a===b) return 0;
    if(adj[a] && adj[a][b]) return 1;
    if(adj[a]){ for (var m in adj[a]) if(adj[m] && adj[m][b]) return 2; }
    return Infinity;
  }

  function match(fixes, ways, opts){
    opts=opts||{};
    var searchRadius=opts.searchRadius||40, sigmaMin=opts.sigmaMin||5,
        beta=opts.beta||10, maxRouteDist=opts.maxRouteDist||200, nodeTol=opts.nodeTol||1.5;
    var graph=buildGraph(ways,nodeTol);

    var cols=[];
    for (var i=0;i<fixes.length;i++){
      var sigma=Math.max(sigmaMin, fixes[i].acc||sigmaMin), cands=[];
      for (var w=0;w<ways.length;w++){
        var pr=projectFull(fixes[i].lat,fixes[i].lon,ways[w].geometry);
        if (pr.dist<=searchRadius){ var z=pr.dist/sigma;
          cands.push({wayId:ways[w].wayId,dist:pr.dist,seg:pr.seg,t:pr.t,plat:pr.lat,plon:pr.lon,emit:0.5*z*z}); }
      }
      cols.push(cands);
    }

    var V=[], back=[];
    for (var col=0;col<cols.length;col++){
      V[col]={}; back[col]={};
      var cands2=cols[col];
      if (col===0){ for(var a=0;a<cands2.length;a++) V[0][cands2[a].wayId]=cands2[a].emit; continue; }
      var prevCands=cols[col-1];
      var gpsStep=haversineM(fixes[col-1].lat,fixes[col-1].lon,fixes[col].lat,fixes[col].lon);
      var distFromNode={};
      function ensure(nodeId){ if(!distFromNode[nodeId]) distFromNode[nodeId]=dijkstraFrom(graph,nodeId,maxRouteDist); }
      for (var p=0;p<prevCands.length;p++){ if(V[col-1][prevCands[p].wayId]===undefined)continue;
        var si=graph.wayNodeIds[prevCands[p].wayId]; if(!si)continue; ensure(si[prevCands[p].seg]); ensure(si[prevCands[p].seg+1]); }
      for (var c=0;c<cands2.length;c++){
        var cur=cands2[c], bestCost=Infinity, bestPrev=null;
        for (var pp=0;pp<prevCands.length;pp++){
          var prev=prevCands[pp]; if(V[col-1][prev.wayId]===undefined)continue;
          var routeD=snapToSnapDist(graph,prev,cur,distFromNode);
          if(!isFinite(routeD))continue;
          var tot=V[col-1][prev.wayId]+Math.abs(routeD-gpsStep)/beta;
          if(tot<bestCost){bestCost=tot;bestPrev=prev.wayId;}
        }
        if(bestPrev!==null){ V[col][cur.wayId]=bestCost+cur.emit; back[col][cur.wayId]=bestPrev; }
      }
      if (Object.keys(V[col]).length===0){ // gap-vangnet: herstart keten
        for (var g2=0;g2<cands2.length;g2++){ V[col][cands2[g2].wayId]=cands2[g2].emit; back[col][cands2[g2].wayId]=null; }
      }
    }

    var path=new Array(cols.length).fill(null), last=cols.length-1;
    while(last>=0 && Object.keys(V[last]).length===0) last--;
    if(last<0) return {path:path, candidates:cols, graph:graph};
    var bestEnd=null, bestEndCost=Infinity;
    for (var ww in V[last]) if(V[last][ww]<bestEndCost){bestEndCost=V[last][ww];bestEnd=ww;}
    path[last]=bestEnd;
    for (var col2=last;col2>0;col2--){ var pv=back[col2][path[col2]]; path[col2-1]=(pv==null)?null:pv; }
    return { path:path, candidates:cols, graph:graph,
             stats:{nFixes:fixes.length,nWays:ways.length,nNodes:graph.nodes.length} };
  }

  // Topologie-eerst variant: de transitiekost wordt primair bepaald door de
  // hop-klasse (gedeelde knoop = sterkste indicatie), met een lichte metrische
  // verfijning binnen een klasse. Lexicografisch: topologie zet de grove
  // structuur, meters kiezen tussen even-aangrenzende buren.
  // Junction-aware: een hop-1-overstap naar een zijweg wordt extra bestraft naar
  // rato van hoe ver je snap-punt nog van de gedeelde knoop af zit — overstappen
  // is pas logisch als je de aftakking nadert.
  // opts: { searchRadius=40, sigmaMin=5, hop1=4, hop2=12, gamma=0.02, junctionWeight=0.08 }
  function matchTopo(fixes, ways, opts){
    opts=opts||{};
    var searchRadius=opts.searchRadius||40, sigmaMin=opts.sigmaMin||5;
    var HOP1=(opts.hop1!=null)?opts.hop1:4, HOP2=(opts.hop2!=null)?opts.hop2:12;
    var gamma=(opts.gamma!=null)?opts.gamma:0.02;
    var JW=(opts.junctionWeight!=null)?opts.junctionWeight:0.08;
    var built=buildWayAdjacency(ways);
    var adj=built.adj, junctions=built.junctions;

    var cols=[];
    for (var i=0;i<fixes.length;i++){
      var sigma=Math.max(sigmaMin, fixes[i].acc||sigmaMin), cands=[];
      for (var w=0;w<ways.length;w++){
        var pr=projectFull(fixes[i].lat,fixes[i].lon,ways[w].geometry);
        if (pr.dist<=searchRadius){ var z=pr.dist/sigma;
          cands.push({wayId:ways[w].wayId,dist:pr.dist,plat:pr.lat,plon:pr.lon,emit:0.5*z*z}); }
      }
      cols.push(cands);
    }

    var V=[], back=[];
    for (var col=0;col<cols.length;col++){
      V[col]={}; back[col]={};
      var cur=cols[col];
      if(col===0){ for(var a=0;a<cur.length;a++) V[0][cur[a].wayId]=cur[a].emit; continue; }
      var prev=cols[col-1];
      var gpsStep=haversineM(fixes[col-1].lat,fixes[col-1].lon,fixes[col].lat,fixes[col].lon);
      for (var c=0;c<cur.length;c++){
        var cw=cur[c], bestCost=Infinity, bestPrev=null;
        for (var p=0;p<prev.length;p++){
          var pw=prev[p]; if(V[col-1][pw.wayId]===undefined) continue;
          var hc=hopClass(adj, pw.wayId, cw.wayId);
          if(!isFinite(hc)) continue;                 // >2 hops / niet verbonden -> verboden
          var base = (hc===0)?0 : (hc===1)?HOP1 : HOP2;
          var projStep=haversineM(pw.plat,pw.plon,cw.plat,cw.plon);
          var refine=gamma*Math.abs(projStep-gpsStep);  // fijnregeling binnen klasse
          // junction-aware: straf een hop-1-overstap naar rato van afstand tot de
          // gedeelde knoop — overstappen is pas logisch bij de aftakking.
          var jpen=0;
          if(hc===1 && JW>0){
            var js=junctions[pw.wayId+'|'+cw.wayId];
            if(js){ var nd=Infinity;
              for (var jx=0;jx<js.length;jx++){ var d=haversineM(pw.plat,pw.plon,js[jx][0],js[jx][1]); if(d<nd) nd=d; }
              jpen=JW*nd;
            }
          }
          var tot=V[col-1][pw.wayId]+base+refine+jpen;
          if(tot<bestCost){ bestCost=tot; bestPrev=pw.wayId; }
        }
        if(bestPrev!==null){ V[col][cw.wayId]=bestCost+cw.emit; back[col][cw.wayId]=bestPrev; }
      }
      if(Object.keys(V[col]).length===0){ // gap-vangnet
        for (var g2=0;g2<cur.length;g2++){ V[col][cur[g2].wayId]=cur[g2].emit; back[col][cur[g2].wayId]=null; }
      }
    }

    var path=new Array(cols.length).fill(null), last=cols.length-1;
    while(last>=0 && Object.keys(V[last]).length===0) last--;
    if(last<0) return { path:path, candidates:cols };
    var bestEnd=null, bestEndCost=Infinity;
    for (var ww in V[last]) if(V[last][ww]<bestEndCost){ bestEndCost=V[last][ww]; bestEnd=ww; }
    path[last]=bestEnd;
    for (var col2=last;col2>0;col2--){ var pv=back[col2][path[col2]]; path[col2-1]=(pv==null)?null:pv; }
    return { path:path, candidates:cols, adj:adj,
             stats:{nFixes:fixes.length, nWays:ways.length} };
  }

  return { match:match, matchTopo:matchTopo, projectFull:projectFull };
})();
module.exports = Viterbi;
