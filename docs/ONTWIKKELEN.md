# Telonline Verkeerstellingen

Losse HTML-tools voor Nederlandse verkeers- en parkeertellingen, online op
**telonline.org**. Elk hulpmiddel is één HTML-bestand: geen framework, geen
buildstap, geen account, geen backend (op het opslaan van planningen na).
Veldwerk op de telefoon (iPhone/Safari), verwerking op de desktop.

Dit bestand is de plattegrond. Wat er nu speelt, welke afspraken vastliggen en
wat er op de backlog staat, staat in **`docs/OVERDRACHT_STAND_VAN_ZAKEN.md`** —
begin daar bij een nieuwe sessie.

## Werkwijze

```
  telplanning ──opdracht──▶ veld-app ──ZIP──▶ telreconstructie ──_recon.zip──▶ telrapport
  (vooraf)                  (telefoon)         (optioneel, desktop)             (kaart + analyse)
       ▲                                                                              │
       └──────────────────────────── dekking terug ───────────────────────────────────┘
```

Tellen levert per sessie een ZIP met semikolon-CSV's. Reconstrueren is
optioneel: het legt de route opnieuw op het wegennet, bepaalt de looprichting en
zet parkeertikken aan de juiste kant van de weg. Telrapport leest ruwe en
gereconstrueerde ZIP's door elkaar. QGIS is een alternatief eindpunt (zie
Scripts); de ZIP's gaan verder een KNIME-pijplijn in.

## Bestanden

### Veld (telefoon)

| Bestand | Rol |
|---|---|
| `traffic_counter.html` | Static — tellen vanaf een vast punt |
| `parkeertelling.html` | autoparkeren, lopend langs een traject |
| `fietsparkeren.html` | fietsparkeren, idem |
| `capaciteitstelling.html` | parkeercapaciteit per vak en per terrein |
| `pocket_count.html` | Pocket — telefoon in de zak; vier sub-modi: simpel, transect, winkelstraat, parkeren. `pocket_count.html#parkeren` start meteen in parkeren |

### Desktop

| Bestand | Rol |
|---|---|
| `telplanning.html` | planning maken en dekking beoordelen |
| `telreconstructie.html` | nabewerking: hersnappen, richting, handmatige correctie |
| `telrapport.html` | kaartvisualisatie en analyse, ook van verzamel-ZIP's |

### Publiek en documentatie

| Bestand | Rol |
|---|---|
| `index.html` | startscherm (NL/EN) |
| `over.html` | introductie voor nieuwe bezoekers |
| `traffic_counter_help.html` | handleiding — de functies per tool staan hier |
| `zip_format_reference.html` | technische specificatie van alle ZIP's en CSV's (EN) |

### Intern — bewust niet gelinkt

| Bestand | Rol |
|---|---|
| `snap_methodology.html` | uitleg van de snap-methodiek (EN) |
| `snaptrace.html` | rig: GPS-spoor tegen OSM bekijken |
| `winkelstraat_rekenrig.html` | rig: rekenmodel winkelstraat |

### Server

`planningen/` — `planning_list.php`, `planning_save.php`, `planning_delete.php`.
Nodig voor het bewaren van planningen vanuit `telplanning.html`: PHP 5.6+ en een
schrijfbare map `/planningen/`. Zonder server werkt de rest gewoon.

### Scripts

| Script | Waar | Doel |
|---|---|---|
| `build_bezocht.py` | hier | upgradet oude pocket-ZIP's (v2.2) naar het segmentformaat; alleen voor oud materiaal |
| `telonline_qgis_loader.py` | telonline.org | laadt een map met ZIP's in QGIS, één laag per teltype |
| `relabel_modus.py`, `voeg_modusletter_toe.py` | buiten de suite | omzetting van het archief — klaar, bewaard voor een verdwaalde oude ZIP |

### Overige mappen

- `docs/overdracht/overdracht_v2_XX.md` — per release een overdracht; oudere in `_archief/`.
- `VELDTEST_3.0.md` — draaiboek voor de veldtest op de iPhone vóór versie 3.0.
- `_archief/overpass_rig/` — regressietests en `valideer.py`; zie de README daar.
- `_archief/` verder — eerdere rigs en prototypes, alleen ter naslag.

## Plaatsen

Zet alles in één map op een webserver en klaar. De tools linken relatief naar
elkaar, en de knop "Direct reconstrueren" geeft de ZIP via IndexedDB door —
daarvoor moeten veld-app en reconstructor op dezelfde origin staan.

Wat er van buiten wordt opgehaald:

- **Bibliotheken** via CDN (cdnjs, unpkg): Leaflet 1.9.4, JSZip 3.10.1,
  PapaParse 5.4.1, Leaflet.draw 1.0.4 (alleen telplanning).
- **Lettertypen**: Google Fonts (Oswald, Share Tech Mono).
- **Kaarttegels**: OpenStreetMap, CARTO, PDOK. De CARTO-sleutel staat in drie
  bestanden: `telrapport.html`, `telplanning.html`, `telreconstructie.html`.
- **Wegennet**: Overpass API, twee endpoints (overpass-api.de en
  private.coffee), met een gedeelde tegel-cache in IndexedDB.
- **Straatnaam**: Nominatim, in de veld-apps.
- **Weer**: Open-Meteo, in telrapport.

Tellingen zelf verlaten de browser niet: ze gaan alleen als ZIP naar de
gebruiker. Wat wel naar buiten gaat zijn de verzoeken hierboven, en die
verraden het gebied of de positie waar je telt.

## Conventies

- **CSV**: puntkomma als scheidingsteken, punt als decimaalteken, UTF-8.
- **ZIP-namen**: `_car` auto · `_fts` fiets · `_cap` capaciteit ·
  `_pkt_<s|t|w|p>` pocket per sub-modus · `_sta` Static (sinds v2.73). Na reconstructie `<sessie_id>_recon.zip`
  (de `sessie_id` zelf verandert niet). Een bewaarde kaart:
  `TelVerzameling_<jjjjmmdd>.zip`. Het oude `_trn`-formaat wordt alleen nog
  gelezen.
- **Schema**: elke wijziging aan kolommen of sleutels eerst langs KNIME. De
  specificatie in `zip_format_reference.html` wordt door een test tegen de
  exportcode bewaakt.
- **Gedeelde code**: blokken die in meer bestanden voorkomen (o.a.
  `HIGHWAY_RE`, de Overpass-afhandeling, de tegel-cache, de segmentatie) moeten
  byte-identiek blijven. `valideer.py` controleert dat.
- **Taal**: interfaces en handleiding Nederlands; technische referentie Engels.
- **Metadata**: Open Graph wel, Twitter/X-kaarten niet.
- **Huisstijl**: Oswald, met Share Tech Mono als monospace.

## Ontwikkelen

Wijzigingen zo additief mogelijk; alles wat niet bedoeld is te veranderen blijft
byte-identiek aan de vorige release. Per release: `valideer.py` (JS-syntax,
tagbalans, byte-identiteit, gedeelde blokken), de functionele tests uit
`_archief/overpass_rig/`, en een nieuwe `docs/overdracht/overdracht_v2_XX.md`. Het versienummer
onderaan `index.html` gaat elke release omhoog; `valideer.py` controleert dat.
