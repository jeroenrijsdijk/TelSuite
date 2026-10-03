# TrafficCounterSuite v2.34 — Overdracht

Domein/product-rebrand: **`rvmk.nl` → `telonline.org`** en productnaam **→ "Telonline Verkeerstellingen"**, over de hele suite. 12 bestanden gewijzigd t.o.v. v2.33; alle overige byte-identiek.

## Toegepaste regel

Elke plek behoudt z'n oorspronkelijke karakter:

| Was | Karakter | Wordt |
|---|---|---|
| `rvmk.nl` (URL's, header-spans, kaart-voetteksten, "ga naar", pageTitles) | domein | `telonline.org` |
| `RVMK.NL` (h3 op index) | domein (caps) | `TELONLINE.ORG` |
| `rvmk-parkeertelling` / `rvmk-fietsparkeren` (User-Agent + GPX `creator`) | interne identifier | `telonline-parkeertelling` / `telonline-fietsparkeren` |
| `TelSuite`, `TrafficCounterSuite`, `RVMK Verkeersteller` (titels, subtitels, JSON-LD alternateName) | productnaam | `Telonline Verkeerstellingen` |

## Gewijzigde bestanden (12)

- **index.html** — title-suffix, canonical, `og:url`, `og:site_name`, JSON-LD (`url`×2, `alternateName`, creator-`name`), de zichtbare `<h3>` (→ `TELONLINE.ORG`), en beide i18n-`pageTitle`s (EN+NL).
- **over.html** — title, meta-description (`telonline.org (Telonline Verkeerstellingen) is…`), canonical, de `<h1>` ("Wat is telonline.org?"), de openingszin, en "Ga naar telonline.org" in stap 1.
- **parkeertelling / fietsparkeren / capaciteitstelling** — header-`<span>`, de op de kaart-PNG ingebakken voettekst, de Overpass-`User-Agent` en de GPX-`creator`.
- **parkeer_reconstructie / winkelstraat_rekenrig** — page-title-suffix.
- **snap_methodology / zip_format_reference** — title + subtitel.
- **telplanning** — subtitel.
- **traffic_counter_help** — de "Online TelSuite"-kop → "Telonline Verkeerstellingen" (het redundante "Online" laten vervallen), plus de `over.html`-beschrijving in de bestandenlijst.
- **telrapport** — één code-comment (niet zichtbaar).

## Validatie

- **`node --check`** schoon op alle JS-dragende bestanden; **JSON-LD** in index.html parseert correct (nieuwe `alternateName` + `url`).
- **HTML-tagbalans** schoon op alle 12.
- **Merk-sweep:** geen `rvmk`/`RVMK`/`TelSuite`/`TrafficCounterSuite` meer in de suite, met één bewuste uitzondering (zie hieronder).
- **Byte-identiteit:** exact 12 bestanden gewijzigd t.o.v. v2.33.

## Bewuste keuzes / aandachtspunten (ter beoordeling)

1. **`telsuite_osm`** — de interne IndexedDB-cachenaam in `parkeer_reconstructie.html` is *niet* hernoemd. Niet zichtbaar voor gebruikers, en hernoemen zou de tile-cache van bestaande gebruikers wegvagen (ze her-cachen dan alles). Laten staan lijkt me juist; zeg het als je 'm toch mee wilt.
2. **Engelse referentie-docs** — `snap_methodology.html` en `zip_format_reference.html` zijn Engelstalig maar dragen nu de Nederlandse productnaam in hun titel/subtitel ("ZIP Format Reference — Telonline Verkeerstellingen"). Consistent met "productnaam overal", maar taalkundig gemengd. Wil je daar liever het (taalneutrale) domein `telonline.org`? Eén woord en ik pas die twee aan.
3. **`over.html` "Wat is telonline.org?"** — ik hield jouw domein-formulering aan (je schreef "Wat is rvmk.nl?", niet "Wat is TelSuite?"). Wil je daar juist de productnaam ("Wat is Telonline Verkeerstellingen?"), zeg het.
4. **capaciteitstelling `User-Agent`/`creator`** — die was al `rvmk-parkeertelling` (leende de parkeertelling-identifier), nu dus `telonline-parkeertelling`. Bestaande eigenaardigheid, faithful meegenomen; te wijzigen naar `telonline-capaciteitstelling` als je wilt.
5. **Release-ZIP-naam** — nog steeds `TrafficCounterSuite_vX.zip` (mijn interne artefactnaam voor de overdracht-keten, niet in de code/product). Kan mee-hernoemd worden als je dat netter vindt.

## Backlog (ongewijzigd, wacht op oppakken)

- **`parkeer_reconstructie.html` → `telreconstructie.html`** (bestand + alle verwijzingen).
- **Overpass fallback-helper** in `telrapport.html` (de twee losse `fetch()`-aanroepen zonder mirror-fallback).
- **Overpass-mirrornaam** `overpass.kumi.systems` → `overpass.private.coffee` (8 bestanden).
- `over.html`: `__volgt__`-placeholder invullen met de echte QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding (optioneel).
- Parkeren uit pocket halen; plakkerigheid-kernel naar telrapport; %bezet dag×uur; QGIS-loader joins.
