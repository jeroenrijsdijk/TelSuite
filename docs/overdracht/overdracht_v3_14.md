# Overdracht v3.14 — planning als link

Jay: "Nu we de planning json downloaden, is er een beschrijving hoe je een telling
json inlaadt?" Die was er niet, want inladen kon nergens. Daarna: "Ik wil vanuit
een mail of link een telling kunnen starten." Uit twee voorstellen (A: een link
naar het bestand op de server; B: de planning in de link zelf): "B is de mooiste
optie, maak die maar. Kan pocket parkeren direct mee, of is dat een extra
release?" Pocket ging mee.

## 1. Wat er veranderd is

**Telplanning: Deel als link.**
- Een knop boven *Maak Telling*. Hij staat aan en uit samen met Maak Telling.
- De knop maakt dezelfde planning als Maak Telling (`maakPlanning()`, nu een
  aparte functie) en zet die in een link. Er gaat niets naar de server.
- Een venster toont app, aantal wegen en grootte. Knoppen:
  - *Kopieer link*: via het klembord, met als terugval selecteren en
    `execCommand`;
  - *Delen…*: alleen als de browser `navigator.share` heeft;
  - *Openen ↗*.
- Uitleg in het venster: de planning gaat niet via de server, en open de link
  in Safari of Chrome.
- Boven 6000 tekens een waarschuwing in het rood. De link wordt wel gemaakt.
- **Teltype** heeft een derde keuze: *Pocket-parkeren (bezet/leeg, telefoon in
  de zak)*, waarde `pocket`.
  - Een hertelling van een pocket-ZIP zet het teltype nu op pocket.
  - *Opdrachten* toont het label *Pocket-parkeren* (paars).
  - Een pocket-opdracht van de server start als
    `pocket_count.html?plan=/planningen/…#parkeren`.
  - `TELAPP_MAP` is vervangen door `PLANLINK_APP` uit het gedeelde blok: één
    lijst voor link en server.

**Het linkformaat.**
- De drie vormen:
  - `parkeertelling.html#plan=1.<data>`
  - `fietsparkeren.html#plan=1.<data>`
  - `pocket_count.html#parkeren&plan=1.<data>`
- `<data>` = base64url(deflate-raw(JSON)), zonder opvulling.
- De JSON is `{n, d, t, c, y, w: [[osm_way_id, naam, highway, lijn]]}`.
- De lijn is een polyline (Google-codering, 1e5, ±1 m).
- Achter het `#`, omdat een browser dat deel niet naar de server stuurt.
- De `1` is de versie van het formaat. Een andere versie geeft *de link komt uit
  een nieuwere versie*.
- Een punt of haakje dat een mailprogramma achter de link plakt, wordt genegeerd.
- Inpakken en uitpakken met de ingebouwde `CompressionStream`. Die zit in
  Safari vanaf 16.4, net als het schermslot dat pocket al gebruikt.
- Uitpakken levert hetzelfde object als de JSON van de server (`geometrie_wkt`
  weer als `LINESTRING (lon lat, …)`, 5 decimalen). Daardoor kon de laadcode
  van de apps blijven zoals hij was.

**Gedeeld blok `planlink`.**
- Het blok staat byte-identiek in vier bestanden: telplanning, parkeertelling,
  fietsparkeren en pocket.
- `valideer.py` bewaakt dat met een nieuwe md5-groep, de zeventiende.
- Ankers: `/* ── Planning als link (v3.14) ──` … `/* ── einde gedeeld blok planlink ── */`.
- Functies:
  - `planlinkInpakken`, `planlinkUitpakken`, `planlinkUitHash`, `planlinkUrl`;
  - de polyline heen en terug;
  - `planlinkWktCoords`;
  - base64url;
  - `PLANLINK_APP`, `PLANLINK_LANG` (6000), `PLANLINK_VERSIE`.

**Parkeertelling en fietsparkeren.**
- `loadPlanFromUrl` leest nu ook `#plan=`. Staan zowel `?plan=` als `#plan=`
  in de link, dan gaat de link voor.
- Een fout komt als leesbare zin in de statusregel, bijvoorbeeld *Opdracht
  laden mislukt: de link is beschadigd of afgebroken*.
- Na herladen staat de planning er weer, want het `#`-deel blijft in de adresbalk.

**Pocket-parkeren.**
- De directe ingang herkent `#parkeren` ook als er `&plan=…` achter staat. Dat
  geldt zowel in de `<head>` als in `directeModus`.
- `laadPkPlanning()` draait bij het laden, met of zonder directe ingang. Het
  leest de link of `?plan=` van de server.
- Boven de vier telvakken staat een regel *Opdracht: <naam> · n straten · zie
  Kaart*, in lichtpaars. Bij een fout staat er in het oranje *⚠ Opdracht niet
  geladen: <reden>*. Zonder planning is er geen regel.
- De *Kaart* tekent de geplande straten in paars (`#8e44ad`, 55%), onder route en
  tikken. Het kaartbeeld omvat ze, dus je ziet het gebied al vóór je eerste stap.
  In de legenda staat dan *gepland*.
- In de ZIP komt niets van de planning. Na opslaan begint de directe ingang een
  nieuwe telling met dezelfde planning: de pagina laadt niet opnieuw.

**Documentatie.**
- **Handleiding:**
  - nieuwe sectie *Planning als link* bij Telplanning, met de valkuil van de
    ingebouwde browser (Gmail-app, WhatsApp) en de lengte;
  - het teltype bij Maak Telling;
  - Pocket bij *Opdrachten*;
  - een verwijzing bij Pocket → Parkeren.
- **Privacyverklaring:** een planning via de link komt niet op de server, maar
  gaat wel langs de mail of app (NL en EN).
- **ZIP-referentie:** sectie *Planning link (telplanning → field apps)*.
- **README:** telplanning-regel; voor een link is geen PHP nodig.

## 2. Wat niet

- **Een planning terug inladen in telplanning** om hem aan te passen. De
  gedownloade JSON kan nog steeds nergens worden ingeladen. Dat staat op de
  backlog bij *Planningen zonder server*.
- **De server-route weghalen.** *Maak Telling* schrijft nog naar de server en
  *Opdrachten* blijft werken. Weghalen is Jay's besluit (backlog).
- **Detectie van een ingebouwde browser.** Die is niet betrouwbaar: WhatsApp
  gebruikt SFSafariViewController, en dat is van buiten niet te onderscheiden
  van Safari. Daarom staat de waarschuwing in het venster van telplanning en in
  de handleiding, en niet als melding in de app. In het eerdere voorstel stond
  nog "een regel in de app bij een link-start". Die is vervallen, omdat de app
  hem bij elke link zou moeten tonen.
- **Mail-knop.** Een `mailto:` met een link van 2 kB of meer wordt op Windows
  door sommige programma's afgekapt. Daarom zijn er *Kopieer link* en *Delen…*
  (op Windows Chrome/Edge opent dat het deelmenu van Windows, met Mail en
  Outlook).

## 3. Tests

`functest_planlink.js` (nieuw, 29 tests, Node 18+, geen modules):
- A. het blok staat gelijk in alle vier de bestanden;
- B. heen en terug: alle velden, namen met `&`, `#`, `'` en `é`, coördinaten
  binnen 1 m, ook ten westen van Greenwich, en een lege planning;
- C. de polyline tegen het voorbeeld van Google;
- D. de link per teltype, telplanning in een submap, en het `#`-deel lezen;
- E. kapotte links:
  - afgebroken;
  - onzin;
  - zonder versie;
  - versie 2;
  - met een punt erachter;
- F. de lengte van een wijk van 40 straten: 2141 tekens.

`planlinktest.py` (nieuw, 42 tests, Chromium):
- A. telplanning:
  - de knop uit en aan;
  - de link per teltype;
  - het venster (info, Openen);
  - Kopieer naar het klembord;
  - Delen verborgen zonder `navigator.share`;
  - de waarschuwing bij een te groot gebied;
- B. parkeertelling en fietsparkeren:
  - paarse wegen en de teller ingevuld;
  - de planning blijft na herladen;
  - een kapotte link geeft een melding;
- C. pocket:
  - meteen het parkeerscherm;
  - de regel met de opdracht;
  - 11 paarse straten en de legenda;
  - tellen en Stop leveren een ZIP;
  - zonder planning geen regel en geen legenda;
  - een kapotte link geeft de reden;
- D. de server-route voor parkeertelling en pocket, en *Opdrachten* bouwt
  `?plan=…#parkeren`.

Bekeken in Chromium: het venster in telplanning, het parkeerscherm van pocket
met de regel, en de *Kaart* met de paarse straten en *gepland* in de legenda.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | blok `planlink`; `maakPlanning`; knop en venster *Deel als link*; teltype pocket; `TELTYPE_LABEL`, `startOpdracht` met `PLANLINK_APP`; hertelling van pocket |
| `parkeertelling.html`, `fietsparkeren.html` | blok `planlink`; `loadPlanFromUrl` leest ook `#plan=` |
| `pocket_count.html` | blok `planlink`; `#parkeren&plan=`; `laadPkPlanning`, `toonPkPlanning`; regel `#pk-plan`; paars op de Kaart, legenda *gepland* |
| `traffic_counter_help.html` | sectie *Planning als link*; teltype; Opdrachten; verwijzing bij Pocket → Parkeren |
| `privacy.html` | planning via de link niet op de server (NL/EN) |
| `zip_format_reference.html` | het linkformaat |
| `index.html` | versie v3.14 |
| `README.md` | telplanning; geen PHP nodig voor een link |
| `_archief/overpass_rig/functest_planlink.js`, `planlinktest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt; groep `planlink` |

## 5. Validatie

```
valideer.py           ALLES OK — 8 verwachte bestanden gewijzigd; groep planlink (4 bestanden) OK,
                      andere gedeelde blokken ongemoeid en OK
functest_planlink.js  29/29 (nieuw)
planlinktest.py       42/42 (nieuw)
laadtest.py           47/47
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
