# Overdracht v3.10 — logica: pocket-id bij Start, kwaliteitsrapport

Jay, na de lijst met ideeën: "Na de test van 3.9 doen we in 3.10 de logica
updates die bij punt 5 en punt 6 staan." Na de veldtest: "Tests zijn geslaagd."

Over KNIME: "Ik maak in knime een lijst van alle _sessie bestanden, ik gebruik er
geen data uit. Met die lijst ga ik andere bestanden uit de zip halen." Op de vragen
over de controles en de GeoPackage kwam geen bezwaar; ik heb het voorstel
aangehouden (zes controles, nog niet in de GeoPackage), met één wijziging die
hieronder staat.

## 1. Pocket-id vast vanaf Start

**Wat er mis was.**
- Pocket maakte zijn `sessie_id` bij Stop, met de tijd van dat moment.
- Werd dezelfde telling twee keer ingepakt, bijvoorbeeld na een geannuleerd
  deelvenster en herstel, dan kreeg hij een ander id: twee "verschillende"
  sessies voor dezelfde telling.
- De tijd in het id was de eindtijd, terwijl de andere apps de starttijd gebruiken.

**Nu.**
- Bij Start maakt pocket de stam van het id: `pocketStam = genSid(startTime)`,
  `<jjjjmmdd>_<uummss>_<xyz>`.
- Bij het inpakken komt de moduscode erachter (`pocketSid()`). Dat gebeurt pas
  daar, omdat de modus bij Start niet in alle routes al vastligt.
- Het id gaat mee in de noodkopie (`sessieId`) en Doortellen houdt het vast.
- Het blok `noodkopie` gebruikt het nu ook als telling-id (`kopieTelling()`).
- Een kopie van vóór v3.10 heeft geen id. Die krijgt het uit de starttijd, met
  letters die óók uit de starttijd volgen (`stamUitStart`), zodat twee vensters
  op hetzelfde id uitkomen.
- Bij het herstellen kijkt pocket zowel naar dat id als naar de starttijd. Een
  kopie die onder v3.8/v3.9 is afgesloten, komt dus ook niet terug.

**Gevolgen.**
- Formaat en bestandsnamen blijven gelijk.
- Binnen de suite leest niets de tijd uit het id: telrapport gebruikt `datum` en
  `start_tijd`, de reconstructor gebruikt het id alleen als naam.
- KNIME gebruikt `_sessie.csv` alleen als lijst, dus daar verandert niets.
- `zip_format_reference.html` vermeldt het.

## 2. Kwaliteitsrapport per telling

Telrapport rekent bij het inladen per telling een rapport uit, uit de bestanden
die al in de ZIP zitten (`kwaliteitRapport`, grenzen in `KW`). In de ZIP komt
niets bij.

| controle | let op als | geldt voor |
|---|---|---|
| Aantallen | `n_waarnemingen` ≠ regels in `_telregels`; parkeer-apps ook ≠ som in `_straten` (fiets: `totaal`) | alle |
| Tijd | een tik meer dan 60 s vóór de start of na het eind, of zonder tijd | alle |
| GPS-spoor | tikken in een gat; een gat is > 60 s zonder punt én > 50 m sprong. Een gat zonder tikken is *info* | parkeer-apps, pocket |
| Onderbrekingen | — (alleen *info*: aantal en duur uit `_onderbrekingen.csv`) | Static |
| Positie | een tik zonder GPS-positie | parkeer-apps, pocket |
| Nauwkeurigheid | mediaan > 15 m, of meer dan 20% van de punten boven 20 m; Static: de fix boven 20 m, of geen fix | alle |
| Op de route | een tik meer dan 50 m van het spoor op zijn tijdstip | parkeer-apps, pocket |

**Eén wijziging ten opzichte van het voorstel.**
- De apps loggen een GPS-punt pas na 5 m verplaatsing. Wie stilstaat, maakt dus
  geen punten, terwijl de GPS gewoon werkt.
- Daarom telt een gat alleen als de positie erover verspringt.
- "Tikken zonder verse fix" is uit de ZIP niet af te leiden. Daarvoor in de
  plaats komen *Positie* (tikken zonder GPS-positie) en de tikken die in een gat
  vielen; hun positie kan verouderd zijn.

**Welke positie telt.** De routecontrole gebruikt de rauwe GPS-kolommen:
`lat_gps`/`lon_gps` bij de parkeer-apps, `lat`/`lon` bij pocket. De
correctietool in telrapport en de reconstructor verschuiven alleen de marker,
dus een correctie geeft hier geen aandachtspunt. Een achteraf verschoven
GPS-positie wel.

**Hoe ligt een tik op de route?** Het spoorpunt vóór en ná de tik, en het punt
daartussen op het tijdstip van de tik. De kleinste afstand telt. Tikken in een
gat doen hier niet mee.

**In beeld.**
- In de sessierij, onder *geclusterd*, staat *✓ kwaliteit* of *⚠ n
  aandachtspunten*.
- Een klik daarop opent het paneel: per controle het oordeel, wat er gevonden is
  en één zin uitleg. De telling blijft daarbij aan.
- Escape of een klik buiten het paneel sluit het. *Alles wissen* ruimt de
  rapporten op.
- Een ⚠ is een aandachtspunt, geen oordeel. ⓘ is ter informatie.
- Een ZIP die achteraf consequent is bewerkt, valt in het rapport niet op; dat
  staat ook in het paneel.

**Documentatie.**
- `verantwoording.html` (stand 3.10): bij *Het bestand is achteraf te bewerken*
  staat dat telrapport een deel van de vergelijking zelf doet, en de lijst *Wat een
  beoordelaar kan nagaan* begint nu met het kwaliteitsrapport.
- De handleiding heeft een alinea *Kwaliteit per telling* bij de sessielijst.

## 3. Wat niet

- **Niet in de GeoPackage.** Mijn voorstel, waar Jay geen bezwaar tegen maakte: eerst kijken hoe het rapport bevalt.
  Een kolom `kwaliteit` in de laag `sessies` kan later.
- **Oude Static-formaten** (alleen het overzicht, vóór v2.73) krijgen geen
  rapport. Er is daar geen `_sessie.csv` en geen `_telregels.csv`.
- **Een ZIP die telrapport weigert** (bijvoorbeeld een parkeer-ZIP zonder
  `_netwerk.csv`, of Static zonder GPS-fix) krijgt ook geen rij. Dat was al zo.

## 4. Tests

`functest_kwaliteit.js` is nieuw (33 tests). Hij knipt de rekenfunctie uit
telrapport en voert hem met nagebootste ZIP-inhoud:
- het lezen van tijden in alle vormen, ook met zone en met een datum als
  jjjjmmdd;
- een nette parkeertelling: zes keer ok;
- aantallen: `_sessie`, `_straten`, en fiets met de kolom `totaal`;
- tijd: buiten de sessie, binnen de marge, zonder tijd, en pocket over
  middernacht;
- het GPS-spoor:
  - 5 minuten stilstaan is geen gat;
  - een gat van 4 minuten met een sprong is *info*;
  - korter dan 60 s is geen gat;
  - tikken in een gat zijn een aandachtspunt en doen niet mee in de route;
- positie, nauwkeurigheid (mediaan en aandeel);
- de route: een tik 200 m verschoven geeft een aandachtspunt, een verschoven
  marker niet;
- Static: onderbrekingen, de fix (±8, ±35, geen), en n.v.t. waar geen spoor is;
- alleen een `_sessie.csv`: geen fout.

`logicatest.py` is nieuw (25 tests), in Chromium.

*A. pocket-id*
- Het id staat in de noodkopie, met de starttijd en de moduscode.
- De ZIP en `_sessie.csv` dragen het; de `start_tijd` is gelijk aan de tijd in
  het id.
- iPhone, deelvenster geannuleerd, herstel in een nieuw venster, Download:
  dezelfde ZIP-naam.
- Doortellen in een ander venster houdt het id vast.
- Een kopie van vóór v3.10 krijgt het id uit de starttijd, in twee vensters
  hetzelfde.

*B. telrapport*
- Echte ZIP's van pocket (na Doortellen) en Static geven *✓ kwaliteit*.
- Een parkeertelling:
  - net: *✓*;
  - met een verschoven tik: *⚠ 1 aandachtspunt*;
  - met een fout aantal: *⚠ 1 aandachtspunt*.
- Een klik opent het paneel met *Op de route* als aandachtspunt, en zet de
  telling niet uit.
- Escape sluit het paneel; *alles wissen* ruimt de rapporten op.

Tegen v3.9 vinden beide de nieuwe functies niet. De logicatest faalt al bij A1:
geen id in de kopie, en als telling-id de starttijd.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `pocket_count.html` | `pocketStam`, `pocketSid`, `stamUitStart`; id bij Start, in de kopie, bij Doortellen en herstel; `kopieTelling` |
| `telrapport.html` | `kwaliteitRapport` en hulpfuncties, `kwaliteit`, regel in de sessierij, paneel, CSS |
| `zip_format_reference.html` | pocket `sessie_id` vast vanaf Start |
| `verantwoording.html` | het kwaliteitsrapport; stand 3.10 |
| `traffic_counter_help.html` | *Kwaliteit per telling* |
| `index.html` | versie v3.10 |
| `_archief/overpass_rig/functest_kwaliteit.js`, `logicatest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
VALIDATIE
```
