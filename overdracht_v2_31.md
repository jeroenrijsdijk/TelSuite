# TrafficCounterSuite v2.31 — Overdracht

Kleine afronding vóór een pauze: **`zip_format_reference.html`** is bijgewerkt met het `_pkt_<letter>`-schema. Alleen dit bestand wijzigt; de rest is byte-identiek aan v2.30. Onderaan een **stand-van-zaken** zodat we over een paar weken zo weer verder kunnen.

## Wat is bijgewerkt

- De `_pkt`-regel in "Filename markers & survey-type coding" is uitgesplitst naar vier sub-letters: `_pkt_s` (simpel · vrije tekst), `_pkt_t` (transect · car/truck/moto/bike/ped), `_pkt_w` (winkelstraat · stilstaand/tegemoet), `_pkt_p` (parkeren · bezet/leeg).
- Nieuwe noot **"Pocket modus letter"**: de letter zit in de `sessie_id` zelf (niet alleen de bestandsnaam), dus hij overleeft reconstructie (`…_pkt_w.zip` → `…_pkt_w_recon.zip`); oudere kale `_pkt`-ZIP's zijn te retrofitten met `voeg_modusletter_toe.py`.
- Pocket-sectie: `filename-hint` → `*_pkt_s.zip`; de vier voorbeeld-`sessie_id`'s dragen nu `_pkt_s`.

Validatie: HTML-tagbalans schoon; byte-identiteit t.o.v. v2.30 uitsluitend `zip_format_reference.html`.

---

## Stand van zaken (voor de herstart)

### Waar de suite staat: v2.31
Recente releases in volgorde:
- **v2.24** — modus-mislabeling in de reconstructor gefixt (geen blinde `parkeren`-fallback meer; modus uit profiel/woordenschat).
- **v2.25** — zip-referentie: codering- en naamconventies gedocumenteerd.
- **v2.26/2.27** — handleiding: `parkeer_reconstructie` toegevoegd, telmodi-telfout hersteld, en de drie ontbrekende pocket-submodi (transect/winkelstraat/parkeren) volledig uitgeschreven + "welke modus wanneer".
- **v2.28** — nieuwe publieke intropagina `over.html` (drie-stappen-workflow), gelinkt vanaf `index.html`.
- **v2.29** — Jay's handmatig herschreven handleiding opgenomen (+ twee div-balansfixes); `over.html` kaartafbeelding-tekst gecorrigeerd.
- **v2.30** — pocket modus-letter in `sessie_id`/bestandsnaam (`_pkt_s/t/w/p`).
- **v2.31** — deze: referentie bijgewerkt met het letter-schema.

### Losse tools naast de suite (in outputs)
- `relabel_modus.py` — corrigeert een verkeerde `app_type`/`modus` in bestaande ZIP's op naam-markers (`_car`/`_fts`/`_pkt`) + type-woordenschat; droogloop-standaard, niet-destructief.
- `voeg_modusletter_toe.py` — retrofit van bestaande pocket-ZIP's naar het `_pkt_<letter>`-schema (ZIP-naam + interne bestanden + `sessie_id`); droogloop-standaard.
- `recon_qgis_loader.py` — laadt een map met (recon-)ZIP's recursief in QGIS, één laag per telptype (modus).
- Volgorde bij opschonen van een oud archief: eerst `relabel_modus.py` (modus goedzetten), dan `voeg_modusletter_toe.py` (letter toevoegen).

### Kernafspraken die vastliggen
- **Naam-markers:** `_car`→auto/parkeren, `_fts`→fiets/parkeren, `_cap`→capaciteit, `_trn`→transect, `_pkt_<s|t|w|p>`→pocket. Fiets herken je ook aan de inhoud: één van `fiets`/`brommer`/`breed`/`wrak` = fietstelling.
- **Route A** voor de modus-letter: de code hoort bij de identiteit (`sessie_id`), niet alleen bij de bestandsnaam — daarom overleeft hij reconstructie zonder wijziging in `parkeer_reconstructie.html`. KNIME wordt op het nieuwe `sessie_id`-formaat aangepast (Jay).
- De kaartafbeelding (`_kaart.png`) zit **alleen** in de kaart-apps (parkeertelling, fietsparkeren, capaciteitstelling), niet in pocket/static.

### Open backlog (niets besloten, klaar om op te pakken)
- **Parkeren uit pocket** halen naar een eigen modus/tool (parkeren = toestand, geen stroom).
- **Plakkerigheid-kernel** als winkelstraat-gegate punt-laag naar `telrapport` porten (proeftuin staat klaar).
- **%bezet per dag×uur-cel** — vraagt tik-met-tijd-én-categorie → schema/KNIME-afstemming.
- **QGIS-loader** — optionele join op `_straten.csv`/`_bezocht.csv` (bezetting per weglijn) + GPS-sporen.
- **Handleiding** — veiligheidsblok-kop `<h1>` → `<h4>` voor consistentie (jouw keuze).
- **`over.html`** — eventueel een Engelse variant.

### Werkwijze-reminder
Round-trip blijft de manier: jij bewerkt een bestand handmatig en geeft het terug; ik integreer + valideer (node --check, tag-balans, byte-identiteit). Eén regel context bij teruggave ("ik heb secties X en Y aangeraakt") maakt het sneller en betrouwbaarder.

Tot over een paar weken.
