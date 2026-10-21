# Overpass-rig (v2.49)

Regressietests voor het gedeelde Overpass-blok en de tegel-cache. Ze knippen de
blokken rechtstreeks uit de HTML op hun ankercommentaren, dus ze testen de echte
code en niet een kopie. Draai ze opnieuw na elke wijziging aan:

  - het OVP-blok (`ovpKeur` / `ovpStatusUitHttp` / `ovpBackoffMs`)
  - `leesTegels` / `cacheWaysInTiles`
  - de fetch-discipline in de parkeer-apps of in pocket
  - `overpassFetch` / `haalWayGeometrie` in telrapport en telreconstructie
  - een CSV-kopregel in een van de apps (draai dan test_zipref.py)
  - het verzamel-ZIP-formaat of de weergavestaat in telrapport

Draaien vanuit de suite-map:

    node _archief/overpass_rig/functest.js          # parkeertelling.html, 37 tests
    node _archief/overpass_rig/functest_pocket.js   # pocket_count.html, 18 tests
    node _archief/overpass_rig/functest_telrapport.js  # telrapport.html, 16 tests
    node _archief/overpass_rig/functest_tikpositie.js   # tikPositie + clusters, 9 tests
    python3 _archief/overpass_rig/valideer.py       # JS-syntax, tagbalans, byte-identiteit
    python3 _archief/overpass_rig/test_zipref.py   # ZIP-referentie tegen de exportcode
    python3 _archief/overpass_rig/check_encoding.py # geldige UTF-8 in alle tekstbestanden
    node _archief/overpass_rig/functest_verzameling.js  # verzamel-ZIP, 26 tests (npm install jszip)
    node _archief/overpass_rig/functest_legezip.js  # lege telling, 16 tests (npm install jszip papaparse)
    node _archief/overpass_rig/functest_reconpaar.js   # origineel vs _recon, 22 tests
    node _archief/overpass_rig/functest_weekknop.js    # weekprofiel-knop bovenaan, 11 tests
    node _archief/overpass_rig/functest_zijkolom.js    # ruimteverdeling zijkolom, 20 tests
    node _archief/overpass_rig/functest_coordinaten.js # welk coordinaat op de kaart, 29 tests
    node _archief/overpass_rig/functest_taartbol.js    # clusterbol als taart, 24 tests
    node _archief/overpass_rig/functest_shiftsolo.js   # shift-klik isoleert telling, 27 tests
    node _archief/overpass_rig/functest_hwvoorkeur.js  # highway-voorkeur in de matcher + versiestempel, 22 tests
    node _archief/overpass_rig/functest_gpxtijd.js     # GPX-tijden in echte UTC, drie parkeer-apps, 31 tests
    node _archief/overpass_rig/functest_segmenttabel.js  # weekprofiel: tabel, 95%-marge, koppeling met het diagram, 23 tests
    python3 _archief/overpass_rig/laadtest.py          # elke pagina echt laden in Chromium, 45 tests (v3.15: deel D vervallen)
    python3 _archief/overpass_rig/hersteltest.py       # harde crash + doortellen, alle veld-apps, 133 tests
    python3 _archief/overpass_rig/statictest.py        # Static door de keten: export, telrapport, verzameling, reconstructor, 24 tests
    python3 _archief/overpass_rig/opruimtest.py        # noodopslag weg na bevestigde download, en alleen dan; twee vensters (v3.8), 139 tests
    node _archief/overpass_rig/functest_kwaliteit.js   # v3.10: kwaliteitsrapport in telrapport, 33 tests (papaparse)
    python3 _archief/overpass_rig/logicatest.py        # v3.10: pocket-id bij Start, kwaliteitsrapport in Chromium, sessierij compact (v3.11/v3.12), 30 tests
    python3 _archief/overpass_rig/robuusttest.py       # v3.9: volle opslag, persist, schermslot pocket, voorpagina, telplanning ophalen, 87 tests
    node _archief/overpass_rig/functest_planlink.js    # v3.14: planning als link, inpakken en uitpakken, 29 tests (Node 18+)
    python3 _archief/overpass_rig/planlinktest.py      # v3.14: link maken in telplanning, openen in parkeertelling/fiets/pocket; v3.15: zonder server; v3.16: capaciteitscontouren standaard uit, 51 tests
    node _archief/overpass_rig/functest_bbox.js        # v3.17: bbox-filter van telrapport, ook voor verzamelingen, 11 tests (jszip papaparse)
    python3 _archief/overpass_rig/onderhoudtest.py     # v3.17: pocket zonder _netwerk.csv, zoekTerreinen met geheugen, 17 tests
    python3 _archief/overpass_rig/opslaantest.py       # v3.18: ZIP opslaan in de parkeer-apps per platform (Android, ingebouwde browser, desktop, iPhone), 48 tests
    node _archief/overpass_rig/functest_gebied.js      # v3.19: gebied vooraf ophalen: tegelset, zoekvraag, regel, 22 tests
    python3 _archief/overpass_rig/gebiedtest.py        # v3.19: gebied vooraf in de cache, lopen zonder verzoek, verversafstand, planning uit een link in telplanning; v3.20: tegelschema 3 (deel F), 51 tests
    node _archief/overpass_rig/functest_tegelcache.js  # v3.20: tegels schrijven: hele cellen, per segment, knooppunten, 13 tests
    python3 _archief/overpass_rig/stukkentest.py       # v3.21: telrapport per stuk voor fiets en auto: origineel, _recon, auto, correctietool, 21 tests
    python3 _archief/overpass_rig/herstelmeldingtest.py  # v3.22: één herstelmelding in de vijf veld-apps; Static Nederlands en in het palet van telrapport, 103 tests
    python3 _archief/overpass_rig/gpsmiddeltest.py     # v3.23: Static middelt de GPS: schatter met nagebootste ruis, app met versnelde klok, adres, 39 tests
    python3 _archief/overpass_rig/gpkgtest.py          # GeoPackage uit telrapport: van veld-app tot QGIS, met het QGIS-project, 80 tests
                                                       # (ook sql.js@1.14.2 in node_modules; het QGIS-deel draait als
                                                       #  PyQGIS er is, via gpkg_qgis.py, anders overgeslagen)
                                                       # (playwright + leaflet/jszip/papaparse/fontsource in node_modules)
    python3 _archief/overpass_rig/tekstgelijk.py oud.html nieuw.html  # zelfde tekst, woord voor woord (bij opmaakwijzigingen)

`tekstgelijk.py` is voor een opmaakwijziging zonder tekstwijziging, zoals de kale
documentatiepagina's in v3.3. Het vergelijkt alle tekst in `<title>` en `<body>`,
ook verborgen tekst, en slaat script, stijl en witruimte over. De scheidingstekens
`· — ( )` tellen niet mee; geef met `--negeer` een andere set.

`valideer.py` vergelijkt met een vorige release; pas OUD_DIR/NIEUW_DIR en de
verwachte sets (gewijzigd/verwijderd) aan. De mappen mogen ook uit de omgeving
komen (`VALIDEER_OUD`, `VALIDEER_NIEUW`). Met `VALIDEER_ZONDER_RELEASE=1` slaan
de release-controles over (welke bestanden veranderden, het nummer, de
overdracht): voor een PR zonder nieuw versienummer.

**Op GitHub** draait `.github/workflows/tests.yml` dit alles bij elke PR, zie
`docs/ONTWIKKELEN.md`. Hij vindt de tests op hun naam:
- `functest*.js`: Node, in één job, met jszip, papaparse en sql.js via `NODE_PATH`;
- `<naam>test.py` (kleine letters, eindigt op `test.py`): een browsertest met een
  eigen job; `test_zipref.py` valt daar buiten en draait in de eerste job.

Een nieuwe test met zo'n naam doet dus vanzelf mee. Een hulpscript mag niet op
`test.py` eindigen. Elke test moet bij een fout met een andere code dan 0
eindigen (`sys.exit(1)`, `process.exit(1)`); anders ziet GitHub hem als groen.

**Geen vaste tijdzone.** De runner van GitHub draait in UTC, de Claude-omgeving
in Europe/Amsterdam. Een test die een kloktijd verwacht, rekent die uit in de
tijdzone van de browser (zie `logicatest.py` A5). Faalt een test alleen op
GitHub, probeer hem dan lokaal met `TZ=UTC`.

De tests van `gpx_snap.html` zijn sinds v2.65 mee verhuisd naar de aparte gpx-tak.
IndexedDB en Overpass worden nagebouwd, dus er gaat geen verkeer de deur uit.

## Encoding

Schrijf documenten met Python of een editor, niet met een shell-heredoc
(`cat > bestand <<'EOF'`). In deze omgeving sneuvelt daarbij af en toe de eerste
byte van een multibyte-teken: "Eén" werd `E\xa9n`, ongeldige UTF-8. Het viel
niet op omdat de rest van het bestand gewoon leesbaar bleef.

Controleren kan met:

    python3 _archief/overpass_rig/check_encoding.py
