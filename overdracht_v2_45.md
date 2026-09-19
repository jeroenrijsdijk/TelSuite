# TrafficCounterSuite v2.45 — Overdracht

Twee dingen in één release: de reconstructie-uitleg in `over.html` herschreven naar gebruikerstaal, en **`parkeer_reconstructie.html` hernoemd naar `telreconstructie.html`** (inclusief alle verwijzingen). Negen bestanden gewijzigd t.o.v. v2.44 (waarvan één hernoemd).

---

## 1. Hernoeming → `telreconstructie.html`

De naam `parkeer_` was achterhaald: de tool reconstrueert allang ook loop-, transect- en winkelstraattellingen. De nieuwe naam sluit aan bij het `tel`-familiepatroon (`telplanning` → `telreconstructie` → `telrapport`).

**Bestand hernoemd**, plus **22 pad-verwijzingen** bijgewerkt over 7 bestanden:

| Bestand | Aard van de verwijzingen |
|---|---|
| `parkeertelling`, `fietsparkeren`, `capaciteitstelling` | elk 4×: cache-comment, handoff-comment, `location.href`-doel, foutmelding |
| `pocket_count` | 4×: idem |
| `over.html` | link "Open de reconstructie-tool" |
| `traffic_counter_help.html` | link in de Planning-kaart + Bestanden-lijst |
| `zip_format_reference.html` | 2× in de documentatietekst |

**Zichtbare naam** ook bijgewerkt (6 plekken): `<title>` en `<h1>` van de tool zelf → "Telreconstructie", de code-comment, de alt-tekst in `over.html`, en de link + beschrijving in de handleiding.

**Kritiek gecontroleerd:** de handoff-keten uit v2.43/v2.44 loopt via `location.href = 'telreconstructie.html?handoff=1'` — die is meegehernoemd, dus de "Direct reconstrueren"-knoppen blijven werken. Een link-integriteitscheck over alle HTML-bestanden meldt **geen dode links**.

> **Let op bij deployen:** dit hernoemt een bestand. Bestaande bladwijzers naar `parkeer_reconstructie.html` breken. Overweeg op de server een redirect van de oude naar de nieuwe naam.

## 2. Stap 2 in `over.html` in gebruikerstaal

De oude tekst beschreef het mechanisme ("herberekent de tikken aan de hand van de gps-route, kijkend naar de logica van de opeenvolgende linkjes"). De nieuwe legt uit wat de gebruiker ervan merkt, in drie korte alinea's:

1. **Het probleem** — GPS is een paar meter onnauwkeurig; bij een kruising of tussen hoge gebouwen kan een tik op de verkeerde straat belanden.
2. **Wat de reconstructie doet** — kijkt achteraf naar de hele wandeling in één keer, bepaalt daardoor veel beter welke straat je werkelijk liep, en zet elke tik alsnog goed. Voegt zijde en looprichting toe; blijft er iets fout staan, dan corrigeer je dat zelf op de kaart.
3. **Resultaat + geruststelling** — schonere kaart, beter kloppend rapport. Expliciet: *je telling zelf verandert niet* — het aantal blijft wat je geteld hebt, alleen de plaatsbepaling wordt nauwkeuriger.

Die laatste zin is bewust toegevoegd: "nabewerken" kan de indruk wekken dat er aan de cijfers gesleuteld wordt. Voor een tool waarop conclusies worden gebaseerd is dat precies de twijfel die je wegneemt.

Behouden: Jay's badge "warm aanbevolen", de screenshot-plek, de link naar de tool.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon op alle acht gewijzigde bestanden.
- **Link-integriteit:** elk `href="*.html"` én elke `location.href`-doel bestaat; geen dode links. `telreconstructie.html` aanwezig, `parkeer_reconstructie.html` weg.
- **Merk-sweep:** nul resterende treffers op `parkeer_reconstructie` of "Parkeer-reconstructie".
- **Byte-identiteit:** t.o.v. v2.44 wijzigden uitsluitend de hierboven genoemde bestanden.

## Backlog (bijgewerkt)

- ~~`parkeer_reconstructie.html` → `telreconstructie.html`~~ ✓ gedaan.
- Dekkingskaart / audio breder uitrollen naar de andere tel-modi.
- Overpass fallback-helper in `telrapport.html`; mirrornaam `overpass.kumi.systems` → `overpass.private.coffee`.
- `over.html`: `__volgt__`-placeholder invullen met de QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
