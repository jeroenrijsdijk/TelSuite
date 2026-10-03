# Viterbi map-matching — GEPARKEERD (sinds v2.12)

Geëxtraheerd uit `../telrapport_viterbi.html` (de gearchiveerde fork). De rapport-tool
zelf is opgevolgd door `../../telrapport.html` (productie-renderer, v2.11-compleet).

## Waarom geparkeerd
Veld-validatie op echte ZIPs liet zien dat Viterbi géén universele snap-upgrade is:

- **txb (convergente trio, 130419432 e.a.):** sub-meter-convergent → irreducibel.
  Viterbi *verplaatst* de ambiguïteit (14 tikken 7/7 over twee buren), lost 'm niet op.
  Bevestigt de v2.10-closure.
- **evj (winkelstraat):** schone data, ways op 8 m, en `matchTopo` haakt tóch op 37/42
  fixes af. Limiet van het topologische HMM in dichte voetganger-netten.
- **zia (transect):** "off-netwerk" bleek een fetch-gat — bospad = `highway=track`,
  uitgesloten door de oude Overpass-filter. Opgelost in v2.12 (filter-de-drift), niet
  iets dat Viterbi kon redden. Plus: scherm-uit-workflow → schaars/brokkelig spoor →
  trajectorie-matching breekt structureel.

**Sweet spot:** continue-loop simpel/object-surveys (dicht GPS-spoor, op gemapt netwerk).
Daar gaf Viterbi wél een schoon continu pad. Voor de tel-modi (transect/winkelstraat)
is het het verkeerde gereedschap — die leunen op locatie + GPS-snelheid, niet op traject.

## Bestanden
- `viterbi_engine.js` — geïsoleerde Newson-Krumm `matchTopo` (IIFE). `require()`-baar,
  muteert geen teldata. Interface: `{ match, matchTopo, projectFull }`.
- `vtest.js  <zip>`      — één pocket-ZIP: coverage, continuïteit, tik-hertoekenning, trio.
- `vbatch.js <zip...>`   — multi-walk-overzicht: tellingen + snap-coverage R40 vs R60.
- `vdiag.js  <zip>`      — null-uitsplitsing (off-netwerk vs HMM-drop) + eerlijke tik-vergelijking.
- `vsweep.js <zip>`      — parameter-sweep (searchRadius/hop/method) tegen null-rate.
- `vfinal.js <zip>`      — convergente-trio + tik-vergelijking op de dekkende config.
- `voff.js   <zip...>`   — off-netwerk-fractie (fixes >40 m van elke way).
- `vacc.js   <zip...>`   — correlatie nauwkeurigheid × tijdgaten × way-afstand.
- `vspan.js  <zip...>`   — bbox-diagonaal + padlengte (bewoog de waarnemer?).

## Draaien
```
node vtest.js pad/naar/<sessie>.zip
```
Node 18+; vereist de `unzip` CLI op PATH. De rig spiegelt `loadPocketZip` +
`viterbiWaysForSession` byte-voor-byte, dus dezelfde ingestion als de tool.

## Ont-parkeren (later, indien gewenst)
Port `viterbi_engine.js` als **simpel-only opt-in** ín `telrapport.html` (één bestand,
geen tweede fork). Niet de hele tool terugkopiëren — dat herintroduceert de drift.
