# Overdracht v3.34 — Passanten per uur

Na v3.33 deden we een pas op de plaats. Jay: "Het werk zit inderdaad nog in de
brug van Archief Naar Rapport, en van Archief naar Planning. Verder wil ik
passanten nog omrekenen naar een grootheid die winkeliers snappen. Het gaat
over passanten per uur langs een bepaalde plek."

## 0. Het gesprek vooraf

1. **Mijn voorstel:** omrekenen met de moving-observer-methode. Jay: "hebben we
   dat niet al uitgewerkt?", met een link naar `winkelstraat_rekenrig.html`.
   Dat klopte. Het rig had de schatter al, met poolen als ratio of sums, per
   looprichting, en de stilstaanders per 100 m. Ik had eerst in het rig moeten
   kijken.
2. **Waar het komt.** Jay: "Qua winkelstraat kan ik me voorstellen dat het een
   eigen rapport is - op basis van de aanbeboden winkeltellingen rektn hij - je
   selecteert een dag en uur en op het netwerk verschijnen de gemeten
   gemiddelden in passanten per uur, ook als tekstueel label. Basiskaart eronder
   en niet teveel opties."
3. **De keuzes.** Jay: "Zet de loopsnelheid maar op 1,1 m/s. Middel alle gemeten
   zaterdagen naar 1 waarde. Zo ook voor de andere weekdagen. Je werkt met de
   (korte 40-60meter) segmenten toch?"
   - Ja: de stukken van `splitWayIntoSegments` (streven 40 m; een weg korter
     dan 60 m blijft heel), dus 30 tot 60 m.
   - Eén richting gelopen: de gemeten stroom met een sterretje, niet
     verdubbeld. Dat was mijn voorstel en Jay sprak het niet tegen.
4. **Archief naar planning:** "daar moet ik nog eens naar kijken - ik zal erop
   letten tijdens het werken." Dat staat in de backlog.

Aan de ZIP's en het schema verandert niets. Passanten leest alleen.

## 1. De rekenkern: gedeeld blok `passanten`

- **Uit het rekenrig gehaald** als pure module `PASSANTEN`:
  - `sessie(d)`: passages, tikken per passage, richting;
  - `voegToe`: per stuk straat;
  - `bereken(segmenten, v)`: cellen per weekdag en uur.

  Byte-identiek in `passanten.html` en `winkelstraat_rekenrig.html`, bewaakt
  door `valideer.py`.
- **Formule:** cel = 3600 · Σm ÷ Σ(L/v + t), per gelopen richting gepoold en dan
  opgeteld. Stilstaanders: 100 · Σstil ÷ ΣL.
- **`v` = 1,1 m/s** (`PASSANTEN.V_VOET`). Het rig begint nu ook op 1,1 en houdt
  zijn invoerveld.
- **Erbij:** per cel de datums (`c.datums`), voor de popup.
- **Nagerekend:**
  - Het rig vóór de verbouwing, de verbouwde versie en een losse
    Python-berekening geven op de testgegevens precies dezelfde cellen, bij
    1,3 en bij 1,1 m/s.
  - De volgorde waarin het rig sessies laat zien, hangt af van welke ZIP het
    eerst klaar is met lezen; dat was al zo.

## 2. De pagina `passanten.html`

- **Inlezen:** ZIP's kiezen, een map kiezen, of slepen (ook een hele map).
  - Mee doen alleen winkelstraat-tellingen. Wat de telling zelf zegt, gaat
    voor: eerst de modus in `_sessie.csv`, dan de letter `_pkt_w` in de
    sessie-id of de naam. Alleen in het oude formaat zonder beide tellen de
    tikken *tegemoet*/*stilstaand*.
  - Dat kwam uit de test. Eerst telde een pocket-simpel-ZIP met zulke tikken
    toch mee.
  - Een reconstructie gaat voor het origineel. Een dubbele telt één keer.
  - Wat niet meedoet, staat erboven met de reden, en ook hoeveel tikken buiten
    een passage vielen.
- **Dag en uur:** knoppen *ma* … *zo* en de uren.
  - Alleen wat gemeten is, is aan te klikken.
  - Standaard het moment met de meeste gemeten stukken.
  - Een andere dag houdt het uur als dat kan.
- **Kaart:** CARTO Positron.
  - Gemeten stukken in een kleur van bleek zeegroen tot diep petrol, zoals in
    het rig. De schaal loopt over alle dagen en uren, zodat een kleur steeds
    hetzelfde betekent.
  - Stukken die wel geteld zijn maar niet op dat moment: dun en grijs.
- **Labels:** het afgeronde getal halverwege het stuk, met `*` als maar één
  richting gemeten is.
  - Het drukste label eerst, en een label dat een geplaatst label raakt,
    valt weg. Bij inzoomen komen ze terug.
- **Popup** (bij een klik):
  - straat en lengte;
  - "≈ 589 passanten per uur", met de marge (95%);
  - dag en uur;
  - hoe vaak langsgelopen, op welke datums;
  - of beide richtingen gemeten zijn, met de twee stromen;
  - de stilstaanders per 100 m.
  - Bij een grijs stuk staat wanneer het wél gemeten is.
- **Marge:** Garwood op Σm, het gedeelde blok `poisson` uit telrapport. Hij
  wordt geschaald met wat één tegenligger in die cel waard is (q ÷ Σm). Zonder
  tegenliggers geldt het gemiddelde venster per stroom. Dat is een benadering
  als de vensters van de stromen erg verschillen.
- **Legenda:** rechtsboven in de kaart, op een telefoon eronder.
- **Onder de kaart** staat de uitleg in één alinea, met een link naar de
  handleiding.
- **Geen plaatje of PDF in deze versie.** Dat had ik vooraf gezegd; het staat
  in de backlog.

## 3. Elders

- **`index.html`:** *Passanten* / *Footfall* onder *Achter je bureau*, na
  Rapport; versie v3.34.
- **Handleiding:** een hoofdstuk *Passanten per uur* (`#passanten`), en een
  verwijzing vanuit *Winkelstraat*. Daar staat ook: tel als *tegemoet* alleen
  wie je tegemoet loopt, niet wie jou inhaalt. Dat is de aanname van de
  formule.
- **`over.html` en `about.html`:** de groepen op de voorpagina.
- **Privacyverklaring (NL en EN):** Passanten leest alleen in de browser; de
  kaart haalt tegels bij CARTO.
- **`sitemap.xml`:** `passanten.html`.
- **Stand van zaken:**
  - de rij van `telarchief.html` heette nog Ordenen, nu Archief;
  - het rekenrig blijft op de site, want Jay gebruikt het.

## 4. Tests

- **`functest_passanten.js`** (nieuw, 19):
  - de formule, en een andere loopsnelheid geeft een andere waarde;
  - de cel (weekdag:uur);
  - twee zaterdagen worden één cel, met ratio of sums en niet het
    gemiddelde;
  - de richting uit de volgorde, en uit de GPS (heen, terug, minder dan 8 m is
    onbekend);
  - de stilstaanders per 100 m, en een tik buiten een passage;
  - het uur van het midden van een passage;
  - een stuk zonder geometrie;
  - en dat het rekenrig hetzelfde blok heeft.
- **`passantentest.py`** (nieuw, 25), in Chromium met gemaakte ZIP's:
  - Voorstraat, heen en terug;
  - Kerkstraat, alleen heen;
  - Steegje, één passage, met de richting uit de GPS;
  - twee zaterdagen en een donderdag, een reconstructie, een
    pocket-simpel-ZIP en een lege ZIP.

  De verwachte waarden rekent de test zelf uit.
  - **A.** Inlezen: wat meedoet, wat niet en waarom, de reconstructie voor het
    origineel, de samenvatting.
  - **B.** Dag en uur: alleen do en za; za 13 als standaard.
  - **C.** Kaart: elke waarde volgens de formule, de labels, de sterretjes,
    grijs op donderdag, de schaal over alle dagen.
  - **D.** Labels zonder overlap bij het eerste beeld, uitgezoomd (minder, de
    drukste blijft) en ingezoomd (alle 8).
  - **E.** De popup en de marge.
  - **F.** Twee zaterdagen worden één waarde (ratio of sums ≠ gemiddelde).
  - **G.** Op 390 px.
- **Bekeken:** op 1300 en 390 px, met een popup open. De legenda stond eerst
  linksonder en viel op een laptop half onder de rand. Nu staat hij rechtsboven,
  en op een telefoon onder de kaart.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | nieuw |
| `winkelstraat_rekenrig.html` | rekent met het gedeelde blok `passanten`; standaard 1,1 m/s |
| `index.html` | *Passanten* / *Footfall*; versie v3.34 |
| `traffic_counter_help.html` | hoofdstuk *Passanten per uur*; verwijzing bij Winkelstraat |
| `over.html`, `about.html`, `privacy.html` | Passanten |
| `sitemap.xml` | `passanten.html` |
| `_archief/overpass_rig/functest_passanten.js`, `passantentest.py` | nieuw |
| `valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
VALIDATIE_HIER
```
