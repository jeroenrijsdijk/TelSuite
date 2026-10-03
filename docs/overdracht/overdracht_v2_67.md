# Overdracht v2.67 — de highway-voorkeur werkt

Eén reparatie in `telreconstructie.html`. De voorkeur van de profielen `auto` en
`fiets` bestond sinds v2.18 op papier, maar kwam nooit aan in de matcher. Jay had
dit eerder al opgemerkt en koos voor directe reparatie, zonder voorafgaande
replay.

---

## 1. Samenvatting

1. `MATCHER.matchTrajectory` krijgt een vijfde, optionele parameter `hwCost`.
   Die telt per way op bij de emissiekost.
2. Nieuwe regel in `_reconstructie_log.csv`: `highway_voorkeur`. Daaraan zie je
   of een recon-ZIP met of zonder werkende voorkeur is gemaakt.
3. Nieuwe test `functest_hwvoorkeur.js` (18 tests).
4. Autorit-reconstructie geparkeerd: Jay telt zelden vanuit de auto.

## 2. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telreconstructie.html` | `MATCHER`: parameter `hwCost` en tabel `wegKost`; functie `hwVoorkeurTekst()`; één log-regel |
| `_archief/overpass_rig/functest_hwvoorkeur.js` | nieuw |
| `_archief/overpass_rig/README.md` | testregel erbij |
| `_archief/overpass_rig/valideer.py` | verwachte sets v2.67 |
| `OVERDRACHT_STAND_VAN_ZAKEN.md` | afspraak toegevoegd, backlog bijgewerkt |

Alle andere HTML-bestanden zijn byte-identiek aan v2.66. Van de gedeelde blokken
is alleen de hash van `MATCHER` veranderd.

## 3. Wat er misging

`reconstrueer()` riep de matcher zo aan:

```
MATCHER.matchTrajectory(netMatch, adj, events, segCount, S.profiel.highwayCost)
```

De functie had maar vier parameters. JavaScript gooit een extra argument
zonder melding weg, dus de voorkeur verdween. De overdracht van v2.18
beschreef hem als emissieterm, maar de kern kwam byte-identiek over uit pocket,
en daar bestaan geen profielen.

Het gevolg: overal waar een fiets- of voetpad dicht langs de rijbaan loopt,
koos de reconstructor gewoon de dichtstbijzijnde weg. Bij een autotelling kon
een tik dus op het fietspad belanden, bij een fietstelling op de rijbaan.

## 4. De reparatie

```
function matchTrajectory(net, adj, fixes, segCounter, hwCost) {
  ...
  wegKost[wayId] = hwCost ? (+hwCost(net[wayId].highway) || 0) : 0;   // één keer per way
  ...
  emit: 0.5*z*z + wegKost[wayIds[w]]
```

- De kosten worden per way één keer berekend, niet per fix.
- Het `highway`-type zat al in het netwerk. Dat geldt voor de verse fetch
  (`verwerkOsmWays`) en voor het originele `_netwerk.csv`, dus de voorkeur werkt
  ook zonder verversing.
- Een onbekend type, of een profiel dat niets teruggeeft, telt als 0.
- De waarden zijn die uit v2.18: −2 voor geprefereerd, +4 voor vermeden.

**Hoe ver trekt de voorkeur?** De emissie is ½·(d/σ)², met σ = max(5, acc).

- Sta je 2 m van een vermeden weg, dan wint een geprefereerde weg tot ruim
  17 m afstand (bij acc 5).
- Bij slechtere GPS wordt dat bereik groter.
- Een fietspad 25 m verderop trekt een fietsteller niet van de rijbaan.

De test legt beide grenzen vast. Is er alleen het vermeden type, dan wordt dat
alsnog gekozen (geen `null`).

**Wandelprofielen ongewijzigd.** `transect`, `winkelstraat`, `simpel` en
`pocket-parkeren` geven 0 terug, en `x + 0` is in drijvende komma exact `x`.
Getoetst in twee lagen:

- 300 willekeurige netwerken en sporen: de oude matcher (v2.66) en de nieuwe,
  zonder voorkeur en met een neutrale voorkeur, geven **byte-gelijke** uitvoer.
  300/300.
- In de test: alle vier de profielen geven hetzelfde pad als zonder voorkeur,
  terwijl `auto` op datzelfde netwerk wél anders kiest. Zo is zeker dat de test
  een verschil kán zien.

## 5. Herkennen welke ZIP's van vóór de reparatie zijn

`_reconstructie_log.csv` krijgt een regel, direct onder `offset_m`:

```
highway_voorkeur;actief (auto) voorkeur residential,living_street,…,service / vermijd cycleway,footway,pedestrian,path,track
highway_voorkeur;neutraal
```

**Een recon-ZIP zonder deze regel is gemaakt vóór v2.67.** Dat is betrouwbaarder
dan de versiemarkering: `reconstructie_versie` in dezelfde log staat nog op
`v2.18`, en de `reconstructie`-kolom in `_sessie.csv` op `v2.24` (zie backlog).

De log is diagnostiek en wordt niet verwerkt. Toch voor de volledigheid naar
**KNIME**: er komt een log-regel bij. Belangrijker: auto- en fietsreconstructies
kunnen vanaf nu een andere `osm_way_id`/`segment_index` en markerpositie hebben
dan dezelfde ZIP vóór v2.67. Dat gebeurt alleen waar paden parallel liggen.

## 6. Gevolg voor de gpx-tak

De gpx-tak draagt `MATCHER` op de stand van v2.64. Die kopie wijkt nu af,
dus de laatste vijf tests van `functest_gpxsnap.js` melden dat als je de nieuwe
`telreconstructie.html` ernaast legt. `gpx_snap.html` geeft geen voorkeur mee.
Neemt de tak de nieuwe matcher over, dan verandert daar dus niets aan het
gedrag.

## 7. Validatie

```
valideer.py                       ALLES OK — alleen telreconstructie.html gewijzigd (+1328 bytes)
  gedeelde blokken                10 groepen OK; MATCHER nieuwe hash a23e7acc
  gedeelde constanten             zijde-offset 5 bestanden OK
functest_hwvoorkeur.js            18/18
oud vs nieuw (ad hoc)             300/300 byte-gelijk zonder of met neutrale voorkeur
overige functests                 34+18+16+9+26+16+22+11+20+29+24+27 OK
test_zipref.py                    referentie sluit aan op de code
check_encoding.py                 alles geldige UTF-8
```

## 8. Backlog-wijzigingen

- Weg: "highway-voorkeur doet niets" (gerepareerd).
- Nieuw: oude auto- en fietsreconstructies opnieuw draaien of laten staan —
  Jay beslist.
- Nieuw: één versieconstante voor log en sessiekolom.
- Autorit-reconstructie: van "vraagt ontwerp" naar **geparkeerd**. Het grootste
  obstakel is met deze release weg.
