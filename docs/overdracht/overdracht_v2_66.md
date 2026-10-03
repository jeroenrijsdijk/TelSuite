# Overdracht v2.66 — README, verzameltest, zijde-offset gekoppeld, autorit-analyse

Vier onderwerpen. Drie zijn gebouwd. Het vierde, de autorit-reconstructie, is
geanalyseerd maar **bewust niet gebouwd** (§4). Daarbij kwam een bug in de
reconstructor boven die al sinds v2.18 bestaat.

---

## 1. Samenvatting

1. `README.md` in de suite-root opnieuw geschreven, als plattegrond.
2. `functest_verzameling.js` heeft nu een eigen FileReader-shim en slaagt weer
   op Node 22 zonder extra stappen (26/26).
3. Zijde-offset gekoppeld. De 4 m stond niet in twee maar in **vijf**
   bestanden. `valideer.py` controleert nu dat de waarde overal gelijk is.
4. Autorit-reconstructie geanalyseerd. De highway-voorkeur van de profielen
   blijkt nooit bij de matcher aan te komen.

## 2. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | alleen commentaar bij `SIDE_OFFSET_M`, +44 bytes elk |
| `telreconstructie.html` | alleen commentaar bij `OFFSET_M`, +21 bytes |
| `telrapport.html` | alleen commentaar bij `OFFSET_M`, +74 bytes |
| `README.md` | herschreven (§3.1) |
| `_archief/overpass_rig/functest_verzameling.js` | FileReader-shim (§3.2) |
| `_archief/overpass_rig/valideer.py` | nieuwe sectie *gedeelde constanten (waarde)*; verwachte sets v2.66 |
| `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

Er is geen code gewijzigd, alleen commentaar. Ook de gedeelde blokken
(`RECON`, `MATCHER`, OVP, segmentatie) zijn ongewijzigd. De vingerafdruk van de
rekenkern in de gpx-tak klopt dus nog.

## 3. Wat er gebouwd is

### 3.1 README: plattegrond, geen tweede stand van zaken

De oude README hoorde bij v2.18. Hij heette nog "Telapp suite" en kende de
reconstructor nog als `parkeer_reconstructie.html`. Zijn ZIP-tabel,
KNIME-sleutels en kleurcodes liepen inmiddels achter op de code. Dat is
dezelfde drift als bij `HIGHWAY_RE`, maar dan in documentatie.

De nieuwe README bevat daarom alleen wat stabiel is:

- wat de suite is en de werkstroom;
- alle bestanden, ingedeeld naar rol;
- wat er van buiten wordt opgehaald (gecontroleerd tegen de code);
- de conventies;
- hoe je ontwikkelt.

Versienummers, features per tool en kolomdetails staan er niet in. Daarvoor
verwijst hij naar de stand van zaken, de handleiding en de ZIP-referentie.

Weggelaten uit de oude README:

- De kleurtabel. Telrapport gebruikt die kleuren alleen voor
  auto/fiets/capaciteit.
- De belofte van een "← Menu"-link op elke pagina. Zes van de veertien
  pagina's (index niet meegeteld) hebben die link niet, waaronder pocket,
  telrapport en de reconstructor.

### 3.2 De shim

Node heeft `File` en `Blob`, maar geen `FileReader`. JSZip leest een blob
alleen in als `FileReader` bestaat (`lib/utils.js`, `prepareContent`). Zonder
`FileReader` stuurt JSZip het `File`-object ongelezen door en weigert het
daarna met "Can't read the data".

De shim volgt het contract dat JSZip verwacht: `onload(e)` met
`e.target.result`, `onerror(e)` met `e.target.error`. Hij wordt alleen
geplaatst als `FileReader` ontbreekt. Het succespad en het foutpad zijn
allebei los getest.

### 3.3 Zijde-offset: vijf plekken, één controle

In de backlog stonden twee plekken. Het zijn er vijf:

| bestand | naam | rol |
|---|---|---|
| `parkeertelling.html` | `SIDE_OFFSET_M` | live plaatsing bij de tik |
| `fietsparkeren.html` | `SIDE_OFFSET_M` | idem |
| `capaciteitstelling.html` | `SIDE_OFFSET_M` | idem, per vak |
| `telreconstructie.html` | `OFFSET_M` | plaatsing na reconstructie |
| `telrapport.html` | `OFFSET_M` | correctietool: een versleepte tik landt 4 m uit de as |

Het commentaar in de reconstructor noemde alleen `parkeertelling.html`. In
`telrapport.html` stond helemaal geen verwijzing, terwijl daar de handmatige
correctie aan hangt.

**Waarom geen blok-md5 zoals bij `HIGHWAY_RE`.** De namen verschillen. Om een
byte-identieke regel te krijgen had ik in telrapport en de reconstructor zes
plekken moeten hernoemen, en dat is precies het soort wijziging dat je
niet wilt. Daarom controleert `valideer.py` de **waarde**:

- Per bestand zoekt een regex naar `var|let|const NAAM = …;`.
- Er moet precies één treffer per bestand zijn. Twee declaraties is een fout,
  want dan weet je niet welke telt.
- De waarde moet in alle vijf bestanden gelijk zijn.

Beide foutgevallen zijn nagebootst en worden gevangen: één bestand op 5 geeft
`DRIFT`, een dubbele declaratie geeft `FOUT … 2 declaraties`.

Elke declaratie zegt nu in zijn commentaar: *zelfde waarde in 5 bestanden,
bewaakt door valideer.py*. De controle is de machinekant van de koppeling; het
commentaar is de mensenkant, zodat wie één vier aanpast weet dat er nog vier
zijn.

**Niet bewaakt:** vier zichtbare teksten noemen de 4 m ook:

- de kop van `telreconstructie.html` (`4&nbsp;m`);
- de handleiding ("4 meter loodrecht");
- `zip_format_reference.html` ("~4&nbsp;m");
- drie commentaarregels in telrapport.

Die moeten bij een wijziging met de hand mee. Ze bewaken kost meer dan het
oplevert.

## 4. Autorit-reconstructie — analyse, niet gebouwd

### 4.1 Waarom niet gebouwd

Het ontwerp uit juli (vier stappen, zie `current-state`) dateert van vóór de
reconstructor. Sindsdien staat het grootste deel er al, maar dan voor lopende
sessies. Wat overblijft raakt de matcher, en daarvoor geldt de afspraak: geen
snap-parameters zonder replay op echte data. De autorit-ZIP van 13 juli zit
niet in deze sessie.

### 4.2 Het ontwerp van juli naast wat er nu staat

| stap uit juli | stand in `telreconstructie.html` | wat ontbreekt voor de auto |
|---|---|---|
| 1. herfetch alleen gaten | anders opgelost: verse fetch van de hele trail-bbox via de tegelcache; origineel blijft als `_netwerk_origineel.csv` | de bbox groeit kwadratisch met de ritlengte. Voor 12,5 km in de stad is dat nog goed, voor lange ritten is een corridor-fetch nodig (`routeStukken` uit de gpx-tak) |
| 2. matching op autoschaal | `MATCHER` staat er | highway-voorkeur doet niets (§4.3); geen tijdspoort; kandidaten zoeken is O(fixes × ways) |
| 3. richtingslaag | staat er, gevalideerd (HALF_S 12, HYST 1, GAP_S 25) | naar verwachting niets: bij rijsnelheid is de richting ondubbelzinnig |
| 4. tikken hertoekennen | staat er | — |

Daarbovenop ontbreekt een **rit-profiel**. Er is geen profiel dat een
autorit herkent. Herkennen kan op snelheid (mediane snelheid van de trail),
met een schakelaar om het zelf te kiezen. Het profiel legt twee dingen vast:
de voorkeur voor de rijbaan, en wat de tikken in een autorit betekenen.

### 4.3 De bug: de highway-voorkeur komt nooit aan

- De profielen `auto` en `fiets` geven `hwPref(...)` mee.
- `reconstrueer()` geeft die als vijfde argument door:
  `MATCHER.matchTrajectory(netMatch, adj, events, segCount, S.profiel.highwayCost)`.
- `matchTrajectory` heeft maar vier parameters (`.length === 4`) en gebruikt de
  voorkeur nergens.

De overdracht van v2.18 beschrijft de voorkeur als emissieterm (−2 voor
geprefereerd, +4 voor vermeden). Die term is nooit in de kern beland; de
kern kwam byte-identiek over uit pocket.

Aangetoond met de echte `MATCHER`:

- een rijbaan en een vrijliggend fietspad liggen 10 m uit elkaar;
- de auto rijdt op de rijbaan, maar de GPS ligt 6 m ernaast, richting het
  fietspad;
- zonder voorkeur: 20/20 fixes op het fietspad;
- met de auto-voorkeur: **ook 20/20 op het fietspad**.

Met de beschreven term zou de rijbaan winnen: emissie −1,28 tegen +4,32.

**Gevolgen:**

- Auto-parkeertellingen kunnen na reconstructie op een parallel fietspad
  liggen.
- Fietsparkeertellingen kunnen op de rijbaan belanden. Precies dat wilde
  v2.18 voorkomen.
- In Nederland, met veel vrijliggende fietspaden, is dit het grootste
  afzonderlijke risico voor de autorit.

**Reparatie:** drie regels in de emissie, waar de profielen het netwerk al op
leveren (`net[w].highway` wordt al gevuld). Maar het **verandert de uitkomst
van bestaande auto- en fietsreconstructies**. Dus eerst replay: dezelfde ZIP's
voor en na, en per tik bekijken wat er verschuift.

De gpx-tak draagt dezelfde kern, maar geeft geen voorkeur mee. Daar verandert
het gedrag dus niet, alleen de vingerafdruk.

### 4.4 Tijdspoort en verdichten — hoe ze samengaan

Het ontwerp van juli zegt: *GPS-gaten zijn erkende onderbrekingen, geen
interpolatie.* De les uit de gpx-tak zegt: *verdicht, anders breekt de ketting
op `hopClass`.* Dat lijkt elkaar tegen te spreken, maar het gaat samen met de
tijd als scheidslijn:

- **Binnen de tijdspoort** (bijv. Δt ≤ 25 s, gelijk aan de `GAP_S` van de
  richtingslaag): een grote sprong komt door snelheid. Tussenpunten met vlakke
  emissie houden de ketting heel, net als in de gpx-tak.
- **Buiten de tijdspoort**: knippen. De trail wordt opgedeeld in stukken en
  `matchTrajectory` draait per stuk. Geen verzonnen route door een tunnel of
  een achtergrondpauze.

Beide kunnen **vóór** de matcher, als voorbewerking van de fixes. Zo doet
`bereidFixes` het in de gpx-tak. De kern blijft dan onaangeraakt, op de
highway-voorkeur na.

### 4.5 Voorgestelde volgorde

| stap | wat | raakt de kern | nodig |
|---|---|---|---|
| A | meetopzet: de reconstructie headless draaien op een ZIP, met als uitvoer % gematcht, aantal ketting-herstarts, aandeel fixes op fiets-/voetpad, tijdgaten > 25 s, grootste stap | nee | de ZIP's |
| B | highway-voorkeur repareren, voor/na gemeten op auto- en fiets-ZIP's | ja, 3 regels | A |
| C | tijdspoort + verdichten als voorbewerking | nee | A, autorit-ZIP |
| D | rit-profiel + herkenning op snelheid | nee | C |
| E | corridor-fetch + ruimtelijke index — alleen als de meting erom vraagt | nee | A |

Na A vertelt elke stap met een meting wat hij opleverde. Dat is dezelfde
discipline als bij K/RATIO/S_MIN. Realistisch zijn dit drie tot vier sessies,
geen enkele release.

## 5. Validatie

```
valideer.py                       ALLES OK
  byte-identiteit                 precies de 5 verwachte HTML-bestanden gewijzigd
  gedeelde blokken                10 groepen OK (hashes ongewijzigd)
  gedeelde constanten             zijde-offset, 5 bestanden, waarde 4, OK
  negatieftest                    één bestand op 5 -> DRIFT; dubbele declaratie -> FOUT
functest_verzameling.js           26/26 op Node 22, zonder extra stappen
overige functests                 34+18+16+9+16+22+11+20+29+24+27 OK
test_zipref.py                    referentie sluit aan op de code
check_encoding.py                 alles geldige UTF-8
shim                              onload- en onerror-pad volgens JSZip-contract
highway-voorkeur                  bug aangetoond met de echte MATCHER (§4.3)
```
