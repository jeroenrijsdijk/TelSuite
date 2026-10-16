# Overdracht v3.9 — robuustheid

Jay, na mijn lijst met backlog en eigen ideeën: "ja, neem maar op in versie 3.9,
samen met de vier dingen onder 'wat zou ik als eerste doen' wordt dat een
robuustheids-release. Na de test van 3.9 doen we in 3.10 de logica updates die
bij punt 5 en punt 6 staan." Punt 5 is het pocket-id bij Start, punt 6 het
gezondheidsrapport per telling. Daarvoor had hij gemeld: "Als je in planning een
gebied tekent moeten de wegen uit OSM opgehaald worden. De app geeft geen
voortgang daarvan en geeft ook geen signaal als het faalt."

## 1. Wat er veranderd is

**Volle noodopslag wordt gemeld** (blok `noodkopie`, vijf veld-apps)
- Lukt het wegschrijven van de noodkopie niet, bijvoorbeeld omdat de opslag vol
  is, dan staat er bovenin een oranje melding (`#kopie-vol`): *Noodopslag vol:
  nieuwe tikken worden niet meer bewaard voor als de browser crasht. De telling
  zelf loopt door; stop en sla op zodra het kan.* Static toont hem in het Engels.
- De melding neemt geen tikken af (`pointer-events: none`) en verdwijnt vanzelf
  zodra wegschrijven weer lukt.
- De vorige kopie blijft staan. Tot v3.9 werd een mislukte `setItem` stil
  ingeslikt in de `try/catch` van de app, en vanaf dat moment was er geen
  noodkopie meer zonder dat iemand het wist.
- Het zit in `kopieSchrijf`, dus één plek voor alle vijf de apps.

**De browser vragen de opslag te bewaren.** Start en Doortellen roepen
`navigator.storage.persist()` aan (`kopieBlijvend`). Safari kan websitegegevens
wissen van een site die je een week niet bezocht. Of de browser het verzoek
honoreert, verschilt per browser. Firefox kan het één keer vragen.

**Pocket vraagt het schermslot terug.** De browser geeft het scherm-aan-slot
vrij als je de app even verlaat. Pocket vroeg het daarna niet terug, dus ging het
scherm midden in een telling uit. Nu:
- zolang er geteld wordt, vraagt pocket het terug zodra de pagina weer zichtbaar
  is;
- lukt dat niet (sommige browsers willen een gebaar), dan bij de eerstvolgende
  aanraking;
- na Terug of Stop niet meer.

De parkeer-apps en Static deden dit al.

**Voorpagina: *Nog niet opgeslagen*.**
- `index.html` leest de noodkopieën van alle vijf de apps (zelfde domein) en toont
  ze in een oranje blok boven de tools, nieuwste eerst, met app, aantal tikken en
  tijd. Bijvoorbeeld: *Pocket · parkeren — 23 tikken · vr 16-10 08:05*.
- Een rij linkt naar de app. Pocket-parkeren gaat naar `#parkeren`; daar staat
  de herstelmelding klaar.
- Tellingen op de lijst `telsuite_afgesloten` (v3.8), lege kopieën en kopieën
  die niet te lezen zijn, worden niet getoond.
- Bij Static staat *afgerond* als de telling gestopt maar niet opgeslagen is.
- Tweetalig, met de taalknop van de voorpagina. Zonder kopieën is het blok er
  niet.

**Telplanning: wegen ophalen.** Wat er mis was:
- de laadmelding verscheen nooit: `style.display = ''` viel terug op de
  CSS-regel `display: none`;
- de melding stond ook niet midden op de kaart (`280px + 50%` in plaats van
  `140px + 50%`);
- een hangend verzoek bleef eeuwig "ophalen", en de tweede server kwam nooit aan
  de beurt;
- een rate-limit of time-out die Overpass als HTTP 200 met een `remark` stuurt,
  gaf stil nul wegen of een deel ervan.

Nu:

| situatie | wat je ziet |
|---|---|
| ophalen | melding midden op de kaart: *Wegen ophalen…*, met verstreken seconden en ontvangen kB (en *server 2*, *n gebieden* waar dat speelt) |
| server antwoordt niet binnen 45 s | door naar server 2 |
| antwoord afgebroken (`remark`) | niet gebruikt, door naar server 2 |
| rate-limit (429/503/504 of `remark`) | door naar server 2 |
| verouderde data (> 7 dagen) | door naar server 2 |
| leeg gebied | *Geen wegen gevonden in dit gebied*; server 2 wordt niet gevraagd |
| lukt bij geen server | rode melding met de reden per server, een advies (*Teken een kleiner gebied* bij afgebroken of te laat, *Wacht een halve minuut* bij overbelast) en *Opnieuw* / *Sluiten* |

- De statusregel rechtsboven verwijst bij een fout naar de melding.
- Telplanning heeft daarvoor nu het gedeelde blok `OVP-blok` (`ovpKeur`,
  `ovpStatusUitHttp`), byte-identiek met de andere zes bestanden. `valideer.py`
  bewaakt het nu in zeven bestanden.
- De tijdslimiet staat in `OPHAAL_TIMEOUT_MS` (45 s per server; de query zelf
  mag 25 s rekenen).
- Een afgebroken antwoord wordt ook niet gebruikt als er wegen in zitten. Je
  kunt dan niet zien welke ontbreken, en een halve planning valt anders pas in
  het veld op.

**Privacyverklaring.**
- Wat er stond: dat de planningenmap met een wachtwoord was afgeschermd.
- Wat er nu staat (NL en EN): de map is op dit moment niet afgeschermd; wie het
  adres kent, kan de planningen opvragen. Vul als teller daarom een voornaam of
  initialen in.
- De handleiding zegt hetzelfde.

Zet Jay de afscherming in Plesk terug (zie de stand van zaken, §4 0a), dan kan
de oude zin terug.

**Handleiding.**
- In *Onderbreking, herstel & doortellen*: de alinea *Opslag vol* en een regel
  over de voorpagina.
- In *Contour tekenen*: wat je ziet tijdens het ophalen, en wanneer de app een
  antwoord weigert.

## 2. Wat niet

- **De opgehaalde wegen in de tegelcache zetten** (zodat het veldwerk met nul
  verzoeken begint) zit er niet in. Dat hoort bij *Gebied vooraf ophalen* op de
  backlog: een tegel mag alleen in de cache als hij helemaal gedekt is, en dat
  vraagt meer dan dit herstel.
- **Bij volle opslag zelf ruimte maken** (bijvoorbeeld het wegennet van de
  parkeer-apps weggooien) is bewust niet gedaan. Zonder `_netwerk.csv` mist
  telrapport na herstel de geometrie van de eerdere straten. Liever eerlijk
  melden dan stil gegevens kwijtraken.

## 3. Tests

`robuusttest.py` is nieuw en heeft 87 tests:
- **A. volle opslag**, in de vijf veld-apps (pocket in twee modi):
  - geen melding zolang er ruimte is;
  - na het volschrijven van de opslag een melding die geen tikken afneemt;
  - de vorige kopie blijft staan;
  - weer ruimte: de melding is weg en de kopie loopt bij.
- **B. persist** bij Start (alle zes routes) en bij Doortellen (parkeertelling,
  pocket, Static); niet bij alleen openen of herstellen.
- **C. pocket-schermslot**, met een nagebootste `navigator.wakeLock`:
  - terug na een app-wissel;
  - geweigerd bij terugkomen: terug bij de eerstvolgende aanraking;
  - met een actief slot vraagt een aanraking niets;
  - na Terug niets meer.
- **D. voorpagina**:
  - drie tellingen, nieuwste eerst, met link, aantal, weekdag en tijd;
  - een afgesloten, een kapotte en een lege kopie niet;
  - Static *afgerond*;
  - Engels;
  - een echte pocket-telling verschijnt, en is na opslaan weer weg.
- **E. telplanning**, met een nagebootste Overpass per server:
  - een hangende server: de melding staat midden op de kaart en de tijd loopt
    mee; na de tijdslimiet neemt server 2 het over;
  - een afgebroken antwoord bij beide: foutmelding, niets gebruikt, en
    *Opnieuw* lukt daarna;
  - een rate-limit bij server 1: server 2 neemt het over;
  - een leeg gebied: de melding, server 2 niet gevraagd;
  - verouderde data;
  - overbelast bij beide: het advies om te wachten.

Tegen v3.8 falen A, B en C op elk punt dat nieuw is. D en E kunnen daar niet
eens lopen, omdat het blok op de voorpagina en de nieuwe meldingen ontbreken. In
telplanning had de oude laadmelding in Chromium breedte en hoogte nul.

Daarnaast bekeken in Chromium:
- de voorpagina op telefoonformaat met twee niet opgeslagen tellingen;
- telplanning op 1280 px, met de laadmelding en met de foutmelding.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `traffic_counter.html` | blok noodkopie: `kopieSchrijf` vangt af, `kopieVol`, `kopieBlijvend` |
| `pocket_count.html` | idem, plus het schermslot (`wakeLockGewenst`, terugvragen bij zichtbaar en bij aanraken) |
| `index.html` | blok *Nog niet opgeslagen*; versie v3.9 |
| `telplanning.html` | OVP-blok; ophalen met voortgang, tijdslimiet, keuring en melding; CSS van `#loading` |
| `privacy.html` | de planningenmap is niet afgeschermd (NL en EN) |
| `traffic_counter_help.html` | *Opslag vol*, voorpagina, ophalen in telplanning, serverbestanden |
| `_archief/overpass_rig/robuusttest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py        ALLES OK — 9 verwachte bestanden gewijzigd; 16 groepen gedeelde blokken OK
                   (OVP-blok nu 7 bestanden, noodkopie 5); 14 publieke pagina's OK
robuusttest.py     87/87 (nieuw)
opruimtest.py      139/139
hersteltest.py     133/133, los twee keer gedraaid (zie hieronder)
laadtest.py        47/47
statictest.py      24/24
gpkgtest.py        80/80
functests          alle 15 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```

In de volledige ronde gaf `hersteltest` één keer 132/133. De fout zat in de
nagetekende `_kaart.png` van fietsparkeren, die een paar regels van de referentie
verschilde. Ik draaide toen tegelijk de nieuwe test tegen v3.8, dus de machine
was zwaar belast. Los gedraaid slaagde hij twee keer volledig. De kaartafbeelding
komt niet aan bod in v3.9. Het is de wisselvalligheid die al op de backlog staat
(vaste wachttijden); daar staat nu ook dit geval bij.

## 6. Volgende: v3.10

Na de veldtest van v3.9 (checklist in de stand van zaken, §4 punt 9):
- **Pocket-id bij Start.** Pocket maakt zijn sessie-id nu bij Stop, met de tijd
  van dat moment. Bij Start maken en in de noodkopie bewaren. Het formaat blijft
  gelijk, de betekenis verandert (starttijd in plaats van eindtijd): eerst KNIME
  nagaan.
- **Gezondheidsrapport per telling** in telrapport:
  - gaten in het GPS-spoor;
  - tikken zonder verse fix;
  - de nauwkeurigheid;
  - onderbrekingen;
  - kloppen de aantallen in alle bestanden.

  Alles uit wat al in de ZIP staat; geen schemawijziging.
