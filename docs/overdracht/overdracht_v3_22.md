# Overdracht v3.22 — Static in de familie, één herstelmelding

Jay vroeg om "een voorstel om onze eerste module ooit, het statisch tellen
vanaf 1 plek, in harmonie te brengen met de rest van de app". Het voorstel had
drie lagen:
1. gelijktrekken;
2. Static op de weg;
3. opgaan in pocket (afgeraden).

Jay antwoordde: "Taal: nederlands. Van Static draait niet in knime. Maak
Herstelmelding: één gedeeld blok voor alle vijf veld-apps."

Deze release bevat laag 1 en de gedeelde herstelmelding. Over laag 2 is nog niet
besloten; zie §4. Het ZIP-schema verandert niet.

## 1. Static gelijkgetrokken

**Nederlands.** `lang="nl"` en alle teksten: knoppen, statusregels,
GPS-meldingen, kompas en vragen.
- Richting B staat standaard op *Oost* (was *East*).
- Nominatim krijgt `Accept-Language: nl`, dus plaats en land komen in het
  Nederlands in de export (*Nederland*).

**Huisstijl van de parkeer-apps.** Van boven naar onder:
- donkere kop met ←, *Stand Still and Count* (zoals op de voorpagina),
  *telonline.org* en een ? naar de handleiding;
- statusbalk met GPS-stip en *🔒 aan*;
- sessiepaneel met start, einde, plek en de klok;
- ▶ Start en ■ Stop;
- *Plek / notities*;
- de richtingen als ◀ A en B ▶, met *kompas*;
- totaalbalk, telkaarten, ↩ ongedaan maken, ↓ Download ZIP en *Wissen*;
- de tellog.

De telkaarten blijven zoals ze waren: per type twee +1-knoppen, de −-knoppen en
de toetsen voor de computer. De GPS-stip is alleen groen tijdens het tellen.

**Kleuren van telrapport.** Tot v3.22 had Static een eigen palet: de fiets was
hier blauwgroen en in telrapport paars. `TYPE_KLEUR` in Static is nu gelijk aan
`SS_TYPE_COLOR` in telrapport. `valideer.py` bewaakt dat als gedeelde constante
`typekleuren`. Op het geel van de motor staat de tekst donker (`inktOp`): wit is
op geel in de zon niet te lezen.

**Opslaan via `bewaarZip`.** Het gedeelde blok staat nu in vier bestanden.
- Static meldt nu ook *ZIP opgeslagen* of *ZIP niet opgeslagen*, en een
  ingebouwde browser van een app (WebView) telt niet als opgeslagen.
- Het blok kreeg een haak, `zipBewaard()`. Die geeft true als de telling met
  deze ZIP af is (kopie en melding weg), en false bij een tussentijdse ZIP.
  Dat laatste gebeurt alleen in Static, als je tijdens het tellen een ZIP
  maakt.
- `zipSleutel` verwees naar variabelen van de parkeer-apps. Hij staat nu net
  na het blok.
- Static's eigen `saveBlob` is weg, en `exportCSV` heet nu `exportZip`.

**Na Stop meteen weer Start**, zoals in de parkeer-apps. Is de vorige telling
nog niet opgeslagen, dan vraagt Static het eerst. *Wissen* vraagt alleen nog
bij een telling die niet is opgeslagen.

**De export blijft gelijk.** De kolommen van `_sessie`, `_telregels` en
`_onderbrekingen` veranderen niet. `_overzicht.csv` blijft Engels, omdat
telrapport hem leest, ook van oude tellingen (`parseStandStillCsv`). Daarom
heeft elk type nu twee namen: `label` (Engels, voor het overzicht) en `naam`
(Nederlands, voor op het scherm).

## 2. Eén herstelmelding voor de vijf veld-apps

Nieuw gedeeld blok `herstelmelding` in parkeertelling, fietsparkeren,
capaciteitstelling, pocket en Static.

| | tot v3.22 | v3.22 |
|---|---|---|
| parkeer-apps | gele balk met "N vermeldingen hersteld van <tijd>", losse Doortellen-knop, downloaden met de knoppen onderaan, geen Weggooien | de melding hieronder |
| pocket | bruin blok: Doortellen, Download, Verwijder | idem |
| Static | Engelse bruine balk: Continue, Download, Discard | idem |

**De melding.** Een bruin blok, met dezelfde kleuren als de melding van v3.8.
- Tekst: "⚠️ Onderbroken telling hersteld: 4 tikken, gestart 11:32, laatst
  bewaard 11:33." Pocket zet de modus erbij.
- Een tijd van een andere dag krijgt dag en datum, zoals de lijst op de
  voorpagina ("do 15-10 10:05").
- Knoppen: ▶ Doortellen, ↓ Download ZIP, ✕ Weggooien.

**Gedrag.**
- **Afgerond.** Bij een gestopte, nog niet opgeslagen Static-telling staat er
  "Afgeronde telling, nog niet opgeslagen … gestopt 11:40", zonder Doortellen.
- **Download ZIP.** Is de ZIP aantoonbaar opgeslagen, dan zijn kopie en melding
  weg. Static sluit een onderbroken telling zo af op het laatst bekende moment.
  Pocket gaat zoals altijd via zijn voorbeeldscherm.
- **Weggooien.** De vraag staat in het blok (`herstelWeg`). Daarna roept het
  blok de functie van de app aan, die de kopie afsluit en het scherm leegmaakt.
  De parkeer-apps konden een herstelde telling tot nu toe alleen weggooien door
  een nieuwe sessie te starten. Ze hebben daarvoor nu `herstelWeggooien` in het
  gedeelde blok `herstel-haken`.
- **Nieuwe telling terwijl de melding staat.** Er komt eerst een vraag
  (`herstelNieuw`): "Nieuwe telling starten? De herstelde telling (4 tikken)
  wordt dan weggegooid." Die vraag vervangt de eigen vragen van de parkeer-apps
  (`startSession`) en pocket (`magNieuwStarten`). In Static staat Start uit
  zolang de melding er is.
- **Taal.** Tweetalig via de taal van de pagina, zoals de melding van v3.8.
  Alleen pocket kent een taalknop.

**Haken per app.** Elke app levert twee dingen: een lege
`<div id="herstel-melding">` op de plek van de melding, en `HERSTEL_ACTIES`, de
namen van zijn functies.
- parkeer-apps: `hervatSessie`, `exportZip`, `herstelWeggooien`;
- pocket: `hervatTelling`, `restoreDownload`, `restoreDiscard`;
- Static: `doortellenStatic`, `exportZip`, `verwijderStatic`.

Die functies vragen zelf niets meer, zodat tests ze direct kunnen aanroepen.

**Ook aangepast.**
- Blok `hervatSessie`: `herstelOpen()` staat nu in de herstelmelding.
- Pocket: de directe parkeer-ingang vraagt `herstelOpen()`.

## 3. Gevonden, niet veranderd

- **GPS-betrouwbaarheid.** Het leesbare overzicht schrijft bij `GPS reliable`
  "Yes (< 25m)", maar Static rekent een positie al vanaf 20 m als betrouwbaar
  (`GPS_ACCEPT_ACC`). De oude handleiding zei 25 m, de nieuwe zegt 20 m (de
  code). De tekst in het overzicht is niet veranderd: dat is de export.
- **Kop van de parkeer-apps.** *Walk and Survey Parked Cars* loopt op een
  telefoon over twee regels. Dat was al zo.

## 4. Laag 2: Static op de weg (nog niet besloten)

Na de GPS-fix snapt Static het punt op de dichtstbijzijnde weg, met dezelfde
knip in stukken als v3.21.
- **Richtingen.** De namen komen uit het netwerk: de weg volgen tot de eerste
  kruising met een straat met een naam ("richting Gorsstraat").
- **Welke knop welke richting is.** Dat volgt uit je positie ten opzichte van
  de as. Het kompas beslist alleen als je te dicht op de as staat.
- **Bevestigen.** Een minikaartje met ⇄ om te wisselen.

In de export komen er dan kolommen achteraan bij, zoals `osm_way_id`,
`segment_index` en of A met of tegen de OSM-richting gaat. Jay: "Van Static
draait niet in knime". Een uitbreiding raakt dus alleen
`zip_format_reference.html` en telrapport (een Static-telling met pijlen op zijn
stuk). Eerst Jays keuze.

## 5. Tests

- **`herstelmeldingtest.py`** (nieuw, 103 tests, Chromium):
  - *A.* In alle vijf apps dezelfde opbouw, tekst en knoppen.
  - *B.* Weggooien: nee laat alles staan. Ja haalt de melding en de kopie weg,
    zet de telling op de lijst, maakt het scherm leeg en toont na herladen
    niets meer.
  - *C.* Een nieuwe telling terwijl de melding staat.
  - *D.* Download ZIP vanuit de melding.
  - *E.* Static: afgerond, zonder Doortellen.
  - *F.* Static: een tussentijdse ZIP laat de telling lopen.
  - *G.* Engels, en een tijd op een andere dag.
  - *H.* Static Nederlands, met het palet van telrapport.
- **Bijgewerkt:** `hersteltest.py`, `laadtest.py` en `opruimtest.py` kijken
  naar `#herstel-melding`, en Static's export heet `exportZip()`.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter.html` | Nederlands, huisstijl, palet, `bewaarZip` met `zipBewaard`, herstelmelding, Start na Stop |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | blokken `herstelmelding` en `herstel-haken`; `bewaarZip` met haak; `hervatSessie` zonder `herstelOpen`; `startSession` en `restoreSession` via de melding |
| `pocket_count.html` | blok `herstelmelding`; `restoreSession`, `restoreDownload`, `restoreDiscard`, `magNieuwStarten`, `hervatTelling` en de directe ingang via de melding |
| `traffic_counter_help.html` | hoofdstuk Static in het Nederlands (`#static`, `#sta-…`); herstelmelding bij parkeren, pocket en *Onderbreking, herstel & doortellen* |
| `zip_format_reference.html` | de knop heet nu *Doortellen* (was *Continue*); verder ongewijzigd, het schema blijft |
| `index.html` | versie v3.22 |
| `_archief/overpass_rig/herstelmeldingtest.py` | nieuw |
| `hersteltest.py`, `laadtest.py`, `opruimtest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt (groepen `herstelmelding`, `herstel-haken`, `bewaarZip` met Static, constante `typekleuren`) |

## 7. Validatie

```
valideer.py            ALLES OK — 8 verwachte bestanden gewijzigd; gedeelde blokken OK
                       (herstelmelding 5 bestanden, herstel-haken 3, bewaarZip 4, noodkopie 5);
                       constante typekleuren OK (Static = telrapport)
herstelmeldingtest.py  103/103 (nieuw)
hersteltest 133, statictest 24, opruimtest 139, laadtest 45, robuusttest 87, logicatest 30,
planlinktest 51, onderhoudtest 17, opslaantest 48, gebiedtest 51, stukkentest 21, gpkgtest 80
functests              alle 20 groen
test_zipref.py         referentie sluit aan op de code
check_encoding.py      alles geldige UTF-8
```
