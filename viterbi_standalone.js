// ============================================================================
// VITERBI MAP-MATCHING — standalone module (HMM over GPS-trace)
// ----------------------------------------------------------------------------
// Newson-Krumm HMM:
//   - states  : per GPS-fix de kandidaat-ways binnen een zoekradius
//   - emission: Gaussisch op loodrechte afstand fix->way, sigma = max(sigmaMin, acc)
//   - transition: |routeDist(c,c') - gpsDist(z_i,z_{i+1})| / beta   (Newson-Krumm)
//                 routeDist = echte netwerkafstand via Dijkstra over een
//                 vertex-graaf opgebouwd uit gedeelde geometrie-eindpunten.
//
// Geen externe afhankelijkheden. Werkt op:
//   ways:  [{ wayId, geometry:[[lat,lon],...] }, ...]   (uit _netwerk.csv)
//   fixes: [{ lat, lon, acc }, ...]                      (uit _gps.csv)
// ============================================================================

(function (global) {
  'use strict';

  var LAT_M = 111320;

  // ---- geo helpers ---------------------------------------------------------
  function lonM(lat) { return LAT_M * Math.cos(lat * Math.PI / 180); }

  // Loodrechte afstand punt -> way-geometrie (meters) + projectie-positie langs
  // de way (meters vanaf begin). Cartesisch, accuraat op stadsschaal.
  function projectPointToWay(plat, plon, geometry) {
    var lm = lonM(geometry[0][0]);
    var px = plon * lm, py = plat * LAT_M;
    var best = Infinity, bestPos = 0, cum = 0;
    for (var i = 0; i < geometry.length - 1; i++) {
      var ax = geometry[i][1] * lm,   ay = geometry[i][0] * LAT_M;
      var bx = geometry[i+1][1] * lm, by = geometry[i+1][0] * LAT_M;
      var dx = bx - ax, dy = by - ay, len2 = dx*dx + dy*dy, segLen = Math.sqrt(len2);
      var d, t;
      if (len2 === 0) { d = Math.hypot(px - ax, py - ay); t = 0; }
      else {
        t = Math.max(0, Math.min(1, ((px-ax)*dx + (py-ay)*dy) / len2));
        d = Math.hypot(px - (ax + t*dx), py - (ay + t*dy));
      }
      if (d < best) { best = d; bestPos = cum + t * segLen; }
      cum += segLen;
    }
    return { dist: best, pos: bestPos };
  }

  function haversineM(lat1, lon1, lat2, lon2) {
    var lm = lonM((lat1 + lat2) / 2);
    var dx = (lon2 - lon1) * lm, dy = (lat2 - lat1) * LAT_M;
    return Math.hypot(dx, dy);
  }

  // ---- network graph (vertex-level) ----------------------------------------
  // Bouwt een graaf waarin elke (gesnapte) coordinaat een knoop is en elke
  // way-edge een verbinding met gewicht = lengte. Ways die een vertex delen
  // raken zo automatisch verbonden. nodeTol: eindpunten binnen deze afstand (m)
  // worden dezelfde graaf-knoop (vangnet tegen 6-decimalen-afronding).
  function buildGraph(ways, nodeTol) {
    nodeTol = nodeTol || 1.0;
    var nodes = [];          // [{lat,lon}]
    var adj   = [];          // node -> [{to, w}]
    var grid  = {};          // ruimtelijke hash voor node-dedup
    var cell  = Math.max(nodeTol, 0.5);

    function keyOf(lat, lon) {
      var gy = Math.round(lat * LAT_M / cell);
      var gx = Math.round(lon * lonM(lat) / cell);
      return gx + ',' + gy;
    }
    function getNode(lat, lon) {
      // zoek bestaande knoop binnen nodeTol in de 9 omliggende cellen
      var gy = Math.round(lat * LAT_M / cell);
      var gx = Math.round(lon * lonM(lat) / cell);
      for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) {
        var bucket = grid[(gx+dx) + ',' + (gy+dy)];
        if (!bucket) continue;
        for (var i = 0; i < bucket.length; i++) {
          var n = nodes[bucket[i]];
          if (haversineM(lat, lon, n.lat, n.lon) <= nodeTol) return bucket[i];
        }
      }
      var id = nodes.length;
      nodes.push({ lat: lat, lon: lon });
      adj.push([]);
      var k = gx + ',' + gy;
      (grid[k] = grid[k] || []).push(id);
      return id;
    }
    function addEdge(a, b, w) {
      if (a === b) return;
      adj[a].push({ to: b, w: w });
      adj[b].push({ to: a, w: w });
    }

    // way -> lijst van graaf-node-ids langs de geometrie (voor projectie->node)
    var wayNodeIds = {};
    ways.forEach(function (way) {
      var g = way.geometry;
      var prev = getNode(g[0][0], g[0][1]);
      var ids = [prev];
      for (var i = 1; i < g.length; i++) {
        var cur = getNode(g[i][0], g[i][1]);
        addEdge(prev, cur, haversineM(g[i-1][0], g[i-1][1], g[i][0], g[i][1]));
        ids.push(cur);
        prev = cur;
      }
      wayNodeIds[way.wayId] = ids;
    });

    return { nodes: nodes, adj: adj, wayNodeIds: wayNodeIds };
  }

  // Dijkstra van bronknoop naar alle knopen, afgekapt op maxDist (m) zodat we
  // in een dichte binnenstad niet de hele graaf doorploegen per query.
  function dijkstra(graph, src, maxDist) {
    var dist = new Float64Array(graph.nodes.length).fill(Infinity);
    dist[src] = 0;
    // binaire min-heap
    var heap = [{ n: src, d: 0 }];
    function push(x) { heap.push(x); var i = heap.length-1;
      while (i>0){ var p=(i-1)>>1; if (heap[p].d<=heap[i].d) break; var t=heap[p];heap[p]=heap[i];heap[i]=t;i=p; } }
    function pop() { var top=heap[0], last=heap.pop(); if (heap.length){ heap[0]=last; var i=0,n=heap.length;
      for(;;){ var l=2*i+1,r=l+1,s=i; if(l<n&&heap[l].d<heap[s].d)s=l; if(r<n&&heap[r].d<heap[s].d)s=r; if(s===i)break; var t=heap[s];heap[s]=heap[i];heap[i]=t;i=s; } } return top; }
    while (heap.length) {
      var cur = pop();
      if (cur.d > dist[cur.n]) continue;
      if (cur.d > maxDist) continue;
      var edges = graph.adj[cur.n];
      for (var e = 0; e < edges.length; e++) {
        var nd = cur.d + edges[e].w;
        if (nd < dist[edges[e].to]) { dist[edges[e].to] = nd; push({ n: edges[e].to, d: nd }); }
      }
    }
    return dist;
  }

  // Kortste netwerkafstand tussen twee ways: min over alle node-paren van hun
  // geometrie. Goedkoop want we hebben de Dijkstra-afstanden vanaf de
  // src-way-knopen al; we nemen het minimum naar de dst-way-knopen.
  function wayToWayDist(graph, distFrom, dstWayId) {
    var ids = graph.wayNodeIds[dstWayId];
    if (!ids) return Infinity;
    var best = Infinity;
    for (var i = 0; i < ids.length; i++) if (distFrom[ids[i]] < best) best = distFrom[ids[i]];
    return best;
  }

  // ---- candidate generation ------------------------------------------------
  // Project punt -> way en geef ook de SEGMENT-index (welke edge van de
  // geometrie) + de afstand-langs-die-edge. Nodig om het snap-punt als tijdelijke
  // knoop in de graaf te splicen voor exacte route-afstand tussen snap-punten.
  function projectFull(plat, plon, geometry) {
    var lm = lonM(geometry[0][0]);
    var px = plon * lm, py = plat * LAT_M;
    var best = Infinity, bestSeg = 0, bestT = 0, bestLat = geometry[0][0], bestLon = geometry[0][1];
    for (var i = 0; i < geometry.length - 1; i++) {
      var ax = geometry[i][1]*lm, ay = geometry[i][0]*LAT_M;
      var bx = geometry[i+1][1]*lm, by = geometry[i+1][0]*LAT_M;
      var dx = bx-ax, dy = by-ay, len2 = dx*dx+dy*dy;
      var t = (len2===0)?0:Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/len2));
      var cx = ax+t*dx, cy = ay+t*dy, d = Math.hypot(px-cx, py-cy);
      if (d < best) { best=d; bestSeg=i; bestT=t; bestLat=cy/LAT_M; bestLon=cx/lm; }
    }
    return { dist: best, seg: bestSeg, t: bestT, lat: bestLat, lon: bestLon };
  }

  // Per fix: alle ways met loodrechte afstand <= searchRadius, met de volledige
  // projectie (snap-punt + segment-index) zodat de transitie exact kan rekenen.
  function candidatesForFix(fix, ways, searchRadius, wayById) {
    var out = [];
    for (var i = 0; i < ways.length; i++) {
      var pr = projectFull(fix.lat, fix.lon, ways[i].geometry);
      if (pr.dist <= searchRadius)
        out.push({ wayId: ways[i].wayId, dist: pr.dist, seg: pr.seg, t: pr.t, plat: pr.lat, plon: pr.lon });
    }
    return out;
  }

  // Route-afstand tussen twee SNAP-PUNTEN over de graaf. Elk snap-punt ligt op
  // edge `seg` van zijn way, fractie t. We rekenen: (rest van src-edge naar zijn
  // twee eindknopen) + Dijkstra tussen eindknopen + (deel van dst-edge). Zo meet
  // de transitie de werkelijk afgelegde netwerkafstand, niet way-tot-way.
  function snapToSnapDist(graph, srcCand, dstCand, distCacheFrom, maxDist) {
    // edge-eindknopen (graaf-node-ids) van src en dst
    var srcIds = graph.wayNodeIds[srcCand.wayId];
    var dstIds = graph.wayNodeIds[dstCand.wayId];
    if (!srcIds || !dstIds) return Infinity;
    var srcA = srcIds[srcCand.seg],   srcB = srcIds[srcCand.seg + 1];
    var dstA = dstIds[dstCand.seg],   dstB = dstIds[dstCand.seg + 1];
    // edge-lengtes
    var srcEdgeLen = haversineM(graph.nodes[srcA].lat, graph.nodes[srcA].lon, graph.nodes[srcB].lat, graph.nodes[srcB].lon);
    var dstEdgeLen = haversineM(graph.nodes[dstA].lat, graph.nodes[dstA].lon, graph.nodes[dstB].lat, graph.nodes[dstB].lon);
    // zelfde edge? dan is het puur het verschil in fractie langs die ene edge
    if (srcA === dstA && srcB === dstB) return Math.abs(dstCand.t - srcCand.t) * srcEdgeLen;
    // afstand van src-snappunt naar zijn twee eindknopen
    var srcToA = srcCand.t * srcEdgeLen, srcToB = (1 - srcCand.t) * srcEdgeLen;
    var dstToA = dstCand.t * dstEdgeLen, dstToB = (1 - dstCand.t) * dstEdgeLen;
    // Dijkstra-afstanden vanaf srcA en srcB zijn voorberekend in distCacheFrom
    var dA = distCacheFrom[srcA], dB = distCacheFrom[srcB];
    var best = Infinity;
    // src eindknoop -> dst eindknoop, plus de stukjes binnen de edges
    best = Math.min(best, srcToA + dA[dstA] + dstToA);
    best = Math.min(best, srcToA + dA[dstB] + dstToB);
    best = Math.min(best, srcToB + dB[dstA] + dstToA);
    best = Math.min(best, srcToB + dB[dstB] + dstToB);
    return best;
  }

  // ---- main matcher --------------------------------------------------------
  // opts: { searchRadius=40, sigmaMin=5, beta=10, maxRouteDist=200, nodeTol=1 }
  // Returns { path:[wayId per fix], cost, candidates:[[...]], stats }
  function match(fixes, ways, opts) {
    opts = opts || {};
    var searchRadius  = opts.searchRadius  || 40;   // m, binnenstad-kandidaatradius
    var sigmaMin      = opts.sigmaMin      || 5;    // m, vloer op GPS-ruis
    var beta          = opts.beta          || 10;   // m, transitie-schaal (Newson-Krumm)
    var maxRouteDist  = opts.maxRouteDist  || 200;  // m, Dijkstra-afkap per query
    var nodeTol       = opts.nodeTol       || 1.0;  // m, node-dedup tolerantie

    var graph = buildGraph(ways, nodeTol);

    // trellis kolommen: per fix de kandidaten (met emissie-kost). Elke kandidaat
    // is een TOESTAND geïdentificeerd door wayId (de projectie seg/t hangt eraan).
    var cols = [];
    for (var i = 0; i < fixes.length; i++) {
      var sigma = Math.max(sigmaMin, fixes[i].acc || sigmaMin);
      var raw = candidatesForFix(fixes[i], ways, searchRadius);
      var cands = raw.map(function (c) {
        var z = c.dist / sigma;               // ½(d/σ)²  = -log Gaussische emissie
        return { wayId: c.wayId, dist: c.dist, seg: c.seg, t: c.t,
                 plat: c.plat, plon: c.plon, emit: 0.5 * z * z };
      });
      cols.push(cands);
    }

    // Viterbi forward. Toestand-sleutel = wayId binnen een kolom.
    var V = [];      // per kolom: { wayId -> bestCost }
    var back = [];   // per kolom: { wayId -> prevWayId }

    for (var col = 0; col < cols.length; col++) {
      V[col] = {}; back[col] = {};
      var cands2 = cols[col];
      if (col === 0) {
        for (var a = 0; a < cands2.length; a++) V[0][cands2[a].wayId] = cands2[a].emit;
        continue;
      }
      var prevCands = cols[col-1];
      var prevByWay = {}; for (var pb = 0; pb < prevCands.length; pb++) prevByWay[prevCands[pb].wayId] = prevCands[pb];
      var fixPrev = fixes[col-1], fixCur = fixes[col];
      var gpsStep = haversineM(fixPrev.lat, fixPrev.lon, fixCur.lat, fixCur.lon);

      // Pre-Dijkstra: vanaf de twee EINDKNOPEN van de edge waarop elke vorige
      // kandidaat is geprojecteerd. Gecached per eindknoop (gedeeld tussen
      // kandidaten die op dezelfde edge-eindknoop uitkomen).
      var distFromNode = {};   // nodeId -> Float64Array
      function ensureDijkstra(nodeId) {
        if (distFromNode[nodeId]) return;
        var dist = new Float64Array(graph.nodes.length); dist.fill(Infinity); dist[nodeId] = 0;
        distFromNode[nodeId] = multiDijkstra(graph, [nodeId], dist, maxRouteDist);
      }
      for (var p = 0; p < prevCands.length; p++) {
        if (V[col-1][prevCands[p].wayId] === undefined) continue;
        var sIds = graph.wayNodeIds[prevCands[p].wayId];
        if (!sIds) continue;
        ensureDijkstra(sIds[prevCands[p].seg]);
        ensureDijkstra(sIds[prevCands[p].seg + 1]);
      }

      for (var c = 0; c < cands2.length; c++) {
        var cur = cands2[c];
        var bestCost = Infinity, bestPrev = null;
        for (var pp = 0; pp < prevCands.length; pp++) {
          var prev = prevCands[pp];
          if (V[col-1][prev.wayId] === undefined) continue;
          var sIds2 = graph.wayNodeIds[prev.wayId];
          var distCacheFrom = {};
          distCacheFrom[sIds2[prev.seg]]     = distFromNode[sIds2[prev.seg]];
          distCacheFrom[sIds2[prev.seg + 1]] = distFromNode[sIds2[prev.seg + 1]];
          var routeD = snapToSnapDist(graph, prev, cur, distCacheFrom, maxRouteDist);
          if (!isFinite(routeD)) continue;            // niet verbonden binnen afkap
          var trans = Math.abs(routeD - gpsStep) / beta;  // Newson-Krumm
          var tot = V[col-1][prev.wayId] + trans;
          if (tot < bestCost) { bestCost = tot; bestPrev = prev.wayId; }
        }
        if (bestPrev !== null) {
          V[col][cur.wayId] = bestCost + cur.emit;
          back[col][cur.wayId] = bestPrev;
        }
      }
      // gap-vangnet: geen geldige voorganger voor één kandidaat -> herstart keten
      if (Object.keys(V[col]).length === 0) {
        for (var g2 = 0; g2 < cands2.length; g2++) {
          V[col][cands2[g2].wayId] = cands2[g2].emit;
          back[col][cands2[g2].wayId] = null;
        }
      }
    }

    // backtrace vanaf goedkoopste eindtoestand
    var path = new Array(cols.length).fill(null);
    var lastCol = cols.length - 1;
    while (lastCol >= 0 && Object.keys(V[lastCol]).length === 0) lastCol--;
    if (lastCol < 0) return { path: path, cost: Infinity, candidates: cols, graph: graph };

    var bestEnd = null, bestEndCost = Infinity;
    for (var w in V[lastCol]) if (V[lastCol][w] < bestEndCost) { bestEndCost = V[lastCol][w]; bestEnd = w; }
    path[lastCol] = bestEnd;
    for (var col2 = lastCol; col2 > 0; col2--) {
      var prev = back[col2][path[col2]];
      if (prev === null || prev === undefined) { /* keten-herstart */ path[col2-1] = null; }
      else path[col2-1] = prev;
    }

    return {
      path: path,
      cost: bestEndCost,
      candidates: cols,
      graph: graph,
      stats: {
        nFixes: fixes.length,
        nWays: ways.length,
        nNodes: graph.nodes.length,
        avgCands: cols.reduce(function(s,c){return s+c.length;},0) / Math.max(1,cols.length)
      }
    };
  }

  // multi-source Dijkstra met voorgeseede dist-array
  function multiDijkstra(graph, seedNodes, dist, maxDist) {
    var heap = [];
    function push(x){ heap.push(x); var i=heap.length-1;
      while(i>0){var p=(i-1)>>1; if(heap[p].d<=heap[i].d)break; var t=heap[p];heap[p]=heap[i];heap[i]=t;i=p;} }
    function pop(){ var top=heap[0],last=heap.pop(); if(heap.length){heap[0]=last;var i=0,n=heap.length;
      for(;;){var l=2*i+1,r=l+1,s=i; if(l<n&&heap[l].d<heap[s].d)s=l; if(r<n&&heap[r].d<heap[s].d)s=r; if(s===i)break; var t=heap[s];heap[s]=heap[i];heap[i]=t;i=s;} } return top; }
    for (var i = 0; i < seedNodes.length; i++) push({ n: seedNodes[i], d: 0 });
    while (heap.length) {
      var cur = pop();
      if (cur.d > dist[cur.n]) continue;
      if (cur.d > maxDist) continue;
      var edges = graph.adj[cur.n];
      for (var e = 0; e < edges.length; e++) {
        var nd = cur.d + edges[e].w;
        if (nd < dist[edges[e].to]) { dist[edges[e].to] = nd; push({ n: edges[e].to, d: nd }); }
      }
    }
    return dist;
  }

  var API = { match: match, buildGraph: buildGraph, projectPointToWay: projectPointToWay, haversineM: haversineM };
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
  else global.ViterbiMatch = API;

})(typeof window !== 'undefined' ? window : this);
