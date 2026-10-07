# Overdracht v3.0 — de geteste v2.77, nu als 3.0

De veldtest uit `VELDTEST_3.0.md` is op 7 oktober 2026 door Jay gedraaid:
**alles groen, op iPhone en op Android.** Er kwam niets uit dat gerepareerd
moest worden. Daarmee is de release-kandidaat v2.77 versie 3.0.

---

## 1. Wat 3.0 is

3.0 is **byte-identiek aan v2.77**, op het versienummer onderaan `index.html`
na (`v2.77` → `v3.0`). Dat is een bewuste keuze. De veldtest is op v2.77
gedaan. Zou 3.0 ook maar één regel code veranderen, dan droeg ongeteste code
het label "getest". `valideer.py` bewaakt dit: `index.html` is het enige
gewijzigde suite-bestand.

De versiestempel van de reconstructor blijft `v2.74`, want de reconstructor is
niet veranderd. Een reconstructie onder 3.0 schrijft dus nog steeds
`reconstructie_versie;v2.74` in de log.

**Na 3.0 nummeren we door met v3.1, v3.2, …** De overdrachten heten
`overdracht_v3_1.md` enzovoort. `valideer.py` vergelijkt versies als getallen,
dus 3.0 > 2.77 en 3.10 > 3.9.

## 2. Nieuw: een ZIP per versie op GitHub

Vanaf 3.0 maakt GitHub bij elke release automatisch een downloadbare ZIP.

**Hoe het werkt.** De workflow `.github/workflows/release.yml` draait na elke
push naar `main`:

1. Hij leest het versienummer onderaan `index.html`.
2. Bestaat er nog geen tag met dat nummer, dan maakt hij een **GitHub
   Release** met die tag.
3. Daaraan hangt **`telsuite-<versie>.zip`**, gebouwd met `git archive`.
4. Als releasetekst gebruikt hij `docs/overdracht/overdracht_<versie>.md`.

Een push zonder nieuw versienummer (alleen documentatie, bijvoorbeeld) maakt
geen release. Mislukt er iets, dan kun je hem opnieuw starten via *Actions →
Release → Run workflow*.

**Wat er in de ZIP zit.** Alles wat op de server hoort: de HTML-bestanden,
`sitemap.xml`, de PHP-scripts in `planningen/`, `README.md` en `LICENSE`
(bij GPL hoort de licentie bij wat je verspreidt). Ongeveer 400 kB.

**Wat er niet in zit** staat in `.gitattributes` (`export-ignore`):
`_archief/`, `docs/`, `.github/`, `CLAUDE.md`, `.gitignore`,
`.gitattributes`, `build_bezocht.py` en **`planningen/.htaccess`**.

Dat laatste is bewust. Op de server staat in dat bestand het echte
`AuthUserFile`-pad. Upload je de ZIP over de site heen, dan blijft jouw
`.htaccess` staan. Wie de suite vers installeert, haalt hem uit de repo en
richt hem één keer in, zoals beschreven in het bestand zelf.

**Vangnet.** De workflow weigert een ZIP met `.csv`, `.zip`, `.gpx`, `.kml`,
`.kmz`, `.geojson`, `.png` of `.json` erin. `.gitignore` houdt die al uit de
repo, maar een release is publiek en moet dus twee keer op slot.

**Oude versies** krijgen geen ZIP met terugwerkende kracht. Bij de oudere
commits staat niet betrouwbaar welke stand welke release was. 3.0 is
dezelfde code als v2.77, dus de reeks begint netjes bij de geteste versie.

GitHubs eigen knop *Source code (zip)* bij elke release houdt zich ook aan
`.gitattributes`. Die levert dus dezelfde inhoud, alleen in een submap.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `index.html` | versie v3.0 (enige wijziging in de suite) |
| `.github/workflows/release.yml` | nieuw: release + ZIP per versie |
| `.gitattributes` | nieuw: wat niet in de ZIP gaat |
| `_archief/overpass_rig/valideer.py` | `RELEASE = 'v3.0'`, verwacht alleen `index.html` |
| `docs/VELDTEST_3.0.md` | uitkomst van de veldtest |
| `docs/OVERDRACHT_STAND_VAN_ZAKEN.md`, `docs/ONTWIKKELEN.md`, `CLAUDE.md` | 3.0, release-ZIP, overdrachtnaam |

## 4. Validatie

```
valideer.py        ALLES OK — alleen index.html gewijzigd t.o.v. v2.77 (-1 byte); 12 groepen gedeelde blokken OK
opruimtest.py      52/52
hersteltest.py     133/133
laadtest.py        46/46
statictest.py      24/24
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
release-ZIP        lokaal nagebouwd met git archive: 22 bestanden, ~400 kB,
                   geen data, geen docs/_archief/.htaccess
workflow           YAML geldig; shell-stappen door bash -n; versiestap leest v3.0
```

`valideer.py` meldt nog steeds dat het contactveld in `privacy.html` ingevuld
moet worden. Dat staat bij Jay (stand van zaken §4, punt 0b).

De workflow zelf draait pas echt op GitHub, bij de merge van deze PR. Daarna
hoort onder *Releases* **TelSuite v3.0** te staan, met `telsuite-v3.0.zip`.
