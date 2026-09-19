# TrafficCounterSuite v2.32 — Overdracht

Carto vereist sinds kort een API-key voor hun rasterbasiskaarten (`basemaps.cartocdn.com`) — bevestigd via de officiële Carto-documentatie. Jay's key is toegevoegd op alle drie de plekken in de suite die een Carto-laag gebruiken.

## Gewijzigde bestanden

| Bestand | Wijziging |
|---|---|
| `telplanning.html` | Carto-URL (`positron`-basemap) krijgt `?key=…` |
| `telrapport.html` | Carto-URL (`positron`-basemap) krijgt `?key=…` |
| `parkeer_reconstructie.html` | Carto-URL (`grijs`-basemap) **gemoderniseerd** van het oude Fastly-domein naar hetzelfde endpoint als de andere twee, + `?key=…` |

Alle overige bestanden zijn byte-identiek aan v2.31.

## Wat er precies gebeurde

**Drie Carto-referenties in de hele suite**, geen andere (gecontroleerd op zowel `cartocdn` als het bredere `carto`; de treffer in `traffic_counter_help.html` is een vals alarm — "carto**grafie**").

`telplanning.html` en `telrapport.html` gebruikten al hetzelfde moderne endpoint (`{s}.basemaps.cartocdn.com/light_all/…`); daar is alleen `?key=cb1_2a2n_1_3583b21ab7073b803a894288` achter de URL gezet.

`parkeer_reconstructie.html` gebruikte een **ander, ouder Fastly-domein** (`cartodb-basemaps-{s}.global.ssl.fastly.net`) — terwijl de eigen code-comment daar al zei *"URL byte-identiek aan telrapport.html"*. Dat klopte niet meer; een stille drift die al langer in de code zat. Carto zelf probeert dit Fastly-domein al jaren uit te faseren ten gunste van `basemaps.cartocdn.com`. In plaats van de key op het verouderde domein te plakken (onzeker of dat domein de key eigenlijk wel honoreert, en het blijft een aflopende zaak), is de URL gemoderniseerd naar exact hetzelfde endpoint als de andere twee tools — waarmee de bestaande comment nu ook weer klopt.

Resultaat: alle drie de basemap-URL's zijn nu **byte-identiek**:
```
https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=cb1_2a2n_1_3583b21ab7073b803a894288
```

## Validatie

- **`node --check`** schoon op alle drie de bestanden.
- **HTML-tagbalans** schoon op alle drie.
- **URL-gelijkheid:** geverifieerd dat alle drie de basemap-URL's exact dezelfde string zijn (domein + pad + key).
- **Byte-identiteit:** t.o.v. v2.31 wijzigden uitsluitend `telplanning.html`, `telrapport.html`, `parkeer_reconstructie.html`. Geen ander bestand aangeraakt.
- Bevestigd dat het oude Fastly-domein nergens meer voorkomt in de suite.

## Kanttekening

De key is een publieke, rate-limited tile-key (bedoeld om client-side in de browser-URL te staan, net als bij Google Maps-achtige diensten) — geen geheime server-credential. Embedding in de HTML-broncode is hoe Carto de key zelf bedoelt te gebruiken; niets bijzonders aan de hand qua veiligheid.

## Backlog (ongewijzigd)

- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding (optioneel, Jay's keuze).
- `zip_format_reference.html`: geen verdere wijziging nodig — dit was een basemap-fix, geen schema-wijziging.
- Engelse variant van `over.html`, als gewenst.
- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
