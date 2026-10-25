# Overdracht v3.35 — weekoverzicht in Passanten

Jay: "als ik in passanten.html op een link klik, kun je dan hetzelfe
weekvoerzicht geven als in telrapport: een tabel met 7 dagen (ma-zo), alle uren,
en het aantal passanten?"

Met "link" bedoelt Jay een stuk straat. In telrapport opent een klik op een
pocket-stuk direct het weekprofiel (`openWeekprofile`). Passanten doet dat nu
ook. Aan de berekening en de ZIP's verandert niets.

## 1. Het weekoverzicht

- **Openen:** een klik op een stuk straat, gekleurd of grijs, opent een
  venster boven de kaart.
  - Bovenaan staan de straat, de lengte, hoe vaak je er langsliep en op
    hoeveel dagen.
  - Sluiten kan met ✕, met een klik ernaast of met Escape.
- **Tabel:** de dagen ma–zo als rijen en de uren 0–23 als kolommen, zoals in
  telrapport.
  - Een gemeten cel toont de passanten per uur, met `*` als maar één
    looprichting gemeten is. De achtergrond heeft dezelfde kleurschaal als de
    kaart; op een donkere cel is de tekst wit.
  - Een niet gemeten cel is gearceerd en leeg.
- **Gem.:** een kolom per dag en een rij per uur.
  - **Rekenregel (`samen`):** dezelfde regel als in een cel. Per looprichting
    worden de tegenliggers en de ontmoetingsvensters van alle passages
    opgeteld, dan wordt er gedeeld, en daarna worden de richtingen opgeteld.
  - **Geen gemiddelde van cellen:** het is dus niet het gemiddelde van de
    celwaarden. In de test geeft de hoek "gem." 471, tegen 419 als je de twee
    cellen zou middelen.
  - **Waarom *gem.*:** telrapport noemt die kolom ∑, maar hier gaat het om een
    aantal per uur, niet om een som. Daarom staat er *gem.*
- **Details per cel:** onder de tabel.
  - Standaard staat de cel van de dag en het uur die op de kaart staan
    geselecteerd. Is die cel voor dit stuk niet gemeten (een grijs stuk), dan
    de cel met de meeste passages.
  - Een klik op een andere cel toont de details van die cel. Dat is de inhoud
    van de oude popup: het aantal met de marge, hoe vaak en op welke datums,
    de richtingen en de stilstaanders.
  - De knop *Toon zaterdag 13:00 op de kaart* zet de kaart op dat moment en
    sluit het venster.
- **Weg:** de Leaflet-popup op de kaart, met `popupNiet` voor een grijs stuk.
  Het weekoverzicht toont nu ook wanneer een grijs stuk wél gemeten is.
- **Telefoon:** de tabel schuift binnen het venster; de pagina zelf wordt niet
  breder.

## 2. Elders

- **`index.html`:** versie v3.35.
- **Handleiding, *Passanten per uur*:** de rij *Klik op een stuk* beschrijft
  nu het weekoverzicht.

## 3. Tests

**`passantentest.py`** 35 (was 25), nieuw deel W:
- Klik op de Voorstraat: het venster opent, met straat, lengte en "6 keer
  langsgelopen, op 3 dagen".
- De tabel heeft 7 dagen plus *gem.*, met 24 uren plus *gem.*
- Alleen za 13 en do 11 zijn gevuld, met de afgeronde waarden.
- *Gem.* per dag en per uur klopt. De hoek wordt samen gerekend en is niet het
  gemiddelde van de twee cellen.
- De cel van de kaart is gekozen, en de details kloppen. De marge omsluit de
  waarde.
- Klik op do 11, dan *Toon op de kaart*: het venster is dicht en de kaart
  staat op do 11.
- Een grijs stuk (de Kerkstraat op donderdag) opent het venster op za 13, met
  het sterretje.
- Escape sluit het venster.
- Op 390 px schuift de tabel binnen het venster en wordt de pagina niet
  breder.

**Bekeken:** op 1300 px en op 390 px.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | weekoverzicht (`openWeek`, `tekenWeek`, `samen`, `toonOpKaart`); popup op de kaart weg |
| `index.html` | versie v3.35 |
| `traffic_counter_help.html` | *Klik op een stuk* |
| `_archief/overpass_rig/passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
VALIDATIE_HIER
```
