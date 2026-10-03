# TrafficCounterSuite v2.46 — Overdracht

Capaciteitscontouren (en hun labels) staan bij opstarten voortaan **uit**. Plus: Carto-key in telrapport gecontroleerd. Alleen `telrapport.html` wijzigt; de rest byte-identiek aan v2.45.

## 1. Capaciteitscontouren standaard uit

De contouren én de bijbehorende aantal-labels zitten allebei in `capNetwerkLayers` en worden door dezelfde knop ("capaciteitscontouren", groep Kaart) aangestuurd. Drie plekken bepaalden de begintoestand; alle drie nu op "uit":

| Plek | Was | Nu |
|---|---|---|
| Toggle-knop | `class="dot-btn active"` | `class="dot-btn"` (inactief) |
| Contouren (polygon/polyline) | direct `.addTo(map)` bij het laden | volgen de toggle-stand, net als de labels al deden |
| `resetAll()` | zette de toggle terug op **aan** | zet 'm terug op **uit** en verwijdert de lagen |

Die laatste was makkelijk over het hoofd te zien: zonder die aanpassing zouden de contouren na "Alle sessies verwijderen" alsnog terugkomen.

De labels hadden al een `capBtn.classList.contains('active')`-check (ze arriveren asynchroon en respecteerden de toggle dus al) — die logica is ongewijzigd en werkt nu vanzelf mee, omdat de knop bij opstarten inactief is.

`toggleCapNetwerk()` zelf is **niet** gewijzigd: één klik zet contouren én labels alsnog aan, precies zoals voorheen.

## 2. Carto-key gecontroleerd

De key komt correct door. `telrapport.html` heeft vier basemaps; alleen `positron` is een Carto-laag en die draagt de key:

```
https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=cb1_2a2n_1_3583b21ab7073b803a894288
```

De URL loopt via `cfg.url` naar de enige `L.tileLayer(...)` in `setBasemap()`, dus de key gaat mee in elk tegelverzoek. De andere drie basemaps (OSM, PDOK Topo, PDOK Luchtfoto) hebben geen Carto-key nodig. **Geen wijziging nodig.**

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- Zeven gerichte checks OK: knop niet meer standaard actief, contouren niet meer direct toegevoegd, contouren én labels volgen de toggle, reset zet ze uit, `toggleCapNetwerk` ongewijzigd, Carto-key aanwezig.
- **Byte-identiteit:** t.o.v. v2.45 wijzigde uitsluitend `telrapport.html`.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen naar de andere tel-modi.
- Overpass fallback-helper in `telrapport.html`; mirrornaam `overpass.kumi.systems` → `overpass.private.coffee`.
- `over.html`: `__volgt__`-placeholder invullen met de QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
