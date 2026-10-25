# Overdracht v3.38 — teller: GPC eruit, de knop blijft

Een kleine release na v3.37 (PR #52). Twee dingen aan de teller.

## 0. Het gesprek vooraf

1. **Global Privacy Control.** In v3.37 had ik ingebouwd dat een browser met
   GPC aan niet meetelt. Jay vroeg daarna: "Global Privacy Control - moeten we
   die echt respecteren? er is toch niet zoveel aan de hand?"
   - Het hoeft niet. GPC is alleen in een paar Amerikaanse staten bindend
     (Californië, Colorado, Connecticut, New Jersey, Oregon), en daar gaat het
     over het verkopen of delen van persoonsgegevens. Dat gebeurt hier niet:
     er gaat een hash van een bestandsnaam naar de eigen server, zonder IP.
   - Het scheelt ook weinig: Firefox (als je het aanzet), Brave en DuckDuckGo
     sturen het. Safari en Chrome doen het niet zonder extensie.
   - Mijn voorkeur was laten staan, omdat het bijna niets kost. Jay: "GPC eruit,
     de knop blijft".
2. **Gelijktijdige eerste verzoeken.** In de testronde van v3.37 vond
   `tellertest.py` één keer 428 waar 429 hoorde. Oorzaak:
   - de opslagmap bestond nog niet en de eerste verzoeken kwamen tegelijk;
   - één verzoek maakte de map, de andere zagen hun `mkdir` mislukken en gaven
     een 503.

   In de praktijk was het onschuldig: een 503 laat de vingerafdruk wachten, en
   het eerste bezoek aan de voorpagina maakt de map al. Toch een fout.

PR #52 was al gemerged voor deze twee wijzigingen op de branch stonden; daarom
een eigen release.

## 1. Wat er veranderd is

- **Blok `teller`** (byte-identiek in de vijf veld-apps):
  - de regel `if (navigator.globalPrivacyControl) return false;` is weg;
  - het commentaar zegt waarom, met Jay's zin;
  - niet versturen blijft: buiten http(s), zonder WebCrypto of fetch, en met
    `telsuite_niet_tellen` (de knop).
- **`privacy.html`:**
  - de zinnen over GPC zijn weg, in het Nederlands en het Engels;
  - de stand bij de knop is alleen nog *Dit toestel telt mee.* of *Dit
    toestel telt niet mee.*
- **`teller/index.php`:** na een mislukte `mkdir` kijkt het script nog eens
  met `is_dir`. Heeft een ander verzoek de map net gemaakt, dan gaat het
  gewoon door.
- **`index.html`:** versie v3.38.

Aan de server-API, de opslag, de ZIP's en het schema verandert niets. Wat al
geteld is, blijft staan.

## 2. Tests

- **`functest_teller.js`** (25):
  - de test "GPC: niets" is nu "GPC telt niet: wel verstuurd";
  - "ook inhalen niet, als het niet mag" gebruikt nu de knop in plaats van GPC.
- **`tellertest.py`** (33):
  - **A:** twintig tegelijk, tien keer, elk op een lege server met vier
    PHP-werkers. Elk antwoord moet 200 en nieuw zijn, en er komen er precies
    twintig bij.
    - Met het script van v3.37 faalde dat in de meeste runs (bekeken).
  - **D:** met GPC wordt een telling wel verstuurd en geteld (411). De
    privacyverklaring zegt dan "Dit toestel telt mee." en noemt GPC niet.
  - **E:** telt daardoor één verder (offline 411, daarna 412).

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `pocket_count.html`, `traffic_counter.html` | blok `teller`: GPC eruit |
| `privacy.html` | GPC-zinnen en GPC-stand weg |
| `teller/index.php` | `is_dir` na een mislukte `mkdir` |
| `index.html` | versie v3.38 |
| `_archief/overpass_rig/functest_teller.js`, `tellertest.py`, `valideer.py`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Na de merge (voor Jay)

Hetzelfde als bij v3.37, als dat nog niet gedaan is: open
https://telonline.org/teller/. Daar hoort `{"tellingen":409}` te staan, of
meer. Zie `overdracht_v3_37.md` §3 voor wat je anders kunt zien.

## 5. Validatie

```
valideer.py            ALLES OK — precies de 7 verwachte bestanden gewijzigd; gedeelde blokken OK (teller, 5 bestanden)
functest_teller.js     25/25
tellertest.py          33/33
laadtest, vingerafdruktest, opslaantest, deeltest lokaal groen; de rest op GitHub
```
