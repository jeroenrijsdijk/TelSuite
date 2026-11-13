# Overdracht v3.49 — telrapport snel bij veel tellingen

Jay: "Het clusteren van punten is het traagste onderdeel van het tekenen van de
kaart. Kun je daar nog wat snelheidswinst vinden?" Na de meting en het voorstel
(A–D): "Doe A,B,C en D maar zorg wel dat er iets van een voortgangsindicatie is
/ blijft."

## 0. De meting

**De testset** is gemaakt en lijkt op die van Jay: 185 pocket-tellingen, elk
met een eigen wegennet van 230 wegvakken. Samen zijn dat 42.550 wegvakken en
ongeveer 9.000 tikken. Jay's GeoPackage van 13 november had 185 tellingen,
43.310 wegvakken en ruim 11.000 tikken.

**Het CPU-profiel** (v3.48):

| waar | aandeel |
|---|---|
| `heeftWegvakken`: per telling alle wegvakken langs (in `drawClusters` en `clusterDekking`) | 34% |
| `updateStats`: aan het eind van elke `drawClusters`, twee keer alle wegvakken | 14% |
| `pmuMeting` + `pocketZichtbaar`: per wegvak alle bezoeken van alle tellingen | 20% |
| `setAttribute`: elke lijn opnieuw stijlen, ook als er niets verandert | 6% |

**Het clusteren zelf** (`gapCluster`, `projectOnPolyline`) kwam in het profiel
niet voor.

**Bij het laden** gebeurde dit allemaal opnieuw na elke ZIP, voor alle tellingen
die er al stonden. Daarbij kwam `fitBounds` per ZIP: Leaflet rekent bij elke
verschuiving alle lijnen opnieuw. De tijd groeide dus met het kwadraat van het
aantal tellingen.

## 1. Wat er veranderd is

### A. Twee opzoeklijsten

- **`wegvakkenVan`**: per telling een `Set` met de sleutels van de wegvakken
  waar ze een entry in `wayData[k].sessions` heeft.
  - Vullen kan alleen via `koppel(k, e)`, op de vier plekken waar een telling
    aan een wegvak gekoppeld wordt: pocket-tik, pocket-0-bezoek, en
    `telPerStuk` (geteld en gelopen).
  - Losmaken via `ontkoppel(sid)`, in `telPerStuk`.
  - `resetAll` leegt hem.
- **`bezoekenOp`**: per wegvak de bezoeken uit `visitData`, als `{ sid, v }`.
  Hij wordt gevuld waar `visitData` gevuld wordt, in laadvolgorde. `pmuMeting`
  telt dus in dezelfde volgorde op als voorheen.
- **Wat ze gebruiken in plaats van alles langs lopen:**
  - `heeftWegvakken`;
  - de 0-badges in `drawClusters`;
  - `telPerStuk`;
  - `pmuMeting`;
  - `updateStats`;
  - het fietsmaximum in `recolorAll`;
  - in `loadPocketZip`: de ontbrekende geometrie en de lijnen;
  - de stippen onder het tijdfilter (`drawTimeDots`).

### B. De tellers één keer per actie

- `drawClusters` roept `updateStats()` niet meer aan; `redrawAllClusters` doet
  het één keer aan het eind.
- De andere aanroepers van `drawClusters` riepen al `updateStats()` aan.
  `loadPocketZip` doet het nu ná `drawClusters`, zodat "locaties" klopt. De
  terugroep van de Overpass-geometrie en de weergave van een verzameling
  roepen het er nu bij aan.
- **Bijvangst:** met de bollen uit bleef "locaties" tot nu op het oude getal
  staan. `drawClusters` stopte dan voor `updateStats`. Nu staat het op 0.
- **Bijvangst bij een verzameling:** na het zetten van de zichtbaarheid worden
  ook de kleuren bijgewerkt (`recolorAll`). Tot nu kleurden de wegvakken van
  verborgen tellingen mee tot de volgende actie.

### C. Een lijn alleen opnieuw stijlen als zijn stijl verandert

- `zetStijl(line, st)` onthoudt de stijl als tekst (`line._stijl`). Bij
  dezelfde stijl roept hij `setStyle` niet aan. `recolorOne` gebruikt hem voor
  alle vier zijn stijlen.
- De hover op een wegvak (twee plekken) zet de lijn dik en daarna
  `_stijl = null`. De `recolorOne` bij het weggaan zet hem dan echt terug.

### D. Laden in een bundel, met voortgang

- **`ingestFiles` opent een bundel** (`bundelOpen`) en sluit hem in een
  `finally` (`bundelKlaar`).
- **In de bundel** onthouden `recolorAll`, `drawClusters`, `renderSessions`,
  `updateUI` en `updateStats` alleen dát het moet. `kaartOp` onthoudt het
  laatste kaartbeeld; zo gaan `fitBounds` en `setView` bij het laden.
  `bundelKlaar` doet alles één keer: eerst het kaartbeeld, dan kleuren, bollen,
  lijst, UI en tellers. Het eindbeeld is dat van de laatst geladen telling, net
  als voorheen.
- **Een teller (`diepte`):** twee keer laden door elkaar heen tekent niet
  halverwege.
- **Buiten een bundel** werkt alles direct, zoals voorheen: losse aanroepen en
  de tests die `loadZip` of `loadPocketZip` zelf aanroepen.
- **Voortgang** (Jay: "zorg wel dat er iets van een voortgangsindicatie is /
  blijft"):
  - "⏳ laden… k/n" per ZIP, zoals altijd;
  - daarna "⏳ kaart tekenen… (n tellingen)" tot de kaart klaar is.

  Telrapport wacht eerst een beeldje, of hooguit 100 ms, zodat die tekst ook
  echt te zien is. Een tabblad op de achtergrond krijgt geen beeldjes en mag
  niet blijven hangen.

## 2. Resultaat

**Dezelfde set van 185 tellingen, v3.48 tegen v3.49:**

| actie | v3.48 | v3.49 |
|---|---|---|
| 185 ZIP's laden | 279 s | 15 s |
| bollen (locaties) aan | 9,3 s | 0,29 s |
| clusterafstand 15 m | 9,4 s | 0,28 s |
| tijdfilter aan / schuiven / uit | 5,6 / 5,5 / 10,6 s | 0,26 / 0,22 / 0,31 s |
| groep Winkelstraat uit / aan | 1,2 / 9,3 s | 0,19 / 0,33 s |
| modusknop uit / aan | 1,1 / 2,1 s | 0,08 / 0,12 s |
| één telling uit / aan | 2,0 / 1,8 s | 0,06 / 0,07 s |
| solo / terug | 2,6 / 15,0 s | 0,15 / 0,50 s |

Gemeten op dezelfde machine. Die was niet helemaal ongestoord: er liepen af en
toe andere tests. De verhoudingen zijn betrouwbaarder dan de seconden.

**Wat er nu nog in het laden zit:** het aanmaken van 85.000 SVG-lijnen (een
zichtbare en een kliklijn per wegvak), en het tekenen daarvan door de browser.
Leaflet met `preferCanvas` zou dat sneller maken. Dat verandert wel de
tekenlaag, met hover en klik op lijnen, en is daarom niet in deze release
(backlog).

**Gelijk gebleven.** Na het laden en na elk van 16 acties zijn de kaart en de
export gelijk:

- de bollen per telling;
- de stijl van elk wegvak;
- de tellers;
- het kwaliteitsrapport;
- de sessielijst;
- de stippen en routes;
- de GeoPackage-lagen.

De acties zijn:

- bollen uit en aan, de clusterafstand;
- het tijdfilter aan, schuiven en uit;
- een groep uit en aan, een modusknop uit en aan;
- een telling uit en aan, het knopje fiets;
- solo en terug.

Er is één verschil, de bijvangst van B: "locaties" met de bollen uit. Dit is
gecontroleerd op twee sets:

- 46 ZIP's, met echte parkeer-, fiets-, pocket- en capaciteit-ZIP's uit de
  veld-apps;
- 185 ZIP's.

## 3. Tests

- **`snelheidtest.py`** (nieuw, 22): 150 gemaakte tellingen, met 28.750
  wegvakken.
  - Laden via de dropzone, met de voortgang "laden… 1/150", halverwege, en
    "kaart tekenen…". De grens is 60 s; lokaal 8 s.
  - `wegvakkenVan` en `bezoekenOp` zijn gelijk aan alles langs lopen.
  - "Locaties" = het aantal bollen; de tikken in de bollen = `clusterDekking`.
    Met de bollen uit staat "locaties" op 0.
  - Na een hover krijgt een wegvak zijn kleur terug.
  - Acties met een grens van 3 s; lokaal 50–430 ms: bollen, tijdfilter, groep,
    clusterafstand.
- **Bijgewerkt:**
  - `functest_kort.js`: `bezoekenOp`, `wkey` en `zetStijl` in zijn nagebouwde
    omgeving;
  - `functest_verzameling.js`: stubs voor `recolorAll` en `updateStats`.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | A–D |
| `index.html` | versie v3.49 |
| `_archief/overpass_rig/snelheidtest.py` | nieuw |
| `_archief/overpass_rig/functest_kort.js`, `functest_verzameling.js` | volgen de code |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py          ALLES OK — de 2 verwachte bestanden
snelheidtest.py      22/22
vergelijking         v3.48 = v3.49 op 46 en 185 tellingen, op "locaties" na (B)
volledige ronde lokaal: zie de PR
```
