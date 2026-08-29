# TrafficCounterSuite v2.21 — Overdracht

Deze release brengt **view-model per modus** in telrapport — **Fase A** (kaart + popup). De aanleiding: pocket-tellingen zijn geen variant van één meting maar verschillende **meet-ontologieën**, en één p/m·u-lens over alles gaf oneerlijke uitkomsten. Vanaf nu dispatcht telrapport per **soort**:

- **flux** (transect) — een *stroom* dóór een dwarsdoorsnede. p/m·u, tijd-genormaliseerd, richting, dag×uur-weekprofiel. Ongewijzigd gedrag; dit was en blijft correct.
- **census** (parkeren/winkelstraat/simpel) — een *inventaris* langs de link. Tellingen, **niet** door presence-tijd gedeeld; dichtheid per 100 m; gepoold als **gemiddelde** over sessies. Parkeren = census-mét-toestand (krijgt een bezettingsgraad-regel).

De vaste-observatie-tools (auto, fiets) houden hun eigen, al correcte view. Alles additief; byte-identiteit bewaakt op alle ongewijzigde bestanden. **Sinds v2.20 is alleen `telrapport.html` inhoudelijk gewijzigd**, plus één eerlijkheidszin in de help. De reconstructor is niet aangeraakt.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `telrapport.html` | ✦ bijgewerkt | (A) view-model-registry `SOORT_VAN_MODUS` + helpers (`modusVan`, `soortVanPocket`, `censusSessiesOp`, `censusDensForKey`, `soortenOpSegment`, `dominanteSoort`, `CENSUS_RAMP`, `maxCensusDens`); (B) `pmuForKey`/`buildWeeklyHeatmap`/`renderSegmentSessionTable`/`renderSegmentBreakdown` kregen een optionele `sidOK`-predicaat zodat flux alleen over flux-sessies rekent; (C) `wayHeat` pocket-tak dispatcht op dominante soort; (D) `recolorAll` berekent `maxCensusDens`; (E) `openWeekprofile` verbouwd tot verdeler (`renderFluxSectie` + `renderCensusSectie`, retourneert boolean); (F) nieuwe census-renderers `renderCensusSectie`/`renderCensusBreakdown`/`renderCensusSessionTable`; (G) legenda-HTML gesplitst (flux p/m·u + census-dichtheid) + toon/verberg op `hasFluxPocket`/`hasCensusPocket`; (H) `.soort-kop`- en `.census-bar`-CSS; (I) knop `Toon weekprofiel ›` → `Toon detail ›` |
| `traffic_counter_help.html` | ✦ bijgewerkt | (J) één `Let op (v2.21)`-alinea in de weekprofiel-sectie: de popup is nu modus-bewust (p/m·u hoort bij transect; census-modi openen een inventaris-view) |

Ongewijzigd (byte-identiek t.o.v. v2.20): `parkeer_reconstructie.html`, `pocket_count.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `traffic_counter.html`, `telplanning.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `README.md`, `winkelstraat_rekenrig.html`, `build_bezocht.py`, `planningen/*`, `_archief/*` en alle eerdere overdrachten.

**Geen schema-wijziging.** v2.21 raakt uitsluitend de interpretatie-laag (telrapport). Geen nieuwe CSV-velden, geen KNIME-sign-off nodig. De `reconstructie`-vlag blijft op `v2.20` (telrapport gebruikt 'm alleen op waarheid).

---

## Deel 1 — De view-model-registry (het fundament)

**Aanleiding.** Binnen `app_type=pocket` leven vier modi met wezenlijk verschillende grootheden. Een transect meet een *stroom* (p/m·u is correct: normaliseren voor duur én lengte maakt metingen vergelijkbaar). Een winkelstraat- of simpel-inventaris meet een *voorraad* — die door tijd delen is een categoriefout. Parkeren is een voorraad-mét-toestand (bezet/leeg). Deze release codeert dat verschil expliciet.

**Registry, gespiegeld aan `PROFIELEN`.** De reconstructor dispatcht al per profiel; telrapport doet dat nu stroomafwaarts:

```
const SOORT_VAN_MODUS = { transect:'flux', parkeren:'census', winkelstraat:'census', simpel:'census' };
```

`modusVan(sid)` leest `sessions[sid].meta.modus`; er hoefde niets aan de dataplumbing te veranderen. `soortVanPocket(sid)` mapt modus → soort.

**Legacy-gedrag bewaard.** Een blanco/onbekende modus (oude pocket-ZIP zonder `modus`-veld) → **flux**. Zo houden bestaande ZIP's exact hun huidige p/m·u-weergave; geen stille herinterpretatie van oude data. Nieuwe (2.20+) ZIP's dragen wél een modus en krijgen daarmee vanzelf de juiste view.

---

## Deel 2 — Kaart: dispatch op dominante soort

**`wayHeat` pocket-tak.** Per segment bepaalt `dominanteSoort(key)` (meeste tikken over de zichtbare pocket-sessies) welke grammatica de lijnkleur krijgt:
- **flux** → p/m·u via `pmuForKey(key, fluxOK)` — nu gefilterd op **uitsluitend flux-sessies**, zodat census-visits een gemengd segment niet vervuilen. Kleur via de bestaande `intensityClass` (blauw→rood).
- **census** → dichtheid per 100 m via `censusDensForKey(key)`, gekleurd op een **eigen sequentiële ladder** (`CENSUS_RAMP`, paars licht→diep). Losgekoppeld van de divergerende p/m·u-ladder zodat het oog census-dichtheid niet tegen flux-tempo afleest.

**Gemengd segment** (bv. transect én winkelstraat op dezelfde straat): de dominante soort kleurt de lijn; de popup splitst beide (zie Deel 3). Dit is de door jou gekozen regel.

**Relatieve census-schaal.** `recolorAll` berekent `maxCensusDens` over alle zichtbare census-segmenten (analoog aan `maxFietsTotaal`); de ladder normaliseert daarop. Bewust relatief — geen verzonnen absolute drempels tot veldkennis ze rechtvaardigt (Fase B).

---

## Deel 3 — Popup: verdeler per soort

**`openWeekprofile` is nu een verdeler** en retourneert een boolean (`true` als er iets getoond is). Hij verzamelt de soorten op het segment en rendert per aanwezige soort een sectie:
- **`renderFluxSectie`** — het bestaande weekprofiel (hm-meta + warmtekaart + sessietabel + categorie-uitsplitsing), maar overal gefilterd op flux-sessies via `sidOK`.
- **`renderCensusSectie`** — nieuw. Een inventaris-uitleg + `renderCensusBreakdown` + `renderCensusSessionTable`.

Bij een gemengd segment krijgen beide een `.soort-kop`-kop ("Flux — transect", "Census — winkelstraat"). `showWegvakDetail` gebruikt `if (openWeekprofile(key)) return;` — bij een leeg resultaat valt hij netjes terug op het gewone paneel.

**Census-uitsplitsing (`renderCensusBreakdown`).** Per (categorie × richting) het **gemiddelde** aantal over de census-sessies, plus dichtheid per 100 m. De richting-kolom verschijnt adaptief (alleen bij transect-achtige data; census heeft 'm meestal niet). Draagt een categorie een bezet/leeg-toestand, dan verschijnt een **bezettingsgraad**-regel (`bezet / (bezet+leeg)`, een ratio die invariant is onder de poolkeuze).

**Census-sessietabel (`renderCensusSessionTable`).** Per sessie datum, aantal en per-100 m. De sluitregel is bewust een **`gem.`** (gemiddelde) — geen `∑` — want een inventaris telt niet op over herhaalde bezoeken.

---

## Deel 4 — Legenda gesplitst

De pocket-legenda splitst op soort: `legend-pocket` ("Voetganger flux (transect) – p/m·u", de intensiteitsklassen) toont bij `hasFluxPocket`; een nieuw blok `legend-census` ("Census … – dichtheid", paarse gradient + `0 … N /100m`) toont bij `hasCensusPocket`. Beide worden afgeleid uit `soortVanPocket` over de geladen pocket-sids. Zo is elke kleur op de kaart decodeerbaar — een kaart met onverklaarde kleuren is een bug, geen politoer, dus deze minimale legenda hoort in Fase A.

---

## Het ene ontwerpoordeel — bevestigen a.u.b.

**Census pool't als gemiddelde, niet als som.** Twee inventarisaties van dezelfde straat tellen dezelfde winkels twee keer; optellen dubbeltelt. Daarom is de census-dichtheid (én de breakdown, én de sessietabel-sluitregel) het **gemiddelde** over de sessies die het segment aandeden. Flux blijft som+normaliseren (meer observatietijd = meer passages, en p/m·u haalt dat er weer uit). Dit is de enige semantische keuze die ik zelf heb gemaakt; als jouw domein-intentie anders is (bv. "laatste inventaris telt" of "max"), is het één regel in `censusDensForKey` + `renderCensusBreakdown`. Zeg het en ik pas het aan.

*Noot:* bij niet-herhaalde segmenten (één inventaris) is gemiddelde = som = de enkele waarde, dus het verschil bijt alleen bij een echte her-inventarisatie — en daar is het gemiddelde het juiste.

---

## Validatie

- **`node --check`** schoon op de inline-JS van alle drie de geraakte bestanden.
- **HTML-tagbalans** schoon (Python-parser, scripts/styles gestript) op alle drie.
- **Byte-identiteit:** t.o.v. pristine v2.19 verschillen exact drie bestanden (help, reconstructie, telrapport); sinds v2.20 verschilt alleen `telrapport.html` (reconstructie byte-identiek aan 2.20).
- **Functionele Node-sandbox-test (census-rekenkern):** winkelstraat, 2 sessies (30 en 34 winkels, ~43,4 m) → `censusDens` = 73,71 = gemiddelde 32 / 43,4 × 100 (gemiddeld gepoold, **niet** de som 64). Breakdown: kledingzaak gem. 19 (= (18+20)/2), horeca gem. 13 — niet 38/26. Sessietabel sluit met `gem. 32`. Parkeren (bezet 14 / leeg 6) → bezettingsgraad **70 %**, "gem. 14 van 20 plekken bezet". Alle waarden correct.
- **Legenda-logica** coherent: flux → p/m·u-legenda, census → dichtheidsladder, elk op eigen aanwezigheid.

---

## Fase B — backlog (politoer, bewust uitgesteld)

- **%bezet-headline** verfijnen (nu een regel onder de census-breakdown; kan prominenter voor parkeren).
- **Vaste census-drempels** i.p.v. de relatieve schaal, zodra echte data de verdeling toont; gepolijste legenda-schaal met vaste swatches.
- **Sessielijst-iconen/labels per modus** (de session-list dispatcht al op modus sinds 2.19; nu nog visueel aankleden per soort).
- **Gemengde-segmenten visuele afwerking** (bv. een subtiele split-indicatie op de lijn i.p.v. alleen dominante kleur).
- **Zero-inventaris-segmenten** (census-sessie die een segment beliep maar 0 telde) — nu buiten `censusSessiesOp` (die vereist totaal > 0); overweeg expliciete "0 geteld"-weergave.

## Buiten deze release (staand)

- `zip_format_reference.html`: recon-ZIP-sectie (incl. `_segmentsamenvatting.csv`) nog te documenteren.
- Browser-bevestiging van de v2.20-popup + census-view op echte transect/winkelstraat-recon-ZIP's, en dat `_segmentsamenvatting.csv` in een echt veld-`_recon.zip` belandt.
- Pocket live-verbeteringen: `fetch_fail`-trace-events + sequence-guard tegen out-of-order fetch die `cacheLat/Lon` overschrijft.
- Snap/richting-werk: stall→reset + temporele time-gate porten naar `pocket_count.html` na de resterende testwandelingen; richting-laag (sliding-window-regressie) — beide nog geen bouwbeslissing.
- `gebiedsnaam` in `_sessie.csv` (wacht op KNIME-sign-off); bezettingsgraad-herberekening voor auto (wacht op parkeertelling-rebuild).
