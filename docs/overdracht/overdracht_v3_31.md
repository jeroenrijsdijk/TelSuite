# Overdracht v3.31 — Ordenen

Jay: "Het wordt ook tijd voor een soort organizer. Originelen waarvan een _recon
is kunnen in een map, en ik wil aangeboden .zips verplaatsen naar een map per
type telling. Waar kunnen we dat kwijt?"

Voorstel met vier keuzes. Jay koos:
- **plek:** een eigen pagina *Ordenen*;
- **mappen:** "zoals de voorpagina";
- **originelen:** een submap per soort;
- **bron:** "één map, ter plekke", dus ordenen binnen het gekozen archief.

Er verandert niets aan de tellingen, de ZIP's of het schema. Ordenen verplaatst
alleen bestanden.

## 1. Wat het doet

`telarchief.html`, op de voorpagina onder *Achter je bureau* (*Ordenen* / *Sort*).

1. **Lezen.** Je kiest je archiefmap (`showDirectoryPicker`, lezen en
   schrijven). De pagina leest elke `.zip`, ook in submappen; mappen met een
   punt ervoor slaat hij over. Van elke ZIP berekent hij de SHA-256 en leest
   hij `_sessie.csv`, of `verzameling.json` voor een verzameling.
2. **Plan.** Per bestand toont de tabel waar het nu staat, waar het heen gaat
   en waarom.
   - Bovenaan staan de tellers: te verplaatsen, waarvan dubbel, staat al goed,
     blijft liggen, naamconflict.
   - Wat al goed staat, is verborgen tot je het aanvinkt.
   - Elke verplaatsing heeft een vinkje.
   - Op een smal scherm schuift de tabel binnen zijn kader.
3. **Uitvoeren.** Pas na de knop wordt er verplaatst, alleen wat aangevinkt is.
   Per rij ✓ of de reden waarom niet. Daarna een regel per verplaatsing in
   `ordenen_logboek.csv` in het archief: `tijdstip;van;naar;reden;sha256`.
   Het logboek wordt aangevuld en nooit overschreven.

## 2. De indeling (`ORDENEN`, los getest)

- **Soort:** eerst de naam, dan de inhoud, zoals de ZIP-referentie het zegt
  ("filename markers win").
  - `_car` → Autoparkeren, `_fts` → Fietsparkeren, `_cap` → Capaciteit;
  - `_pkt_p|s|t|w` → Pocket parkeren, Pocket simpel, Transect, Winkelstraat;
  - `_sta` → Stilstaand;
  - `TelVerzameling_…` of `verzameling.json` → Verzamelingen.
  - Zonder merkteken (een `_recon` van auto of fiets heet `<sid>_recon.zip`)
    komt de soort uit `app_type` in `_sessie.csv`, en voor pocket uit `modus`
    of de letter in de sessie-id.
- **Reconstructie:** de naam eindigt op `_recon`, of `_sessie.csv` heeft de
  kolom `reconstructie`.
- **Originelen:** zijn de sessie-id's gelijk en is er een reconstructie, dan
  gaat het origineel naar `<soort>/originelen`.
  - Is de reconstructie later weg, dan komt het origineel bij een volgende
    keer ordenen terug in `<soort>`.
  - Zonder `_sessie.csv` geldt de naam zonder `_recon` en zonder het
    merkteken.
- **Dubbelen:** bestanden met dezelfde SHA-256. Er blijft er één staan:
  - eerst die al op zijn plek staat;
  - dan een naam zonder `(1)`;
  - dan het kortste pad.

  De rest gaat naar `dubbel/`, en krijgt daar een volgnummer als de naam al
  bezet is. Andere inhoud onder een bijna gelijke naam is geen dubbel: beide
  blijven.
- **Nooit overschrijven.**
  - Staat er op de bestemming al een ander bestand, dan is het een
    naamconflict en blijft het bestand liggen.
  - Gaan twee bestanden naar dezelfde plek, dan gaat de eerste en is de
    tweede een conflict.
  - Hoofdletters tellen niet (Windows en macOS). Een map `autoparkeren/` is
    dus `Autoparkeren/` en geldt als goed.
- **Blijft liggen:** alles wat geen telling van telonline.org is: andere ZIP's,
  het oude `_trn`-formaat, onleesbare ZIP's (met de reden).

## 3. Verplaatsen

- **Eerst `move()`.** `FileSystemFileHandle.prototype.move`, een hernoeming
  binnen de schijf (in Chromium 141 aanwezig).
- **Lukt `move()` niet, of ontbreekt het:**
  1. kopiëren;
  2. de kopie teruglezen en de SHA-256 vergelijken;
  3. pas dan het origineel weghalen. Wijkt de kopie af, dan gaat de kopie weg
     en blijft het origineel.
- **Vlak voor het schrijven** wordt nog eens gekeken of de bestemming vrij is.

## 4. Andere browsers

Firefox en Safari kennen `showDirectoryPicker` niet. Daar zie je *Alleen
bekijken*: een mapkeuze (`webkitdirectory`) die het plan toont, met dezelfde
paden zonder de gekozen map. *Uitvoeren* en de vinkjes staan uit, en een
melding zegt waarom. Jay werkt op Windows met Chrome of Edge, dus daar kan
alles.

## 5. Elders bijgewerkt

- **`index.html`:** *Ordenen* / *Sort* onder *Achter je bureau*; versie v3.31.
- **`over.html` en `about.html`:**
  - het "(gepland)" bij het organiseren van ZIP's wijst nu naar Ordenen;
  - de alinea over de groepen noemt ordenen.
- **Handleiding:** sectie *ZIP's ordenen* (`#ordenen`) onder Algemeen. Daar
  staat ook de vraag aan wie zelf scripts of KNIME gebruikt: zoekt dat in
  submappen?
- **Privacyverklaring:**
  - Nederlands: Ordenen leest en verplaatst alleen in de gekozen map, met
    toestemming, en stuurt niets het netwerk op;
  - het Engelse deel zegt hetzelfde.
- **`sitemap.xml`:** `telarchief.html` erbij.
- **`docs/ONTWIKKELEN.md`:** de pagina in de plattegrond.

Telrapport hoefde niet mee: een hele map slepen leest de submappen al
(`walkEntry`). Het vinkje *bij een paar alleen de _recon-versie laden* laat de
originelen in `originelen/` weg. Een kopie in `dubbel/` laadt niet twee keer,
omdat de sessie-id al bekend is.

## 6. Open

- **KNIME.** Jay is gevraagd of zijn flow ook in submappen zoekt. Er is nog
  geen antwoord. De pagina en de handleiding wijzen erop.
- **Een knop "terugzetten"** volgens het logboek bestaat niet. Het logboek
  maakt het met de hand mogelijk.

## 7. Tests

- **`functest_ordenen.js`** (nieuw, 32): de indeling los van de browser.
  - de soort per merkteken, en uit `_sessie.csv` als het merkteken ontbreekt;
  - de naam gaat voor de inhoud;
  - originelen bij een reconstructie (ook pocket, op de sessie-id), en terug
    als de reconstructie weg is;
  - dubbelen (wie blijft, het volgnummer in `dubbel/`);
  - naamconflicten, en hoofdletters;
  - overslaan, met de reden.
- **`ordenentest.py`** (nieuw, 41), in Chromium op echte bestanden in de Origin
  Private File System, met een nagebootste `showDirectoryPicker`.
  - **Het plan:** voor elk van de 11 ZIP's de goede bestemming, de tellers,
    verborgen wat goed staat, en de knop.
  - **Uitvoeren:**
    - de boom is daarna precies zoals verwacht, met elke inhoud ongewijzigd;
    - niets is weg, en een uitgevinkte rij blijft liggen;
    - het logboek klopt, met de SHA-256 per regel;
    - met `move()` is elke verplaatsing een hernoeming (6 keer).
  - **Opnieuw lezen:** alles staat goed, op de uitgevinkte rij na.
  - **Zonder `move()`:** de kopieerweg, met dezelfde uitkomst.
  - **Zonder `showDirectoryPicker`:** alleen bekijken, en het plan is
    hetzelfde.
- **Bekeken:** de pagina met een plan op 1300 en 390 px breed.

## 8. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telarchief.html` | nieuw |
| `index.html` | Ordenen onder Achter je bureau; versie v3.31 |
| `over.html`, `about.html` | verwijzing naar Ordenen |
| `traffic_counter_help.html` | sectie *ZIP's ordenen* |
| `privacy.html` | Ordenen (NL en EN) |
| `sitemap.xml` | `telarchief.html` |
| `_archief/overpass_rig/functest_ordenen.js`, `ordenentest.py` | nieuw |
| `valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 9. Validatie

```
valideer.py            ALLES OK — telarchief.html nieuw, de 6 andere verwachte bestanden gewijzigd; titel 55, description 136;
                       sitemap 16 adressen; gedeelde blokken OK
functest_ordenen.js    32/32 (nieuw)
ordenentest.py         41/41 (nieuw)
alle overige browsertests en de 21 functests groen; test_zipref en check_encoding OK
```
