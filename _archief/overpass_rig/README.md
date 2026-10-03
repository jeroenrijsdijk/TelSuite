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
    python3 _archief/overpass_rig/laadtest.py          # elke pagina echt laden in Chromium, 46 tests
    python3 _archief/overpass_rig/hersteltest.py       # harde crash + doortellen, alle veld-apps, 133 tests
    python3 _archief/overpass_rig/statictest.py        # Static door de keten: export, telrapport, verzameling, reconstructor, 24 tests
    python3 _archief/overpass_rig/opruimtest.py        # noodopslag weg na bevestigde download, en alleen dan, 52 tests
                                                       # (playwright + leaflet/jszip/papaparse/fontsource in node_modules)

`valideer.py` vergelijkt met een vorige release; pas OUD_DIR/NIEUW_DIR en de
verwachte sets (gewijzigd/verwijderd) aan.

De tests van `gpx_snap.html` zijn sinds v2.65 mee verhuisd naar de aparte gpx-tak.
IndexedDB en Overpass worden nagebouwd, dus er gaat geen verkeer de deur uit.

## Encoding

Schrijf documenten met Python of een editor, niet met een shell-heredoc
(`cat > bestand <<'EOF'`). In deze omgeving sneuvelt daarbij af en toe de eerste
byte van een multibyte-teken: "Eén" werd `E\xa9n`, ongeldige UTF-8. Het viel
niet op omdat de rest van het bestand gewoon leesbaar bleef.

Controleren kan met:

    python3 _archief/overpass_rig/check_encoding.py
