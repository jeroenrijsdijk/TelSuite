# Overdracht v2.76 — noodopslag weg na de download, en alleen dan

Jay: "Ik heb het idee dat de app de LocalStorage niet leegt als de bestanden
gedownload zijn." Dat klopte, in drie apps op drie verschillende manieren.
Bij het testen van de oplossing kwam een vierde probleem boven, in de andere
richting: Static wiste soms een telling die níet was opgeslagen.

---

## 1. Wat er misging (gereproduceerd in de browser, v2.75)

Normale route per app: tellen, Stop, download, eventueel Sluiten, daarna een
app-wissel en weggaan, en dan de app opnieuw openen.

| app | wat bleef staan | gevolg |
|---|---|---|
| **pocket** (alle modi) | `pocket_sessie`, opnieuw weggeschreven na Sluiten | bij heropenen een herstelmelding voor een telling die al gedownload was |
| parkeertelling, fietsparkeren, capaciteit | `<app>_sessie_netwerk` (het wegennet van de sessie) | geen melding, wel de wegen van waar je telde, tot de volgende Start |
| Static | `static_sessie`, tot je Static opnieuw opende | geen melding; opgeruimd bij het volgende bezoek |

**Pocket.** `closePreview()` wiste de kopie wel. Maar na Stop is `telHistory`
nog gevuld, en `saveSession()` draait bij elke app-wissel en elke paginawissel.
Die schreef de afgeronde telling dus meteen opnieuw weg. Via de eigen ingang
`#parkeren` speelde het niet, omdat daar na Sluiten direct een nieuwe, lege
telling begint.

**Parkeer-apps.** De export wiste beide sleutels. Maar een Overpass-antwoord
dat na Stop binnenkwam (de fetch van de laatste GPS-fix, 600 ms vertraagd)
schreef het wegennet daarna opnieuw weg. `pasNetwerkToe()` keek niet of de
sessie nog liep.

**Static.** Bewust ontwerp uit v2.72: opruimen bij het volgende bezoek. Maar
de vlag "geëxporteerd" werd gezet zodra de ZIP gemaakt was, niet als hij
opgeslagen was. Met een geannuleerd deelblad op de iPhone betekende dat: de
afgeronde telling werd als geëxporteerd gemarkeerd, en bij het volgende bezoek
**stil gewist, zonder dat hij ooit was opgeslagen**. Dat zat erin sinds v2.72.

## 2. De regel nu

**De noodkopie verdwijnt zodra de ZIP aantoonbaar is opgeslagen, en niet
eerder. Daarna schrijft niets hem opnieuw weg.**

"Aantoonbaar opgeslagen" betekent:

- **iPhone:** het deelblad is voltooid. `navigator.share()` geeft een belofte
  die slaagt bij opslaan of delen, en faalt bij annuleren of als het gebaar
  verlopen is. `saveBlob()` geeft die uitkomst nu door (`true`/`false`).
- **Desktop en Android:** de download is aan de browser overgedragen
  (`true`).
- **Pocket:** *Sluiten* op het voorbeeldscherm telt ook als bevestiging.
  Dat is ongewijzigd sinds v2.11.

Lukt opslaan niet, dan blijft de kopie staan. De knop in het voorbeeldscherm
(pocket) of *Export CSV* (Static) probeert opnieuw; slaagt dat, dan verdwijnt
hij alsnog. Wordt de app eerder gesloten, dan biedt hij de telling de volgende
keer weer aan.

## 3. De wijzigingen

**Pocket** (`pocket_count.html`)

- `saveBlob()` geeft een belofte met de uitkomst.
- Nieuwe vlag `exportAfgerond` en functie `exportBevestigd()`: kopie weg, vlag
  aan. `saveSession()` doet niets meer zolang de vlag aan staat.
- De automatische poging na Stop, de knop in het voorbeeldscherm en *Sluiten*
  roepen `exportBevestigd()` aan.
- De vier start-functies zetten de vlag weer uit. Een nieuwe telling of
  doortellen na herstel heeft dus gewoon noodopslag.

**Static** (`traffic_counter.html`)

- `saveBlob()` geeft een belofte met de uitkomst.
- `exportBevestigd()` wist de kopie meteen als de telling afgerond is (END).
  Een tussentijdse export tijdens het tellen laat hem staan.
- `bewaarStatic()` doet niets meer na een bevestigde export.
- Het opruimen bij het laden blijft, voor kopieën uit v2.72–v2.75.

**Parkeer-apps** (drie bestanden, dezelfde twee wijzigingen)

- `pasNetwerkToe()` schrijft het wegennet alleen weg als `sessionActive` waar
  is. In het geheugen groeit het net gewoon door.
- `stopSession()` annuleert de wachtende, vertraagde fetch. Dat scheelt ook een
  Overpass-verzoek na Stop.

## 4. Privacyverklaring en handleiding

- `privacy.html` zei "na een afgeronde export ruimt de tool dat zelf op". Nu
  staat er de regel uit §2.
- Ook vermeld: de **wegennet-cache in IndexedDB**. Dat is openbare OSM-data,
  maar hij laat wel zien in welke gebieden je telde, en hij blijft staan tot je
  hem leegt. Die cache ontbrak in de verklaring.
- De handleiding zegt hetzelfde, in de algemene sectie over herstel en in de
  Static-sectie.

## 5. Nieuwe test: `opruimtest.py` (26 tests)

| deel | wat |
|---|---|
| A | normale route in alle vijf de apps (pocket in twee modi): na download, Sluiten, app-wissel en weggaan geen kopie en geen melding. Het nep-Overpass laat de fetch na Stop echt binnenkomen |
| B | iPhone, deelblad geannuleerd (pocket, Static): de kopie blijft en heropenen biedt de telling aan |
| C | iPhone, deelblad voltooid: meteen weg, ook zonder Sluiten |
| D | iPhone, eerst geannuleerd, dan via de knop opgeslagen: pas dan weg |
| E | tellernaam blijft bewaard (bedoeld) |

Het deelblad wordt nagebootst met een iPhone-user-agent en een eigen
`navigator.share`. Op v2.75 gedraaid geeft de test **9 fouten**, waaronder het
stille wissen door Static. Op v2.76 slagen alle 26.

## 6. Bewust niet veranderd

- **Parkeer-apps en een geannuleerd deelblad.** Die vallen terug op een
  download-link en wissen de kopie dan toch. Dat is bestaand gedrag en staat op
  de backlog, om gelijk te trekken met pocket en Static. Niet nu gedaan: het
  raakt de export van de apps die in de veldtest centraal staan.
- **De wegennet-cache** ruimt oude tegels nooit op. Dat is een cache, geen
  sessiedata; automatisch opruimen staat op de backlog.
- **Voorkeuren** (taal, tellernaam, kantelmodus) blijven staan, zoals de
  privacyverklaring zegt.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `pocket_count.html` | zie §3 |
| `traffic_counter.html` | zie §3 |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | zie §3 |
| `privacy.html` | regel uit §2, wegennet-cache, datum |
| `traffic_counter_help.html` | twee passages over de noodopslag |
| `index.html` | versie v2.76 |
| `_archief/overpass_rig/opruimtest.py` | nieuw, 26 tests |
| `_archief/overpass_rig/functest.js` | harness kent nu `sessionActive` (die bestond in de app al als globale variabele); +3 tests voor de nieuwe voorwaarde in `pasNetwerkToe()` |
| `_archief/overpass_rig/hersteltest.py` | de laatste Static-controle volgt de nieuwe regel: na END en download is de kopie meteen weg, niet pas bij het volgende bezoek |
| `_archief/overpass_rig/valideer.py`, rig-`README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py        ALLES OK — precies de 8 verwachte bestanden gewijzigd, gedeelde blokken OK
                   12 externe domeinen, alle in privacy.html; LET OP: contact nog invullen
opruimtest.py      26/26   (op v2.75: 9 FOUT)
hersteltest.py     133/133
laadtest.py        46/46
statictest.py      24/24
functests          alle 13 groen (functest.js nu 37)
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```

## 9. Voor de veldtest

`VELDTEST_3.0.md` controleert het herstel al. Eén extra check die dit
bevestigt op de echte iPhone: tel kort in pocket, Stop, sla de ZIP op via het
deelblad, wissel naar een andere app en open pocket opnieuw. Er hoort **geen**
herstelmelding te komen. Doe hetzelfde, maar annuleer het deelblad: dan
**wel** een melding.
