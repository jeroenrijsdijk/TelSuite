# Overdracht v3.8 — noodkopie: één venster schrijft

Jay: "Als ik een telling heb afgebroken, en ik sluit het window, dan kan ik weer
verder met de opgeslagen gegevens in de cache. Als je dan op doorgaan klikt en
de telling afmaakt en bewaart is alle data binnen. Maar na het opslaan
verwijdert hij de eerder afgebroken telling niet - de eerder afgebroken telling
blijft achter." Na de diagnose en het voorstel: "Bouw maar, en neem stap 3 mee."

## 1. Wat er mis was

De route zelf was in orde. Nagespeeld in alle veld-apps, op desktop en als
iPhone met deelvenster, met een browserprofiel dat bewaard blijft:
- tellen, venster echt dicht;
- opnieuw openen, op de knop Doortellen drukken, afmaken en opslaan;
- weer dicht en open.

In alle zeven gevallen was de noodkopie weg en kwam er geen herstelmelding.

Het ging mis met **twee vensters**. Venster A heeft de afgebroken telling nog in
het geheugen. Venster B herstelt hem, telt door en slaat op, en de kopie is weg.
Maar zodra A verborgen wordt (tabwissel, scherm uit, weggaan), schrijft A zijn
oude stand terug. Gemeten in parkeertelling, pocket en Static: daarna stond de
kopie met de 4 tikken van vóór de onderbreking er weer. Dat is precies "de
eerder afgebroken telling blijft achter": de oude stand, niet de afgemaakte.

Op de iPhone ontstaat zo'n tweede venster makkelijk. Een icoon op het
beginscherm opent vaak een nieuw Safari-tabblad, en het oude blijft bestaan.
Op de computer kan het een tweede tabblad zijn.

Daarbij kwam een tweede probleem boven. Static schrijft elke 10 s een hartslag,
en een oud Static-venster overschreef zo ook een telling die in een ander venster
nog liep. Gemeten: de kopie sprong om de 10 s even van 10 naar 4 tikken. Crasht
het tellende venster op zo'n moment, dan zijn de tikken van na de onderbreking
weg.

## 2. Wat er veranderd is

Een nieuw gedeeld blok **noodkopie**, byte-identiek in de vijf veld-apps
(`/* ── Noodkopie: één venster schrijft (v3.8)` … `einde gedeeld blok noodkopie ── */`).

**Eén eigenaar.**
- Elk venster krijgt bij het laden een eigen id (`KOPIE_VENSTER`).
- De kopie draagt dat id (`venster`) en het id van de telling (`telling`).
- Alleen het venster dat eigenaar is, schrijft. Start en Doortellen maken een
  venster eigenaar.
- Een hersteld venster dat (nog) niet doortelt, schrijft niet.

**Afgesloten blijft dicht.**
- Na bevestigd opslaan of bewust weggooien komt het id van de telling op een
  korte lijst in `localStorage`: `telsuite_afgesloten`, de laatste 30.
- Geen enkel venster schrijft daarna nog een kopie van die telling.
- Vindt een app bij het openen zo'n kopie (bijvoorbeeld van een venster met
  oude code), dan wist hij die zonder melding.

Bewust weggooien is: Verwijder in pocket, Discard of Reset in Static, en een
nieuwe telling starten terwijl er een herstelde klaarstaat (alle apps, na de
bevestigingsvraag die er al was).

**Doortellen controleert eerst.** Is de kopie veranderd sinds dit venster hem
herstelde, dan weigert Doortellen. Dat gebeurt als een ander venster intussen
doortelde of opsloeg. Anders zou je met een verouderde stand verder tellen en
de nieuwere overschrijven.

**Stap 3: het oude venster meldt het.**
- Een venster dat buitenspel komt te staan, legt stil:
  - parkeer-apps: GPS, Overpass-timer, straatnaam-interval en schermslot uit,
    en geen vraag meer bij herladen;
  - pocket: GPS en schermslot uit;
  - Static: klok, GPS en schermslot uit.
- Daarna toont het een melding over de hele pagina (`#kopie-elders`) met een
  knop **Opnieuw laden**. Na herladen toont het venster de actuele stand.
- Er zijn drie redenen, elk met een eigen tekst. De taal volgt `<html lang>`:
  Static is Engels, pocket volgt de taalknop.

| reden | tekst |
|---|---|
| `elders` | Deze telling gaat verder in een ander venster. |
| `afgesloten` | Deze telling is in een ander venster opgeslagen of weggegooid. |
| `nieuw` | In een ander venster is een nieuwe telling begonnen. |

Wanneer een venster dit controleert:
- bij elke poging om te schrijven;
- bij het `storage`-event (een ander venster schreef, wiste of sloot af; dit
  komt meteen binnen als dat venster niet bevroren is);
- bij `pageshow` (ook terug uit het terug-geheugen van de browser);
- zodra het venster weer zichtbaar wordt.

**Het id van een telling per app**

| app | id |
|---|---|
| parkeertelling, fietsparkeren, capaciteit | `sessionId` |
| Static | `sessieId` |
| pocket | de starttijd (ISO). Pocket maakt zijn sessie-id pas bij Stop; Doortellen houdt de starttijd vast |

**Per app** levert de app drie haken: `KOPIE_SLEUTEL`, `kopieTelling()` en
`kopieStilleggen()`. In de drie parkeer-apps zijn die ook gelijk, in een eigen
bewaakt blok (`/* ── Noodkopie: haken parkeer-apps (v3.8) ── */`). De aanroepen
staan op vaste plekken:

| plek | aanroep |
|---|---|
| wegschrijven (`saveSession`, `bewaarStatic`) | `kopieMagSchrijven()`, dan `kopieSchrijf(data)` |
| Start (en de vier start-functies van pocket) | `kopieNieuw()` |
| Doortellen (`hervatSessie`, `hervatTelling`, `doortellenStatic`) | `kopieClaim()` |
| opslaan bevestigd (`bewaarZip`, `exportBevestigd`) | `kopieAfsluiten()` |
| weggooien | `kopieAfsluiten()` |
| herstellen bij het openen | `kopieHerstelbaar(id)` |

`venster` en `telling` staan alleen in de noodkopie in de browser, niet in de
ZIP. Het schema verandert niet.

## 3. Wat niet, en grenzen

- **Een hersteld venster dat niet doortelt, schrijft niets meer.** Tot v3.8
  schreef het de herstelde stand terug bij verbergen, wat niets toevoegde. Wel
  vervalt zo:
  - een Ongedaan maken in een herstelde parkeer-app;
  - een aangepaste notitie in een herstelde Static.
  Die komen in de ZIP, maar niet in de noodkopie, tot je doortelt.
- **Twee lopende tellingen van dezelfde app in twee vensters** kunnen niet,
  net als vroeger: er is één kopie per app. Wie later start, wint. Het andere
  venster krijgt de melding *nieuwe telling* en laat geen oude stand meer
  achter.
- **Static: Download van een herstelde, onderbroken telling** laat de kopie
  staan, zoals sinds v2.76 (een tussentijdse export). Dat is ongewijzigd.
- Een venster dat bevroren is (iOS in de achtergrond) ziet het pas als het
  weer zichtbaar wordt. Het schrijft in de tussentijd ook niets, dus dat is
  veilig.

## 4. Tests

`opruimtest.py` heeft een nieuw deel **G, twee vensters**: 87 tests, totaal 139.

- **G1. Doortellen in B, opslaan, A verborgen**, voor parkeertelling,
  fietsparkeren, capaciteit, pocket (parkeren, simpel) en Static, met de echte
  knop:
  - A meldt dat de telling verder gaat;
  - de kopie is die van B;
  - na opslaan en A verbergen staat er niets meer (Static ook na 11 s
    hartslag), en heropenen geeft geen melding;
  - een teruggezette oude kopie van die telling wordt niet hersteld;
  - herladen vanuit de melding vraagt niets;
  - geen JS-fouten.
- **G2. Static**: 13 s lang elke seconde gemeten, de kopie houdt de 10 tikken
  van B. Vóór v3.8 sprong hij naar 4.
- **G3. A telt door nadat B herstelde**: Doortellen in B weigert en meldt het,
  de kopie blijft die van A, en A schrijft gewoon verder.
- **G4. Weggooien in B sluit de telling af**: pocket Verwijder, en een nieuwe
  sessie in parkeertelling. A legt stil en zet niets terug; de kopie is die van
  de nieuwe sessie.

Tegen v3.7 faalt G1 op precies de gemelde punten: A meldt niets, de kopie
staat er na opslaan nog, en heropenen biedt de oude telling weer aan, ook als
een oude kopie wordt teruggezet. Voor G2 gaf dezelfde meting vóór de wijziging
de sprong van 10 naar 4. De bestaande delen A–F (52 tests) en `hersteltest.py`
(doortellen in één venster, 133 tests) slagen ongewijzigd.

De melding is in Chromium op telefoonformaat bekeken, in parkeertelling, pocket
en Static: leesbaar, in de letter en kleuren van de herstelmelding.

`valideer.py` bewaakt twee nieuwe groepen: `noodkopie` (5 bestanden) en
`noodkopie-haken` (de drie parkeer-apps). Het gedeelde blok `hervatSessie`
(doortellen) en `bewaarZip` kregen elk één regel, in alle drie gelijk.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | blok noodkopie, haken, aanroepen |
| `pocket_count.html` | blok noodkopie, haken, aanroepen |
| `traffic_counter.html` | blok noodkopie, haken, aanroepen |
| `traffic_counter_help.html` | alinea *Twee vensters* in *Onderbreking, herstel & doortellen* |
| `privacy.html` | de lijst met id's van afgesloten tellingen (NL en EN) |
| `index.html` | versie v3.8 |
| `_archief/overpass_rig/opruimtest.py` | deel G |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py        ALLES OK — 8 verwachte bestanden gewijzigd; 16 groepen gedeelde blokken OK
                   (nieuw: noodkopie 5 bestanden, noodkopie-haken 3); 14 publieke pagina's OK
opruimtest.py      139/139 (nieuw: deel G, 87 tests)
hersteltest.py     133/133
laadtest.py        47/47
statictest.py      24/24
gpkgtest.py        80/80
functests          alle 15 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
