# Overdracht v2.53 — alleen nog het huidige formaat

Alle oude bestanden zijn omgezet en nieuwe data komt alleen nog in de huidige
vorm binnen, dus de versie-etiketten en de terugvalpassages waren ruis geworden.
Drie documentatiebestanden, samen −2.664 bytes. Geen code gewijzigd.

| Bestand | Verschil |
|---|---|
| `zip_format_reference.html` | −1.330 |
| `traffic_counter_help.html` | −1.017 |
| `snap_methodology.html` | −317 |

---

## 1. Leidraad

Weg gaat wat een ZIP van vroeger beschrijft of hoe je die bijwerkt. Blijft staan
wat vandaag nog geldt — alleen zonder het versie-etiket ervoor. Een noot als
"v2.8 — trajectory-corrected: …" beschrijft geen oud formaat maar hoe het nu
werkt; die houdt zijn inhoud en verliest zijn prefix.

## 2. `zip_format_reference.html`

**Verwijderd**
- "For v2.2 ZIPs without this column, tools interpret it as 0" bij
  `segment_index`.
- De noot over `build_bezocht.py` die oude pocket-ZIPs naar v2.3 tilde, en het
  aanhangsel dat uitlegde dat dat script niet trajectory-aware is.
- De hele alinea **Legacy note** over reconstructies van vóór v2.24 die een lege
  `modus` op `parkeren` zetten, inclusief de verwijzing naar `relabel_modus.py`.
- Bij de modusletter: dat oudere pocket-ZIPs nog een kaal `_pkt` kunnen zijn en
  dat `voeg_modusletter_toe.py` die bijwerkt.
- In de regel over type-herkenning: "or legacy sessions", en `relabel_modus.py`
  als tweede toepasser van die regels. De reconstructor blijft staan.

**Etiketten eraf, inhoud intact**
- Bestandsomschrijvingen in de pocket-lijst: `(v2.3+)`, `(v2.8)`, `(v2.9)`, en
  de vergelijking "v2.3: per (way, segment) instead of per way".
- Vier csv-titels: `_telregels.csv (v2.3+, conf columns v2.8, gps columns v2.9)`,
  `_gps.csv (v2.3+)`, `_netwerk.csv (v2.3+)`, `_bezocht.csv (v2.3+)`.
- Vier noot-prefixen: `v2.8 — conf/conf_level`, `v2.9 — gps_stab/gps_level`,
  `v2.8 — trajectory-corrected`, `v2.8:` bij `_gps.csv` en bij `_bezocht.csv`.
- In de reconstructietabel: `(v2.23+)` bij `_straten.csv` en `(v2.20+)` bij
  `_segmentsamenvatting.csv`.

## 3. `traffic_counter_help.html`

- De kaart **"Oude pocket-ZIPs opwaarderen"** in de pocket-exportsectie, met de
  drie `build_bezocht.py`-commandoregels en de voetnoot dat ZIPs zonder
  netwerkgeometrie niet retro-converteerbaar zijn.
- De tip bij de dekkingsmatrix die daarnaar terugverwees.

`build_bezocht` komt nu nergens meer voor in de handleiding.

## 4. `snap_methodology.html`

- De sectie **"build_bezocht.py is not on this path"**, die uitlegde waarom dat
  server-side pad geen adjacency-bewustzijn had.

---

## 5. Eén ding dat ik niet stilletjes heb aangepast

De reconstructor schrijft **twee versiestempels die het niet met elkaar eens
zijn**, en allebei zijn het bevroren letterlijke strings:

| Waar | Waarde |
|---|---|
| `_sessie.csv`, kolom `reconstructie` | `v2.24` (hardcoded, r.1802) |
| `_reconstructie_log.csv`, sleutel `reconstructie_versie` | `v2.18` (hardcoded, r.1820) |

Geen van beide volgt de echte versie. Ik heb ze laten staan, want `reconstructie`
is een waarde die in KNIME kan worden gefilterd — dat is jouw sign-off, niet de
mijne. In de referentie staat nu eerlijk dat het "currently the literal string
`v2.24`" is in plaats van "e.g. v2.24", zodat niemand het voor een
versie-annotatie aanziet.

## 6. Terugvalcode in de tools — bewust niet aangeraakt

Je zei "passages", dus ik heb de documentatie gedaan en de code met rust
gelaten. Maar er staat wel degelijk terugvalcode, en die is nu dood:

| Plek | Wat |
|---|---|
| `telrapport.html` r.998, r.1736 | v2.2-pad: rij zonder `segment_index` → `segIdx=0` |
| `telrapport.html` r.1044 | ontbrekende kolom bij oudere ZIP → `null` |
| `telrapport.html` r.1872 | **haalt geometrie via Overpass op als `netCSV` ontbreekt** — expliciet "backwards compat met heel oude pocket-ZIPs" |
| `telrapport.html` r.2090 | tikken uit `wayData` als `visitData` geen `nTel` heeft |
| `telplanning.html` r.885 | v2.2-ZIPs zonder `segment_index` → `segIdx=0` |

Die op r.1872 is de interessante: dat is een van de laatste Overpass-aanroepen in
de suite, en hij bestaat alleen voor ZIPs die niet meer bestaan. Weghalen
betekent één netwerkverzoek minder en een stuk minder code in de pocket-lader.

Ik zou dat wel apart houden van deze release. Documentatie weghalen is
omkeerbaar en onschadelijk; een terugvaltak weghalen is dat niet, en als er
ergens nog één niet-omgezette ZIP in een map staat, faalt hij stil in plaats van
luid. Als je wilt kan ik ze schrappen en er een expliciete melding voor
terugzetten ("deze ZIP mist `_netwerk.csv` en is van vóór de omzetting"), zodat
falen zichtbaar is.

---

## 7. Validatie

```
JS-syntax (node --check)                    15/15 OK
HTML-tagbalans, vergeleken met v2.52        geen afwijking
byte-identiteit                             precies 3 bestanden gewijzigd
gedeelde blokken byte-identiek              6 groepen OK
functionele tests                           34 + 18 + 16 + 9 OK
resterende legacy-verwijzingen in docs      0
```
