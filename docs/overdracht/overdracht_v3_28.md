# Overdracht v3.28 — capaciteit in de GeoPackage, een kaartje in de _recon.zip, de introductie herschikt

De tweede helft van de lijst "kleine klussen zonder keuzes" (na v3.26):
- capaciteitsterreinen als eigen laag in de GeoPackage;
- de kaart-PNG naast de `_recon.zip`;
- `over.html` (en `about.html`) volgens de indeling van de voorpagina.

De kaart-PNG bleek een keuze te vragen. Jay: "De kaart png mag heel basic
zijn - gewoon om met een viewer even snel te kijken wat er in de zip zit.
Ondergrond is niet nodig. Netwerk en tikken is genoeg." Op de vraag waar hij
komt: in de ZIP.

De kolommen in de CSV's veranderen niet. De `_recon.zip` krijgt er een bestand
bij (`_kaart.png`, zie §2); de referentie is bijgewerkt.

## 1. GeoPackage: de laag `terreinen`

Tot nu toe ging capaciteit niet mee, en meldde de export dat. Nu staan de
capaciteitsvlakken van de kaart in een eigen laag.

- **Wat erin gaat:** precies de vlakken die telrapport tekent (`capLayers`),
  zichtbaar, met hun groep.
  - De groep hangt sinds deze versie aan het vlak (`poly._capGroep`).
  - Een terrein komt uit `_netwerk.csv` (POLYGON). Een straat uit een
    capaciteitstelling tekent telrapport ook als vlak (`L.polygon` sluit de
    lijn); die gaat dus net zo mee.
  - Een groep zonder geometrie staat niet op de kaart en gaat niet mee.
- **Kolommen:** `sessie_id`, `naam`, `osm_way_id`, `totaal`, `regulier`,
  `gehandicapt`, `laadpaal`, `gereserveerd`, `datum`, `teller`.
- **Geometrie:**
  - `POLYGON` met één ring, gesloten;
  - de schrijver kent sinds deze versie vlakken: WKB-type 3, met omhullende.
- **Stijl:** zoals op de kaart.
  - Paars vlak (`#8e44ad`, 18% dekking) met een rand van 0,66 mm.
  - Het totaal staat wit en vet in een paarse cirkel, binnen het vlak.
- **Project:** de laag heet *Capaciteit*. Hij ligt onderop en staat in de
  legenda.
  - Het kaartbeeld omvat de vlakken: het project zoomt op alle kaartlagen
    behalve de wegvakken.
- **Geen melding meer** dat capaciteit niet meegaat. In `export_info` is
  `niet_meegenomen` nu leeg. Het mechanisme blijft, voor later.

QGIS 3.34 draaide lokaal mee:
- de laag is geldig, met vulling en cirkellabel;
- het project geeft de lagenboom en de legenda met *Capaciteit*;
- de opmaak A4 is gerenderd en bekeken.

## 2. De kaart in de `_recon.zip`

`kaartPng()` in telreconstructie tekent een plaatje op een canvas.
`bouwZipBlob` legt het als `<sid>_kaart.png` in de ZIP, bij interactief
exporteren en in de batch.

- **Waarom deze naam:** dezelfde naam als in de ZIP's van de parkeer-apps. Er
  komt dus geen nieuwe naam in het schema, en wie de ZIP's verwerkt, kent het
  bestand al.
- **Wat erop staat:**
  - een wit vlak, zonder kaarttegels (die zijn niet CORS-schoon, en Jay wil
    geen ondergrond);
  - het wegennet in grijs: het netwerk van de reconstructie, ook als het
    vers is opgehaald;
  - het GPS-spoor gestreept in oranje, zoals op de kaart in de reconstructor;
  - de tikken in de kleur van die kaart. Onzeker is oker; ongesnapt staat
    niet op de kaart.
- **Kop:** `TELRECONSTRUCTIE <sessie_id>`, met daaronder de datum, het
  profiel en de aantallen (geplaatst, onzeker, ongesnapt).
- **Legenda:** elke soort met zijn aantal, het GPS-spoor en het wegennet. Ook
  de bronvermelding "wegennet © OpenStreetMap-bijdragers" en de versie.
- **Beeld:**
  - 1600 px breed; het kaartvlak is 700 tot 1600 px hoog;
  - het beeld omvat de tikken en het spoor, met 15% ruimte, en minstens zoveel
    als de veld-apps nemen;
  - Mercator, met dezelfde schaal in x en y.
- **Geen exporttijdstip** in het plaatje. Dezelfde reconstructie geeft zo
  byte voor byte hetzelfde bestand. In de veld-apps staat de tijd er wel in;
  dat maakte `hersteltest` wisselvallig (v3.27).
- **Zonder tikken en GPS** komt er geen plaatje, maar wel de ZIP. Mislukt het
  tekenen, dan gaat de ZIP ook zonder plaatje.
- **`RECON_VERSIE`** wordt v3.28, de regel van `valideer.py`.

## 3. `over.html` en `about.html`

Ze volgen nu de voorpagina (backlog sinds v2.69).
- **Onder *De werkwijze — drie stappen*:**
  - een alinea over de drie groepen van de voorpagina, en hoe die bij de
    stappen horen;
  - een alinea *Vooraf: plannen* over Telplanning. Die stond er nog niet in.
    De planning gaat als link naar de telefoon; pocket, autoparkeren en
    fietsparkeren tonen de straten en halen het wegennet van het hele gebied
    meteen op.
- **Stap 1:** de tools staan in de twee groepen van de voorpagina:
  - *Verkeer tellen — wat komt er langs*: Stilstaand tellen, en pocket Simpel,
    Transect en Winkelstraat;
  - *Parkeren tellen — wat staat er*: pocket Parkeren, Autoparkeren,
    Fietsparkeren, Auto-parkeercapaciteit, en de twee geplande opties.
  - Tot nu toe was de indeling stilstaand / parkeertellingen / wandelend
    tellen. Pocket Parkeren stond bij wandelend tellen.
- **De beschrijvingen bij de tools zijn ongewijzigd**, ook "niet de op de
  rijbaan" in `over.html` (Jay's tekst; in `about.html` stond het al goed).
  Alleen de namen van de pocket-modi kregen *Pocket:* ervoor, zoals op de
  voorpagina.
- **De GIS-alinea** noemt nu ook de parkeercapaciteit in de GeoPackage.

## 4. Tests

- **`gpkgtest.py`** 93 (was 82):
  - deel A maakt er een capaciteitstelling bij, als ZIP in elkaar gezet: een
    terrein en een groep zonder geometrie;
  - deel C:
    - `terreinen` is precies de vlakken op de kaart;
    - een POLYGON, gesloten, met de punten van `_netwerk.csv`;
    - de capaciteit per soort en het totaal;
    - de omhullende;
    - de stijl;
    - `niet_meegenomen` is leeg, en er komt geen melding;
  - deel G (QGIS): de vulkleur en het label met cirkel, de lagenboom en de
    legenda met *Capaciteit*, en vijf lagen in het project.
- **`gpkg_qgis.py`** leest de laag `terreinen`.
  - Bij het bouwen crashte QGIS op `ls.format().background()`: een verwijzing
    in een tijdelijk object. Het format wordt nu eerst bewaard.
- **`reconkaarttest.py`** (nieuw, 16):
  - een parkeertelling, gereconstrueerd;
  - `<sid>_kaart.png` in de ZIP: geldig en 1600 px breed;
  - in het gedecodeerde plaatje elke soort tik in zijn kleur, het wegennet
    grijs en het spoor oranje;
  - geen verzoek om kaarttegels;
  - twee keer exporteren geeft byte voor byte hetzelfde;
  - zonder tikken: geen plaatje, wel de ZIP.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | laag `terreinen`; vlakken in de schrijver; QML `vlakken`; project en legenda; de melding weg |
| `telreconstructie.html` | `kaartPng`, `_kaart.png` in de ZIP; `RECON_VERSIE` v3.28 |
| `over.html`, `about.html` | indeling van de voorpagina, plannen vooraf, capaciteit in de GIS-alinea |
| `traffic_counter_help.html` | GeoPackage met capaciteit; het kaartje bij de reconstructie |
| `zip_format_reference.html` | laag `terreinen`; `_kaart.png` in de `_recon.zip` |
| `index.html` | versie v3.28 |
| `_archief/overpass_rig/reconkaarttest.py` | nieuw |
| `gpkgtest.py`, `gpkg_qgis.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — 7 verwachte bestanden (tegen v3.27); gedeelde blokken OK; RECON_VERSIE v3.28
gpkgtest.py            93/93 (was 82; QGIS 3.34 deel G meegedraaid, opmaak als PNG bekeken)
reconkaarttest.py      16/16 (nieuw; het plaatje bekeken)
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
