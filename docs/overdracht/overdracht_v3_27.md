# Overdracht v3.27 — het wegennet van pocket in de noodkopie, oude tegels weg

Uit de lijst "kleine klussen zonder keuzes" (na v3.26). Deze release doet de
drie voor de veld-apps en de tests:
- het netwerk van pocket na Doortellen ook in de ZIP;
- oude tegels uit de cache opruimen;
- `hersteltest` minder wisselvallig maken.

Het ZIP-schema verandert niet.

## 1. Pocket: het wegennet in de noodkopie

**Het probleem (backlog sinds v3.17).** De noodkopie van pocket bewaarde de
tikken en de route, maar niet het wegennet van de snap-motor ("te groot"). Na
een onderbreking was dat netwerk weg:
- *Doortellen* leverde een `_netwerk.csv` met alleen de wegen van na de
  onderbreking, of geen bestand als er geen nieuw netwerk kwam. Telrapport
  haalde de rest via Overpass.
- *Download ZIP* uit de herstelmelding had geen `_netwerk.csv`, en de
  trajectorie-hertoekenning bij Stop (`reassignTrajectory`) sloeg over. De
  tikken hielden de weg die de snap-motor ze live gaf. Daardoor verschilden
  `_gps.csv` en `_telregels.csv` van een telling zonder onderbreking.

**Nu.** Het netwerk staat onder een eigen sleutel, `pocket_sessie_netwerk`,
naast `pocket_sessie`. Zo doen de parkeer-apps het ook (`<sleutel>_netwerk`).
- **Inhoud:** `{ sessieId, wegen: { id: [highway, naam, [lat, lon, …], [knooppunten]] } }`.
  - Compact, zonder `{lat:…, lon:…}` per punt.
  - Met de knooppunten, zodat bij herstel ook de aansluitingen
    (`snap.adjacency`) terugkomen. Die heeft de hertoekenning nodig.
  - `snap.elements` houdt daarvoor sinds deze versie de `nodes` van elke weg
    bij.
- **Schrijven** (`netwerkKopieSchrijf`):
  - alleen als het netwerk groeide (`netwerkKopieVuil`);
  - samen met de gewone noodkopie in `saveSession`, en dus pas vanaf de
    eerste tik;
  - alleen door het venster dat eigenaar is (`kopieMagSchrijven`);
  - een netwerk dat binnenkomt, schrijft meteen, maar alleen de netwerkkopie
    (`netwerkBewaren`). Schreef het ook `pocket_sessie`, dan kon een venster
    dat de telling net herstelde niet meer doortellen: `kopieClaim` ziet dan
    een kopie die sinds het herstel veranderde. `opruimtest` en `logicatest`
    vingen dat in de eerste ronde.
- **Lezen** (`netwerkKopieLees`, in `restoreSession`):
  - alleen een kopie met dezelfde sessie-id;
  - elke weg terug in `snap.elements` en de aansluitingen (`snapRegisterWay`).
- **Doortellen:** de start-functies maken `snap.elements` leeg.
  `hervatTelling` zet het herstelde netwerk daarna terug.
- **Opruimen:**
  - het gedeelde blok noodkopie wist `KOPIE_SLEUTEL + '_netwerk'` al bij
    opslaan en weggooien;
  - `clearSession` (een nieuwe telling) wist hem nu ook.
- **Opslag vol.** Het netwerk wijkt voor de tikken:
  - lukt het netwerk niet, dan gaat de netwerkkopie weg en probeert pocket het
    deze telling niet meer;
  - lukken de tikken niet terwijl er een netwerkkopie staat, dan gaat die weg
    en worden de tikken opnieuw geschreven. Er komt dan geen melding.
  - Telrapport haalt de ontbrekende wegen in beide gevallen zelf.
- **Grootte:**
  - een gewone telling: enkele tientallen kB;
  - de grootste die we zagen: de fietstelling van vóór v3.20, met 1926
    wegen. In dit formaat is dat ongeveer 0,4 MB.
  - De opslag is ~5 MB voor heel telonline.org.

**Gevolg.** Een herstelde telling geeft dezelfde ZIP als een telling zonder
onderbreking: `_netwerk.csv` compleet, en de hertoekenning loopt over de hele
route. Alleen `_snap_trace.csv` ontbreekt nog (diagnose, bewust).

**De Overpass-terugval in telrapport blijft.** Oude pocket-ZIP's (van vóór
v3.27, na Doortellen) missen wegen of het hele bestand. Ook na een volle
opslag kan het nog gebeuren. `onderhoudtest.py` deel A toetst de terugval
nog steeds.

## 2. Tegels opruimen

De tegelcache (IndexedDB `telsuite_osm`, store `tiles`) groeide tot nu toe
zonder eind. Een verlopen tegel werd alleen vervangen als je er weer kwam.

**Nieuw gedeeld blok `tegels opruimen`**, byte-identiek in de vijf bestanden
die de cache gebruiken: parkeertelling, fietsparkeren, capaciteitstelling,
pocket en telreconstructie.
- **Wat weg gaat:**
  - tegels ouder dan 90 dagen, en tegels zonder tijdstempel;
  - 90 dagen ligt ruim boven de langste houdbaarheid (veld-apps 14 dagen,
    reconstructor 60). Er verdwijnt dus niets dat nog gelezen wordt;
  - tegels van een oud schema zijn vanzelf oud.
- **Wanneer:** vijf seconden na het openen, hooguit één keer per dag.
  `localStorage` `telsuite_tegels_opgeruimd` onthoudt wanneer het laatst.
- **Hoe:** eerst zoeken met een cursor die alleen leest, en dus niemand
  ophoudt. Daarna alles in één transactie wissen.
- **Wat blijft:** de store `handoff` (ZIP naar de reconstructor).
- **Zonder cache:** het blok maakt de database aan zoals de rest van de code
  het doet, met beide stores.
- **Fouten:** best effort. Lukt het niet, dan merkt niemand er iets van.

**Privacyverklaring.** "Hij blijft staan tot je hem leegt" klopte niet meer.
Nu: een gebied dat 90 dagen niet opnieuw is opgehaald, ruimen de apps zelf op;
eerder legen kan nog steeds. Dit staat in het Nederlandse en het Engelse deel.

## 3. hersteltest minder wisselvallig

**De oorzaak.** De fout van v2.75 en v3.9 zat niet in de wachttijden. Hij
zat in `_kaart.png` van parkeertelling en fietsparkeren: in de kop van het
plaatje staat het tijdstip van exporteren, tot op de minuut. De test maakt
twee exports, een paar seconden na elkaar: de referentie en die na herstel.
Viel er een minuutgrens tussen, dan verschilde het bestand. Op een trage
machine liggen de twee verder uit elkaar, en gebeurt het vaker.

**De oplossing.** De test vergelijkt een PNG nu pixelrij voor pixelrij,
zonder de kopbalk:
- de kopbalk is 4% van de breedte;
- de eerste rij eronder telt ook niet mee: het PNG-filter kijkt een rij
  omhoog;
- er is geen module voor nodig, alleen `zlib`.

Een verschil in de kaart zelf blijft een fout. Dat is gecontroleerd met twee
plaatjes die alleen in één stip verschilden.

Verder in de test:
- **Wachten op het netwerk.** De pocket-delen wachten nu tot het wegennet
  binnen is: pocket haalt het ongeveer 4 s na de start.
  - Tot nu toe tikte de test al eerder, en telde pocket zonder netwerk. De
    melding heette daarom "Overpass geblokkeerd".
  - Nu wordt er echt gesnapt, en vergelijkt de test `_netwerk.csv` na herstel
    ook.
- **De vaste wachttijden** per GPS-stap blijven. Ze waren niet de oorzaak, en
  ze bepalen hoe ver de nagebootste wandeling loopt.

## 4. Tests

- **`hersteltest.py`** 157 (was 133):
  - **Pocket, vier modi.** Na herstel is het wegennet terug, en is de ZIP
    gelijk aan die zonder onderbreking, ook `_netwerk.csv`. Alleen
    `_snap_trace.csv` mist.
  - **Nieuw deel *het wegennet in de noodkopie*:**
    - een raster met kruisingen (gedeelde knooppunten), crash, en herladen in
      een browser die géén wegennet krijgt (Overpass leeg, geen tegels);
    - de kopie heeft de sessie-id en alle 21 wegen, met soort, naam,
      coördinaten en knooppunten;
    - wegen en aansluitingen komen terug;
    - na Doortellen staat de kopie er weer;
    - de ZIP heeft `_netwerk.csv` met alle wegen, en alle 12 tikken liggen op
      een weg uit dat netwerk;
    - na de export zijn beide kopieën weg.
  - **Ook:**
    - een netwerk van een andere telling wordt niet geladen;
    - opslag vol op twee manieren: tikken bewaard, geen netwerk, geen melding,
      geen tweede poging.
  - **Tegenproef.** Met de pocket van v3.26 faalt dit deel (geen kopie, geen
    `_netwerk.csv`, tikken na Doortellen zonder weg). In de vier modi wijken
    dan `_gps.csv` en `_telregels.csv` af.
- **`onderhoudtest.py`** 31 (was 17), deel C *tegels opruimen*:
  - in alle vijf de bestanden vanzelf na het openen: tegels van 91 dagen, van
    een oud schema en zonder tijdstempel weg; tegels van vandaag, 60 en 88
    dagen en de handoff blijven;
  - dezelfde dag niet nog eens, een dag later wel;
  - zonder cache geen fout, en daarna werkt de cache gewoon.
- **`functest_pocket.js`** 20 (was 18): een binnengekomen netwerk zet
  `netwerkKopieVuil` en schrijft de netwerkkopie; hetzelfde netwerk nog eens
  niet. De test kreeg een stub voor `netwerkBewaren`, zoals al voor
  `snapRegisterWay`.
- **`opruimtest.py`** (139, aantal gelijk): bij "de kopie staat er nog" telt
  de test nu de kopie zelf, zonder `pocket_sessie_netwerk` ernaast. Bij "geen
  kopie" moet ook het netwerk weg zijn; dat was al zo.
- `valideer.py`: groep `tegels opruimen` (5 bestanden).

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `pocket_count.html` | netwerkkopie (`netwerkKopieSchrijf`/`Lees`/`Opgeven`), `nodes` in `snap.elements`, `hervatTelling`; blok tegels opruimen |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | blok tegels opruimen |
| `telreconstructie.html` | blok tegels opruimen; `RECON_VERSIE` v3.27 (regel van `valideer.py`: het bestand veranderde; de stempel gaat als `reconstructie_versie` mee in de `_recon.zip`) |
| `privacy.html` | de cache ruimt zichzelf op (NL en EN) |
| `traffic_counter_help.html` | pocket: het wegennet na een onderbreking; opslag vol |
| `zip_format_reference.html` | pocket `_netwerk.csv`: compleet na herstel sinds v3.27, oudere ZIP's niet |
| `index.html` | versie v3.27 |
| `_archief/overpass_rig/hersteltest.py`, `onderhoudtest.py`, `opruimtest.py`, `functest_pocket.js`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — 9 verwachte bestanden; gedeelde blokken OK, nieuw: tegels opruimen (5 bestanden);
                       RECON_VERSIE v3.27
hersteltest.py         157/157 (was 133)
onderhoudtest.py       31/31 (was 17)
opruimtest.py          139/139
functest_pocket.js     20/20 (was 18)
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
