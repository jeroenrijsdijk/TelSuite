# TrafficCounterSuite v2.26 — Overdracht

Kleine correctie in **`traffic_counter_help.html`**. Alleen dit bestand wijzigt; de rest is byte-identiek aan v2.25.

## Wat is aangepast

1. **`parkeer_reconstructie.html` toegevoegd** — aan de intro-kaart "Planning & Rapportage" (met korte omschrijving: route-consistente hersnap, richtingslaag, handmatige link-correctie) en aan het Bestanden-overzicht aan het eind, in dezelfde stijl als de andere tools.
2. **Telmodi-telfout gerepareerd.** De intro-kaart "Tellen" zei "6 verschillende tel-modi" maar toonde 7 links, waarvan twee (`telrapport.html`, `telplanning.html`) geen telmodi zijn — ze stonden al terecht in de kaart eronder. Nu: 5 teltools (Static, Autoparkeren, Fietsparkeren, Capaciteitstelling, Pocket), met de vermelding dat Pocket 4 sub-modi kent.

## Gevonden, nog niet opgelost — bewust met rust gelaten

**De Pocket-sectie documenteert alleen de `simpel`-submodus** (het scherm met Auto/Fiets/Voetganger/Iets Anders). De drie andere pocket-submodi — **transect** (richting A/B, moving-observer), **winkelstraat** (stilstaand/tegemoet) en **parkeren** (pocket-variant) — ontbreken volledig in de handleiding, inclusief het modus-keuzescherm dat daaraan voorafgaat. Dit is geen kleine fix maar het schrijven van in feite drie nieuwe secties; bewust niet meegenomen in deze release zodat de vorm eerst besproken kan worden.

Ook gesignaleerd, geen actie: `relabel_modus.py` en `recon_qgis_loader.py` staan niet in het Bestanden-overzicht (logisch, ze zijn van na de laatste keer dat de lijst is bijgewerkt); `snap_methodology.html`, `snaptrace.html` en `winkelstraat_rekenrig.html` worden nergens vanuit de handleiding gelinkt — vermoedelijk bewust (interne reference-/rig-tools, geen publieksdocumentatie), maar niet geverifieerd met Jay.

## Validatie

- **HTML-tagbalans** schoon.
- **Byte-identiteit:** sinds v2.25 wijzigde uitsluitend `traffic_counter_help.html`.
- Geverifieerd: `parkeer_reconstructie.html` komt 3× voor (twee content-links + het bestaande gebruik elders), de oude "6 tel-modi"-tekst is weg, de telrapport/telplanning-duplicatie in de Tellen-kaart is verwijderd.

## Backlog (ongewijzigd meegenomen, met bovenstaande nieuwe punten)

- **Pocket-submodi documenteren** (transect/winkelstraat/parkeren) in de handleiding — nieuw, uit deze scan.
- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
