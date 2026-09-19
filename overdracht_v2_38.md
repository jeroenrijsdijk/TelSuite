# TrafficCounterSuite v2.38 — Overdracht

**Dekkingskaart in pocket parkeren** — een uitklapkaart die laat zien waar je al geteld hebt, voor het systematisch tellen van grote wijken. Alleen `pocket_count.html` wijzigt; de rest byte-identiek aan v2.37.

## Aanleiding

Bij een grote wijk met veel straten is het lastig te onthouden waar je al bent geweest. Kern-inzicht (van Jay): je **tikken** zijn het eerlijke signaal ("hier heb ik geteld"), niet je route — want een straat waar je alleen dóórheen reed kleurt anders ten onrechte als "gedaan". De kaart toont daarom drie lagen en laat het oog het werk doen.

## Wat is toegevoegd

- **Knop "🗺 Kaart"** onderaan-midden van het parkeer-scherm, tussen Terug (links) en Stop (rechts) — als sessie-actie, buiten de tel- en undo-zone (geen dure mis-tik op undo). Verschijnt/verdwijnt met Terug/Stop.
- **Schermvullende overlay** met een Leaflet-kaart (Leaflet 1.9.4 via cdnjs, zelfde als de rest van de suite; laadt licht, rendert pas bij openen) en een "✕" om terug te klappen naar het tellen. Drie lagen:
  1. **Straten** — OSM-basemap, zodat je ziet wat nog leeg is (ook straten waar je nog niet was).
  2. **GPS-route** — blauwe lijn uit `routeLog` ("hier was ik").
  3. **Tik-stippen** — uit `telHistory`, op de tik-positie, gekleurd per status (bezet = rood, leeg = groen) met een rand per zijde (links = witte rand, rechts = donkere rand). Tik een stip voor de details (zijde · status · straat · tijd).
- **Legenda** onderin de overlay.

Het onderscheid valt vanzelf op z'n plek: straat mét stippen = geteld; straat met alleen de route-lijn = daar was je, maar telde je niet; straat zonder allebei = nog te doen.

**Zon-bestendig:** grote volle stippen (radius 8) met contrastrand, verzadigde kleuren, stevige route-lijn (weight 4), donkere balk/legenda voor contrast op een fel scherm.

## Grenzen (bewust)

- Alleen **pocket parkeren** — net als de audio-proef. Fietsparkeren/capaciteit/simpel/transect/winkelstraat porten later als het bevalt.
- **Geen** live "je-bent-hier-al"-waarschuwing — de stippen vóór je zijn betrouwbaarder dan een algoritme dat over drift/doorrijden struikelt.
- Kaart is er om **op te zoeken**; je blijft schermloos tellen. Pocket-filosofie intact.
- **Additief:** tellogica, de vier knoppen en de undo's zijn byte-identiek gebleven; alleen knop + overlay + kaartfuncties toegevoegd.

## Technische noten

- Pocket had nog géén Leaflet (schermloze app); nu toegevoegd. De kaart initialiseert lazy bij de eerste keer openen; `invalidateSize()` na het tonen (Leaflet-container was verborgen).
- De live-app kent geen offset-marker (~4 m naast de as) — die maakt de reconstructor pas. De stippen staan dus op de tik-positie (`lat`/`lon`, je GPS-positie bij de tik). Voor dekking prima; in QGIS/na reconstructie zie je later de gecorrigeerde offset.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- 12 structuurchecks OK (Leaflet-CDN, knop↔functie, overlay/canvas, route uit `routeLog`, tikken uit `telHistory`, tonen/verbergen, centrale knop-CSS).
- **Byte-identiteit:** t.o.v. v2.37 wijzigde uitsluitend `pocket_count.html`.

## Als het bevalt — vervolg (backlog)

- Dekkingskaart porten naar de andere pocket-submodi en/of de losse parkeer-apps.
- Eventueel zijde-offset op de stippen (links/rechts uit elkaar trekken) voor scherper beeld.
- Audio-proef breder uitrollen (staat al op de backlog).

## Backlog (ongewijzigd)

- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
