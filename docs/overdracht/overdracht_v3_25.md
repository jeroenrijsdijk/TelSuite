# Overdracht v3.25 — lettertypen op de eigen server

Jay: "google fonts zelf hosten zou ik willen, maar maakt dat het installeren bij
anderen niet ingewikkelder?" Nee: de lettertypen gaan mee in de release-ZIP,
in een map `fonts/`. Installeren blijft de ZIP uitpakken op een webserver.
Jay: "ga".

Het ZIP-schema van de tellingen verandert niet.

## 1. Wat er is

**`fonts/` (nieuw):**
- `oswald-latin-wght-normal.woff2` (28 kB) en `oswald-latin-ext-wght-normal.woff2`
  (24 kB). Oswald als één variabel lettertype voor de diktes 200 tot 700, in
  twee delen. De browser haalt het uitgebreide deel pas als er zo'n teken op de
  pagina staat.
- `share-tech-mono-latin-400-normal.woff2` (14 kB).
- `fonts.css`: drie `@font-face`-regels, met de familienamen die de pagina's
  al gebruikten (`'Oswald'`, `'Share Tech Mono'`). Aan de opmaak van de
  pagina's verandert dus niets.
- `OFL-Oswald.txt` en `OFL-ShareTechMono.txt`: de licenties (SIL Open Font
  License 1.1, meeleveren mag). Share Tech Mono heeft *Share* als
  gereserveerde naam; de bestanden zijn ongewijzigd, dus dat geeft niets.
- Bron: Fontsource 5.3.0 via npm (`@fontsource-variable/oswald`,
  `@fontsource/share-tech-mono`). Dat zijn de bestanden van Google Fonts zelf.

**Pagina's.** Elf pagina's linken nu `fonts/fonts.css` in plaats van Google
Fonts:
- capaciteitstelling, fietsparkeren, index (via `@import`), parkeertelling,
  pocket, telplanning (de `preconnect` is ook weg), telreconstructie en Static;
- de interne pagina's `snap_methodology.html` en `winkelstraat_rekenrig.html`;
- de referentie.

Pagina's die vroeger maar een paar diktes vroegen, krijgen nu het variabele
lettertype. Dat ziet er hetzelfde uit.

**Privacyverklaring.**
- De rij *Google Fonts* is weg.
- Onder *Op de server van telonline.org* staat dat de lettertypen daar sinds
  oktober 2026 staan, en dat Google Fonts tot dan je IP-adres zag.
- In het Engelse stuk staat hetzelfde.

**Release.** De ZIP wordt met `git archive` gebouwd. `fonts/` staat niet in
`.gitattributes` en gaat dus mee. De controle op data in de ZIP kijkt naar
csv/zip/gpx/kml/png/json; `.woff2`, `.css` en `.txt` vallen daar niet onder.

**Ontwikkelen.** `docs/ONTWIKKELEN.md` noemt `fonts/` bij de bestanden en bij
"zet alles in één map". Ook `about.html` (v3.24) staat er nu in.

## 2. Gevolgen om te weten

- **Eén HTML-bestand los kopiëren** zonder de map `fonts/` geeft de
  reserveletter (sans-serif, monospace). De tool werkt gewoon.
- **Een lokaal geopend bestand** (`file://`) vindt de lettertypen ook. In
  Chromium getest. Firefox staat lettertypen uit dezelfde map of een submap
  toe; niet getest.
- **telrapport** vraagt in de labels op de kaart (clusterbollen, nummers) om
  Oswald, maar laadde hem nooit; daar staat een reserveletter. Dat heb ik zo
  gelaten: het is nu één regel, maar het verandert hoe de kaart eruitziet. In
  de backlog als Jay's keuze.

## 3. Tests

- **`lettertypetest.py`** (nieuw, 43 tests, Chromium):
  - *C.* `fonts/` is compleet. `.gitattributes` houdt de map niet uit de ZIP.
    `fonts.css` verwijst alleen naar bestanden in de map zelf.
  - *A.* Geen pagina noemt nog `fonts.googleapis.com` of `fonts.gstatic.com`
    (behalve de privacyverklaring, in tekst).
  - *B.* Elke pagina die Oswald of Share Tech Mono gebruikt, linkt
    `fonts/fonts.css` en laadt die lettertypen echt (`document.fonts.load`),
    zonder één verzoek aan Google.
- **`laadtest.py`** neemt de lettertypen uit de repo. Tot nu toe bootste hij
  Google Fonts na met kopieën uit `node_modules`. De breedtetoets van de
  voorpagina meet zo met de echte lettertypen.
- **CI** (`.github/actions/testopzet`) installeert `@fontsource` niet meer.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `fonts/` | nieuw: drie `.woff2`, `fonts.css`, twee licenties |
| 11 pagina's (zie §1) | `fonts/fonts.css` in plaats van Google Fonts |
| `privacy.html` | Google Fonts weg; de lettertypen op de eigen server |
| `index.html` | ook versie v3.25 |
| `_archief/overpass_rig/lettertypetest.py` | nieuw |
| `laadtest.py`, `valideer.py`, `README.md`, `.github/actions/testopzet/action.yml`, `.github/workflows/tests.yml` (commentaar), `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py            ALLES OK — 12 verwachte bestanden gewijzigd; gedeelde blokken OK;
                       privacyverklaring: 11 externe domeinen, alle vermeld (was 12, Google Fonts weg)
lettertypetest.py      43/43 (nieuw)
laadtest.py            46/46 (met de lettertypen uit de repo; +1 voor about.html uit v3.24)
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
