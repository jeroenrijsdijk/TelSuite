# TrafficCounterSuite v2.29 — Overdracht

Deze release neemt Jay's **handmatig bijgewerkte handleiding** op in de suite, plus twee kleine reparaties en één inhoudelijke correctie in `over.html`. Alleen `traffic_counter_help.html` en `over.html` wijzigen t.o.v. v2.28; de rest is byte-identiek.

## Herkomst & scope van Jay's edits

Jay's upload was gebaseerd op **v2.27** (dus vóór `over.html` bestond) en bevatte al alle v2.27-toevoegingen (pocket-submodi, QGIS-loader, parkeer_reconstructie-verwijzingen) — er is niets van eerder werk verloren. Zijn wijzigingen (75 regels, geconcentreerd in de intro, de methodiek-sectie en de Static-intro):

- Herschreven/aangescherpte bewoordingen in de intro en methodiek.
- "TELLEN en RAPPORTAGE/PLANNING" → "…/BEWERKING/PLANNING"; telplanning- en reconstructie-omschrijvingen bijgewerkt; OSM-copyrightlink toegevoegd; CSV "ready for telrapport.html, Excel or KNIME".
- Methodiek ingekort: de items "Eén telprotocol", "De teller is een instrument — kalibreer jezelf" en "Tijd boven volledigheid" verwijderd; een nieuw blok **"Denk aan je eigen veiligheid"** (rode *belangrijk*-badge) toegevoegd.
- Static-mode-intro geherstructureerd (badge vóór titel, zinnen als losse regels).

Deze redactionele keuzes zijn **één-op-één overgenomen**, niet "gecorrigeerd".

## Reparaties (noodzakelijk voor correcte rendering)

Twee HTML-balansfouten, beide hetzelfde patroon — bij het inkorten is een `<div class="method-item">`-opening verwijderd maar bleef de bijbehorende `</div>` staan:

1. **Intro-blok (methodiek):** losse `</div>` na de "Uitgangspunt"-choice-card verwijderd.
2. **Veiligheidsblok:** ontbrekende `</div>` toegevoegd zodat `method-item` sluit vóór `</section>` (anders lekte de open div door naar de volgende sectie).

Zonder deze fixes rendert de pagina vanaf de methodiek-sectie verkeerd.

## Terug-gemergd (v2.28-delta die in Jay's v2.27-basis ontbrak)

- `over.html` toegevoegd aan het Bestanden-overzicht van de handleiding (stond in v2.28, ontbrak in Jay's basis).

## Correctie in `over.html`

Naar aanleiding van Jay's vraag: de kaartafbeelding (`_kaart.png`) zit **niet in elke ZIP**. Geverifieerd in de broncode — alleen `parkeertelling.html`, `fietsparkeren.html` en `capaciteitstelling.html` (de apps met een live kaart) voegen `_kaart.png` + `.gpx` toe; `pocket_count.html` heeft geen live kaart en dus geen kaartafbeelding, en `traffic_counter.html` exporteert één CSV. Stap 1 in `over.html` is aangepast: "…met de tellingen en de GPS-route — bij de apps met een live kaart (parkeertelling, fietsparkeren, capaciteitstelling) zit er ook een kaartafbeelding in."

## Aandachtspunt (niet gewijzigd, ter beoordeling)

Het nieuwe veiligheidsblok gebruikt een **`<h1>`** als kop, terwijl alle andere methodiek-kopjes `<h4>` zijn. Een `<h1>` rendert veel groter en het document heeft al twee h1's. Bewust niet aangepast (het is een redactionele keuze), maar het is het overwegen waard om er `<h4>` van te maken voor consistentie — één woord en ik pas het aan.

## Validatie

- **HTML-tagbalans** schoon op `traffic_counter_help.html`, `over.html` én `index.html`.
- **TOC-integriteit:** alle ankers hebben een bestaand id; geen dubbele id's.
- **Byte-identiteit:** t.o.v. v2.28 wijzigden uitsluitend `traffic_counter_help.html` en `over.html`.

## Backlog (ongewijzigd)

- Veiligheidsblok-kop `<h1>` → `<h4>` (optioneel, ter beoordeling).
- Engelse variant van `over.html`, als gewenst.
- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
