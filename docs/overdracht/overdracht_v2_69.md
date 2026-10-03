# Overdracht v2.69 — voorpagina naar wat je telt, en een dode herstelfunctie

De voorpagina is opnieuw ingedeeld en pocket-parkeren heeft een eigen ingang.
Bij het testen in een echte browser kwam een bestaande fout boven: in pocket
werkte het **sessieherstel** niet. Een onderbroken telling werd nooit
teruggeboden en bij de volgende start stil gewist. Die fout is gerepareerd, want
zonder die reparatie werkte de nieuwe ingang ook niet.

---

## 1. Samenvatting

1. `index.html` bestaat nu uit drie groepen: **Verkeer tellen** (wat komt er
   langs), **Parkeren tellen** (wat staat er) en **Achter je bureau**.
2. Pocket-parkeren staat als eerste kaart onder *wat staat er*. De kaart linkt
   naar `pocket_count.html#parkeren`.
3. `pocket_count.html` start met `#parkeren` meteen in parkeren, maar alleen als
   er niets te herstellen is.
4. **Reparatie:** de opstart van pocket liep vast, waardoor het sessieherstel
   nooit draaide.
5. Nieuwe `laadtest.py`: laadt elke pagina echt in Chromium (29 tests).

## 2. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `index.html` | drie groepen, nieuwe en herschreven kaartteksten NL/EN, bureaupaneel, zichtbare focus, versie v2.69 |
| `pocket_count.html` | opstart na `DOMContentLoaded`; directe ingang `#parkeren` |
| `_archief/overpass_rig/laadtest.py` | nieuw |
| `_archief/overpass_rig/valideer.py` | `RELEASE` en verwachte sets |
| `_archief/overpass_rig/README.md`, `README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

Alle andere HTML-bestanden zijn byte-identiek aan v2.68.

## 3. De voorpagina

```
VERKEER TELLEN — wat komt er langs
  Stilstaand tellen            traffic_counter        (ongewijzigd)
  Tellen in beweging           pocket, drie modi      (ongewijzigd)
PARKEREN TELLEN — wat staat er
  Snel tellen: bezet of leeg   pocket #parkeren       (nieuw)
  Per vak, op de kaart         parkeertelling
  Geparkeerde fietsen          fietsparkeren
  Alleen de plekken            capaciteitstelling
ACHTER JE BUREAU — voor en na het veldwerk
  Plannen · Reconstrueren · Rapport                   (compact paneel)
```

**Teksten.** De parkeerkaarten zijn herschreven, zodat ze zeggen wanneer je
welke kiest. Pocket-parkeren is snel, per kant, bezet of leeg, met grote vlakken
en een tikgeluid. Parkeertelling is de volledige telling per plek: goed of fout
geparkeerd, leeg of bijzonder. De twee verkeerskaarten zijn ongewijzigd. De
pocketkaart zegt weer terecht "drie modi", want parkeren heeft nu een eigen
kaart.

**Vorm.** Er is geen nieuw ontwerp gemaakt; de bestaande huisstijl is
doorgetrokken.

- Groepskoppen in Oswald met de vraag rechts ernaast.
- Pocket-parkeren krijgt dezelfde kleur (`#2e6b8a`) als de Parkeren-knop in
  pocket zelf.
- Het bureaupaneel gebruikt `subgrid`, zodat de omschrijvingen onder elkaar
  beginnen, hoe lang de langste titel ook is. Zonder subgrid-steun staat de
  omschrijving onder de titel.
- Kaarten en bureaulinks hebben nu een zichtbare focusrand voor het
  toetsenbord.

Gecontroleerd met de echte lettertypen op 360 en 390 px breed (NL en EN): alles
op één regel waar het hoort, niets breder dan het scherm.

## 4. De directe ingang

```
index.html → pocket_count.html#parkeren
```

- Pocket slaat het keuzescherm over en start meteen in parkeren.
- Alleen als er **niets te herstellen** is. `startParkeren()` wist de
  noodopslag, en een onderbroken telling gaat altijd voor. Staat de
  herstelmelding er, dan blijft het keuzescherm staan en doet de hash niets.
- De tabtitel wordt "Pocket Parkeren", en de hash blijft in de adresbalk. Je
  kunt deze ingang dus als **eigen icoon op het beginscherm** zetten.
- Het scherm-aan-slot kan zonder tik vooraf worden geweigerd. Daarom vraagt de
  eerste aanraking het opnieuw aan als het er nog niet is.

Pocket-parkeren is bewust geen eigen tool. Schema, ZIP-naam `_pkt_p` en
reconstructor blijven hetzelfde.

## 5. De reparatie: sessieherstel was dood

**Wat er gebeurde.** Onderaan het script van pocket stond:

```
applyLang();
document.addEventListener('visibilitychange', ...);
window.addEventListener('pagehide', saveSession);
restoreSession();
```

`applyLang()` vult ook `#preview-title` en de andere teksten van het
voorbeeldscherm. Maar dat scherm staat pas **na** het script in de HTML. Op dat
moment bestond het element nog niet, `applyLang()` gaf een fout, en het script
stopte. Alles daarna draaide nooit:

- `restoreSession()` — de herstelmelding is nooit verschenen;
- de listeners voor `visibilitychange` en `pagehide`.

**Wat dat betekende.** Het opslaan per tik werkte wel (`saveSession()` staat bij
elke tik). Een onderbroken telling stond dus netjes in de opslag. Maar hij werd
nooit teruggeboden, en elke nieuwe start (`start*` roept `clearSession()` aan)
wiste hem stil.

Het taalsysteem leek wel te werken. De eerste teksten werden nog gezet
voordat `applyLang()` vastliep, de rest staat in de HTML al in het Nederlands,
en de taalknop werkt later, als alles bestaat, wél goed.

**De reparatie.** De twee listeners blijven direct in het script. `applyLang()`
en `restoreSession()` draaien nu in een `DOMContentLoaded`-handler, als de hele
pagina er staat. De directe ingang is een tweede handler daarna. Handlers draaien
in volgorde, dus de herstelcontrole heeft altijd al beslist voordat de ingang
kijkt.

**Getest in Chromium:**

- de herstelmelding verschijnt ("2 tikken hersteld …");
- de opslag blijft staan;
- "Download" bouwt de ZIP en toont het voorbeeldscherm zonder fouten.

Hoe lang dit al stuk was, weet ik niet. Het herstelpad is in elk geval een
tijd niet in het veld gebruikt. Let dus op bij de eerste keer dat je hem echt
nodig hebt.

Mogelijk verschijnt na deze update eenmalig een herstelmelding voor een oude,
nooit afgesloten sessie die nog in de opslag stond. Dat is dan terecht: kies
Download of Verwijder.

## 6. Nieuwe test: `laadtest.py`

`node --check` en de tagbalans zien een fout als deze niet: de syntax klopt, het
misgaan zit in de volgorde van de pagina. Daarom een test die elke pagina echt
laadt. Hij start zijn eigen webserver en leidt de CDN-bibliotheken en Google
Fonts om naar lokale kopieën in `node_modules`. Al het andere externe verkeer
wordt geblokkeerd.

| deel | wat |
|---|---|
| A | elke HTML-pagina laadt zonder JS-fout (15 pagina's) |
| B | pocket: vier situaties rond `#parkeren` en herstel |
| C | index: link-doelen bestaan, NL/EN-sleutels compleet en gelijk, niets breder dan 360 px |

Op v2.68 gedraaid geeft hij 9 fouten: pocket laadt fout, het herstel is dood en
de bureaulinks ontbreken. Op v2.69 zijn alle 29 tests groen.

Hij vraagt Playwright met Chromium, plus in een `node_modules`: `leaflet@1.9.4`,
`leaflet-draw@1.0.4`, `jszip`, `papaparse`, `@fontsource/oswald` en
`@fontsource/share-tech-mono`.

## 7. Validatie

```
valideer.py                       ALLES OK
  byte-identiteit                 index.html en pocket_count.html gewijzigd, de rest identiek
  gedeelde blokken                10 groepen OK
  releasenummer                   index v2.69 · vorige v2.68 · stand v2.69 · overdracht_v2_69.md
laadtest.py                       29/29
functests                         alle 13 groen
test_zipref.py                    referentie sluit aan op de code
check_encoding.py                 alles geldige UTF-8
```

## 8. Backlog-wijzigingen

- "Parkeren uit pocket halen" — grotendeels gedekt door de eigen ingang. Een
  echte afsplitsing pas als parkeren een eigen kant op gaat.
- Nieuw: `over.html` en de handleiding volgen de nieuwe indeling nog niet.
- Nieuw: pocket vraagt het scherm-aan-slot niet opnieuw aan na terugkeer in de
  app.
