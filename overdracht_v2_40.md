# TrafficCounterSuite v2.40 — Overdracht

Lay-out-fix in pocket parkeren: de onderste drie knoppen (Terug · Kaart · Stop) overlapten elkaar — de gecentreerde Kaart-knop liep over de brede "Stop & Download". Opgelost met een flex-balk. Alleen `pocket_count.html` wijzigt; de rest byte-identiek aan v2.39.

## Wat & waarom

De drie knoppen stonden los, elk `position:fixed`: Terug links (14px), Stop rechts (14px), Kaart op schermmidden (`left:50%`). Omdat "■ Stop & Download" breed is, botste de gecentreerde Kaart-knop ertegen. Een vaste pixel-verschuiving zou op een andere schermbreedte weer misgaan.

**Fix:** de drie pk-knoppen in een **flex-balk** (`#pk-btnbar`, `justify-content: space-between`), in de volgorde Terug · Kaart · Stop. Ze verdelen zich nu over de breedte en kunnen niet meer overlappen, ongeacht het scherm. De pk-knoppen zijn iets compacter gemaakt (padding 11×13, font 0.75rem) zodat de drie op iPhone-breedte comfortabel passen.

De winkelstraat-knoppen (`#ws-back`/`#ws-stop`) delen de basis-CSS maar staan op een ander scherm met maar twee knoppen; die zijn bewust **ongemoeid** gelaten (behouden hun eigen fixed-positionering).

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- Geverifieerd: flex-balk aanwezig, volgorde Terug·Kaart·Stop, oude 50%-centrering van de Kaart-knop verwijderd, en de show/hide-JS stuurt de drie knoppen nog per id aan (geen JS-wijziging nodig).
- **Byte-identiteit:** t.o.v. v2.39 wijzigde uitsluitend `pocket_count.html`.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen naar de andere tel-modi als het bevalt; eventueel zijde-offset op de kaartstippen.
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
