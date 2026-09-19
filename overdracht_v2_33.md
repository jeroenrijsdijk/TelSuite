# TrafficCounterSuite v2.33 — Overdracht

Jay's handmatig bijgewerkte `over.html` en `traffic_counter_help.html` zijn ingepast. Alleen deze twee bestanden wijzigen t.o.v. v2.32; de rest is byte-identiek. (Dit is stap 1 van twee — de domein/product-rebrand volgt in v2.34.)

## Jay's wijzigingen (één-op-één overgenomen)

**over.html** — flink herschreven:
- Intro herschreven (TelSuite-framing eruit → "een set online browser-teltools"); tweede alinea toegevoegd over de laagdrempeligheid.
- Stap 1 fors uitgebreid met een volledige opsomming van alle telmodi (Stilstaand, Parkeertellingen, Wandelend/Moving Observer), inclusief de geplande opties.
- Stap 2: badge "optioneel" → "warm aanbevolen"; beschrijving herschreven.
- Onderaan: `.more-links` vervangen door drie CTA-knoppen (tellen / handleiding / zip-info); GIS-alinea met een QGIS-loader-link.
- Branding → "Built by JRI and Claude - Anthropic".

**traffic_counter_help.html** — klein:
- `build_bezocht.py` uit het Bestanden-overzicht gehaald.
- "Google Fonts (Oswald, Share Tech Mono)" uit de externe-dependencies-regel geschrapt.
- Branding → "Built by me and Claude - Anthropic".

## Reparaties (alleen markup, geen tekst aangeraakt)

In `over.html` twee tag-hygiëne-dingen die in de browser wél renderen maar door de tagbalans-validatie zakken:
1. Niet-gesloten `<p class="step-desc">Ga naar rvmk.nl…</p>` — botste met het sluiten van de step-card; `</p>` toegevoegd.
2. Losse `</p>` na de laatste CTA-knop — verwijderd.

## Aandachtspunt (bewust niet aangeraakt)

`over.html` bevat een placeholder-link voor het QGIS-loaderscript: `<a href="__volgt__">__volgt__</a>`. Duidelijk een "volgt nog"; niet gewijzigd. Vul te zijner tijd het echte pad in (bijv. een link naar `recon_qgis_loader.py` of een pagina daarover).

## Validatie

- **HTML-tagbalans** schoon op beide bestanden.
- **TOC-integriteit** (handleiding): alle ankers hebben een bestaand id; geen dubbele id's.
- **Byte-identiteit:** t.o.v. v2.32 wijzigden uitsluitend `over.html` en `traffic_counter_help.html`.

## Volgende stap

v2.34 — domein/product-rebrand: `rvmk.nl` → `telonline.org`, productnaam → "Telonline Verkeerstellingen", over alle betreffende bestanden.
