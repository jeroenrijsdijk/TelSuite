# Overdracht v3.37 — de teller op de voorpagina

Jay: "De echte wens is dat er op de voorpagina van telonline.org "Al 253
tellingen gedaan"." En daarna: "Dan dus een kleine eigen teller op de server.
We staan op 409 tellingen op dit moment."

## 0. Het gesprek vooraf

1. **De vraag.** Jay: "Kun je ook ergens loggen dat er een echte gebruiker is
   geweest, dat er een zip gemaakt en gedownload is? Ik wil geen mensen volgen,
   maar wil zo graag weten of het gebruikt wordt. Is er een andere manier
   wellicht?"
2. **De echte wens** bleek een getal op de voorpagina. Na het bespreken van de
   mogelijkheden koos Jay een kleine eigen teller op de server, die begint op
   409.
3. **Wat ik zelf gekozen heb** (aan Jay gemeld vóór het bouwen; hij heeft er
   niets anders over gezegd):
   - elke telling uit de vijf veld-apps telt één keer per ZIP-naam, ook die van
     Jay zelf;
   - alleen een vingerafdruk (SHA-256) van de ZIP-naam gaat naar de server;
   - de server bewaart alleen die vingerafdrukken, buiten de webmap;
   - Global Privacy Control telt als "niet meetellen", en de privacyverklaring
     heeft een knop om het per toestel uit te zetten;
   - zonder verbinding wacht de vingerafdruk en gaat hij later mee;
   - een rem van 60 nieuwe per uur;
   - op de voorpagina "Al 409 tellingen gedaan"; is de teller niet te lezen,
     dan staat er niets.

Aan de ZIP's, het schema en de KNIME-kant verandert niets.

## 1. Hoe het werkt

**In de veld-apps: het gedeelde blok `teller`.** Het staat byte-identiek in
parkeertelling, fietsparkeren, capaciteitstelling, pocket en Static, direct na
het blok `vingerafdruk` (md5-groep `teller` in `valideer.py`).

- **`telTelling(naam)`:**
  - rekent de SHA-256 van `telonline.org teller <ZIP-naam zonder .zip>`;
  - stuurt die als `h=<64 hex>` met een POST naar `/teller/`
    (`keepalive`, zonder cookies).
- **Wanneer:**
  - in de drie parkeer-apps en Static: in `bewaarZip`, op de regel na de
    vingerafdruk;
  - in pocket: in `showPreview`, als de ZIP er is.
- **Niet versturen** (`tellerMag()`):
  - buiten http(s) (dus niet bij een bestand dat lokaal geopend is);
  - zonder WebCrypto of fetch;
  - met Global Privacy Control aan;
  - als `localStorage` `telsuite_niet_tellen` gezet is.
- **De wachtrij** (`telsuite_teller_wacht` in `localStorage`, hooguit 50):
  - bij geen verbinding of een 429, 502, 503 of 504 wacht de vingerafdruk;
  - bij elk ander antwoord (ook 400, 404, 405) gaat hij uit de rij, zodat een
    server zonder teller de rij niet laat groeien;
  - vier seconden na het laden van een app gaan er hooguit vijf mee
    (`tellerInhalen`).

**Op de server: `teller/index.php`** (PHP 8, geen database).
- `GET /teller/` geeft `{"tellingen": N}`, met `Cache-Control: public,
  max-age=60`.
- `POST /teller/` met `h=<64 hex>`:
  - een nieuwe vingerafdruk telt mee: `{"tellingen": N, "nieuw": true}`;
  - een bekende vingerafdruk telt niet nog eens: `"nieuw": false`;
  - hoofdletters tellen als dezelfde;
  - geen geldige vingerafdruk: 400;
  - meer dan `TELLER_MAX_PER_UUR` (standaard 60) nieuwe in het laatste uur:
    429 met `Retry-After: 3600`. Een bekende vingerafdruk gaat niet tegen de
    rem in.
- Andere methoden: 405 met `Allow: GET, POST`.
- **De opslag:**
  - `gezien.txt` heeft één regel van 64 tekens per telling, dus
    N = 409 + grootte / 65;
  - `recent.txt` bevat de tijden van de laatste nieuwe, voor de rem;
  - geen IP-adressen;
  - lezen en schrijven onder `flock`, zodat twee tegelijk niet dubbel of mis
    tellen.
- **Waar de opslag staat:**
  - `TELLER_MAP` als die gezet is, anders twee mappen boven het script.
  - Op telonline.org (Plesk, `httpdocs`) is dat
    `/var/www/vhosts/telonline.org/teller-data`. Die map maakt het script zelf
    aan bij het eerste verzoek. Komen de eerste verzoeken tegelijk, dan maakt
    één de map en gaan de andere gewoon door; zonder die tweede blik gaven ze
    een 503. De test vond dat in de eerste ronde.
  - Ligt de opslag in de webmap, dan weigert het script met 503, in plaats van
    de lijst op straat te leggen.
  - Een nieuwe release raakt de opslag niet: die staat niet in de repo.

**De voorpagina** (`index.html`):
- leest `/teller/` en toont onder de titel "Al 409 tellingen gedaan", in het
  Engels "409 counts so far";
- het getal staat in Nederlandse notatie (1.234);
- zonder teller (geen PHP, 404, geen verbinding) blijft de regel weg.

**De privacyverklaring** (`privacy.html`):
- het punt *Teller* (`#teller`) en het Engelse *Counter*;
- daarin staat wat er gaat en wat er bewaard wordt, en wat iemand met de lijst
  zou kunnen: met rekenwerk dag en tijdstip van het begin van een telling
  achterhalen, maar niet de plek;
- de knop *Op dit toestel niet meetellen* / *weer meetellen*, met de stand
  erbij, ook bij Global Privacy Control;
- *Kort* noemt de teller;
- datum 25 oktober 2026.

**De verantwoording** (`verantwoording.html`, punt *Na afloop*): één zin dat de
app bij het opslaan een vingerafdruk van de bestandsnaam stuurt, en niets van
de inhoud. Dat punt zei "Tijdens het tellen … gaat niets naar een server van
telonline.org"; dat klopt nog steeds, maar een jurist moet ook weten wat er bij
het opslaan gebeurt.

## 2. Wat telt en wat niet

**Telt mee:**
- elke ZIP die een veld-app opslaat, één keer per naam;
- twee keer opslaan, of opslaan na doortellen (dezelfde `sessie_id`), telt één
  keer;
- ook tellingen die Jay zelf, of iemand anders, op telonline.org maakt om iets
  te proberen.

**Telt niet mee:**
- een reconstructie (`_recon.zip`): die maakt telreconstructie, niet een
  veld-app;
- telrapport, telplanning, Archief, Passanten;
- tellingen van vóór v3.37 (die zitten in de 409);
- een app die lokaal of op een andere server draait (zonder `/teller/` gaat de
  vingerafdruk na een 404 uit de rij);
- met Global Privacy Control, of met *niet meetellen*.

**Bewust niet:**
- geen unieke bezoekers, geen sessies, geen tijden per telling;
- de rem maakt opdrijven lastig, maar niet onmogelijk. Wie het getal wil
  opdrijven, kan 60 per uur verzinnen. Voor een getal op de voorpagina vond ik
  dat goed genoeg; Jay kan het in `gezien.txt` zien en de rem lager zetten.

## 3. Na de merge (voor Jay)

1. Open https://telonline.org/teller/. Daar hoort `{"tellingen":409}` te
   staan.
2. Wat je anders kunt zien:
   - **PHP-code, een 403 of een 404:** PHP staat uit voor het domein. Zet het
     aan in Plesk (*PHP-instellingen*). Tot die tijd laat de voorpagina de regel
     weg, en tellingen uit die tijd gaan verloren: alleen "later" (429 en 5xx)
     en geen verbinding laten een vingerafdruk wachten.
   - **`"de opslag van de teller is er niet"`:** het script kon
     `/var/www/vhosts/telonline.org/teller-data` niet maken. Maak de map in
     Plesk (*Bestandsbeheer*, naast `httpdocs`).
   - **`"ligt in de webmap"`:** de site staat niet in `httpdocs` maar dieper.
     Zet dan `TELLER_MAP` naar een map buiten de webmap.
3. **Daarna:** de voorpagina toont "Al 409 tellingen gedaan". Bij de volgende
   opgeslagen telling wordt het 410 (de voorpagina mag een minuut achterlopen).
4. **Ander beginaantal:** `BEGIN` in `teller/index.php`, via een PR.
5. **Opnieuw beginnen:** `gezien.txt` weghalen. `recent.txt` mag ook weg.

## 4. Tests

- **`functest_teller.js`** (nieuw, 25), in Node, op het blok uit alle vijf
  apps:
  - de vingerafdruk is de SHA-256 van voorvoegsel + naam, met en zonder `.zip`;
  - één POST naar `/teller/` met alleen `h`;
  - de wachtrij bij geen verbinding, 429, 502, 503 en 504, en niet bij 400,
    404, 405 en 501;
  - geen dubbele in de rij, hooguit 50, inhalen hooguit vijf;
  - niets bij Global Privacy Control, *niet meetellen* of `file:`;
  - het blok is gelijk in de vijf apps en de haken zitten op hun plek.
- **`tellertest.py`** (nieuw, 33), met `teller/index.php` in de ingebouwde
  server van PHP (`php -S`, de suite als webmap, de opslag in een tijdelijke
  map). Zonder PHP slaat hij over en zegt dat.
  - **A. De server:**
    - `php -l`;
    - begint op 409; nieuw telt, dezelfde niet, ook niet in hoofdletters;
    - onzin geeft 400, PUT 405 met `Allow`;
    - de rem (hier 4 per uur) geeft 429 met `Retry-After`; een bekende gaat
      er niet tegenin;
    - de lijst is niet via de website te lezen;
    - in de opslag alleen vingerafdrukken en geen IP;
    - twintig tegelijk (vier PHP-werkers, tien keer, op een lege server): elk
      antwoord 200, en precies twintig erbij;
    - opslag in de webmap: 503.
  - **B. De voorpagina:** "Al 409 tellingen gedaan", "409 counts so far", de
    plek onder de titel; zonder teller (404) geen regel.
  - **C. Een telling in Static (`bewaarZip`):**
    - één POST met de juiste vingerafdruk;
    - 410; nog eens opslaan blijft 410;
    - de voorpagina volgt.
  - **D. Niet meetellen:**
    - de knop in de privacyverklaring, NL en EN, aan en uit, en dan wordt er
      niets verstuurd;
    - Global Privacy Control: niets verstuurd, en de verklaring zegt het.
  - **E. Zonder verbinding:**
    - de vingerafdruk wacht;
    - weer online en de app opnieuw open: alsnog geteld (411), de rij leeg;
    - geen JS-fouten.

Op GitHub draait `tellertest.py` vanzelf mee: ubuntu-24.04 heeft PHP 8.3 aan
boord.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `teller/index.php` | nieuw: de teller |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `pocket_count.html`, `traffic_counter.html` | gedeeld blok `teller`; haak in `bewaarZip` (vier apps) of `showPreview` (pocket) |
| `index.html` | de regel onder de titel; versie v3.37 |
| `privacy.html` | punt *Teller* / *Counter* met de knop; *Kort*; datum |
| `verantwoording.html` | één zin bij *Na afloop* |
| `README.md` | de teller is het enige stuk aan de serverkant |
| `_archief/overpass_rig/functest_teller.js`, `tellertest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `CLAUDE.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt (groep `teller`; *Server*; controle 5 is weer `php -l`) |

## 6. Validatie

```
valideer.py            ALLES OK — precies de 8 verwachte bestanden gewijzigd; gedeelde blokken OK (nieuw: teller, 5 bestanden)
functest_teller.js     25/25
tellertest.py          33/33
alle overige browsertests en functests groen; test_zipref en check_encoding OK
```
