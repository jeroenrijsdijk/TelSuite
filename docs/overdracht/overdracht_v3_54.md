# Overdracht v3.54 — Passanten: voortgang bij het inlezen

Jay: "Voor het inlezen van winkelstraat zips wil ik graag een voortgangs
indicator in passanten.html", en: "In dezelfde update graag alleen recon
inlezen als er twee er ook een origineel in de map staat".

## 1. De voortgang

- `lees` toont in de melding "Bezig met lezen… i van n ZIP's", de naam van het
  bestand dat nu gelezen wordt, en een balk (`.note .balk`).
- **Wanneer:** voor de eerste ZIP, en daarna ten hoogste elke 100 ms. Dan krijgt
  de browser even de beurt (`geefBeurt`, `setTimeout(0)`) om de melding te
  tekenen.
- **In een tab op de achtergrond** geeft `geefBeurt` de beurt niet. Daar kan
  `setTimeout` tot een seconde wachten, en er is toch niets te zien.
- **Na het lezen:** "Bezig met rekenen… n van n ZIP's gelezen", nog één beurt,
  dan `herbereken`. Daarna de gewone samenvatting.
- **Laadtijd** op de gemaakte set van 300 ZIP's: 1,6–2,2 s, voor en na gelijk
  (binnen de ruis). Bij 150 ZIP's komen er 15 tussenstanden.
- De tests wachten op het verdwijnen van "Bezig". Dat woord staat er dus in
  elke tussenstand.

## 2. Het origineel naast zijn reconstructie niet openen

- **Voorheen** las Passanten beide ZIP's helemaal in. Op `sessie_id` bleek dan
  dat de reconstructie voorgaat, en het origineel viel af.
- **Nu**, voor het lezen: staat `<basis>_recon.zip` (ook met " (2)") in de
  keuze, dan wordt `<basis>.zip` (ook met " (n)") niet geopend. De reden blijft
  "origineel; de reconstructie doet mee".
- De voortgang telt alleen de ZIP's die gelezen worden.
- Een hernoemd bestand vangt `leesZip` nog op de inhoud, zoals voorheen.

## 3. Tests

**`passantentest.py`: 102 (was 100).** De test neemt elke melding op met een
MutationObserver, en houdt bij welke ZIP's `JSZip.loadAsync` echt opent.

- Het origineel naast zijn reconstructie wordt niet geopend; de 5 andere wel.
- "0 van 5" met de naam en een balk, dan "Bezig met rekenen… 5 van 5", en aan
  het eind niet meer bezig en geen balk.

Valkuil: een `pg.evaluate` waarvan de laatste uitdrukking een functie is, roept
die functie aan. Eindig zo'n opdracht dus met `; 0`.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `lees`, `voortgang`, `geefBeurt`; het filter op naam; CSS `.note .balk` |
| `traffic_counter_help.html` | de inleiding van Passanten |
| `index.html` | versie v3.54 |
| `_archief/overpass_rig/passantentest.py` | zie §3 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
passantentest.py      102/102
volledige ronde lokaal: zie de PR
```
