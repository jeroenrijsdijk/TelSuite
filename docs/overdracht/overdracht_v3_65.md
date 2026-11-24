# Overdracht v3.65 — Overpass vaker laten slagen

Jay: "is er een manier om de overpass query wat vaker te laten slagen? het gaat
moeizaam". Meestal: "Wegen ophalen mislukt. Server 1: geen verbinding of een
fout bij de server. Server 2: geen antwoord binnen 45 s." En: "Ook in het veld
is er af en toe geen netwerk." Gekozen uit het voorstel: 1 tot en met 3, geen
derde server (VK Maps staat in Rusland; in de telapps zou het gebied rond de
positie van de teller daarheen gaan).

## 0. Achtergrond

- De hoofdserver (overpass-api.de) is al maanden onbetrouwbaar. Het OSM-forum
  meldt misbruik sinds november 2025 (scrapen via residentiële proxies) en
  steeds meer 504's en time-outs (jan–mrt 2026). De wiki: "do not expect high
  reliability".
- Overpass laat een vraag pas toe als er geheugen vrij is voor de opgegeven
  `maxsize` (standaard 512 MiB). Op het forum: met `[maxsize:16Mi]` verdwenen de
  504's voor veel vragen. De wiki: na een 429 een halve minuut wachten.
- "Geen verbinding of een fout" bij server 1 is waarschijnlijk vaak een 504
  zonder CORS-kop: de browser ziet dan een netwerkfout.

## 1. Telplanning

- **`buildQuery(geom, groot)`**: een rechthoek, de contour plus
  `OPHAAL_MARGE_M` (100 m), in plaats van `poly` plus een `around`-cirkel. Een
  bbox is de goedkoopste vraag. Welke wegen binnen de contour vallen, rekent
  `processWays` zelf uit, zoals altijd. Met `[maxsize:67108864]`
  (`OPHAAL_MAXSIZE`, 64 MiB).
- **"out of memory"** in de remark (`e.geheugen`): dezelfde server meteen nog een
  keer, zonder maxsize (`groot`). Daarna gewoon verder.
- **Zelf opnieuw.** Faalt de laatste server en waren alle redenen `tijd`, `fout`
  of `limiet` (`OPHAAL_HERHAAL`), dan `ophaalLater`:
  - over `OPHAAL_WACHT_MS` (30 s) een nieuwe ronde vanaf server 1, tot
    `OPHAAL_RONDES` (3) keer;
  - een melding op de kaart: de redenen, een aftelling, "poging 2 van 3", en de
    knoppen **Nu proberen** (`ophaalNu`) en **Stoppen** (`ophaalStoppen`, dat
    wordt de gewone foutmelding met Opnieuw);
  - na de laatste ronde de foutmelding "… ook na 3 pogingen";
  - `clearAll` (Wis alles) annuleert wachtende pogingen.
- **Niet opnieuw** bij `afgebroken` (Overpass brak de vraag af, meestal te
  groot) of `oud` (verouderde data): daar helpt wachten niet. De melding komt
  meteen, met het advies van een kleiner gebied.

## 2. Telapps

- **`fetchRoads`** (parkeertelling, fietsparkeren, capaciteitstelling, pocket) en
  de terreinvraag van capaciteitstelling: `[maxsize:33554432]` (32 MiB). Rond je
  positie gaat het om 250–300 m, dus dat is ruim. Hun herhaling met backoff
  bleef zoals hij was.
- **`gebiedQuery`** (gedeeld blok *gebied vooraf*, in parkeertelling,
  fietsparkeren en pocket): `[maxsize:134217728]` (128 MiB), een kwart van de
  standaard, ruim voor `GEBIED_MAX_TEGELS`. md5 in alle drie gelijk.
- Zonder netwerk in het veld: de tegelcache (v3.19) blijft het antwoord. Open
  een link thuis op wifi. De handleiding zegt het nu ook bij telplanning.

## 3. Niet gedaan

- **Een derde server** (Jay: geen). Opties waren VK Maps (maps.mail.ru,
  Rusland) en dresel.systems (Europa, onbekend of CORS werkt).
- **Telplanning op de tegelcache van de telapps.** Dat is hetzelfde domein, dus
  het kan: een gebied dat al eens gepland of geteld is, komt dan zonder Overpass
  op de kaart. Het is groter werk, en de wegtypen buiten `HIGHWAY_RE` vallen weg
  (snelweg, trunk, `_link`). Genoemd, niet besloten.
- **De bureautools** (telreconstructie, snaptrace, telrapport): ongewijzigd.

## 4. Handleiding

Telplanning: *Wegen ophalen (sinds v3.65)*. De kleine vraag, het zelf opnieuw
proberen met Nu proberen en Stoppen, wanneer het niet opnieuw probeert, en de
telapps met de tip over wifi.

## 5. Tests

- **Nieuw: `ophaaltest.py`, 30.**
  - **A. De zoekvraag:** een rechthoek van de contour plus ±100 m, maxsize 64 MiB,
    geen poly of around.
  - **B. "out of memory":** server 1 twee keer, de tweede keer zonder maxsize, en
    server 2 niet.
  - **C. Storing bij beide servers:** de melding met redenen, aftelling,
    "poging 2 van 3" en de knoppen; daarna zelf opnieuw, met de wegen.
  - **D. Nu proberen:** meteen. **Stoppen:** mislukt, en geen poging meer; daarna
    Opnieuw.
  - **E. Wis alles tijdens het wachten:** geen poging meer.
  - **F. Afgebroken:** meteen mislukt, en niet opnieuw.
  - **G. De telapps:** de maxsize in alle vier, de terreinvraag en
    `gebiedQuery`.
- **`robuusttest.py` E6** (twee keer 429): eerst de aftelling, na 3 pogingen
  mislukt (3 + 3 verzoeken). Nu 90 (was 89).
- **`gebiedtest.py`**: de omgeving van een link is nu een rechthoek met maxsize
  (was poly).

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | `buildQuery` (bbox, maxsize), out-of-memory, `ophaalLater`/`ophaalStart`/`ophaalNu`/`ophaalStoppen`, de wachtmelding, `clearAll` |
| `parkeertelling.html`, `fietsparkeren.html`, `pocket_count.html` | maxsize in `fetchRoads` en `gebiedQuery` (gedeeld blok) |
| `capaciteitstelling.html` | maxsize in `fetchRoads` en de terreinvraag |
| `traffic_counter_help.html` | *Wegen ophalen (sinds v3.65)* |
| `index.html` | versie v3.65 |
| `_archief/overpass_rig/ophaaltest.py` | nieuw |
| `_archief/overpass_rig/robuusttest.py`, `gebiedtest.py` | zie §5 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py           ALLES OK — de 7 verwachte bestanden; gebied vooraf byte-gelijk
ophaaltest.py         30/30
robuusttest.py        90/90
gebiedtest.py         51/51
volledige ronde lokaal: zie de PR
```
