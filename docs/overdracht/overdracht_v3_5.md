# Overdracht v3.5 — contactadres, GeoPackage op de introductiepagina

Twee kleine wijzigingen in de tekst, geen code.

## 1. Contactadres

Jay: "verkeer@telonline.org is het mailadres waar gebruikers contact kunnen
opnemen. Of via github uiteraard."

| pagina | wat |
|---|---|
| `privacy.html` | het gele invulveld bij *Je rechten en contact* is nu `verkeer@telonline.org`. Alleen het mailadres, geen GitHub: verzoeken over je eigen gegevens horen niet in een openbaar issue. De regel `.invullen` in de CSS is weg; `valideer.py` meldt het veld niet meer. |
| `over.html` | onderaan, boven "Built by": vragen, opmerkingen of resultaten delen via het mailadres of een issue op GitHub |
| `verantwoording.html` | onder *Over deze toelichting*: vragen over de toelichting via het mailadres |
| `README.md` | onder *Do you use it?*: het mailadres en de issues |

Daarmee is punt 0b van "Nog te doen door Jay" in de stand van zaken af.

## 2. GeoPackage op `over.html`

De alinea *Werk je liever in GIS-software?* noemde alleen de QGIS-loader. Nu
ook de GeoPackage uit Telrapport, met het verschil tussen de twee:

- de loader geeft de ruwe tellingen, om zelf mee te rekenen;
- de GeoPackage geeft de kaart uit Telrapport kant-en-klaar, met de kleuren,
  een QGIS-project op een PDOK-ondergrond en een printopmaak op A4.

De alinea zegt ook: naam kiezen bij het bewaren, daarna niet hernoemen. En hij
linkt naar de handleiding (`#rapport-gpkg`). Jay's eigen twee zinnen staan er
letterlijk nog. De regel bovenaan in *In het kort* noemt de GeoPackage ook.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `privacy.html`, `over.html`, `verantwoording.html` | zie boven |
| `index.html` | versie v3.5 |
| `README.md` | contact |
| `_archief/overpass_rig/valideer.py`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

```
valideer.py        ALLES OK — 4 verwachte bestanden gewijzigd; kale stijl in 4 pagina's; geen invulveld meer in privacy.html
laadtest.py        47/47
functests          alle 14 groen
check_encoding.py  alles geldige UTF-8
```
