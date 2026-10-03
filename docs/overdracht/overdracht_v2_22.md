# TrafficCounterSuite v2.22 — Overdracht

Deze release **unificeert** de pocket-weergave in telrapport op één maat en voegt een **globaal modusfilter** toe. Het dag×uur-weekprofiel — dat meer inzicht gaf dan de v2.21-inventarisweergave — is terug voor **alle vier** de pocket-modi (transect, parkeren, winkelstraat, simpel), op de gedeelde **p/m·u**-maat (passages per meter per uur).

Dit **vervangt de Fase A-kaartsplitsing van v2.21** (de aparte paarse census-dichtheidsladder en de flux/census-popup-splitsing). In plaats van uiteenlopende grootheden per soort: één consistente, filterbare maat. Reden dat dit eerlijk blijft: een *tempo-maat pool't vanzelf goed* — teller (tikken) en noemer (aanwezigheidstijd) schalen samen, dus twee inventarisaties van dezelfde straat geven exact dezelfde waarde als één. Geen dubbeltelling, en dezelfde tijd-gewogen formule voor élke modus.

**Weergave-eenheid.** In de tussenversie schaalden we p/m·u ×100 naar "aantal per 100 m·u". Dat is teruggedraaid: bij deze data zitten de p/m·u-waarden al netjes in de tientallen (Druk ≈ 60, Zeer druk ≈ 100), en ×100 (6000/10000) las juist onprettig. De weergave is dus weer **p/m·u**.

Omdat de unificatie de v2.21-splitsing terugdraait, is telrapport **schoon vanaf de v2.20-basis herbouwd** (niet "de splitsing weer uitgekleed"), zodat er één strak pocket-pad staat. De reconstructor is niet aangeraakt.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `telrapport.html` | ✦ herbouwd vanaf v2.20-basis + unificatie | (A) **globaal modusfilter** in de 'Tonen'-groep (`toggles-modus` + `MODUS_META` + `actieveModi` + `pocketZichtbaar`); `wayHeat`, `pmuForKey`, `buildWeeklyHeatmap`, `renderSegmentSessionTable`, `renderSegmentBreakdown`, `showWegvakDetail` en `updateStats` volgen het filter; (B) `%bezet`-regel in de categorie-uitsplitsing (parkeren = census-mét-toestand); (C) `openWeekprofile` retourneert nu boolean + onthoudt `laatsteWegvakKey`, zodat een open popup live meeschakelt met het filter. Weergave blijft **p/m·u** (de tussentijdse ×100-schaling is teruggedraaid); `INTENSITEIT`-klassen en auto/fiets-`heatColor` ongewijzigd |
| `traffic_counter_help.html` | ✦ bijgewerkt | (D) `Vernieuwd (v2.22)`-alinea: alle 4 modi op de p/m·u-maat, pooling-argument, modusfilter, en de parkeer-nuance (per-uur = survey-intensiteit; `%bezet` = eerlijke bezetting) |

Ongewijzigd (byte-identiek t.o.v. v2.20): `parkeer_reconstructie.html` en alle overige HTML/CSV/py/planningen/_archief.

**Geen schema-wijziging.** Uitsluitend de interpretatie-laag (telrapport). Geen nieuwe CSV-velden, geen KNIME-sign-off nodig.

---

## Deel 1 — Eén maat: p/m·u voor alle modi

**Wat.** Elke pocket-waarde (roostercel, rij/kolom-totaal, sessietabel, categorie-uitsplitsing, legenda) wordt getoond in **p/m·u** (passages per meter per uur) — dezelfde vertrouwde maat, nu voor álle vier de modi. De klassegrenzen blijven leesbaar: Rustig 0–10, Matig 10–30, Druk 30–60, Zeer druk 60–100, Extreem 100+.

**Hoe.** `pmuForKey`, `buildWeeklyHeatmap` en de sessietabel rekenen in p/m·u; kleur en klasse-label komen uit `intensityClass(pmu)` op de ongewijzigde `INTENSITEIT`-drempels. (Een tussenversie schaalde de weergave ×100 naar "aantal per 100 m·u"; dat is teruggedraaid omdat de p/m·u-magnitudes bij deze data al prettig lezen en ×100 → 6000/10000 juist niet.)

**Pooling-eigenschap.** Omdat de waarde een *rate* is, is-ie invariant voor herhaalde bezoeken: `Σtikken / (lengte × Σtijd)` — teller en noemer schalen samen. Daardoor is de tijd-gewogen som-pooling (die het weekprofiel al deed) correct voor álle modi; er is geen apart gemiddeld-poolen nodig zoals in de v2.21-census.

---

## Deel 2 — Globaal modusfilter

**Wat.** In de 'Tonen'-groep verschijnt een knop per aanwezige pocket-modus (kleur + label uit `MODUS_META`), standaard actief. Uitschakelen verbergt die modus overal: **kaart, popups én stats volgen**. Zo bekijk je bijvoorbeeld alleen de winkelstraat-tellingen.

**Hoe.** Eén predikaat draagt het filter:
```
pocketZichtbaar(sid) = sessie zichtbaar && (niet-pocket || modusActief(modus))
```
Dat vervangt de kale `sessions[sid].visible`-check in alle pocket-rekenpaden (`wayHeat`, `pmuForKey`, `buildWeeklyHeatmap`, `renderSegmentSessionTable`, `renderSegmentBreakdown`, `showWegvakDetail`, `updateStats`). Voor niet-pocket sessies geeft het predikaat gewoon `visible` terug, dus fiets/auto/capaciteit blijven onaangeroerd.

**UI.** `buildModusToggles()` bouwt de knoppenrij idempotent (herbouwt alleen bij een gewijzigde modi-set; anders synchroniseert het de active-status). Een klik toggelt `actieveModi[modus]` en roept `onModusFilterChange()` → `recolorAll()` + `updateStats()` + (als de popup open staat) een live re-render van het weekprofiel via `laatsteWegvakKey`.

---

## Deel 3 — %bezet blijft de eerlijke parkeermaat

De categorie-uitsplitsing toont per categorie de p/m·u-rate. Dragen de categorieën een bezet/leeg-toestand (parkeren), dan verschijnt een **bezettingsgraad**-regel: `bezet / (bezet+leeg)` — een ratio, dus invariant onder de pooling. Dit is bewust apart gehouden: *per uur* weerspiegelt bij een statische toestand hoe lang je liep (survey-intensiteit), terwijl `%bezet` de werkelijke bezetting is. De nuance staat ook in de help.

---

## Validatie

- **`node --check`** schoon op de inline-JS van telrapport, reconstructie en help.
- **HTML-tagbalans** schoon op alle drie.
- **Byte-identiteit:** t.o.v. pristine v2.19 verschillen exact drie bestanden (help, reconstructie, telrapport); `parkeer_reconstructie.html` is byte-identiek aan v2.20; sinds v2.20 wijzigden alleen telrapport + help.
- **Functionele Node-sandbox-test:**
  - *Modusfilter isoleert* (segment met transect 60 tik/360 s en winkelstraat 10 tik/360 s): alle modi → **8,06** p/m·u; alleen transect → **13,8**; alleen winkelstraat → **2,3**. Elk exact de verwachte deelverzameling — het filter rekent aantoonbaar alleen over de actieve modi.
  - *Weergave p/m·u:* parkeer-segment (20 tik/240 s, ~43,4 m) → categorie-uitsplitsing toont bezet **4,8** / leeg **2,1** / Σ **6,9** p/m·u — leesbare magnitudes (niet ×100).
  - *%bezet:* parkeren bezet 14 / leeg 6 → **70 %**.

---

## Backlog / op de horizon

- **Parkeren uit pocket halen (wens, nog niet ingepland).** De parkeer-pocket-telling (`modus=parkeren`) wordt op termijn uit `app_type=pocket` gehaald en een **eigen, aparte modus/tool**. Reden: parkeren meet een *toestand* (bezet/leeg-bezetting), geen *stroom* — het past niet natuurlijk in de gedeelde pocket-p/m·u-lens. Dit is een richtingsbesluit, geen bouwbesluit; tot die splitsing draait parkeren mee in pocket, met `%bezet` als eerlijke bezettingsmaat in de detailregel en p/m·u als survey-intensiteit. Bij het uitsplitsen: schema-impact op KNIME nalopen (nieuwe/aparte outputs vs. discriminator-kolom).
- **%bezet per dag×uur-cel** voor parkeren (bezetting over de tijd) — het mooiste parkeerinzicht, maar vraagt tik-met-tijd-én-categorie in telrapport (nieuwe CSV → schema → KNIME-sign-off). Nu toont het parkeer-rooster p/m·u (survey-intensiteit) en staat `%bezet` in de detailregel.
- **Modus-iconen/labels in de sessielijst** (visuele aankleding per modus).
- **Vaste drempels** blijven relevant: de `INTENSITEIT`-klassen (in p/m·u) zijn gekalibreerd op voetgangers-transect; herijken zodra veldbrede verdelingen per modus bekend zijn.
- Staand: `zip_format_reference.html` recon-ZIP-sectie; browserbevestiging op echte recon-ZIP's; `fetch_fail`-trace + sequence-guard in pocket; snap/richting-port naar `pocket_count.html`; `gebiedsnaam` in `_sessie.csv` (KNIME).
