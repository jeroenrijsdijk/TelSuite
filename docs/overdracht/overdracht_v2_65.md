# Overdracht v2.65 — gpx_snap.html uit de suite

Geen enkel HTML-bestand van de suite is gewijzigd. `gpx_snap.html` en zijn vier
testbestanden zijn eruit en gaan verder als aparte tak. Daarnaast twee kleine
aanpassingen in de testrig en de documentatie.

---

## 1. Samenvatting

1. `gpx_snap.html` verwijderd uit de suite (byte-identiek meegegeven aan de tak).
2. Zijn tests verhuisd: `functest_gpxsnap.js`, `functest_grofspoor.js`,
   `functest_osrm.js`, `meet_grofspoor.js`.
3. `valideer.py`: gpx_snap uit alle groepen, en een nieuwe controle op
   **verwijderde** bestanden (`VERWACHT_VERWIJDERD`).
4. `OVERDRACHT_STAND_VAN_ZAKEN.md` bijgewerkt; een paar zinnen die door het
   vertrek niet meer klopten zijn rechtgezet.

## 2. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `gpx_snap.html` | **verwijderd** — naar de gpx-tak |
| `_archief/overpass_rig/functest_gpxsnap.js` | **verhuisd** naar de gpx-tak |
| `_archief/overpass_rig/functest_grofspoor.js` | **verhuisd** |
| `_archief/overpass_rig/functest_osrm.js` | **verhuisd** |
| `_archief/overpass_rig/meet_grofspoor.js` | **verhuisd** |
| `_archief/overpass_rig/valideer.py` | groepen zonder gpx_snap; controle op verwijderde bestanden; labels "t.o.v. v2.48" vervangen door "t.o.v. vorige release" |
| `_archief/overpass_rig/README.md` | vier testregels eruit, verwijzing naar de tak erin |
| `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt (zie §4) |
| `overdracht_v2_65.md` | nieuw (dit document) |

Alle HTML-bestanden: byte-identiek aan v2.64. De historische
`overdracht_v2_62/63/64.md` blijven staan — geschiedenis blijft geschiedenis.

## 3. Waarom het zo schoon kon

`gpx_snap.html` was vanaf v2.62 bewust niet gelinkt: geen verwijzing vanuit
`index.html`, `over.html` of de handleiding. De enige draden naar de suite
waren de byte-identiteitsgroepen in `valideer.py` en de testbestanden. Beide
zijn doorgeknipt; een grep op `gpx_snap`, `gpxsnap`, `grofspoor` en `osrm` in
alle HTML/JS/PY van de suite vindt daarna niets meer, alleen de uitleg in de
README en het commentaar in `valideer.py`.

De groepen `RECON-kern`, `MATCHER` en `OSMCACHE` hebben nu één bestand. Ze
blijven in `valideer.py` staan: een groep van één controleert niets op drift,
maar wel dat het ankercommentaar nog bestaat. Komt er ooit weer een tweede
drager, dan is het één regel.

## 4. Wat er in de stand van zaken rechtgezet is

- Carto-sleutel: drie plekken in de suite, niet vier (plus één in de tak).
- De alinea "gpx_snap is de enige tool die data naar buiten kan sturen" is
  vervangen: geen enkele suite-tool stuurt nog een spoor naar een externe
  dienst.
- `hopClass`: de opvang met tussenpunten zit **alleen** in de tak.
  `telreconstructie.html` heeft hem niet — relevant voor de geplande
  autorit-reconstructie.
- `ovpKeur`-blok: "5 bestanden" gecorrigeerd naar 6 (zo telt `valideer.py`).

## 5. Validatie

```
valideer.py                       ALLES OK
  JS-syntax                       15 bestanden OK
  HTML-tagbalans                  ongewijzigd (traffic_counter.html: bekende ruis)
  byte-identiteit                 0 HTML gewijzigd, verwijderd: gpx_snap.html
  gedeelde blokken                10 groepen OK
functest.js                       34/34
functest_pocket.js                18/18
functest_telrapport.js            16/16
functest_tikpositie.js             9/9
functest_legezip.js               16/16
functest_reconpaar.js             22/22
functest_weekknop.js              11/11
functest_zijkolom.js              20/20
functest_coordinaten.js           29/29
functest_taartbol.js              24/24
functest_shiftsolo.js             27/27
functest_verzameling.js           26/26 met FileReader-shim (zie hieronder)
test_zipref.py                    referentie sluit aan op de code
check_encoding.py                 alles geldige UTF-8

gpx-tak (los gedraaid)
functest_gpxsnap.js               39/39 met telreconstructie.html ernaast
functest_grofspoor.js             30/30
functest_osrm.js                  41/41
```

**`functest_verzameling.js` faalt kaal op Node 22 — ook op v2.64.** JSZip
herkent het `File`-object uit de test als blob en grijpt naar `FileReader`, dat
Node niet kent. Met een shim van drie regels (via `node -r`) slaagt hij 26/26.
Het is dus de testomgeving, niet `telrapport.html`. Niet aangepast in deze
release; staat op de backlog.

## 6. Backlog-wijzigingen

Nieuw:
- FileReader-shim in `functest_verzameling.js` zelf opnemen.
- `README.md` in de suite-root is verouderd ("Telapp suite", mist de
  reconstructor en de rebrand).
- Lessen uit de gpx-tak die terug kunnen: verdichten en zichtbare
  ketting-breuken voor `telreconstructie.html`.
- Synchronisatiebeleid voor de rekenkern-kopie in de tak.

Voor Jay (buiten de code): besluiten of `gpx_snap.html` op telonline.org blijft
staan.
