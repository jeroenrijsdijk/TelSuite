# Overdracht v2.72 — Static krijgt een noodopslag, alle veld-apps kunnen doortellen

Twee wensen van Jay, gebouwd en getest:

- Static krijgt dezelfde noodopslag als de parkeer-apps.
- Doortellen na herstel.

Daarnaast is Static doorgelicht. Die tool is de oudste van de suite. Wat
daarbij opviel staat in §6; dat is niet gebouwd, eerst bespreken.

---

## 1. Samenvatting

| app | noodopslag | doortellen na herstel |
|---|---|---|
| Static (`traffic_counter.html`) | **nieuw** — per tik + hartslag elke 10 s | **nieuw**, onderbreking telt niet mee |
| parkeertelling | had al | **nieuw** |
| fietsparkeren | had al | **nieuw** |
| capaciteitstelling | had al | **nieuw** |
| pocket (4 modi) | had al (werkt sinds v2.69) | **nieuw** |

Verder:

- Alle vijf de apps vragen nu eerst bevestiging als je een nieuwe telling
  start terwijl er een herstelde klaarstaat. Voorheen werd die stil gewist.
- Static houdt het scherm aan tijdens het tellen. De andere veld-apps deden dat
  al.

## 2. Static: noodopslag

**Opslaan.** Sleutel `static_sessie`. Opgeslagen wordt:

- tellers, tijdlog, starttijd, eindtijd;
- de GPS-fix;
- notities en richtinglabels;
- de onderbrekingen.

Dat gebeurt bij elke tik, elke −1 en elke Undo, bij het wijzigen van notities
of richtingen, bij Start en End, bij scherm-uit en bij `pagehide`. Daarnaast
elke 10 s een **hartslag** (`laatstActief`).

**Herstel bij het laden.** Er verschijnt een bruine balk onder de statusregel
met drie knoppen: **Continue**, **Download** en **Discard**. De tellers en het
tijdlog staan er al weer.

- **Download zonder door te tellen:** de export loopt tot het laatste bekende
  moment (`laatstActief`), niet tot nu.
- **Afgeronde telling die nog niet gedownload was:** dezelfde balk, zonder
  Continue.
- **Afgerond én geëxporteerd:** wordt bij het laden stil opgeruimd. Dat is
  hetzelfde gedrag als bij de parkeer-apps.
- **Reset en Discard** wissen de opslag.

Static is Engelstalig, dus de nieuwe teksten zijn dat ook (zie §6).

## 3. Static: doortellen en onderbrekingen

Static rekent een telling om naar een uurintensiteit. Een onderbreking waarin
niet geteld is, zou die intensiteit omlaag trekken. Daarom geldt:

- **Continue** legt een onderbreking vast: van `laatstActief` tot het moment
  van doortellen. Dankzij de hartslag klopt die tot op 10 s, ook als er even
  geen verkeer langskwam.
- De klok op het scherm, `Observed duration` en de `Extrapolation factor`
  tellen alleen de **actieve** tijd.
- In de CSV komen, alleen als er onderbroken is, direct na
  `Observed duration`:
  ```
  Interruptions;1;00:03:51 not counted, excluded from duration and per-hour figures
  Interruption 1;2026-09-23 14:37:12;2026-09-23 14:41:03
  ```
- `End time` − `Start time` bevat de onderbreking nog wel. Telrapport gebruikt
  de factor als die er is (gecontroleerd in `parseStandStillCsv`). De
  uurintensiteit in telrapport klopt dus; alleen de getoonde duur is die van
  begin tot eind.
- **Zonder onderbreking is de export ongewijzigd.** Getoetst: v2.71 en v2.72
  geven naast elkaar dezelfde regelopbouw.

Na doortellen laat Static de GPS opnieuw settelen, als de fix bij de
onderbreking nog niet was vastgezet.

`zip_format_reference.html` beschrijft de nieuwe regels. De bewering "losse
CSV, geen ZIP" is daarbij rechtgezet; zie §6.

## 4. Doortellen in de parkeer-apps en pocket

**Parkeer-apps.** Er is een nieuwe knop **▶ Doortellen** onder de
herstelmelding, en de melding noemt hem ook.

- `hervatSessie()` start GPS, kompas, scherm-aan en straatnaam weer.
- Er wordt niets gewist. Sessie-id, teller, starttijd, vermeldingen, tellers,
  GPS-spoor en het opgeslagen wegennet blijven, en alles komt in één ZIP.
- Het wegennet rond de huidige plek wordt opnieuw opgehaald en aangevuld.
- De downloadknoppen zijn tijdens het tellen uit, net als na Start: eerst Stop.
- **Gedeeld blok, byte-identiek in alle drie de apps.** `valideer.py` bewaakt
  het (groep `hervatSessie`). Waar de apps verschillen (`prevLat` alleen in
  capaciteit, `lastMoved`) vangt `typeof` dat op.

**Pocket.** Er is een groene knop **▶ Doortellen** in de herstelmelding.
`hervatTelling()` gaat in twee stappen:

1. De modus gewoon starten: scherm, GPS en scherm-aan.
2. De telling terugzetten: tikken, route, starttijd en de tellers per modus.
   - transect: `tcCounts` en de richtinglabels;
   - winkelstraat: teruggerekend uit de tikken;
   - parkeren: teruggerekend uit de tikken;
   - simpel: het grote getal.

De start-functies wissen de noodopslag, maar `saveSession()` schrijft hem
direct terug. De route loopt door vanaf het laatste routepunt.

**Een nieuwe telling vraagt eerst bevestiging.** In de parkeer-apps gebeurt dat
bij Start, in pocket bij elke modusknop (`magNieuwStarten()`), en in Static zit
Start dicht tot Continue of Discard. Dit was een backlogpunt sinds v2.70.

## 5. Tests (`hersteltest.py`, nu 133 tests)

- **Nep-Overpass.** Er is een raster van woonstraten rond het teststartpunt
  toegevoegd. De apps snappen daardoor echt: alle tikken krijgen een way, en er
  zijn 20 ways in het net.
- **Crash-herstel** zoals in v2.71, nu mét wegennet.
- **Doortellen, per parkeer-app en per pocket-modus:** 6 tikken, crash,
  herladen, Doortellen, 6 tikken, stoppen. Gecontroleerd wordt:
  - alle 12 tikken in de goede volgorde in één ZIP;
  - dezelfde sessie-id of starttijd;
  - het GPS-spoor loopt door;
  - geen JS-fouten.
- **Pocket:** een modusknop bij de herstelmelding vraagt bevestiging, en na
  Annuleren staat alles er nog.
- **Static:**
  - de opslag bestaat na tikken;
  - de balk met Continue verschijnt;
  - na doortellen staan er 12 tikken in de export;
  - de onderbreking staat in de CSV;
  - `Observed duration` is zonder de pauze;
  - na End en export wordt de opslag opgeruimd.

## 6. Static doorgelicht: wat verder opviel (niet gebouwd)

1. **Telrapport leest de eigen export van Static niet.** Static levert sinds
   v2.18 een ZIP, zodat het iOS-deelblad hem kan opslaan. Telrapport kent
   Static alleen als losse CSV (`loadFile` → `.csv`). Een ZIP gaat naar
   `loadZip`, en die meldt "Geen sessie.csv gevonden". Nu moet je eerst
   uitpakken. De oplossing in telrapport is klein: een ZIP met een
   `Traffic Count Export`-CSV herkennen.
2. **Engelstalig.** De andere veld-apps zijn Nederlands, voorpagina en pocket
   zijn tweetalig.
3. **Eigen exportformaat.** Geen `sessie_id`, een tijdlog zonder datum, niet de
   `_sessie`/`_telregels`-familie. Voor KNIME is Static een uitzondering.
   Rechttrekken is een schemawijziging.
4. **Restanten in de HTML.** Een blok "Built with AI by Claude - Anthropic"
   zonder omhullende `div` staat zichtbaar onderaan de pagina. Daarbij hoort
   een losse `</div>`; dat is de tagbalans-ruis die `valideer.py` al jaren als
   bekend wegfiltert.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter.html` | noodopslag, herstelbalk, doortellen, onderbrekingen in de export, scherm-aan, klok telt actieve tijd |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | gedeeld blok `hervatSessie`, knop Doortellen, bevestiging bij Start |
| `pocket_count.html` | `hervatTelling()`, `magNieuwStarten()`, knop Doortellen |
| `zip_format_reference.html` | Static: ZIP-omhulsel en onderbrekingsregels beschreven |
| `index.html` | versie v2.72 |
| `_archief/overpass_rig/hersteltest.py` | nep-Overpass, doortel-scenario's, Static |
| `_archief/overpass_rig/valideer.py` | groep `hervatSessie`, `RELEASE` |
| `OVERDRACHT_STAND_VAN_ZAKEN.md`, rig-`README.md` | bijgewerkt |

## 8. Validatie

```
valideer.py        ALLES OK — 7 verwachte bestanden gewijzigd, 11 groepen gedeelde blokken OK
hersteltest.py     133/133 (+ BEKEND: pocket bewaart snap-trace niet in de noodopslag)
laadtest.py        40/40
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
