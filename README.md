# Telapp suite

Verzameling standalone veldonderzoek-tools voor mobiliteit en infrastructuur in Nederland. Alle apps zijn enkelvoudige HTML-bestanden zonder framework of backend. Data wordt lokaal opgeslagen en geëxporteerd als semikolom-CSV.

## Bestanden

| Bestand | Functie |
|---|---|
| `index.html` | Startscherm |
| `traffic_counter.html` | Verkeerstelling vanaf vaste locatie |
| `traffic_counter_transect.html` | Verkeerstelling wandelend met live kaart |
| `traffic_counter_help.html` | Helppagina verkeerstelling |
| `parkeertelling.html` | Parkeerbezetting wandelend, links/rechts per zijde |

## Gebruik

Zet de bestanden in dezelfde map op een webserver. Geen installatie of buildstap nodig. Werkt in moderne mobiele browsers (Chrome/Safari op iOS en Android).

Vereist internetverbinding voor:
- Google Fonts (Oswald)
- OpenStreetMap kaarttegels (Leaflet)
- Nominatim reverse geocoding (straatnaam)
- Overpass API (weggeometrie voor snapping)

## Parkeertelling — features

- GPS-tracking met nauwkeurigheidsdrempel (≤25m)
- Realtime snapping op OSM-weggeometrie via Overpass API
- Telling per type (Goed / Fout / Leeg / Speciaal) en per zijde (Links / Rechts)
- Bezochte wegvakken gekleurd op kaartexport
- Wake Lock: scherm blijft aan tijdens veldwerk
- Export: semikolom-CSV + PNG-kaart (1920px breed)
- Veiligheidsnet: download wordt getriggerd bij sluiten pagina als nog niet gebeurd

## CSV-structuur parkeertelling

```
nr;tijdstip;type;zijde;straat;lat_marker;lon_marker;lat_gps;lon_gps

# Samenvatting
type;links;rechts;totaal

# Bezettingsgraad per straat
straat;goed;fout;leeg;spec;bezet;vrij;bezettingsgraad_pct

# GPS-track
tijdstip;lat;lon;nauwkeurigheid_m
```

## Technische stijlgids

- Font: Oswald
- Achtergrond: `#f0f0ec`
- CSV: puntkomma-gescheiden, punt als decimaalteken, UTF-8
- Navigatie: elke pagina heeft een ← Menu link naar `index.html`
