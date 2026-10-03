# Overdracht v2.75 — privacyverklaring en afgeschermde planningen

Jay vroeg of er een privacyverklaring op de site moet. Dat doen we. Bovendien
bleken planningen met tellernamen openbaar op te vragen en te verwijderen. Jay
koos ervoor die map af te schermen.

**Twee dingen moet Jay doen voordat dit online gaat** (§5): het wachtwoord van
de planningmap inrichten, en de contactgegevens in de verklaring invullen.

---

## 1. Samenvatting

1. **`privacy.html`** (NL, met een Engelse samenvatting). Te bereiken vanaf de
   voorpagina (naast Help) en vanaf `over.html`.
2. **De voorpagina belooft niet meer te veel.** "Je data blijft op je toestel"
   is nu "je tellingen blijven op je toestel". Daarbij staat dat de diensten
   voor kaart, wegennet en straatnaam wel zien waar je telt, met een link naar
   de privacypagina.
3. **De map `planningen/` is afgeschermd met een wachtwoord**
   (`planningen/.htaccess`, Basic Auth). Bij een fout gaat de map dicht, niet
   open.
4. **Telplanning geeft een leesbare melding** als de server weigert (401/403)
   of als de afscherming nog niet is ingericht (500).
5. **`valideer.py` controleert** dat elk extern domein in de code ook in de
   privacyverklaring staat. Zolang de contactgegevens nog niet zijn ingevuld,
   meldt hij dat.

## 2. Wat de verklaring zegt (uit de code, niet uit aannames)

**Op je toestel**

- de noodopslag van een lopende telling, die na een afgeronde export wordt
  opgeruimd;
- de taalkeuze;
- de naam van de teller, als je die invult;
- je eigen ZIP's.

Alles staat in `localStorage`. Er zijn geen cookies, geen analytics, geen
advertenties en geen account.

**Naar andere diensten.** Elk verzoek gaat met je IP-adres mee. In een tabel:
dienst, domein, wat er meegaat en waarvoor.

| dienst | wat gaat mee | waarvoor |
|---|---|---|
| Nominatim | je positie | straatnaam |
| Overpass (twee servers) | een gebied rond je positie | wegennet |
| tegels van OpenStreetMap, CARTO en PDOK | het bekeken gebied | kaart |
| Open-Meteo | plek en tijd van een telling | weer, alleen in telrapport |
| cdnjs en unpkg | — | code |
| Google Fonts | — | lettertypen |

**Op de server**

- planningen, met tellernaam, in een afgeschermde map;
- de serverlogs van de host.

**Rechten.** Inzage, correctie en verwijdering; klachten bij de Autoriteit
Persoonsgegevens.

Er is geen cookiebanner nodig: `localStorage` wordt alleen functioneel
gebruikt. Geen juridisch advies; dit is een inventaris.

## 3. Planningmap afgeschermd

**Het probleem.** Een planning bevat naam, datum, tijdstip, teller en wegen.
`planning_list.php` gaf ze aan iedereen, en `planning_delete.php` liet iedereen
verwijderen. De scripts zelf waren wel veilig tegen pad-trucs.

**De oplossing.** `planningen/.htaccess` met `AuthType Basic` en
`Require valid-user` voor de hele map, dus ook de losse `planning_*.json`.
Verder `Options -Indexes`, en `.ht*`-bestanden worden nooit uitgeleverd.

**Fouten gaan dicht, niet open.**

- Klopt het pad naar het wachtwoordbestand niet, dan geeft de server een
  500-fout. De map is dan dicht, en telplanning meldt: "is de afscherming van
  /planningen al ingericht?"
- Het enige open geval is een server die helemaal geen `.htaccess` leest, zoals
  nginx. Daarom staat er een controlestap in het bestand en in §5.

**Hoe inloggen werkt.** Telplanning vraagt om het wachtwoord via de gewone
login van de browser. Dat geldt ook voor een veld-app die via telplanning een
opdracht opent: op hetzelfde toestel geldt de login dan al. Een veld-app die
een planning niet kan laden, meldt dat niet. Dat staat op de backlog.

## 4. Controle op domeinen in `valideer.py`

`valideer.py` verzamelt alle `https://`-domeinen uit alle HTML-bestanden en
vergelijkt die met de `<span class="domein">`-vermeldingen in `privacy.html`.
Een subdomein telt als vermeld als het hoofddomein erin staat. `{s}.` in
tegel-URL's wordt eruit gehaald.

Een paar domeinen zijn uitgezonderd, omdat de browser er geen verzoek naar doet:
- `telonline.org` (eigen site);
- `schema.org` (alleen als naam in de metadata);
- de links naar `www.openstreetmap.org` en `open-meteo.com`.

Getest met een verzonnen nieuw domein in telrapport: dat geeft `FOUT … staat
niet in privacy.html`. Zo blijft de verklaring kloppen als er later een dienst
bijkomt.

## 5. Voor Jay, vóór het online zetten

1. **Wachtwoord van de planningmap.** Maak een wachtwoordbestand buiten de
   webroot, bijvoorbeeld met `htpasswd -c …` of "Mapbeveiliging" in het
   hostingpaneel. Vul het volledige pad in bij `AuthUserFile` in
   `planningen/.htaccess`. Controleer daarna in een privévenster dat
   `https://telonline.org/planningen/planning_list.php` om een wachtwoord
   vraagt.
2. **Contact in `privacy.html`.** Vervang het gele veld door de naam en het
   e-mailadres van de beheerder. `valideer.py` meldt het tot dan.

Beide staan ook in de stand van zaken, §4 punt 0a en 0b.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `privacy.html` | nieuw |
| `planningen/.htaccess` | nieuw |
| `index.html` | introzin NL/EN eerlijk, link naar privacy (ook in de voet), versie v2.75 |
| `over.html` | link naar privacy |
| `telplanning.html` | `planningServerMelding()` bij opslaan, lijst en verwijderen |
| `traffic_counter_help.html` | `privacy.html` en de afscherming in de bestandenlijst |
| `_archief/overpass_rig/valideer.py` | controle op domeinen tegen de privacyverklaring, melding bij nog in te vullen velden, `RELEASE` |
| `_archief/overpass_rig/laadtest.py` | +6 tests: telplanning bij 401 en 500, privacy-link, introzin NL/EN |
| `README.md`, rig-`README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py        ALLES OK — 4 HTML gewijzigd, privacy.html nieuw
                   12 externe domeinen in de code, alle vermeld
                   LET OP: "contact" in privacy.html nog invullen
laadtest.py        46/46
hersteltest.py     133/133 in 3 van 4 runs; één run gaf 1 FOUT (zie §8)
statictest.py      24/24
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```

## 8. Open punt: een wisselvallige test

`hersteltest.py` gaf in de eerste run 132 ok en 1 FOUT. Drie herhalingen
daarna waren alle 133/133. Welke test het was, is niet vastgelegd: de uitvoer
van die run is niet bewaard.

Het gaat niet om een fout in deze release. De apps die `hersteltest.py` test
(Static, de drie parkeer-apps en pocket) zijn in v2.75 byte-identiek aan
v2.74. Waarschijnlijk is het een timingkwestie in de browsertest: de test
wacht 250 ms per GPS-stap en 1,2 s op een ZIP. Staat op de backlog: de
wachttijden vervangen door wachten tot een voorwaarde klopt, en de uitvoer
van elke run bewaren.
