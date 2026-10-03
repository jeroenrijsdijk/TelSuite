# TrafficCounterSuite v2.27 — Overdracht

Grote aanvulling op **`traffic_counter_help.html`**: de drie ontbrekende Pocket-submodi zijn uitgeschreven, plus de QGIS-loader is toegevoegd aan het Bestanden-overzicht. Alleen dit bestand wijzigt; de rest is byte-identiek aan v2.26.

## Wat is toegevoegd

**QGIS-loader in Bestanden-overzicht.** `recon_qgis_loader.py` staat nu naast `build_bezocht.py` in de bestandenlijst, met een korte omschrijving (recursief laden, één laag per telptype, samengevoegde netwerklaag).

**Pocket-submodi volledig uitgeschreven.** De handleiding documenteerde eerder alleen de `simpel`-submodus. Nu zijn er vijf nieuwe secties bij:

- **"Welke modus: Simpel of uitgebreid?"** — expliciete leeswijzer vooraf: Simpel is de vuistregel voor bijna al het veldwerk (één type, jaszak-tellen, niets om over na te denken); de drie uitgebreide modi zijn voor als het onderscheid dat ze vastleggen niet achteraf te reconstrueren is (Transect voor echte richting, Winkelstraat voor doorloop-vs-verblijf, Parkeren voor een snelle bezettingsindruk onderweg).
- **"Het moduskeuzescherm"** — het scherm met de vier knoppen (Simpel/Transect/Winkelstraat/Parkeren) dat aan alle vier voorafgaat, inclusief de dataverlies-waarschuwing bij "Terug" en de gedeelde Wake Lock-werking (voorheen alleen bij Simpel beschreven, nu correct als gedeeld gedrag).
- **"Transect — richtingtelling"** — vijf voertuigtypes × twee richtingen, de Kompas-knop voor automatische richting-labels via reverse-geocoding, en de kolommen (`richting`, `richting_a`/`richting_b`).
- **"Winkelstraat — tegemoet & stilstaand"** — de twee categorieën, waarom de looptempo van de waarnemer wordt meegelogd (voor de KNIME-decompositie van flux vs. voorraad), en de link naar de plakkerigheid-analyse die dezelfde categorieën gebruikt.
- **"Parkeren — bezet/leeg links/rechts"** — het 2×2-grid, het verschil met de volwaardige `parkeertelling.html` (geen fout/spec), en de kolomtoewijzing.

Elke nieuwe sectie noemt expliciet welke bestaande CSV-kolom (`type`/`richting`/`snelheid`) de submodus-specifieke waarde draagt — geen schemawijziging, wel nieuwe waarden in bestaande kolommen. De export-tabel in "Export & bezocht.csv" verwijst nu naar deze sub-secties in plaats van kolommen ongedocumenteerd te laten.

Ook opgemerkt en gedocumenteerd: de snap-zekerheid/GPS-stabiliteit-stippen (Simpel-scherm) worden in Transect/Winkelstraat/Parkeren niet getoond — de snap draait wel op de achtergrond, alleen ontbreekt de live indicator. Vermeld als noot bij Transect.

## Validatie

- **HTML-tagbalans** schoon.
- **TOC-integriteit:** elk `<a href="#...">` in de inhoudsopgave heeft een bestaand `id`; geen dubbele id's in het document.
- **Byte-identiteit:** sinds v2.26 wijzigde uitsluitend `traffic_counter_help.html`.
- Inhoud geverifieerd tegen `pocket_count.html`-broncode: de vier moduskeuze-knoppen, de vijf transect-types, de twee winkelstraat-categorieën, het 2×2 parkeren-grid, en de daadwerkelijke `_telregels.csv`/`_sessie.csv`-kolomkoppen (`richting`, `snelheid`, `richting_a`, `richting_b`) zijn rechtstreeks uit de code overgenomen, niet uit het geheugen gereconstrueerd.

## Backlog (ongewijzigd meegenomen)

- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
- Nog steeds ongelinkt vanuit de handleiding (vermoedelijk bewust, niet geverifieerd): `snap_methodology.html`, `snaptrace.html`, `winkelstraat_rekenrig.html`, `relabel_modus.py`.
