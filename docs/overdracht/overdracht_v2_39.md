# TrafficCounterSuite v2.39 — Overdracht

Twee kleine bijstellingen in pocket parkeren (audio + kaart), op verzoek van Jay. Alleen `pocket_count.html` wijzigt; de rest byte-identiek aan v2.38.

## Wijzigingen

1. **Tik-toon per status.** De klik bij een tik was één toon (1100 Hz) voor alles; nu klinkt bezet en vrij verschillend, zodat je zonder te kijken hoort wat je registreerde:
   - **bezet → 440 Hz** (A, hoger)
   - **vrij/leeg → 392 Hz** (G, lager)
   Duur iets verlengd (0.03 → 0.05 s) zodat het toonverschil A/G goed hoorbaar is. De 'ongedaan'-toon (560 Hz) blijft ongewijzigd, en zit qua toonhoogte boven beide tik-tonen — dus goed te onderscheiden.

2. **Witte stip-rand dunner.** Op de dekkingskaart had elke stip een rand van 2.5 px. De witte rand (links) at relatief veel van de vulkleur; die is nu 1.5 px, zodat meer kleur zichtbaar blijft. De donkere rand (rechts) blijft 2.5 px voor contrast — de asymmetrie compenseert dat wit visueel dominanter is dan donker.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- Geverifieerd: tik-toon afhankelijk van status (440/392), witte rand 1.5 / donkere 2.5, undo-toon ongewijzigd (560).
- **Byte-identiteit:** t.o.v. v2.38 wijzigde uitsluitend `pocket_count.html`.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen naar de andere tel-modi als het bevalt.
- Eventueel zijde-offset op de stippen (links/rechts uit elkaar trekken).
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
