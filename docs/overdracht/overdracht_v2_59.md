# Overdracht v2.59 — drie stille fouten en een te volle zijkolom

Drie bestanden, drie losse bugs, alle drie uit de praktijk gemeld: `telreconstructie.html` (+2.942), `telrapport.html` (+4.094) en `zip_format_reference.html` (+420).

---

# Deel 1 — vastloper op een lege telling

## 1. Wat er aan de hand was

De ZIP `20260903_145005_fit_pkt_s.zip` bevat een sessie die is gestart en na 92
seconden gestopt zonder ook maar één tik. Er zit **geen `_gps.csv`** en **geen
`_netwerk.csv`** in, alleen drie CSV's waarvan er twee niets dan een kopregel
hebben. In `_snap_trace.csv` staat de reden: één `fetch_fail` met `err:504` —
Overpass gaf een gateway timeout en er kwam nooit een netwerk binnen.

**Slepen zelf liep niet vast.** De pagina las het bestand, meldde *"Geen netwerk
in ZIP — bbox NaN×-Infinity m"* en bood de knop **Netwerk ophalen en
reconstrueren** aan. Díe knop doodde de tab. Vanuit de gebruiker is dat één
handeling na het slepen, dus de melding "ik sleep hem erin en de site loopt vast"
klopt precies.

## 2. De oorzaak

Bij nul posities is `Math.min.apply(null, [])` gelijk aan `+Infinity` en
`Math.max.apply(null, [])` aan `-Infinity`. `trailBbox()` gaf daardoor een
omgekeerde rechthoek terug die er verderop uitzag als een gewone bbox.

In `coveringTiles` zette `Math.max(ty0, …)` vervolgens **beide** tegelgrenzen op
`Infinity`:

```js
var ty0 = Math.floor(b.la0 / TILE_DEG);            // Infinity
var ty1 = Math.max(ty0, Math.ceil(b.la1 / TILE_DEG) - 1);  // ook Infinity
for (var ty = ty0; ty <= ty1; ty++) …              // Infinity + 1 === Infinity
```

`ty` verandert nooit, de voorwaarde blijft waar, en elke ronde wordt er een
object gepusht. Headless gemeten: twee miljoen iteraties in 10 ms. In de browser
is dat binnen seconden gigabytes — een harde vastloper, geen trage pagina.

Die `Math.max` is trouwens geen fout op zichzelf; hij zorgt ervoor dat een bbox
smaller dan één tegel toch één tegel oplevert. Alleen bij een niet-eindige
invoer keert hij zich tegen zichzelf.

## 3. De reparatie — drie lagen

Het zijn drie verschillende fouten en ze verdienen alle drie hun eigen slot.

**A. Inleesgrens.** Een ZIP zonder bruikbare posities wordt nu geweigerd in
`leesZipInS`, met een melding die de oorzaak uitlegt in plaats van een code:

> Deze telling is leeg: 0 tikken en geen GPS-track. Er valt niets te
> reconstrueren. Dit gebeurt als een sessie wordt gestart en gestopt zonder te
> tellen, bijvoorbeeld wanneer het netwerk niet opgehaald kon worden.

Zulke meldingen zijn gemarkeerd als `gebruikersfout` en krijgen geen stack-regel
achter zich aan; de stap heet **Niets te reconstrueren** in plaats van **Fout**.
Daarbij is meteen een haakjesfout in die stack-regel rechtgezet: er stond
`(' [' + … || '').trim() + ']'`, waardoor de `||` op de hele samenvoeging sloeg
en de `]` buiten de `trim()` viel.

**B. Geen verzonnen bbox.** `trailBbox()` geeft nu `null` bij nul posities in
plaats van een omgekeerde rechthoek. `bereidVoor()` deelt niet meer door nul
(neutrale schaal op 52,1 / 5,1 als terugval), en `verwerk()` stopt netjes als er
geen bbox is in plaats van een fetch-knop aan te bieden die nergens op slaat.

**C. `coveringTiles` weigert onzin.** Een niet-eindige grens geeft een lege
lijst. En er is een plafond van 4.000 tegels (~40 × 40 km): daarboven een luide
fout in plaats van stilletjes een half land bij Overpass opvragen. Ook een
eindige maar absurde bbox kan zo geen geheugen meer opeten.
`cacheGefetchteRoute` wijst een lege tegellijst af met uitleg, zodat er nooit
een query met NaN-grenzen de deur uit gaat.

## 4. Wat dit zegt over de rest

Het onderliggende scenario — Overpass valt weg tijdens een telling — is precies
wat v2.49 aanpakte. Deze ZIP komt van 3 september, dus van vóór die release: de
trace toont een `err:504` die toen nog de retry-storm inging. Met v2.49 zou de
app netter zijn afgekoeld, maar de telling was dan alsnog zonder netwerk
geëindigd. De reconstructor moest daar hoe dan ook tegen kunnen.

Waard om te onthouden: `Math.min`/`Math.max` op een lege reeks is een stille
bron van `±Infinity`, en `Infinity + 1 === Infinity` maakt van elke
teller-gebaseerde lus een eeuwige. Als die combinatie elders in de suite
voorkomt, is het hetzelfde patroon.

## 5. Validatie

```
nieuwe regressietest functest_legezip.js     16/16 OK
JS-syntax (node --check)                     15/15 OK
HTML-tagbalans, vergeleken met v2.58         geen afwijking
byte-identiteit                              alleen telreconstructie.html
gedeelde blokken byte-identiek               6 groepen OK
test_zipref.py                               referentie sluit aan op de code
overige functionele tests                    34 + 18 + 16 + 9 + 26 OK
```

De regressietest bouwt de lege ZIP zelf op uit dezelfde kopregels, dus hij hangt
niet van het geüploade bestand af. Hij dekt vier vormen van kapotte bbox, het
tegelplafond, een normale route als controle, en de volledige route van slepen
tot melding.

```
npm install jszip papaparse
node _archief/overpass_rig/functest_legezip.js
```

---

# Deel 2 — telrapport laadde stilzwijgend de verkeerde helft

## 6. Wat er aan de hand was

Bij een lijst waarin zowel het origineel als de `_recon`-versie zit, laadde
telrapport **het origineel** en gooide het de reconstructie weg. Zonder melding.

Samenloop van twee dingen die elk op zichzelf redelijk zijn:

- **De `sessie_id` verandert niet bij reconstructie.** `telreconstructie` schrijft
  `S.sid` ongewijzigd weg; alleen de bestandsnaam krijgt `_recon`, en de leden
  binnenin houden hun originele `<sessie_id>_…csv`-namen. Origineel en
  reconstructie dragen dus dezelfde identiteit.
- **`loadZip` doet `if (sessions[sid]) return;`** — een tweede ZIP met dezelfde
  sid wordt stil overgeslagen.

En `ingestFiles` sorteerde op bestandsnaam. `_car` komt alfabetisch vóór
`_recon`, dus het origineel was er eerst en de reconstructie werd het slachtoffer
van de dubbelcheck. Precies omgekeerd aan wat je wilt.

## 7. De reparatie — twee lagen

**A. Voorfilter op bestandsnaam.** `kiesReconstructies()` groepeert op basis: van
het origineel valt het app-achtervoegsel af (`_car` / `_fts` / `_cap` / `_trn`;
pocket heeft er geen), van de reconstructie `_recon`. Wat overblijft is dezelfde
basis. Ligt er een reconstructie naast, dan gaat het origineel er niet in. Een
`... (1)`-staart van een tweede download telt niet mee, en hoofdletters maken
niet uit.

**B. Sorteervolgorde als vangnet.** Bij gelijke basis gaat `_recon` nu voorop. Is
een bestand hernoemd waardoor laag A het paar mist, dan valt de bestaande
sid-dubbelcheck alsnog de goede kant op: hij slaat het origineel over in plaats
van de reconstructie. Verder blijft de volgorde gewoon op naam, zodat de
sessiekleuren niet verschuiven.

**En het wordt gezegd.** "3 originelen overgeslagen (reconstructie aanwezig)" in
de dropzone, plus de namen in de console. Stilzwijgend weglaten is nu juist wat
deze release repareert.

**Uit te zetten.** Nieuw vinkje naast het bbox-filter, standaard aan. Wie
origineel en reconstructie naast elkaar wil zien zet het uit — al laadt
telrapport dan nog steeds maar één van de twee, want de sid-dubbelcheck blijft.
Met het vinkje uit is dat de reconstructie, door laag B.

## 8. De documentatiefout die dit blootlegde

In v2.54 documenteerde ik de gereconstrueerde `_sessie.csv` en
`_segmentsamenvatting.csv` met een `sessie_id` die op `_recon` eindigt. **Dat
klopt niet** — `bouwZipBlob()` schrijft `S.sid` ongewijzigd. Drie voorbeelden
gecorrigeerd, en er staat nu een noot bij die het expliciet maakt: de bestandsnaam
wordt `<sessie_id>_recon.zip`, de `sessie_id` zelf blijft gelijk, en een lezer die
daarop sleutelt ziet origineel en reconstructie als één sessie.

Dat is precies het feit waar deze bug op draaide, en het raakt ook KNIME: wie op
`sessie_id` joint gooit origineel en reconstructie op één hoop. Het onderscheid
zit in de kolom `reconstructie` in `_sessie.csv`.

## 9. Validatie van deel 2

```
nieuwe test functest_reconpaar.js   22/22 OK
  paren herkennen                   auto, fiets, capaciteit, transect, pocket
  randgevallen                      "(1)"-kopie, hoofdletters, los CSV, bijna-gelijke sid
  sorteervolgorde                   recon eerst bij gelijke basis, verder op naam
test_zipref.py                      referentie sluit aan op de code
alle overige tests                  34 + 18 + 16 + 9 + 26 + 16 OK
byte-identiteit                     precies 3 bestanden gewijzigd
```

**Wat de tests niet dekken:** jouw echte lijst. Sleep hem erin en kijk of het
aantal sessies klopt met wat je verwacht, en of de melding het juiste aantal
overgeslagen originelen noemt.

---

# Deel 3 — de weekprofiel-knop zakte uit beeld

## 10. Wat er aan de hand was

`showWegvakDetail()` bouwt het detailpaneel op met één tabelrij per zichtbare
sessie, en plakte de knop **Toon weekprofiel ›** daar achteraan. Het paneel is
`max-height: 340px; overflow-y: auto`. Met een handvol tellingen past dat; met
dertig staat de knop honderden pixels onder de vouw.

En dat is niet één van meerdere ingangen — voor een gemengd segment (pocket
naast auto of fiets) is dit de **enige** weg naar het weekprofiel. Een
pocket-only segment opent de popup meteen bij het aanklikken; daar merk je er
niets van. Juist bij veel geladen ZIP's, wanneer het weekverloop het interessantst
wordt, was de ingang onbereikbaar.

## 11. De reparatie

De knop staat nu bovenaan het paneel: `html = knop + html` in plaats van
`html += knop`. Hij zit in een houder `.hm-btn-top` met `position: sticky`, zodat
hij ook blijft staan terwijl je door de sessietabel scrolt — bij dertig rijen wil
je niet eerst terug naar boven.

Twee details die nodig waren: de houder heeft een ondoorzichtige achtergrond
(`var(--bg)`), want de knop zelf is half doorschijnend en de tabel zou er anders
doorheen schuiven, en `top: -12px` compenseert de padding van `#detail-panel`
zodat hij echt tegen de bovenrand plakt.

## 12. Validatie van deel 3

```
nieuwe test functest_weekknop.js   11/11 OK
  volgorde                         knop wordt vooraan geplakt, niet achteraan
  houder                           sticky, ondoorzichtig, z-index, marge genuld
  aanname                          paneel scrollt nog steeds (anders is sticky zinloos)
byte-identiteit                    alleen telrapport.html, +759 bytes
alle overige tests                 22 + 16 + 9 + 34 + 18 + 26 + 16 OK
```

De test leest de broncode, niet een gerenderde pagina — hij controleert dat de
knop vóór de tabel wordt geplakt en dat de CSS-houder de vier eigenschappen heeft
die hem bruikbaar maken. Wat hij niet kan zien: of het er in de browser ook goed
uitziet bij een lange tabel. Even een segment met veel sessies aanklikken.

---

# Deel 4 — de zijkolom liet niets over voor de sessielijst

## 13. Waarom inklappen niet meer hielp

`#sidebar` is een flexkolom waarin **alles `flex-shrink: 0`** is behalve
`#sessions-list`. Die had `flex: 1` met `min-height: 60px` — nog geen
anderhalve sessierij. De lijst kreeg dus letterlijk alleen wat overbleef.

Inklappen van de vier `ctrl-group`s haalt alleen hun body weg. Wat blijft staan:
de header, de dropzone (~94 px), twee filtervinkjes, de statsbar, vier
summary-balken van elk ~29 px, de sectiekop en de voetregel. Bij elkaar zo'n
440 px die je met geen enkele muisklik kwijtraakt.

En dan de echte boosdoener: `#detail-panel` had `max-height: 340px` **met
`flex-shrink: 0`**. Zodra je een wegvak aanklikte nam dat paneel 340 px op en gaf
het niets terug. Op een scherm van 800 px betekende dat: 441 vast + 340 detail =
781, en de sessielijst zakte naar zijn bodem van 60 px. Dat is wat je zag.

## 14. Drie ingrepen

**De sessielijst wint nu de onderhandeling.** `min-height` van 60 px naar
`min(170px, 24vh)`. Een sessierij is 42 à 55 px, dus dat garandeert er drie tot
vier. Het plafond is proportioneel, zodat de lijst op een korte kolom niet zelf
de boosdoener wordt.

**Het detailpaneel mag meekrimpen.** Van `flex-shrink: 0` naar `flex: 0 1 auto`,
met `max-height: min(340px, 40vh)` en een bodem van 84 px. Het scrollt toch al,
dus krimpen verbergt niets — je scrollt gewoon iets meer. Nu geeft het ruimte
terug in plaats van te eisen.

**De dropzone wordt compact zodra er tellingen staan.** Op een leeg scherm is een
grote uitnodiging precies goed; daarna is het een knop die je zelden nog gebruikt
en die 94 px permanente hoogte kost. Compact scheelt bijna 60 px. Puur CSS —
`.dz-text` blijft dezelfde node, dus de voortgangsmeldingen ("laden… 12/40") en
de bbox-terugmelding werken ongewijzigd. Het icoon en de regel "of kies een map…"
verdwijnen, maar die laatste komt terug bij hover, zodat de mapkeuze bereikbaar
blijft.

Daarnaast krappere marges rond de filtervinkjes en de statsbar zodra de kolom
compact staat.

## 15. Wat dat oplevert

Ruwe begroting, sessierij gerekend op 46 px:

| schermhoogte | lijst zonder detailpaneel | lijst mét detailpaneel |
|---|---|---|
| 720 px | 364 px (~7 rijen) | 170 px (~3 rijen) + detail 194 px |
| 800 px | 444 px (~9 rijen) | 170 px (~3 rijen) + detail 274 px |
| 900 px | 544 px (~11 rijen) | 204 px (~4 rijen) + detail 340 px |
| 1080 px | 724 px (~15 rijen) | 384 px (~8 rijen) + detail 340 px |

Vóór deze release was de middelste kolom op elk van die schermen 60 px.

## 16. Wat ik niet heb aangeraakt

De vier `ctrl-group`-summaries kosten samen ~116 px die altijd blijft staan. Die
weghalen betekent functionaliteit verstoppen, en dat is jouw keuze, niet de
mijne. Mocht het nodig blijven: de twee filtervinkjes horen eigenlijk bij het
laden en zouden in een eigen groep kunnen, wat nog eens ~38 px scheelt.

`#sidebar` houdt `overflow: hidden`. Op een extreem korte kolom kan de voetregel
daardoor wegvallen. Met de nieuwe verdeling zit dat pas ver onder 600 px, maar
als je het ooit tegenkomt is `overflow-y: auto` de uitweg — met als prijs dat de
knoppen mee wegscrollen.

## 17. Validatie van deel 4

```
nieuwe test functest_zijkolom.js   20/20 OK
  sessielijst                      flex:1, bodem opgetrokken en geplafonneerd, scrollt
  detailpaneel                     krimpbaar, 40%-plafond, leesbare bodem
  compacte dropzone                icoon en subregel weg, hover brengt de mapkeuze terug
  schakelaar                       hangt aan hasAny, naast de statsbar
  regressie                        .dz-text blijft zichtbaar (voortgangsmeldingen)
byte-identiteit                    alleen telrapport.html
alle overige tests                 11 + 22 + 16 + 9 + 34 + 18 + 26 + 16 OK
```

De test leest de CSS en de JS, niet een gerenderde pagina. Wat hij niet kan zien:
of het in jouw browser ook echt prettig oogt. Laad je lijst, klap alles in, klik
een wegvak aan en kijk of je genoeg sessies ziet.
