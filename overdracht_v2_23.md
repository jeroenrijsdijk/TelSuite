# TrafficCounterSuite v2.23 — Overdracht

Deze release voegt **handmatige link-correctie** toe aan `parkeer_reconstructie.html`. Aanleiding: bij een kruising snappen sommige tikken haaks op de dwarslink i.p.v. de gelopen link — de trajectorie-Viterbi kiest de way die op dat event het dichtst bij ligt, terwijl de route (oranje) rechtdoor loopt. In het veldvoorbeeld stonden vier tikken op de Nieuwstraat i.p.v. de verticaal belopen link. De tool telde zulke gevallen al (`linkGewijzigd`), maar liet ze niet corrigeren.

Gekozen aanpak (na overleg): **jij kiest de juiste link.** In correctiemodus markeer je de foute stippen, klik je de juiste blauwe way, en herberekent de tool way + segment + richting + markerplaatsing voor precies díe tikken — via dezelfde bouwstenen als de reconstructie, zodat het resultaat consistent is met de rest.

Alleen `parkeer_reconstructie.html` is gewijzigd; `telrapport.html` en de help zijn byte-identiek aan v2.22.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `parkeer_reconstructie.html` | ✦ bijgewerkt | Handmatige link-correctie: (A) reconstructie-state (`netMatch`, `segCount`, `reconEvents`, `timeline`, `dirs`) gehoist naar `S` voor hergebruik; (B) `tekenKaart` — ways klikbaar met per-wayId-referenties (`S.wayLines`), stippen klikbaar met markeerstijl, `behoudView`-parameter zodat een correctie niet herzoomt; (C) correctie-module (`toggleCorrModus`, `markeerTik`, `kiesDoelWay`, `herberekenSelectie`, `herberekenEenTik`, `segIdxOp`, `dirVoorWayOpTijd`, `corrStijl`, `wisCorrectie`, `tekenCorrPaneel`, `naamVanWay`); (D) `recon_status='handmatig'` voor gecorrigeerde tikken (via `tp.reconOverride` in alle vier de `telRij`'s — rendering-status blijft `'ok'`); (E) HTML: sectie **Link-correctie** in het resultaatblok |

Ongewijzigd (byte-identiek t.o.v. v2.22): `telrapport.html`, `traffic_counter_help.html` en alle overige bestanden.

**Schema:** additief. Enige verandering is een nieuwe waarde `handmatig` in de bestaande `recon_status`-kolom. Kleine KNIME-check aanbevolen (nieuwe categoriewaarde), maar geen nieuw veld of nieuw bestand.

---

## Zo werkt de correctie

1. **Correctiemodus aan** (knop in het resultaatblok). De reeds-afwijkende tikken (`linkGewijzigd`) krijgen een oranje ring — kandidaten in één oogopslag.
2. **Markeer** de foute stippen (klik; meerdere mogelijk → gele ring).
3. **Klik de juiste blauwe link** (wordt rood gemarkeerd als doel). Het paneeltje toont "N tik(ken) → doel: way ⟨id⟩ (⟨straat⟩)".
4. **Herbereken.** Per gemarkeerde tik:
   - GPS-punt op de doel-way projecteren (`MATCHER.project`) → nieuw snap-punt;
   - `segIdx` op de doel-way (`segIdxOp`, spiegelt de matcher-`segIdxFor`);
   - richting uit de al berekende richtingslaag op díe way rond het tik-tijdstip (`dirVoorWayOpTijd` over `S.timeline`/`S.dirs`);
   - marker herplaatsen — profiel-afhankelijk (parkeren/car: 4 m offset naar de juiste zijde via `RECON.offsetPoint`; transect: op de link);
   - `recon_status='handmatig'`.
5. De aggregaten volgen: `herbouwBezocht` telt `n_tellingen` uit `tp.wayId`/`segIdx`, dus de verplaatste tik telt vanzelf op de nieuwe link. Kaart hertekent (view behouden). **Download de ZIP opnieuw** — de export leest de actuele `S.taps`/`bezocht`, dus de correctie zit erin.

---

## Validatie

- **`node --check`** schoon op de inline-JS; **HTML-tagbalans** schoon.
- **Byte-identiteit:** t.o.v. pristine v2.19 verschillen drie bestanden (help, reconstructie, telrapport); sinds v2.22 wijzigde alleen `parkeer_reconstructie.html`.
- **Integratietest (Node-sandbox):** kruising van een verticale (V) en horizontale (H) way; een tik fout op H, GPS bij de kruising. Na `herberekenEenTik(tp,'V')`: `wayId=V`, `segIdx=0`, `status=ok`, `recon_status(export)=handmatig`, `dir=1`, marker op de V-lijn (lon 5.00000). `herbouwBezocht` telt de tik daarna op V (`n_tellingen=1`) i.p.v. H. Bevestigd dat `netGeoLL` en `netMatch` dezelfde `osm_way_id`-sleutels gebruiken (klik-doel bestaat altijd in `netMatch`).

**Nog te doen (jij, in de browser):** de klik-interactie op een echte recon-ZIP bevestigen — markeren → juiste link klikken → herberekenen → controleren dat de vier stippen naar de gelopen link springen en dat de herschreven ZIP (`_bezocht.csv` + segment-samenvatting + telrij met `recon_status=handmatig`) klopt. De logica is unit-getest; de kaart-interactie zelf draait alleen in de browser.

---

## Aandachtspunten / grenzen

- **Randgeval:** als niet alleen de tik maar óók de GPS-route bij de kruising fout zat (geen bezoek-venster op de juiste way), dan verschuift de tik wél in telrij/segment-samenvatting maar niet in `n_tellingen` (geen venster om in te tellen). In het veldvoorbeeld loopt de route verticaal door, dus dat speelt daar niet.
- **Richting op de doel-way:** afgeleid uit de richtingslaag op díe way; liep de route nooit op de gekozen link, dan is de richting onzeker (offset-profielen → status `onzeker`).
- Correcties gelden op de huidige reconstructie; een verse fetch/herreconstructie draait opnieuw en zet ze terug (verwacht — correctie is een post-stap).

## Backlog (ongewijzigd meegenomen)

- **Parkeren uit pocket halen** (wens): parkeer-pocket-telling op termijn tot een aparte modus/tool maken (parkeren = toestand, geen stroom).
- %bezet per dag×uur-cel (vraagt tik-met-tijd-én-categorie → schema/KNIME).
- Overige staande punten uit v2.22 (zip_format_reference recon-sectie, fetch_fail-trace + sequence-guard, snap/richting-port naar pocket_count, gebiedsnaam in _sessie.csv).
