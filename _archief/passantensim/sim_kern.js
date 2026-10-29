/* ── Passantensimulatie: de kern (SIMKERN, okt 2026) ──────────────────────────
   Eén winkelstraat, één lopende teller die hem één keer in één richting afloopt,
   zoals Jay's rondes. De waarheid is de doorsnedestroom in het midden van elk vak
   (Jay: "vakjes van 40-60 meter, dus neem daar gewoon het midden van").

   Geen tijdstappen: elke voetganger is een stuksgewijs rechte lijn in (t, x),
   en de teller ook. Een ontmoeting is een tekenwissel van x_voet − x_teller
   tussen twee knikpunten; het tijdstip volgt exact uit lineaire interpolatie.

   De stroom langs de straat: herkomst en bestemming komen uit dezelfde set
   punten (twee straateinden en de winkeldeuren), met eigen gewichten wO en wD.
   Dan is de stroom bij x precies bekend:
     naar +: λ · Σ_{p<x} wO_p · Σ_{p'>x} wD_p' / Z,   Z = 1 − Σ wO_p·wD_p
   en zo ook naar −. Met wO ≠ wD (een station aan één kant) is de straat scheef.

   Uitvoer: de waarheid per vak, en de CSV-rijen van één Pocket-sessie
   (sessie, netwerk, bezocht, telregels) zoals PASSANTEN.sessie ze verwacht.
   Pocket wordt nagedaan: routepunten bij ≥ 5 m verplaatsing, een bezoek van het
   eerste tot het laatste routepunt in een vak, een tik op het vak van het
   routepunt dat qua tijd het dichtst ligt, tijden op hele seconden.

   Puur: geen DOM en geen Node. Herhaalbaar via het zaadje.                    */
var SIMKERN = (function () {
  'use strict';

  var STANDAARD = {
    // de straat
    straatMin: 150, straatMax: 600,    // m
    segDoel: 40, segMin: 60,           // zoals SEGMENT_TARGET_M / SEGMENT_MIN_M in Pocket
    deurPerM: 1 / 12,                  // winkeldeuren per meter
    pEind: 0.5,                        // deel van herkomsten/bestemmingen dat een straateinde is
    scheef: [0.5, 0.5],                // a: deel van de einde-herkomsten uit einde x=0 (0,5 = symmetrisch)
    qMin: 300, qMax: 1600,             // passanten per uur, beide richtingen, midden van de straat
    // voetgangers
    groep: [0.55, 0.30, 0.10, 0.05],   // P(groepsgrootte 1, 2, 3, 4)
    groepTussen: [0.3, 0.9],           // s tussen twee leden van een groepje
    vGem: 1.25, vSd: 0.25, vMin: 0.5, vMax: 2.0,
    pSlenter: 0.15, vSlenter: 0.7, vSlenterSd: 0.15,
    pStop: 0.25, stopGem: 60, stopMin: 5,   // even stilstaan (etalage), daarna verder
    stilDicht: 2,                      // vaste stilstaanders (terras, wachten) per 100 m, géén passant
    // de lopende teller
    tempo: 1.45, tempoSd: 0.08,        // m/s, vrij lopen
    drukteQ: 900, drukteK: 0.55,       // vertraging: tempo / (1 + K·(q_tegen/Q)^3)
    segJitter: 0.1, pPauze: 0.05, pauze: [4, 15],
    // waarnemen en tikken
    pZelf: 0.95, pOver: 0.75,          // trefkans aan de eigen kant / de overkant
    pGroep: 0.85,                      // extra factor voor het 2e, 3e … lid van een groepje
    qZicht: 4000,                      // drukte: trefkans × 1 / (1 + q/qZicht)
    vertraging: 0.8, vertragingSd: 0.8, minTussen: 0.35,   // s
    salvo: 3,                          // s; >0: eerst kijken, dan tikken: wat binnen dit venster
                                       // gezien is, wordt in één salvo getikt ("inhaaltikken")
    // gps (zoals Pocket)
    gpsInt: [4, 6], gpsRuis: 4, gpsTau: 20, routeMin: 5,   // ruis met geheugen (s)
    maxGat: 30, minVisitSec: 5, minVisitPts: 3,
    idealGps: false,                   // true: bezoeken exact, tik op het echte vak
    // vaste teller
    pStatic: 0.97
  };

  /* ---------- toeval ------------------------------------------------------- */
  function rng(zaad) {
    var s = zaad >>> 0, extra = null;
    function u() {                                   // mulberry32
      s = (s + 0x6D2B79F5) >>> 0;
      var t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    function n(mu, sd) {
      if (extra !== null) { var e = extra; extra = null; return mu + sd * e; }
      var a = u() || 1e-12, b = u(), r = Math.sqrt(-2 * Math.log(a));
      extra = r * Math.sin(2 * Math.PI * b);
      return mu + sd * r * Math.cos(2 * Math.PI * b);
    }
    function exp(gem) { return -gem * Math.log(1 - u()); }
    function tussen(ab) { return ab[0] + u() * (ab[1] - ab[0]); }
    function kies(w) {
      var x = u() * w.reduce(function (s, v) { return s + v; }, 0);
      for (var i = 0; i < w.length; i++) { x -= w[i]; if (x < 0) return i; }
      return w.length - 1;
    }
    return { u: u, n: n, exp: exp, tussen: tussen, kies: kies };
  }

  /* ---------- trajecten: [[t, x], …], lineair ertussen ----------------------- */
  function zoek(tr, t) {                             // laatste knik met tijd ≤ t
    var lo = 0, hi = tr.length - 1;
    while (lo < hi) { var m = (lo + hi + 1) >> 1; if (tr[m][0] <= t) lo = m; else hi = m - 1; }
    return lo;
  }
  function plek(tr, t) {
    var i = zoek(tr, t);
    if (i >= tr.length - 1) return tr[tr.length - 1][1];
    var a = tr[i], b = tr[i + 1];
    return b[0] === a[0] ? b[1] : a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0]);
  }
  function snelheid(tr, t) {
    var i = zoek(tr, t);
    if (i >= tr.length - 1) return 0;
    var a = tr[i], b = tr[i + 1];
    return b[0] === a[0] ? 0 : (b[1] - a[1]) / (b[0] - a[0]);
  }
  // Alle kruisingen van twee trajecten: [{t, v}] met v de snelheid van 'voet' op dat moment.
  function kruisingen(voet, teller) {
    var t0 = Math.max(voet[0][0], teller[0][0]);
    var t1 = Math.min(voet[voet.length - 1][0], teller[teller.length - 1][0]);
    if (t0 >= t1) return [];
    var ts = [t0, t1];
    voet.forEach(function (p) { if (p[0] > t0 && p[0] < t1) ts.push(p[0]); });
    for (var i = zoek(teller, t0) + 1; i < teller.length && teller[i][0] < t1; i++) ts.push(teller[i][0]);
    ts.sort(function (a, b) { return a - b; });
    var uit = [], vorig = plek(voet, ts[0]) - plek(teller, ts[0]);
    for (var j = 1; j < ts.length; j++) {
      if (ts[j] === ts[j - 1]) continue;
      var d = plek(voet, ts[j]) - plek(teller, ts[j]);
      if ((vorig < 0 && d >= 0) || (vorig > 0 && d <= 0)) {
        var t = ts[j - 1] + (ts[j] - ts[j - 1]) * vorig / (vorig - d);
        uit.push({ t: t, v: snelheid(voet, Math.min(t + 1e-6, ts[j])) });
      }
      if (d !== 0) vorig = d;
    }
    return uit;
  }
  // Kruisingen van een vast punt x0 in een tijdvenster: [{t, richting ±1}].
  function doorPunt(voet, x0, ta, tb) {
    var uit = [];
    for (var i = 0; i < voet.length - 1; i++) {
      var a = voet[i], b = voet[i + 1];
      if ((a[1] - x0) * (b[1] - x0) < 0) {
        var t = a[0] + (b[0] - a[0]) * (x0 - a[1]) / (b[1] - a[1]);
        if (t >= ta && t <= tb) uit.push({ t: t, r: b[1] > a[1] ? 1 : -1 });
      }
    }
    return uit;
  }

  /* ---------- de straat -------------------------------------------------- */
  function wereld(P, r) {
    var L = r.tussen([P.straatMin, P.straatMax]);
    var N = L < P.segMin ? 1 : Math.max(1, Math.round(L / P.segDoel));
    var nDeur = Math.max(1, Math.round(L * P.deurPerM));
    var deuren = [];
    for (var i = 0; i < nDeur; i++) deuren.push(r.u() * L);
    deuren.sort(function (a, b) { return a - b; });
    var x = [0].concat(deuren, [L]);
    var a = r.tussen(P.scheef);
    if (r.u() < 0.5) a = 1 - a;                       // het station aan een willekeurige kant
    var wO = x.map(function (_, j) { return j === 0 ? P.pEind * a : j === x.length - 1 ? P.pEind * (1 - a) : (1 - P.pEind) / nDeur; });
    var wD = x.map(function (_, j) { return j === 0 ? P.pEind * (1 - a) : j === x.length - 1 ? P.pEind * a : (1 - P.pEind) / nDeur; });
    var Z = 1 - x.reduce(function (s, _, j) { return s + wO[j] * wD[j]; }, 0);
    function stroom(xx) {                             // per eenheid λ: [naar +, naar −]
      var oL = 0, oR = 0, dL = 0, dR = 0;
      x.forEach(function (p, j) { if (p < xx) { oL += wO[j]; dL += wD[j]; } else if (p > xx) { oR += wO[j]; dR += wD[j]; } });
      return [oL * dR / Z, oR * dL / Z];
    }
    var qTot = r.tussen([P.qMin, P.qMax]);
    var sm = stroom(L / 2);
    var lam = qTot / 3600 / (sm[0] + sm[1]);          // personen per seconde, alle ritten
    var segLen = L / N, segs = [];
    for (var k = 0; k < N; k++) {
      var xm = (k + 0.5) * segLen, s = stroom(xm);
      segs.push({ k: k, xm: xm, qPlus: 3600 * lam * s[0], qMin: 3600 * lam * s[1] });
    }
    return { L: L, N: N, segLen: segLen, punten: x, wO: wO, wD: wD, a: a, qTot: qTot, lam: lam, segs: segs };
  }

  /* ---------- de lopende teller ------------------------------------------ */
  function teller(P, W, r) {
    var dir = r.u() < 0.5 ? 1 : -1;
    var u0 = Math.max(0.8, r.n(P.tempo, P.tempoSd));
    var qTegen = W.qTot / 2;
    var uBasis = u0 / (1 + P.drukteK * Math.pow(qTegen / P.drukteQ, 3));
    var T0 = 13 * 3600 + 5 * 60 + r.u() * 60;
    var aanloop = 25;
    var x = dir > 0 ? -aanloop : W.L + aanloop, t = T0 - aanloop / uBasis;
    var tr = [[t, x]], inVak = [];
    t = T0; x = dir > 0 ? 0 : W.L; tr.push([t, x]);
    for (var j = 0; j < W.N; j++) {
      var k = dir > 0 ? j : W.N - 1 - j;
      var u = uBasis * (1 + P.segJitter * (2 * r.u() - 1)), binnen = t;
      if (r.u() < P.pPauze) {
        x += dir * W.segLen / 2; t += W.segLen / 2 / u; tr.push([t, x]);
        t += r.tussen(P.pauze); tr.push([t, x]);
        x += dir * W.segLen / 2; t += W.segLen / 2 / u; tr.push([t, x]);
      } else {
        x += dir * W.segLen; t += W.segLen / u; tr.push([t, x]);
      }
      inVak.push({ k: k, t0: binnen, t1: t });
    }
    x += dir * aanloop; t += aanloop / uBasis; tr.push([t, x]);
    return { dir: dir, tr: tr, inVak: inVak, uBasis: uBasis, T0: T0, T1: inVak[inVak.length - 1].t1 };
  }

  /* ---------- de voetgangers ---------------------------------------------- */
  function voetgangers(P, W, T, r) {
    var gemG = P.groep.reduce(function (s, p, i) { return s + p * (i + 1); }, 0);
    var lamG = W.lam / gemG;
    var ta = T.T0 - 1800, tb = T.tr[T.tr.length - 1][0];
    var lijst = [], groep = 0;
    for (var t = ta + r.exp(1 / lamG); t < tb; t += r.exp(1 / lamG)) {
      var o = r.kies(W.wO), d;
      do { d = r.kies(W.wD); } while (d === o);
      var xo = W.punten[o], xd = W.punten[d];
      var v = r.u() < P.pSlenter ? r.n(P.vSlenter, P.vSlenterSd) : r.n(P.vGem, P.vSd);
      v = Math.min(P.vMax, Math.max(P.vMin, v));
      if (P.vSd === 0 && P.pSlenter === 0) v = P.vGem;
      var stop = null;
      if (r.u() < P.pStop) stop = { f: r.u(), duur: P.stopMin + r.exp(P.stopGem) };
      var G = r.kies(P.groep) + 1, kant = r.u() < 0.5 ? 0 : 1, start = t;
      groep++;
      for (var g = 0; g < G; g++) {
        if (g > 0) start += r.tussen(P.groepTussen);
        var dx = xd - xo, tr = [[start, xo]];
        if (stop) {
          var xs = xo + stop.f * dx, ts = start + Math.abs(stop.f * dx) / v;
          tr.push([ts, xs]); tr.push([ts + stop.duur, xs]);
          tr.push([ts + stop.duur + Math.abs((1 - stop.f) * dx) / v, xd]);
        } else tr.push([start + Math.abs(dx) / v, xd]);
        lijst.push({ tr: tr, kant: kant, groep: groep, lid: g, passant: true });
      }
    }
    // vaste stilstaanders: staan er de hele tijd, zijn geen passant
    var nStil = Math.round(P.stilDicht * W.L / 100 * (0.5 + r.u()));
    for (var i = 0; i < nStil; i++) {
      var xx = r.u() * W.L;
      lijst.push({ tr: [[ta, xx], [tb + 60, xx]], kant: r.u() < 0.5 ? 0 : 1, groep: -1, lid: 0, passant: false });
    }
    return lijst;
  }

  /* ---------- Pocket nadoen ------------------------------------------------ */
  function hms(s) {
    s = Math.floor(s);
    return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60].map(function (v) { return (v < 10 ? '0' : '') + v; }).join(':');
  }
  function vakVan(W, x) {
    if (x < 0 || x >= W.L) return null;
    return Math.min(W.N - 1, Math.floor(x / W.segLen));
  }
  function routepunten(P, W, T, r) {
    var tr = T.tr, t = tr[0][0] + r.u() * P.gpsInt[1], eind = tr[tr.length - 1][0];
    var log = [], laatst = null, ex = r.n(0, P.gpsRuis), ey = r.n(0, P.gpsRuis), dt = 0;
    for (; t <= eind; t += (dt = r.tussen(P.gpsInt))) {
      // gps-fouten zijn traag (AR(1) met tijdconstante gpsTau), niet elke fix opnieuw
      var rho = P.gpsTau > 0 ? Math.exp(-dt / P.gpsTau) : 0, w = Math.sqrt(1 - rho * rho);
      ex = rho * ex + w * r.n(0, P.gpsRuis); ey = rho * ey + w * r.n(0, P.gpsRuis);
      var x = plek(tr, t) + ex, y = ey;
      if (laatst && Math.hypot(x - laatst[0], y - laatst[1]) < P.routeMin) continue;
      laatst = [x, y];
      var k = vakVan(W, x);
      log.push({ ts: Math.floor(t), way: k === null ? '2' : '1', seg: k === null ? 0 : k });
    }
    return log;
  }
  function bezoeken(P, log) {                          // buildBezochtCsv
    var v = [], cur = null;
    log.forEach(function (p) {
      var zelfde = cur && cur.way === p.way && cur.seg === p.seg;
      if (!zelfde || p.ts - cur.tEnd > P.maxGat) {
        if (cur) v.push(cur);
        cur = { way: p.way, seg: p.seg, tStart: p.ts, tEnd: p.ts, n: 1 };
      } else { cur.tEnd = p.ts; cur.n++; }
    });
    if (cur) v.push(cur);
    return v.filter(function (b) { return b.tEnd - b.tStart >= P.minVisitSec && b.n >= P.minVisitPts; });
  }

  /* ---------- één run --------------------------------------------------- */
  function run(param, zaad) {
    var P = {}, k;
    for (k in STANDAARD) P[k] = STANDAARD[k];
    for (k in (param || {})) P[k] = param[k];
    var r = rng(zaad);
    var W = wereld(P, r), T = teller(P, W, r), V = voetgangers(P, W, T, r);
    var zicht = 1 / (1 + W.qTot / P.qZicht), tellerKant = r.u() < 0.5 ? 0 : 1;

    // ontmoetingen → bedoelde tikken
    var bedoeld = [], ontmoet = { tegemoet: 0, stilstaand: 0 };
    V.forEach(function (p) {
      kruisingen(p.tr, T.tr).forEach(function (m) {
        var soort;
        if (Math.abs(m.v) < 1e-9) soort = 'stilstaand';
        else if (m.v * T.dir < 0) soort = 'tegemoet';
        else return;                                   // inhalen of ingehaald: niet getikt
        ontmoet[soort]++;
        var kans = (p.kant === tellerKant ? P.pZelf : P.pOver) * zicht;
        if (p.lid > 0) kans *= P.pGroep;
        if (r.u() >= kans) return;
        var d = Math.max(-3, Math.min(5, r.n(P.vertraging, P.vertragingSd)));
        bedoeld.push({ t: m.t + d, tMeet: m.t, soort: soort, passant: p.passant });
      });
    });
    bedoeld.sort(function (a, b) { return a.t - b.t; });
    if (P.salvo > 0) {
      for (var i = 0; i < bedoeld.length;) {
        var j = i;
        while (j + 1 < bedoeld.length && bedoeld[j + 1].t <= bedoeld[i].t + P.salvo) j++;
        for (var q = i; q <= j; q++) bedoeld[q].t = bedoeld[j].t;
        i = j + 1;
      }
    }
    var vorig = -Infinity;
    bedoeld.forEach(function (b) { b.t = Math.max(b.t, vorig + P.minTussen); vorig = b.t; });

    // gps, bezoeken, tikken aan een vak hangen
    var bez, tikken;
    if (P.idealGps) {
      bez = T.inVak.map(function (v) { return { way: '1', seg: v.k, tStart: Math.round(v.t0), tEnd: Math.round(v.t1), n: 9 }; });
      tikken = bedoeld.map(function (b) {
        var k = vakVan(W, plek(T.tr, b.t));
        return { ts: Math.floor(b.t), way: k === null ? '2' : '1', seg: k === null ? 0 : k, soort: b.soort };
      });
    } else {
      var log = routepunten(P, W, T, r);
      bez = bezoeken(P, log);
      tikken = bedoeld.map(function (b) {
        var ts = Math.floor(b.t), best = null, bd = Infinity;
        log.forEach(function (p) { var d = Math.abs(p.ts - ts); if (d < bd) { bd = d; best = p; } });
        return { ts: ts, way: best ? best.way : '2', seg: best ? best.seg : 0, soort: b.soort };
      });
    }

    // waarheid per vak + de vaste teller (perfect en met trefkans) tijdens de ronde
    var ta = T.T0, tb = T.T1;
    W.segs.forEach(function (s) {
      s.staPlus = 0; s.staMin = 0; s.staGeteld = 0;
      V.forEach(function (p) {
        if (!p.passant) return;
        doorPunt(p.tr, s.xm, ta, tb).forEach(function (c) {
          if (c.r > 0) s.staPlus++; else s.staMin++;
          if (r.u() < P.pStatic) s.staGeteld++;
        });
      });
    });

    // de CSV-rijen voor PASSANTEN.sessie
    var GRAAD = 2 * Math.PI * 6371000 / 360, datum = '2026-10-24';
    var invoer = {
      sessie: [{ sessie_id: 'sim' + zaad + '_pkt_w', datum: datum, modus: 'winkelstraat' }],
      netwerk: W.segs.map(function (s) {
        return { osm_way_id: '1', segment_index: String(s.k), straat: 'Simstraat',
          geometrie_wkt: 'LINESTRING (' + (s.k * W.segLen / GRAAD) + ' 0, ' + ((s.k + 1) * W.segLen / GRAAD) + ' 0)' };
      }),
      gps: [],
      bezocht: bez.filter(function (b) { return b.way === '1'; }).map(function (b) {
        return { datum: datum, osm_way_id: '1', segment_index: String(b.seg), straat: 'Simstraat',
          start_tijd: hms(b.tStart), eind_tijd: hms(b.tEnd), duur_sec: String(b.tEnd - b.tStart) };
      }),
      telregels: tikken.map(function (x) {
        return { osm_way_id: x.way, segment_index: String(x.seg), tijdstip: datum + 'T' + hms(x.ts), type: x.soort };
      })
    };
    return { P: P, W: W, T: T, invoer: invoer, nVoet: V.length, bedoeld: bedoeld,
             alleBezoeken: bez, zicht: zicht, ontmoet: ontmoet };
  }

  return { STANDAARD: STANDAARD, run: run, rng: rng, kruisingen: kruisingen, plek: plek };
})();
/* ── einde simkern ── */
