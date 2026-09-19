# Overdracht v2.49 — Overpass: minder vragen, en beter luisteren

Deze release raakt geen enkele telfunctie. Hij gaat over hoe de suite met de
Overpass-servers omgaat. Drie dingen:

1. **De tegel-cache wordt nu ook gelezen.** Sinds v2.43 schrijven de veld-apps
   hun opgehaalde netwerk in tegels, maar las alleen de reconstructor ze terug.
   Wie dezelfde straat voor de derde keer telde, haalde hem ook voor de derde
   keer op. Een gedekt gebied kost nu nul verzoeken.
2. **Antwoorden worden geclassificeerd.** Een gebied zónder wegen liet de app
   net zo hard opnieuw vragen als een netwerkstoring. En omdat Overpass bij
   overbelasting soms een HTTP 200 stuurt met de rate-limit-melding ín de body,
   zagen wij dat als "geen wegen" en dus als reden om meteen de andere mirror
   te proberen. Precies wanneer de servers vol zaten, sloegen wij er het hardst
   op.
3. **Eén backoff-model.** De drie parkeer-apps hadden nog een vaste retry van 5s
   zonder in-flight guard; pocket had sinds v2.18 exponentiële backoff mét
   guard. Dat is nu overal hetzelfde, met pocket als model.

---

## 1. Gewijzigde bestanden

| Bestand | Verschil | Wat |
|---|---|---|
| `parkeertelling.html` | +8.517 | OVP-blok, leesTegels, nieuwe fetch-discipline, `pasNetwerkToe()` |
| `fietsparkeren.html` | +8.517 | idem |
| `capaciteitstelling.html` | +8.516 | idem (eigen `pasNetwerkToe`, zie §5) |
| `pocket_count.html` | +7.895 | OVP-blok, leesTegels, `snapStartFetch()`, `snapVerwerkNetwerk()` |
| `telreconstructie.html` | +3.358 | OVP-blok, classificatie in `overpassFetch`, tegels met naam + schema |

Alle overige bestanden zijn byte-identiek aan v2.48. `telrapport.html`,
`snaptrace.html` en `zoekTerreinen` in capaciteitstelling zijn bewust niet
aangeraakt — zie §7.

---

## 2. Het gedeelde OVP-blok

Byte-identiek in vijf bestanden (`grep OVP_LIMIET`), md5 `43924522`. Het zit
direct onder de endpoint-lijst en leunt op het bestaande `dataIsVers()`.

Vijf uitkomsten van `ovpKeur(data)`:

| Uitkomst | Betekenis | Gedrag |
|---|---|---|
| `ok` | bruikbaar netwerk | verwerken |
| `leeg` | geldig antwoord, hier liggen geen wegen | accepteren, **niet** opnieuw vragen |
| `oud` | deze mirror loopt > `OSM_MAX_LAG_DAGEN` achter | andere mirror proberen |
| `limiet` | 429/503/504, of `rate_limited` in `data.remark` | 30s wachten, niets proberen |
| `fout` | netwerk-/HTTP-storing, runtime error in `remark` | exponentieel wachten |

De `remark`-controle is de belangrijkste toevoeging. Overpass legt runtime-
meldingen in dat veld bij een verder normale 200. Dat werd hiervoor als een lege
respons gelezen.

Nieuwe constanten: `OVP_LIMIET_WACHT_MS = 30000` en `OVP_OUD_WACHT_MS = 300000`.
`ovpBackoffMs(n)` is de formule van v2.18 (500·2ⁿ⁻¹, max 8s); `snapBackoffMs` in
pocket delegeert er nu naartoe, zodat de twee niet uit elkaar kunnen lopen.

**Bij een rate-limit gaan we niet meer door naar de tweede mirror.** Twee
redenen: Overpass voert de query eerst uit en meldt de limiet daarna, dus een
geweigerd verzoek kost de server evenveel als een geslaagd; en `private.coffee`
is een kleine vrijwilligersinstantie, die erbij halen terwijl de hoofdserver ons
afwijst is precies verkeerd.

---

## 3. De tegel-cache lezen

Byte-identiek in de vier veld-apps (`grep leesTegels`), md5 `034ba82b`.

**Alles-of-niets.** De fetch wordt alleen overgeslagen als *álle* tegels die de
fetch-cirkel raken aanwezig én vers zijn. Deelresultaten mengen we niet: een half
gedekte cirkel zou stil wegen missen, precies de fout die de schrijfkant met het
8×8-raster al vermijdt. `leesTegels()` geeft een lijst terug bij volledige
dekking (ook een lége lijst — dan weten we zeker dat hier geen wegen liggen) en
`null` bij een misser.

**TTL 14 dagen**, tegenover 60 dagen in de reconstructor. Bewust anders: daar
ziet de gebruiker de tegelouderdom in beeld en kan hij verversen, hier gebeurt
het stil. Stille veroudering verdient een strakkere grens, zeker naast de
verse-data-garantie van v2.48 (7 dagen). **Dit is een getal waar je het mee
oneens mag zijn** — het staat op één plek in het gedeelde blok.

**Schemaversie 2.** Tegels van vóór v2.49 dragen geen straatnaam; die zou dus
uit `_netwerk.csv` en uit de tik-regels verdwijnen bij een cache-hit. Daarom
tellen ze als misser: ze worden opnieuw opgehaald en meteen mét naam
teruggeschreven. Geen migratie, de cache geneest zichzelf. `cacheWaysInTiles`
schrijft nu `{ key, ts, v: 2, ways }` met `tags: { highway, name }`; de
reconstructor doet hetzelfde, zodat tegels in beide richtingen bruikbaar zijn.

---

## 4. Nieuwe fetch-discipline in de parkeer-apps

Byte-identiek over de drie (`grep startRoadFetch`), md5 `73890360`.

De keten is nu `scheduleRoadFetch` → `startRoadFetch` (in-flight guard,
afkoeling, tegel-cache) → `fetchRoads` (endpoints + classificatie) →
`pasNetwerkToe`. `RETRY_DELAY` is vervallen; `MAX_RETRIES = 4` betekent nog
steeds vier volledige rondes over alle endpoints, maar met oplopende wachttijd.

Wat dit in verzoeken scheelt, gemeten in de functionele test:

| Situatie | v2.48 | v2.49 |
|---|---|---|
| gebied zonder wegen | tot 10, elke 150 m opnieuw | 1 |
| rate-limit (429 of in body) | tot 10 | 1, dan 30s stil |
| beide mirrors verouderd | tot 10 | 2, dan 5 min stil |
| gebied al in de cache | 1 per 150 m | 0 |

---

## 5. Pocket

`snapStartFetch()` is nieuw en draagt nu de poort (in-flight guard, cooldown,
fid-toekenning) die eerst in `snapFetchNetwork` zat, want vóór het eerste
verzoek is er een goedkopere bron. `snapVerwerkNetwerk()` is het toepas-pad,
gedeeld door de fetch-route en de cache-route; alle v2.17/v2.18-garanties
(volgorde-guard, guard vrijgeven, backoff-teller) gelden daarmee ook voor de
cache. Een aanroep van `snapFetchNetwork` zonder `fid` wordt doorgestuurd naar
`snapStartFetch`, dus oude aanroepplekken blijven correct.

**De oneindige retry is weg.** Zolang er nog nooit een netwerk was
(`cacheLat === null`) bleef pocket bij "geen wegen" eindeloos doorvragen met
backoff. Nu is een leeg antwoord een geldig antwoord: `cacheLat` komt te staan,
`snap.ready` wordt gezet, en een tik krijgt eerlijk geen kandidaat in plaats van
eindeloos in de wachtrij te blijven.

**Uitzondering bij verouderde mirrors:** als álle mirrors achterlopen én we al
een werkend netwerk hebben, wachten we 5 minuten. Hebben we nog niets, dan geldt
de fataal-regel van v2.18 en blijven we het gewoon proberen. Verouderd nieuws is
dan beter dan niets.

---

## 6. Voor KNIME

Geen kolomwijziging, maar wel twee dingen in `snap_trace.csv`:

- `snap_path` bij een fetch-event begint nu met `bron:fetch|`, `bron:tegel|` of
  `bron:leeg|`, vóór het bestaande `n_el:…|n_kept:…|n_segs:…`.
- Twee nieuwe waarden in de `event`-kolom: `tegelcache` en `fetch_leeg`.

Beide kolommen zijn vrije tekst, dus formeel geen schemawijziging. Als een
KNIME-node op de exacte vorm van `snap_path` parst, moet die wel mee.

---

## 7. Bewust niet aangeraakt

- **`telrapport.html`.** Drie fetch-plekken: twee kale `fetch()` zonder
  mirror-fallback (r.1526, r.1751) en een `tryOverpass` die de endpoint-lijst
  twee keer inline als array-literal heeft staan. Het zijn alle drie
  ID-opzoekingen (`way(id:…);out geom;`) en dus makkelijk op het gedeelde blok
  te zetten, maar het is een bestand van 5.153 regels en deze release is al
  breed. Staat boven aan de backlog.
- **`zoekTerreinen` in capaciteitstelling.** Vuurt één verzoek per kaartpan
  (600ms debounce, geen dedup, geen cache). Dat is de zwaarste per-handeling
  fetcher in de suite. Ontdubbelen op afstand tot het vorige zoekcentrum is
  klein werk, maar het is een andere querysoort (`amenity=parking`) en een
  andere cache; hoort in een eigen stap.
- **`snaptrace.html`.** Interne rig, niet gelinkt.
- **De afwijking in `capaciteitstelling`'s `pasNetwerkToe`.** Die bouwt `segs`
  uit de vérse elementen, de andere twee uit de cumulatieve pool binnen
  `SNAP_SEGS_RADIUS`. Dat verschil bestond al vóór v2.49 en is nu netjes
  geïsoleerd in de per-app functie in plaats van verstopt in een gedeelde. Of
  het een bewuste keuze was of oude drift weet ik niet — dat is een vraag voor
  jou.

---

## 8. Validatie

```
JS-syntax (node --check, inline JS uit 15 bestanden)      15/15 OK
HTML-tagbalans, vergeleken met v2.48                      geen afwijking
byte-identiteit                                           precies 5 bestanden gewijzigd
gedeelde blokken byte-identiek:
  HIGHWAY_RE          6 bestanden   5f8ce229
  OVP-blok            5 bestanden   43924522
  leesTegels          4 bestanden   034ba82b
  fetch-discipline    3 bestanden   73890360
  cacheWaysInTiles    4 bestanden   098dfcc5
functionele test parkeertelling (node vm, nagebouwde IndexedDB + Overpass)
                                                          34/34 OK
functionele test pocket_count                             18/18 OK
```

De testharnassen staan in `_archief/overpass_rig/`. Ze knippen de blokken
rechtstreeks uit de HTML, dus ze blijven geldig zolang de ankercommentaren
staan — draai ze opnieuw na elke wijziging aan het gedeelde blok.

**Wat de tests niet dekken:** echte IndexedDB op iOS Safari, echt gedrag van
Overpass onder last, en de vraag of 14 dagen TTL in het veld prettig voelt. Dat
moet buiten.

---

## 9. Testen in het veld

1. **Herhaald gebied.** Loop een straat die je eerder deze maand hebt geteld. De
   snap-badge hoort meteen op groen te staan zonder "ophalen". Check daarna in
   `snap_trace.csv` of er `bron:tegel` in staat.
2. **Nieuw gebied.** Eerste ronde vult de cache, tweede ronde over dezelfde route
   hoort nul verzoeken te doen.
3. **Gebied zonder OSM-wegen** (havendijk, buitengebied). Hoort één keer te
   vragen en dan stil te blijven, in plaats van te blijven malen.
4. **Slecht bereik.** De backoff hoort op te lopen tot 8s en niet te ratelen.
5. Let op of straatnamen in `_netwerk.csv` compleet blijven — dat is de
   gevoeligste plek van de cache-route.

---

## 10. Backlog na deze release

**Klein / afgebakend**
- `telrapport.html` op het gedeelde OVP-blok (drie plekken, zie §7).
- `zoekTerreinen` ontdubbelen op zoekcentrum.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>`.
- Engelse variant van `over.html`.

**Meetkunde (vraagt veldtest, niet in deze release)**
- Fetch-radius en verversafstand losser zetten. Nu: radius 300 m, verversen op
  150 m, dus 69% van elke fetch is al bekend gebied. Radius 300 / verversen op
  220 m scheelt een derde van de verzoeken; radius 500 / verversen op 350 m
  halveert ze tegen 19% meer bytes. Voor Overpass tellen verzoeken zwaarder dan
  bytes.
- Gebied vooraf ophalen vanuit `telplanning.html`: je kent je gebied van tevoren,
  dus de cache kan gevuld zijn vóór je de deur uitgaat. Dan telt het veldwerk met
  nul verzoeken. Vraagt echt ontwerp.

**Uitrollen als het bevalt**
- Audio-feedback en dekkingskaart naar de andere tel-modi (wacht nog op jouw
  veldtest van v2.37–v2.41).

**Groter / vraagt ontwerp**
- Parkeren uit pocket halen naar een eigen modus/tool.
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport.
- %bezet per dag×uur-cel.
- QGIS-loader: optionele join op `_straten.csv` / `_bezocht.csv`.
