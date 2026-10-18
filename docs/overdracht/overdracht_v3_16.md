# Overdracht v3.16 — capaciteitscontouren standaard uit

Jay: "Als je de geplande telling opent mag je de capaciteitscontouren weglaten.
Het kaartje is te druk om te lezen. Maak maar een schakelaar voor de contouren en
maak default dat de laag uit is."

## 1. Wat er veranderd is

Alleen de parkeertelling heeft deze laag. Fietsparkeren en pocket tekenen hem
niet; telrapport had al een schakelaar.

- **Standaard uit.** `capLayer` wordt aangemaakt, maar niet meer op de kaart
  gezet.
- **Knop *capaciteit*** in de kop van de kaart, naast *Looproute*. Aan is hij
  gevuld (`aria-pressed="true"`), uit omlijnd. De stijl is `.kaart-schakel`.
- **Pas ophalen bij de eerste keer aanzetten.**
  - `loadCapNetwerk()` was een functie die bij het laden meteen draaide; nu
    draait hij pas bij de eerste klik.
  - Hij geeft het aantal contouren terug, en de belofte wordt bewaard in
    `capGeladen`.
  - Bij elke volgende klik gaat de laag alleen aan of uit, zonder nieuw verzoek.
  - Zonder telling of planning vraagt de app dus ook geen `cap_netwerk.csv` meer op.
- **Geen laag op de server** (404 of leeg): de knop gaat terug naar uit en is
  daarna niet meer te kiezen. De tooltip zegt dan *Geen capaciteitslaag
  beschikbaar*. In de statusregel komt niets, zoals voorheen: daar staat tijdens
  het tellen belangrijkere informatie.
- **De keuze wordt niet onthouden.** Bij elke start staat de laag uit, zoals Jay
  vroeg.

De handleiding heeft bij *Mini-kaart & bearing* een alinea *Capaciteitscontouren
op de kaart*.

## 2. Tests

`planlinktest.py` deel E is nieuw (51 tests in totaal):
- openen met een planning: de contouren staan uit en zijn niet opgehaald, de
  planning is wel geladen;
- knop aan: één keer opgehaald, twee contouren op de kaart;
- knop uit: de laag is van de kaart;
- weer aan: niet opnieuw opgehaald;
- zonder `cap_netwerk.csv`: de knop gaat uit en is niet meer te kiezen;
- geen JS-fouten.

De test klikt via het script. Zonder de Leaflet-CSS (die de tests niet laden)
liggen de kaarttegels over de kop.

Bekeken in Chromium met de echte Leaflet-CSS, op 390 px:
- de kaart met de planning: de knop is uit en er staan geen contouren;
- na een klik: de knop is gevuld en de contour staat erop;
- de knop past in de kop naast de legenda.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html` | knop *capaciteit*, `schakelCapLaag`, `loadCapNetwerk` pas bij de eerste klik, laag standaard uit; CSS `.kaart-schakel` |
| `traffic_counter_help.html` | alinea *Capaciteitscontouren op de kaart* |
| `index.html` | versie v3.16 |
| `_archief/overpass_rig/planlinktest.py` | deel E |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

```
valideer.py           ALLES OK — 3 verwachte bestanden gewijzigd; gedeelde blokken (ook planlink) OK
planlinktest.py       51/51 (deel E nieuw)
laadtest.py           45/45
hersteltest.py        133/133
statictest.py         24/24
opruimtest.py         139/139
logicatest.py         30/30
robuusttest.py        87/87
gpkgtest.py           80/80
functests             alle 17 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
