# Telapp suite

Verzameling standalone veldonderzoek-tools voor mobiliteit en infrastructuur in Nederland. Alle apps zijn enkelvoudige HTML-bestanden zonder framework of backend. Data wordt lokaal opgeslagen en geëxporteerd als ZIP met semikolom-CSV's, GPX en kaart-PNG.

## Bestanden

### Veldtellingen (mobile-first)

| Bestand | Functie |
|---|---|
| `index.html` | Startscherm — overzicht van alle tools |
| `traffic_counter.html` | Verkeerstelling vanaf vaste locatie |
| `traffic_counter_transect.html` | Verkeerstelling wandelend met live kaart |
| `kruispunttelling.html` | Kruispunttelling — 1–12 nummeringschema, hourly extrapolation |
| `parkeertelling.html` | Parkeerbezetting wandelend — auto, links/rechts per zijde |
| `fietsparkeren.html` | Fietsparkeerbezetting wandelend — fiets, wrak, brommer, breed |
| `capaciteitstelling.html` | Parkeercapaciteit per vak en terrein |
| `pocket_count.html` | Eén-knops pocket-telling — telefoon in jaszak |

### Analyse & planning (desktop)

| Bestand | Functie |
|---|---|
| `telrapport.html` | Kaartvisualisatie voor alle teltypen — sleep ZIPs |
| `telplanning.html` | Telplanning aanmaken én dekkings-analyse |
| `zip_format_reference.html` | Technische documentatie ZIP-formaten per app-type |
| `traffic_counter_help.html` | Helpcentrum voor alle tools |

### Server-side (planningen)

| Bestand | Functie |
|---|---|
| `planningen/planning_list.php` | Lijst van beschikbare opdrachten |
| `planningen/planning_save.php` | Opdracht opslaan vanuit telplanning |

### Tools

| Bestand | Functie |
|---|---|
| `build_bezocht.py` | Upgrade pocket-ZIPs naar v2.3 segment-aware formaat (Python stdlib, in-place) |

## Gebruik

Zet de HTML-bestanden in dezelfde map op een webserver. Geen installatie of buildstap nodig. Werkt in moderne mobiele browsers (Chrome/Safari op iOS en Android).

Vereist internetverbinding voor:
- Google Fonts (Oswald, Share Tech Mono)
- OpenStreetMap, CartoDB Positron en PDOK kaarttegels (Leaflet)
- Nominatim reverse geocoding (straatnaam)
- Overpass API (weggeometrie voor snapping)

Voor het opslaan van planningen op de server zijn PHP 5.6+ en een schrijfbare `/planningen/`-map vereist.

## Workflow

```
        veld                       desktop
   ┌───────────────┐          ┌─────────────────┐
   │ telapp        │   ZIP    │ telrapport      │
   │ (in jaszak)   │ ───────▶ │ (kaart-analyse) │
   └───────────────┘          └─────────────────┘
          ▲                            │
          │ opdracht                   │ dekkings-feedback
          │                            ▼
   ┌─────────────────────────────────────────┐
   │ telplanning                             │
   │ (gebiedselectie + dekkings-analyse)     │
   └─────────────────────────────────────────┘
```

## Features per app

### Parkeertelling / Fietsparkeren

- GPS-tracking met nauwkeurigheidsdrempel
- Realtime snapping op OSM-weggeometrie via Overpass API met L/R-weging per highway-type
- Kompas-fusie voor markerplaatsing loodrecht op de wegas
- Mini-kaart met bezochte wegvakken
- Crash recovery (localStorage)
- Wake Lock: scherm blijft aan tijdens veldwerk
- ZIP-export: CSV (sessie, telregels, straten, netwerk, gps), GPX, kaart-PNG (1920px)
- Planningsopdracht laden via URL (`?plan=/planningen/x.json`)

### Capaciteitstelling

- Twee modules: straat doorlopen (per parkeervak) en terrein op het oog (totaal-aantallen)
- Categorieën: regulier / gehandicapt / laadpaal / gereserveerd
- Automatische detectie van parkeerterreinen via OSM (`amenity=parking`)
- NPR-integratie met regime-editor voor sunset-data
- ZIP-export inclusief geometrie

### Transect / Pocket

- Wandelende telling met OSM-snapping
- Pocket: één-knops modus, lang indrukken voor undo
- Pocket v2.2: `_bezocht.csv` met visit-duur per wegvak — voor flux-analyse
- Pocket v2.3: wegvakken opgeknipt in ~40m segmenten — atomaire eenheid is `osm_way_id + segment_index`. Lange straten krijgen daardoor heat per segment in plaats van uniform per way.

### Telrapport

- Sleep meerdere ZIPs tegelijk (gemengde teltypen mogelijk)
- Warmtekaart per wegvak (auto: bezettingsgraad, fiets: √totaal)
- Clustering voor losse stippen (transect/pocket) met gap-slider
- Capaciteitsreferentielaag met nummerbadges
- Tijdfilter (3-uurs venster)
- Vier basemaps: OSM, CartoDB Positron, PDOK Topo grijs, PDOK Luchtfoto
- Sessielijst-interacties: klik (toggle), shift-klik (alles aan/uit), rechtsklik (solo), hover (dim andere)
- Pocket zero-visit detectie: dashed lijn voor wegen die zijn doorlopen zonder telling

### Telplanning

- **Maken**-modus: gebied tekenen, wegen selecteren, planning naar server
- **Dekking**-modus: pocket-ZIPs laden, dagdeel-matrix (6×3 cellen), kleur per dekking
- Wegtype-filters (8 categorieën)
- Opdrachten direct starten in de juiste telapp

## ZIP-formaat

Per teltype een vaste set CSV-bestanden. Korte samenvatting:

| app_type | _sessie | _straten | _netwerk | _capaciteit | _telregels | _gps | _bezocht |
|---|---|---|---|---|---|---|---|
| auto | ✓ | ✓ | ✓ | — | optioneel | optioneel | — |
| fiets | ✓ | ✓ | ✓ | — | optioneel | optioneel | — |
| capaciteit | ✓ | — | aanbevolen | ✓ | optioneel | optioneel | — |
| transect | ✓ | — | — | — | ✓ | optioneel | — |
| pocket | ✓ | — | aanbevolen | — | optioneel | aanbevolen | aanbevolen |

Volledige specificatie in `zip_format_reference.html`.

## KNIME-koppeling

- Sleutel pocket v2.3: `(sessie_id, osm_way_id, segment_index)`
- Sleutel andere apps: `(sessie_id, osm_way_id)` — geen segmenten
- `osm_way_id` koppelt telregels ↔ netwerk
- Straten gegroepeerd op `osmName`, niet op Nominatim-string
- Datum-formaat: `YYYY-MM-DD`
- Voor pocket-flux: `n_tellingen × 60 / duur_sec = passages/min` (uit `_bezocht.csv`, nu per segment)
- Oude v2.2 pocket-ZIPs upgraden met `python build_bezocht.py FILE_OR_DIR`

## Technische stijlgids

- Font: Oswald (Share Tech Mono voor monospace)
- Achtergrond: `#f0f0ec`
- CSV: puntkomma-gescheiden, punt als decimaalteken, UTF-8
- Navigatie: elke pagina heeft een ← Menu link naar `index.html`

Kleurcodering app-types:

| Type | Kleur |
|---|---|
| auto | `#c07800` amber |
| fiets | `#2980b9` blauw |
| capaciteit | `#8e44ad` paars |
| transect | `#5500cc` violet |
| pocket | `#d4007a` roze |

## Versie

Huidige release: **v2.3** — zie `overdracht_v2_3.md` voor de technische overdracht. Pocket wegvakken zijn nu opgeknipt in ~40m segmenten; oude v2.2 ZIPs upgraden via `build_bezocht.py`.
