# CLAUDE.md — TelSuite

Browser-tools voor verkeers- en parkeertellingen (telonline.org). Elk hulpmiddel
is één zelfstandig HTML-bestand. Communiceer met Jay in het Nederlands.

## Eerst lezen

1. `docs/OVERDRACHT_STAND_VAN_ZAKEN.md`: huidige release, vaste afspraken, backlog.
2. `docs/ONTWIKKELEN.md`: plattegrond van bestanden, conventies en externe diensten.
3. De laatste `docs/overdracht/overdracht_v2_XX.md` bij werk dat daarop voortbouwt.

Deze CLAUDE.md is een samenvatting. Bij twijfel gelden de documenten in `docs/`.

## Harde regels

- **Nooit data committen.** Geen CSV, ZIP, GPX, KML, GeoJSON of PNG met echte
  tellingen of sporen. Die kunnen privé looproutes en posities bevatten.
  `.gitignore` vangt dit af; omzeil het niet met `git add -f`.
- **Geen sleutels of wachtwoorden** in de code. Alleen domeinbeperkte
  client-side sleutels (zoals CARTO) zijn toegestaan.
- **Geen framework, geen buildstap, geen npm-afhankelijkheden.** Bibliotheken
  alleen via CDN (cdnjs, unpkg), versies zoals in `docs/ONTWIKKELEN.md`.
- **Additief en byte-identiek.** Raak alleen aan wat de taak vraagt. Na elke
  wijziging moet `git diff --stat` alleen de bedoelde bestanden tonen.
- **Gedeelde blokken blijven byte-identiek** in alle bestanden waar ze staan:
  `HIGHWAY_RE`, `ovpKeur`, `overpassFetch`, `startRoadFetch`, de tegelcache en
  de segmentatie. Wijzig je er één, wijzig ze allemaal en vergelijk met md5.
- **Schema is heilig.** Kolommen, sleutels en ZIP-namen voeden een
  KNIME-pijplijn. Stel elke schemawijziging eerst aan Jay voor en werk
  `zip_format_reference.html` mee bij.

## Conventies

- CSV: puntkomma als scheidingsteken, punt als decimaalteken, UTF-8.
- ZIP-namen: `_car`, `_fts`, `_cap`, `_pkt_<s|t|w|p>`, `_sta`;
  reconstructie: `<sessie_id>_recon.zip`. De modusletter zit in de `sessie_id`.
- Taal: interfaces en handleiding Nederlands, technische referentie Engels.
- Metadata: Open Graph wel, Twitter/X-kaarten **nooit**.
- SEO: gebruik "traffic counting" (de activiteit), niet "traffic counter".
- Huisstijl: Oswald, met Share Tech Mono als monospace, in de tools. De
  documentatiepagina's (handleiding, over, privacy) zijn sinds v3.3 kale HTML met
  één gedeeld stijlblok; kleur alleen waar die iets uitlegt.

## Controle na elke wijziging

1. Inline JavaScript uit elk gewijzigd HTML-bestand halen en `node --check`
   draaien.
2. Tagbalans van het HTML controleren.
3. md5 van gedeelde blokken vergelijken als er meer dan één bestand meedoet.
4. `git diff --stat`: alleen de bedoelde bestanden.
5. PHP gewijzigd: `php -l`.
6. De regressietests in `_archief/overpass_rig/` (zie de README daar). Draai
   ze vanuit de repo-root, bijvoorbeeld `node _archief/overpass_rig/functest.js`.
   - Tests die jszip of papaparse nodig hebben: installeer die **buiten** de
     repo en draai met `NODE_PATH`. Nooit `node_modules` committen.
   - `check_encoding.py` loopt ook door `.git/`. Draai hem op een export:
     `git archive HEAD | tar -x -C <tijdelijke map>`.
   - De Playwright-tests (`laadtest`, `hersteltest`, `statictest`,
     `opruimtest`) hebben Chromium nodig. Sla ze over als dat er niet is, en
     zeg dat.
   - `valideer.py` vergelijkt twee releasemappen; pas `OUD_DIR`, `NIEUW_DIR`
     en de verwachte sets aan.

## Werkwijze

- Bespreek het ontwerp eerst bij niet-triviale keuzes. Jay denkt graag mee
  over aanpak en algoritme. Een korte goedkeuring betekent: doorgaan.
- Zeg het als een wens te complex wordt voor wat hij oplevert.
- Elke release:
  - versienummer onderaan `index.html` ophogen;
  - een nieuwe `docs/overdracht/overdracht_vX_Y.md` schrijven (sinds 3.0:
    v3.1, v3.2, …);
  - `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` bijwerken;
  - één PR naar `main` per release. Na de merge maakt
    `.github/workflows/release.yml` zelf de GitHub Release met
    `telsuite-<versie>.zip`. Een nieuw bestand dat niet op de server hoort,
    krijgt `export-ignore` in `.gitattributes`.
- Het planning-endpoint in `planningen/` heeft geen authenticatie. De
  afscherming gebeurt op de server, niet in de repo.
- **Geen sessielink in commits of PR's.** De repo is openbaar. Zet geen
  `Claude-Session:`-regel en geen `https://claude.ai/code/session_…` in
  commitberichten, PR-beschrijvingen of reacties (afspraak met Jay, v3.2).
  `Co-Authored-By: Claude …` mag blijven. Controleer na het aanmaken van een
  PR of er toch een sessielink in de beschrijving is gezet, en haal die weg.
