# Overdracht v3.66 — Telplanning: de cache als terugval

Jay: "En uit de lokale cache halen, als ophalen niet lukt?" Op het voorstel:
"Keuze 2" (telplanning onthoudt zijn eigen antwoorden en leest de tegels van de
telapps) "En alleen als alles gedekt is."

## 0. Waarom ook eigen antwoorden

De wegencache zit per apparaat in de browser. Jay plant op zijn pc en telt op
zijn telefoon. Op de pc staan dus alleen tegels waar daar een telapp of link is
geopend. Alleen de tegels lezen zou weinig helpen; telplanning moet zelf ook
onthouden wat het ophaalde.

## 1. Wat je ziet

- Overpass werkt: niets nieuws, behalve dat het antwoord bewaard wordt.
- Een hele ronde mislukt (beide servers):
  - **dekt de cache de hele contour**, dan komen de wegen daaruit, zonder nieuwe
    pogingen. De melding: "Overpass lukte niet; de wegen komen uit de cache",
    de redenen per server, "Opgehaald op 12-11-2026 (12 dagen geleden). Wat
    daarna in OpenStreetMap veranderde, zie je niet", en **Vernieuwen** en
    **Sluiten**. De statusregel zegt het ook;
  - **dekt hij maar een deel**, dan niets uit de cache: de gewone nieuwe poging
    of foutmelding (v3.65).
- **Vernieuwen** vraagt Overpass opnieuw. Lukt het, dan worden de wegen uit de
  cache vervangen door verse. De keuze en de knippen blijven staan.

## 2. Code (`telplanning.html`)

- **Eigen cache**: IndexedDB `telsuite_planning` (`CACHE_DB`), store `gebieden`,
  record `{ id, ts, bbox, elements }`. `elements` zijn de Overpass-elementen zoals
  ze kwamen, met knopen.
  - `bewaarGebied(bbox, elements)` na een goed antwoord (`OVP_OK`, niet bij leeg),
    met de bbox van de vraag (`contourBbox(geom, OPHAAL_MARGE_M)`).
  - Bij het bewaren gaan weg: gebieden ouder dan 90 dagen, gebieden die het
    nieuwe helemaal bevat, en de oudste boven `CACHE_MAX` (40).
  - Een aparte database, zodat de tegeldatabase van de telapps geen nieuwe
    versie (met een extra store) nodig heeft.
- **De tegels**: `tegelDb()` opent `telsuite_osm` versie 1 met precies de
  aanmaak van `_tileDb` in de telapps (stores `tiles` en `handoff`). Bestaat hij
  nog niet, dan ontstaat hij dus heel. Alleen lezen. Tegels met schema < 3 (zonder
  knopen) tellen niet.
- **`cacheVoor(geom)`**:
  - bronnen zijn eigen gebieden en tegels, niet ouder dan 90 dagen, die de
    rechthoek met marge raken;
  - **gedekt** als elk punt van een raster van 41×41 over de rechthoek van de
    contour (zonder marge) in een bron ligt;
  - dan de wegen die de rechthoek met marge raken, per id de nieuwste;
  - `ts` is de oudste gebruikte bron.
- **Na een mislukte ronde**:
  - `cacheVoor`; bij volledige dekking `gebruikCache` en
    `processWays(..., uitCache=true)`;
  - anders als in v3.65 (`ophaalLater` of de foutmelding);
  - `ophaalGen` (opgehoogd door Wis alles) laat een late uitkomst vervallen;
  - zolang de cache zoekt, staat de melding op "ophalen".
- **`uitCache`** op een weg (en op de stukken bij knippen). Vernieuwen
  (`cacheVernieuwen`) haalt opnieuw op. In `processWays` gaat een bestaande weg
  met `uitCache` door `herstelUitOverpass(el, false)`: de stukken worden op de
  knopen van de verse weg gelegd, met dezelfde keuze. Een weg uit de cache
  vervangt nooit een verse.
- **`cacheDatum(ts)`**: `op dd-mm-jjjj (vandaag / gisteren / n dagen geleden)`.

## 3. Wat niet verandert

- **Altijd eerst Overpass.** De cache is alleen terugval, zodat een knoop die je
  net in OSM toevoegde (om te knippen) gewoon komt.
- **De tegels van de telapps**: telplanning schrijft er niet in. Zijn vraag dekt
  geen hele tegels, en heeft meer wegtypen dan `HIGHWAY_RE`.
- **Wegen uit tegels** hebben alleen de wegtypen van de telapps (`HIGHWAY_RE`).

## 4. Privacy

`privacy.html` (Nederlands en Engels): het wegennet in de browser laat ook zien
waarvoor je een planning maakte. Telplanning bewaart sinds november 2026 ook zijn
opgehaalde gebieden. *OSM-cache legen* in telreconstructie leegt alleen de cache
van de telapps; de websitegegevens van de browser legen alles.

## 5. Handleiding

Telplanning, *Wegen ophalen*: de cache als terugval (sinds v3.66). Wanneer,
de melding met de datum, Vernieuwen, en waarom niet bij een gedeeltelijke
dekking.

## 6. Tests

**Nieuw: `cachetest.py`, 29.** Met het kruisende raster uit hersteltest (met
knopen):
- **A.** Een goed antwoord gaat de cache in: één gebied, alle elementen, met
  knopen, de rechthoek met marge.
- **H.** Overpass werkt: de cache doet niets.
- **B.** Overpass faalt:
  - één ronde, dan de wegen die de rechthoek raken, allemaal `uitCache`;
  - de melding met redenen, `dd-mm-jjjj (vandaag)` en Vernieuwen;
  - geen nieuwe poging;
  - knippen kan, en een knip op een weg uit de cache blijft `uitCache`.
- **D.** Vernieuwen: vers, de keuze en de knip blijven.
- **C.** Een grotere contour: geen cache, de gewone nieuwe poging.
- **G.** Opruimen: ouder dan 90 dagen weg, bevat door het nieuwe weg.
- **E.** Alleen tegels: schema 2 niet, schema 3 wel, "3 dagen geleden".
- **F.** Een lege cache maakt de tegeldatabase heel aan; parkeertelling opent
  hem daarna met beide stores.

Ongewijzigd groen: `ophaaltest` 30, `robuusttest` 90, `knipplantest` 40,
`planlinktest` 51.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | de cache: `cacheDb`, `tegelDb`, `bewaarGebied`, `cacheVoor`, `gebruikCache`, `cacheVernieuwen`, `cacheDatum`, `contourBbox`; `uitCache` in `processWays`, `maakStuk` en `herstelUitOverpass`; de melding; `ophaalGen` |
| `privacy.html` | het wegennet: ook planningen; wat *OSM-cache legen* leegt |
| `traffic_counter_help.html` | *De cache als terugval (sinds v3.66)* |
| `index.html` | versie v3.66 |
| `_archief/overpass_rig/cachetest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py           ALLES OK — de 4 verwachte bestanden
cachetest.py          29/29
volledige ronde lokaal: zie de PR
```
