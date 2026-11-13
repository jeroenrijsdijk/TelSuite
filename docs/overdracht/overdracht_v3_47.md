# Overdracht v3.47 — telrapport: de stippen na het tijdfilter

Jay: "In telrapport kun je telling zips laden waarna je van ale ingeladen zips
een geopackage kunt maken. In de laatste geopackage zit alleen teltype alles,
terwijl het een mix was van heel veel soorten tellingen. Check eens hoe dat
komt?" Na de uitleg en het voorstel: "Ga".

## 0. Wat er in zijn GeoPackage zat

`telrapport_20261113_1737.gpkg`:

- **`sessies` en `route`:** 185 tellingen, alle op de kaart. 113 winkelstraat
  en 72 simpel, van 14 mei tot 13 november.
- **`wegvakken`:** compleet, 301 getelde stukken met samen ruim 11.000 tikken.
- **`waarnemingen`:** 25 stippen, alle van type "Alles", uit twee tellingen:
  TMX op 29 juni en XVU op 9 juli. "Alles" is een eigen soort, bij Start
  ingetypt.
- **`export_info`:** tijdfilter uit, clusters uit.

De GeoPackage neemt mee wat op de kaart staat (`gpkgLagen`, `map.hasLayer`).
De stippen van de andere 183 tellingen stonden dus niet op de kaart.

## 1. De oorzaak

Het tijdfilter zette de stippen van een telling aan en uit met de typeknopjes
van fietsparkeren en parkeren:

```js
cfg.types.forEach(type => showHideDots(sid, type, dotVisible[type] && inWin));
```

Dat stond zowel in `applyTimeFilter` als in `toggleTimeFilter(false)`.

- **Pocket heeft geen typeknopjes.** `dotVisible.tegemoet`, `.car` en dergelijke
  zijn `undefined`, dus "uit". De stippen gingen weg bij het aanzetten en
  opnieuw bij het uitzetten.
- **Een eigen soort staat niet in `APP_CONFIG.pocket.types`.** De lus raakte
  hem dus nooit aan: "Alles" bleef staan, ook buiten het tijdvenster.
- **`leeg` bestaat in beide.** Pocket parkeren (leeg vak) volgde het knopje
  "leeg" van parkeren, bij het tijdfilter en bij een klik op dat knopje.
- **De sessielijst deed het wel goed.** `applySessionVisibility` had een
  uitzondering voor pocket: alle stippen van een zichtbare telling. Een groep
  uit en aan zetten bracht de stippen dus terug; dat was de omweg.

Nagebootst met een simpele telling (auto), een winkelstraat en een
"Alles"-telling:

| moment | stippen op de kaart |
|---|---|
| na het laden | auto 3, tegemoet 2, stilstaand 1, Alles 2 |
| tijdfilter aan | Alles 2 |
| tijdfilter weer uit | Alles 2 |
| groepsoog uit en aan | alles terug |

## 2. De reparatie

`zetStippen(sid)`, naast `showHideDots`, bepaalt welke stippen van één telling
op de kaart staan:

- **Fietsparkeren en parkeren:** per type, zoals het knopje staat
  (`dotVisible`).
- **Pocket:** alle stippen van een zichtbare telling, ook een eigen soort.

`showHideDots` kijkt daarbij ook naar `visible`. Het tijdfilter zet dat eerst
op "in het venster".

Vijf plekken gaan er nu langs:

1. de sessielijst (`applySessionVisibility`, de uitzondering voor pocket is
   weg);
2. het tijdfilter aan (`applyTimeFilter`);
3. het tijdfilter uit (`toggleTimeFilter`);
4. de typeknopjes;
5. een verzameling met opgeslagen weergave (`pasVerzamelingWeergaveToe`).

Voor fietsparkeren en parkeren verandert er niets. Ze volgden al hun knopjes en
het tijdfilter.

## 3. Test

`tijdfiltertest.py` (nieuw, 21). Hij gebruikt de hulp van `gpkgtest.py`.

- **A.** Vijf tellingen met de veld-apps: parkeertelling, pocket parkeren,
  winkelstraat, simpel (auto), en simpel met de eigen soort "Alles".
- **B.** In telrapport staan alle stippen op de kaart.
- **C.** Tijdfilter aan, met "Alles" zes uur later gezet.
  - De vier tellingen in het venster houden al hun stippen.
  - "Alles" heeft er geen.
  - Een uur waar niets valt: geen enkele stip.
- **D.** Tijdfilter weer uit.
  - Alle stippen staan terug.
  - In de GeoPackage (`waarnemingen`) staat elke soort met het goede aantal.
- **E.** Het knopje "leeg" van parkeren.
  - Alleen de lege plekken van de parkeertelling gaan uit, de lege vakken van
    pocket niet.
  - Weer aan: alles terug.
- **F.** Winkelstraat uit en aan in de sessielijst.

Op de telrapport van v3.46 geeft dezelfde test 9 FOUT: na het tijdfilter staan
alleen "Alles", de lege vakken van pocket en de parkeertelling er nog. Dat is
precies wat Jay zag.

## 4. Wat nog meer dubbel staat (niet in deze release)

Jay vroeg: "zijn er nog meer functies die twee of drie keer ongeveer hetzelfde
doen, kan er nog meer samengevoegd worden ?" Vier dingen, in de backlog van de
stand van zaken. Jay koos om v3.47 bij het tijdfilter te houden.

1. **Een telling aan- of uitzetten op de kaart.** Sessielijst, tijdfilter aan en
   tijdfilter uit zetten elk apart de route, de capaciteit en Static aan of uit.
2. **Fout: de tabel van een clusterbol** (`showClusterDetail`) loopt over
   `cfg.types`. Een eigen pocket-soort ("Alles") ontbreekt; alleen het totaal
   klopt. Nagebootst. `clusterPunten` doet het goed.
3. **Dimmen bij hover** staat drie keer: `setSessionEmphasis` en twee keer in de
   bollen. Daar dimt het alleen stippen en bollen, met 0,12 en 0,15.
4. **`clusterDekking`** doet de puntkeuze van `drawClusters` na. Volgens het
   commentaar moet hij meelopen bij elke wijziging.

Bewust niet samenvoegen:

- de drie projecties op een lijn: elk geeft iets anders terug, en de
  correctietool hangt ervan af;
- de twee laders;
- de gedeelde blokken tussen de bestanden.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `zetStippen`; de vijf plekken hierboven |
| `index.html` | versie v3.47 |
| `_archief/overpass_rig/tijdfiltertest.py` | nieuw |
| `_archief/overpass_rig/functest_verzameling.js` | een stub voor `zetStippen`: de test knipt `pasVerzamelingWeergaveToe` uit de pagina en zet de functies eromheen zelf neer |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py           ALLES OK — de 2 verwachte bestanden
tijdfiltertest.py     21/21 (op v3.46: 12 ok, 9 FOUT)
volledige ronde lokaal: zie de PR
```
