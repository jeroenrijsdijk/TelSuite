# Overdracht v3.2 — QGIS-project in de GeoPackage

Jay, na v3.1: "Static hoef je niet te kunnen exporteren als GeoPackage. Je kunt
nu het QGIS-project maken." Dit is stap 2: in de GeoPackage uit telrapport zit
nu ook een QGIS-project. Dat zet de hele kaart in één keer klaar, inclusief een
printopmaak.

---

## 1. Wat er nieuw is

**Openen:** *Project → Openen vanuit → GeoPackage*, of in het Browser-paneel
het bestand openklappen en dubbelklikken op *telrapport*. Je krijgt:

- de lagen in de goede volgorde, met leesbare namen: *Clusterbollen,
  Waarnemingen, GPS-spoor, Wegvakken*, elk met de opmaak uit v3.1;
- **RD New** (EPSG:28992);
- de groep *Ondergrond*:
  - **PDOK BRT-A grijs** staat aan. PDOK levert die in RD, dus scherp; OSM-tegels
    in een RD-project worden vervormd en vaag.
  - PDOK-luchtfoto en OpenStreetMap staan uitgevinkt klaar.
- ingezoomd op de telling;
- de printopmaak **A4 liggend**:
  - de kaart op het kleinste ronde schaalgetal waarop alles past;
  - een titel met de datum(s), en een ondertitel (aantal tellingen, soorten, wat
    een clusterbol is);
  - een legenda met Waarnemingen, GPS-spoor en Wegvakken;
  - een schaalstok, een noordpijl, en een bronvermelding (PDOK, OpenStreetMap
    voor het wegennet, telonline.org, datum).

**Slepen werkt nog net als in v3.1**, met opmaak per laag.

**Je kiest de naam bij het opslaan.**

- In Edge en Chrome opent een *Opslaan als*-venster.
- In andere browsers vraagt telrapport de naam en downloadt het bestand dan.

## 2. Waarom je de naam kiest, en niet hernoemt

In QGIS uitgezocht (3.34). Een project in een GeoPackage verwijst naar zijn
lagen als `./<bestandsnaam>|layername=…`, relatief aan de map:

| actie | project vindt zijn lagen? |
|---|---|
| bestand verplaatsen naar een andere map | ja |
| bestand hernoemen | **nee** (0 van 4) |

Een padvorm voor "dit bestand zelf" bestaat niet. Getest: `''`, `.`, `./`.
Daarom moet de naam vastliggen **voordat** het project geschreven wordt:

- Met `showSaveFilePicker` (het Opslaan-als-venster) is de naam die de
  gebruiker kiest precies de naam die in het project komt. Bij een bestaand
  bestand vraagt het venster om te overschrijven, in plaats van er "(1)" achter
  te zetten zoals een download doet.
- Het venster moet in dezelfde klik openen. Daarom staat er in
  `exportGeoPackage` vóór `gpkgKiesBestand` geen `await`.
- Zonder dat venster (Firefox, Safari): `prompt` met het voorstel, daarna een
  download onder die naam.
- Annuleren schrijft niets.

Hernoemt iemand het bestand toch, dan werkt slepen nog wel. Alleen het project
vraagt dan om de lagen. De handleiding zegt het, en de ZIP-referentie ook.

## 3. Wat QGIS minimaal nodig heeft

Een project dat QGIS zelf schrijft is 237 kB; het onze is ongeveer 24 kB. Vier
dingen die ik bij het afslanken tegenkwam:

1. **CRS-definitie.** `<spatialrefsys>` met alleen `<authid>` is ongeldig. Lagen
   overleven dat (hun bron geeft het CRS), het project en de opmaak niet.
   Mét de proj4-regel erbij herkent QGIS de EPSG-definitie. De transformatie is
   identiek aan EPSG:28992 (0,0 m verschil).
2. **Project-CRS.** Dat telt pas met
   `<SpatialRefSys><ProjectionsEnabled>1</ProjectionsEnabled></SpatialRefSys>`
   in de properties.
3. **Laag-id's.** Korte id's (`route`, `wegvakken`) vervangt QGIS door een
   nieuwe id. Daarna wees de legenda in de opmaak naar niets, en bleef hij leeg.
   Met `<naam>_telrapport` blijven alle id's staan.
4. **Kaartbeeld in de opmaak.** Dat moet de verhouding van het kaartvlak hebben,
   anders rekent QGIS de schaal uit de breedte. De testtelling (noord-zuid langs
   één straat) gaf eerst 1:63 en een lege kaart. Nu: het kleinste ronde
   schaalgetal uit 250, 500, 750, 1000, 1250, … waarop de telling plus marge
   past, gecentreerd.

**RD in de browser.** Voor het kaartbeeld moet telrapport WGS84 naar RD
omrekenen. Dat doen de benaderingsformules van Schreutelkamp & Strang van Hees
(± 20 regels, geen bibliotheek). Tegen PROJ: overal 0,30 m. Ruim genoeg voor
een kaartbeeld; de data zelf blijft WGS84, en QGIS rekent die exact om.

**De stijl in het project** is dezelfde QML als in `layer_styles`, zonder de
`<qgis>`-schil. `labelsEnabled` gaat naar het `<maplayer>`-element.

**Tekst in de opmaak:** `fontWeight="50"` (normaal), nergens vet.

- Met Arial, dat alleen Regular en Bold heeft, kiest Qt bij 50 de Regular-letter,
  zowel in Qt5 (QGIS 3) als in Qt6 (QGIS 4).
- Vet zou weer het verschil tussen 75 en 700 raken (zie v3.1).

**De legenda in de opmaak** laat de clusterbollen weg. Hun taartkleuren zijn
dezelfde als bij Waarnemingen. De ondertitel legt in één zin uit wat een bol
is. In het lagenpaneel staan de taartpunten wel.

## 4. Kleiner meegenomen

- **Sessielabels** (route-legenda, ook al in v3.1):
  - de parkeer-apps hebben een `start_tijd` met datum, waardoor er "2026-" als
    tijd stond;
  - de teller "(onbekend)" kwam erin.

  Nu: "09-10-2026 · 09:31 · parkeren".
- **Static** staat niet meer in de melding "nog niet in deze export": het hoort
  er niet in. Capaciteit blijft gemeld.
- `GPKG.maak(SQL, lagen, project)`: het derde argument is optioneel en schrijft
  `qgis_projects` in dezelfde vorm als QGIS. Die tabel staat ook bij QGIS niet
  in `gpkg_contents`.

## 5. Tests

`gpkgtest.py` gaat van 55 naar **80 tests**.

- **Opslaan-als.** Het venster bestaat niet zonder scherm; de test bootst het na.
  Het geeft een naam terug en vangt de bytes op.
- **C, project in het bestand:**
  - precies één project `telrapport`;
  - `.qgz` als hex met `telrapport.qgs`;
  - geldige XML;
  - lagen verwijzen naar de gekozen naam;
  - id's eindigen op `_telrapport`.
- **E, correctiemodus:** weigert nog vóór het Opslaan-als-venster.
- **F, naam kiezen (nieuw):**
  - annuleren schrijft niets;
  - zonder het venster wordt de naam gevraagd, met het voorstel als
    standaardwaarde, en heet de download zoals gekozen;
  - het project verwijst naar die naam;
  - annuleren van de vraag geeft geen download.
- **G, QGIS:** het bestand gaat naar een andere map en het project wordt daar
  geopend. Gecontroleerd:
  - CRS EPSG:28992;
  - de lagenboom met zichtbaarheid, en de groep *Ondergrond*;
  - de vier kaartlagen zijn geldig, met id en opmaak (taart, categorieën);
  - de drie ondergronden met de juiste WMTS-bron;
  - het standaardbeeld omvat de telling;
  - de opmaak heeft alle onderdelen, een rond schaalgetal, de telling volledig
    in beeld, en een legenda die aan de lagen gekoppeld is;
  - titel en bronvermelding;
  - de opmaak wordt als PNG geëxporteerd;
  - de RD-benadering wijkt minder dan 1 m af van PROJ;
  - een naam met een spatie werkt ook.

  Hernoemd openen wordt als **BEKEND** gemeld: 0 van 4 lagen.

Gedraaid tegen **QGIS 3.34.4**. De PDOK-lagen konden hier niet laden (geen
internet in de testomgeving). De bron is gecontroleerd tegen de
GetCapabilities van PDOK: `grijs` en `Actueel_ortho25`, matrixset
`EPSG:28992`.

## 6. Nog te doen door Jay

In QGIS 4 het project openen en controleren:

- laadt PDOK grijs?
- staat het kaartbeeld goed?
- zijn de teksten in de opmaak normaal, niet dun en niet vet?
- de opmaak eens als PDF exporteren.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `GPKG_PROJECT` (RD-benadering, kaartbeeld, projectsjabloon met opmaak); `gpkgKiesBestand`, `gpkgProjectInhoud`; `GPKG.maak` met `qgis_projects`; `exportGeoPackage` kiest eerst de naam; sessielabel; Static uit de melding |
| `traffic_counter_help.html` | sectie GeoPackage: naam kiezen, project openen, slepen |
| `zip_format_reference.html` | `qgis_projects`, bestandsnaam als onderdeel van het project |
| `index.html` | versie v3.2 |
| `_archief/overpass_rig/gpkgtest.py`, `gpkg_qgis.py` | project, naam kiezen; 80 tests |
| `_archief/overpass_rig/valideer.py`, `README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py        ALLES OK — 4 verwachte bestanden gewijzigd; 12 groepen gedeelde blokken OK
gpkgtest.py        80/80 (QGIS-deel tegen QGIS 3.34.4)
opruimtest.py      52/52
hersteltest.py     133/133
laadtest.py        46/46
statictest.py      24/24
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
