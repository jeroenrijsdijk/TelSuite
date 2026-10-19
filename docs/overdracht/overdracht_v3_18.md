# Overdracht v3.18 — ZIP opslaan op Android

Jay telde een planning uit WhatsApp met parkeertelling op een Samsung S25
(Android, Chrome; de link opende in Chrome zelf, met de adresbalk):

> "Aan het einde, na druk op de stop knop, bewaarde de app de zip niet
> automatisch. Ik kon de zip niet bewaren, na een tijdje wel reconstrueren."
> "De app meldt ook zelf: Zip niet opgeslagen."
> "De download zip knop is niet grijs meer, maar reageert niet op een tik."
> "Waar ging zoveel tijd overheen?"

De noodkopie deed zijn werk: de telling stond er nog.

## 1. Oorzaak

Het gedeelde blok `bewaarZip` (v2.77) in parkeertelling, fietsparkeren en
capaciteitstelling probeerde op **elk** platform eerst het deelvenster
(`navigator.canShare` → `navigator.share`). Chrome op Android deelt alleen
foto's, video, audio, pdf en tekst; geen ZIP. `canShare` zegt toch ja, en
`share` weigert meteen (NotAllowedError). Het gevolg:
- de app meldde *ZIP niet opgeslagen*, terecht, en liet de noodkopie staan;
- ⬇ Download ZIP bood dezelfde ZIP opnieuw aan, opnieuw via het deelvenster,
  en kreeg opnieuw een weigering. Er is nooit een download geprobeerd. Op de
  knop zelf zag je niets: alleen de statusregel bovenin veranderde.

**Waar de tijd heen ging:** niet naar het inpakken. Gemeten (Chromium, CPU zes
keer vertraagd, 1500 GPS-punten): de ZIP staat er binnen 1,7 s. De tijd ging
naar het herhaald tikken op een knop die niets kon doen.

De losse `saveBlob` van dezelfde apps, pocket en Static deden het al goed:
alleen iOS via het deelvenster, de rest via een download-link. Alleen
`bewaarZip` week daarvan af. Op Android met Chrome werkte de ZIP-knop van de
parkeer-apps zo waarschijnlijk al sinds v2.77 niet. De tests zagen dat niet: ze
bootsten het deelvenster alleen na voor de iPhone (`opruimtest` B–F).

## 2. Wat er verandert

Alleen het gedeelde blok `bewaarZip`, byte-identiek in de drie parkeer-apps:

| platform | tot v3.18 | sinds v3.18 |
|---|---|---|
| iPhone, iPad | deelvenster; voltooid = opgeslagen | ongewijzigd |
| Android (Chrome, Samsung Internet) | deelvenster, geweigerd: *niet opgeslagen*, nooit een download | download; opgeslagen |
| desktop met deelvenster (Chrome op Windows) | deelvenster | download; opgeslagen |
| desktop zonder deelvenster | download; opgeslagen | ongewijzigd |
| ingebouwde browser van een app op Android (WebView, `; wv)` in de user-agent) | download; opgeslagen | download, maar **niet** opgeslagen: de noodkopie blijft, de status zegt het |

De iOS-test is dezelfde als in `saveBlob` en pocket.

**Ingebouwde browser.** Jays link opende in Chrome, dus dit speelde hier niet.
Het is een kleine extra beveiliging. Een WebView kan een `blob:`-download
meestal niet opslaan, en tot v3.18 telde die download toch als opgeslagen: de
noodkopie werd gewist terwijl er geen ZIP was. Nu blijft hij staan. Hij staat
dan wel in de opslag van die app, niet in Chrome. Daarom raadt de status (en
de handleiding) aan de link in Chrome of Samsung Internet te openen.

**Niet gedaan** (op de backlog):
- een waarschuwingsbalk bij het openen in een ingebouwde browser. Dat vraagt
  een nieuw gedeeld blok in vijf apps, voor een probleem dat in het veld nog niet
  is voorgekomen;
- pocket en Static in een ingebouwde browser. Die tellen een download daar nog
  als opgeslagen, en *Sluiten* in het voorbeeldscherm van pocket bevestigt
  altijd (v2.76).

## 3. De telling van Jay

Die staat nog in de noodkopie van Chrome op de S25. Zodra v3.18 online staat:
1. parkeertelling openen in dezelfde Chrome (niet op Start tikken: dat vraagt
   of de herstelde telling weg mag);
2. de herstelmelding verschijnt;
3. ⬇ Download ZIP: de ZIP staat in Downloads, en de noodkopie verdwijnt.

`opslaantest.py` deel B doet precies dit.

## 4. Handleiding

- *Exporteren → ↓ Download ZIP*: iPhone/iPad via het deelmenu, Android en
  desktop als download, met wat er tot v3.18 misging. Een alinea
  *Ingebouwde browser*.
- *Planning als link*: de bestaande tip "Open de link in Safari of Chrome"
  noemt nu ook dat een ingebouwde browser op Android vaak geen ZIP kan opslaan.

## 5. Tests

**`opslaantest.py`** (nieuw, 48 tests, Chromium). Het deelvenster is
nagebootst zoals Chrome op Android het doet: `canShare` zegt ja, `share`
weigert. Voor elk van de drie parkeer-apps:
- *A, Android:* Stop geeft een echte download, zonder deelvenster; een geldige
  ZIP met alle tikken; status *ZIP opgeslagen*; daarna geen noodkopie.
- *B, Android, herstel* (de telling van Jay): niet gestopt, pagina opnieuw
  open, herstelmelding; één tik op ⬇ Download ZIP geeft de ZIP met de
  herstelde tikken; daarna is de kopie weg.
- *C, ingebouwde browser:* de download wordt aangeboden, de status noemt de
  ingebouwde browser, de kopie blijft en heropenen biedt de telling weer aan.
- *D, desktop met deelvenster:* download.
- *E, iPhone:* nog steeds het deelvenster, geen download.

Tegen v3.17 blijft in deel A de download uit (time-out), zoals bij Jay.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | gedeeld blok `bewaarZip`: deelvenster alleen op iOS; in een WebView niet bevestigen |
| `traffic_counter_help.html` | *↓ Download ZIP*, *Ingebouwde browser*, tip bij *Planning als link* |
| `index.html` | versie v3.18 |
| `_archief/overpass_rig/opslaantest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
VALIDATIE
```
