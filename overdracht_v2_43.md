# TrafficCounterSuite v2.43 — Overdracht

**Route A: "Direct reconstrueren"-knop + gedeelde OSM-tegelcache.** Na een telling ben je nu één tik van de reconstructie verwijderd, en wat de tel-app onderweg aan netwerk ophaalt hoeft de reconstructor later niet opnieuw te fetchen. Vijf bestanden gewijzigd t.o.v. v2.42.

## Waarom route A (en niet volledig automatisch)

De reconstructie hangt op een Overpass-fetch over de bbox van de héle route (`timeout:25`) plus Viterbi-matching — precies de dingen die in het veld onbetrouwbaar zijn (wisselend bereik). De tel-apps zijn klein, schermloos en offline-bestendig; de reconstructor is groot, kaart-gedreven en netwerk-afhankelijk. Die samenvoegen kost de veld-apps hun betrouwbaarheid. Route A geeft het gemak zonder de export-flow afhankelijk te maken van veldbereik.

## 1. Direct reconstrueren (handoff)

- **Knop "↻ Direct reconstrueren"** onder de ZIP-knop in `parkeertelling`, `fietsparkeren` en `capaciteitstelling`. Verschijnt zodra de ZIP gebouwd is (na Stop).
- Een ZIP-blob kan niet via een URL mee, dus de overdracht loopt via **IndexedDB**: de app legt de blob in store `handoff` (`telsuite_osm`) en opent `parkeer_reconstructie.html?handoff=1`.
- De reconstructor heeft een **ontvanger** die bij `?handoff=1` de blob ophaalt, als `File` door het bestaande `verwerkBatch()` haalt, en de overdracht daarna **wist** (zodat een refresh niet opnieuw dezelfde telling inlaadt).
- Faalt de overdracht, dan meldt de app dat je de ZIP handmatig kunt slepen — geen stille fout.
- Beide DB-openers (OSMCACHE én de handoff-ontvanger) maken nu **beide stores** aan, zodat de volgorde van openen niet uitmaakt.

Voor bulk blijft het bestaande batch-pad: sleep een hele dag aan ZIP's tegelijk in de reconstructor.

## 2. Gedeelde tegelcache

De reconstructor cachet OSM-netwerk per vaste tegel (`t_<ty>_<tx>`, 0,01° ≈ 1,1 km, 60 dagen vers) in IndexedDB `telsuite_osm`. De veld-apps fetchten wel netwerk (`around:250m`) maar gooiden dat weg. Nu schrijven ze het in **hetzelfde formaat** weg — zelfde origin, dus de reconstructor vindt het automatisch terug.

**De valkuil die dit vermijdt:** een tegel geldt bij de reconstructor als compleet zodra hij vers is. Zou een veld-app een half gevulde tegel wegschrijven (één fetch-cirkel van 250 m dekt nooit een tegel van 1,1 km), dan zou de reconstructor die als vers lezen en **stilletjes wegen missen** — slechtere reconstructies zonder waarschuwing.

**Oplossing:** de app houdt per tegel bij welk deel gedekt is (raster 8×8 = 64 cellen); een tegel gaat pas de cache in als **alle 64 cellen** binnen een opgehaalde cirkel lagen. Bij een systematische wijk-telling loopt een tegel gaandeweg vol en wordt hij precies één keer weggeschreven. Dekt de route maar een deel van een tegel, dan wordt er niets gecached — liever geen cache dan een misleidende.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon op alle vijf.
- **Tegelsleutel-formaat** geverifieerd identiek aan de reconstructor (`t_<floor(lat/0,01)>_<floor(lon/0,01)>`).
- **Functietest dekking:** een gesimuleerde systematische wijkwandeling (11×11 fetches, r=250 m) brengt tegel `t_5185_433` van 0 naar 64/64 en schrijft 'm exact één keer weg. Een enkele fetch schrijft (terecht) niets weg.
- **Byte-identiteit:** t.o.v. v2.42 wijzigden uitsluitend de vier veld-apps + `parkeer_reconstructie.html`.

## Kanttekeningen

- **pocket_count** kreeg wél de gedeelde cache, maar (nog) géén reconstructie-knop — pocket exporteert via `stopTelling()`/share en heeft geen ZIP-knop-paneel. Toe te voegen als het bevalt.
- Cache is **best-effort**: elke fout wordt stil opgevangen; het tellen mag er nooit door verstoord worden.
- De cache vult zich pas bij voldoende dekking — bij een korte telling langs één straat blijft hij leeg. Dat is bedoeld.

## Backlog (ongewijzigd)

- Reconstructie-knop ook in pocket; dekkingskaart/audio breder uitrollen.
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
