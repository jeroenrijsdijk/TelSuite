# Overdracht v2.70 — de parkeer-ingang toont nooit het keuzemenu

Jays wens: via de kaart "Pocket — parkeren" op de voorpagina nooit in het
pocketmenu met de vier modi belanden, maar meteen in parkeren.

v2.69 deed dat al bij het openen, maar niet overal. Er waren drie plekken waar
je alsnog in het menu kwam:

- **bij een onderbroken telling** — het menu met de herstelmelding erboven.
  Direct na v2.69 is dat waarschijnlijk, want het herstel werkte daarvoor niet
  en er kan nog een oude sessie in de opslag staan;
- **na Terug** op het parkeerscherm;
- **na Stop**, onder het voorbeeldscherm.

Daarnaast kon het menu bij het laden heel even zichtbaar zijn, vóórdat het
script het wegzette.

---

## 1. Hoe het nu werkt

Via `pocket_count.html#parkeren` gedraagt pocket zich als parkeer-app:

| moment | v2.69 | v2.70 |
|---|---|---|
| openen, niets te herstellen | parkeerscherm | parkeerscherm |
| openen met onderbroken telling | **menu** + herstelmelding | herstelmelding + alleen de Parkeren-knop |
| Verwijder bij herstel | **menu** | parkeerscherm |
| Download bij herstel → Sluiten | **menu** | parkeerscherm |
| Terug op het parkeerscherm | **menu** | voorpagina |
| Stop → voorbeeldscherm → Sluiten | **menu** | verse parkeertelling |
| Stop zonder voorbeeldscherm (geen GPS-spoor) | **menu** | alleen de Parkeren-knop |
| tijdens het laden | menu kon even flitsen | nooit |

Gewone pocket, zonder `#parkeren`, is ongewijzigd: keuzemenu, en Terug gaat
terug naar het menu.

## 2. Hoe het gebouwd is

**Verbergen vóór de eerste weergave.** Een klein script in `<head>` zet de
klasse `pk-ingang` op `<html>` als de hash `#parkeren` is. Het zet daar ook de
tabtitel. De CSS verbergt dan de kop "Wat tel je?", de toelichting en de drie
andere modusknoppen. De Parkeren-knop blijft staan.

Omdat dit gebeurt voordat de pagina wordt getekend, is het menu nooit zichtbaar,
ook niet even. De test controleert dat in elk frame.

**Waarom de Parkeren-knop blijft staan.** Op twee plekken is er geen
parkeerscherm om naartoe te gaan:

- bij een herstelmelding, want eerst herstellen, dan starten
  (`startParkeren()` wist de noodopslag);
- als er na Stop geen voorbeeldscherm komt. `showPreview()` stopt zonder
  GPS-spoor en zonder segmenten.

Met één knop loopt het scherm dan nooit dood.

**Drie haakjes aan `pkDirect`**, elk één regel:

| functie | via de ingang |
|---|---|
| `restoreDiscard()` | daarna `startParkeren()` |
| `closePreview()` | daarna `startParkeren()` |
| `pkBack()` | naar `index.html` in plaats van het menu |

`stopTelling()` is niet aangeraakt. Het toont het keuzescherm zoals altijd,
maar via de ingang staat daar alleen de Parkeren-knop op.

Een eerste versie liet `stopTelling()` via de ingang niets tonen. Dat gaf een
leeg scherm als er geen voorbeeldscherm kwam; de laadtest ving dat. Daarom nu
de ene knop.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `pocket_count.html` | `<head>`-script, 3 CSS-regels, `pkDirect` en drie haakjes; ingangslogica herschreven |
| `index.html` | versie v2.70 |
| `_archief/overpass_rig/laadtest.py` | deel B herschreven: de hele parkeerroute, 40 tests |
| `_archief/overpass_rig/valideer.py`, `README.md` (rig), `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Als je op de telefoon tóch het menu ziet

Safari kan een oude `pocket_count.html` uit de cache halen. De voorpagina is
dan vers (v2.70 onderaan), pocket nog niet, en de oude pocket kent `#parkeren`
niet. Open pocket één keer en herlaad hem, of wis de websitegegevens van
telonline.org.

Structureel lost de server dit op met `Cache-Control: no-cache` voor
HTML-bestanden. Dan vraagt de browser elke keer kort na of er iets nieuws is.
Dat is een instelling aan de serverkant, niet in de suite.

## 5. Validatie

```
valideer.py                       ALLES OK — index.html en pocket_count.html gewijzigd
  gedeelde blokken                10 groepen OK
  releasenummer                   v2.70 op alle vier de plekken
laadtest.py                       40/40, waaronder:
  parkeerroute                    openen → tik → Stop → Sluiten → verse telling → Terug → voorpagina
  herstel                         melding + alleen Parkeren; Verwijder én Download → parkeren
  zonder voorbeeldscherm          Parkeren-knop, geen doodlopend scherm
  elk frame                       de andere modi nooit zichtbaar (positieve controle: zonder hash wel)
  gewone pocket                   menu, Terug naar menu, herstel met vier modi — ongewijzigd
functests                         alle 13 groen
check_encoding.py                 alles geldige UTF-8
```

## 6. Backlog

Nieuw: tik je bij een herstelmelding een modus aan, dan wist de start de
onderbroken telling zonder te vragen. Dat was altijd al zo, maar het telt pas
nu het herstel werkt. Oplossing: een bevestiging als de melding zichtbaar is.
