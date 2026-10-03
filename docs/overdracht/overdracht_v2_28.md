# TrafficCounterSuite v2.28 — Overdracht

Nieuwe publieksgerichte introductiepagina **`over.html`**, gelinkt vanaf de top van `index.html`. Doelgroep: verkeerskundigen en geïnteresseerden die op rvmk.nl terechtkomen en willen weten wat het is.

## Nieuwe/gewijzigde bestanden

| Bestand | Status | Kern |
|---|---|---|
| `over.html` | ✦ nieuw | Introductiepagina: wat is rvmk.nl, voor wie, en de workflow in drie stappen |
| `index.html` | ✦ bijgewerkt | Linkje bovenaan ("Nieuw hier? Wat is dit?") naar `over.html`, in beide taalvarianten (i18n-sleutel `introLink`) |
| `traffic_counter_help.html` | ✦ bijgewerkt | `over.html` toegevoegd aan het Bestanden-overzicht |

Alle overige bestanden zijn byte-identiek aan v2.26/v2.27.

## Inhoud van `over.html`

- **Wat is dit?** — korte uitleg: TelSuite/rvmk.nl, gratis, browser-based, GPS-bewust, geen install/account.
- **Voor wie?** — verkeerskundigen (gemeenten/adviesbureaus), studenten/onderzoekers, geïnteresseerden.
- **De werkwijze in drie stappen**, zoals gevraagd:
  1. **Tellen** — kies een veldapp, resultaat is een ZIP (tellingen + GPS-route + kaartafbeelding).
  2. **ZIP nabewerken** (gemarkeerd als *optioneel*) — `parkeer_reconstructie.html`: route-consistente hersnap, richtingslaag, handmatige link-correctie.
  3. **Presentatie in Telrapport** — kaartvisualisatie, weekprofiel, intensiteitsklassen, filters.
  Elke stap heeft een korte alinea, een link naar de bijbehorende tool, en een **screenshot-plek**.
- Kleine vermelding dat de ZIP's ook rechtstreeks in QGIS te laden zijn (geen aparte stap, maar een alternatief eindpunt voor GIS-gebruikers).
- Onderaan: CTA terug naar `index.html`, plus links naar de volledige handleiding en de technische ZIP-referentie.

### Screenshot-plekken (zelf-documenterend)

Drie `<img>`-elementen verwijzen naar bestandsnamen die nog niet bestaan; een `onerror`-handler vangt de ontbrekende afbeelding op en toont in plaats daarvan een dashed placeholder-box **met de exacte verwachte bestandsnaam erin**. Zodra jij een bestand met die naam naast `over.html` zet, verschijnt het vanzelf — geen code-wijziging nodig.

| Bestandsnaam (exact) | Bij welke stap |
|---|---|
| `screenshot-tellen.jpg` | Stap 1 — een veldapp tijdens het tellen |
| `screenshot-nabewerken.jpg` | Stap 2 — de parkeer-reconstructie kaartinterface |
| `screenshot-telrapport.jpg` | Stap 3 — een kaartvisualisatie in telrapport |

Andere extensie (`.png` i.p.v. `.jpg`) werkt niet zonder de `src` in `over.html` aan te passen — laat het weten als je liever PNG aanlevert, dan pas ik dat aan.

## Ontwerpkeuzes

- **Taal: Nederlands.** Past bij de genoemde doelgroep en bij de rest van de suite (buiten `index.html` en de technische Engelstalige `zip_format_reference.html`). `index.html` blijft tweetalig; het linkje bovenaan is dus zowel in NL als EN gelabeld, maar wijst in beide gevallen naar dezelfde Nederlandse pagina. Wil je een Engelse variant, dan is dat een aparte, expliciete vervolgstap.
- **Bestandsnaam `over.html`** — kort, matcht de bestaande naamgevingsstijl.
- **Visuele stijl** hergebruikt de bouwstenen van `index.html` (Oswald, `#f0f0ec`-achtergrond, accentkleur-gestreepte kaarten) zodat de pagina niet als vreemde eend aanvoelt — geen nieuwe stijl-taal geïntroduceerd.
- **Geen build-stap, geen dependencies** — puur HTML/CSS/inline-JS, consistent met de rest van de suite.

## Validatie

- **HTML-tagbalans** schoon op alle drie de bestanden.
- **i18n-koppeling** geverifieerd: `introLink`-sleutel bestaat in zowel de EN- als NL-dictionary, `data-i18n="introLink"` is gekoppeld, link wijst naar `over.html`.
- **Screenshot-fallback** geverifieerd: alle drie de `<img>`-tags hebben een werkende `onerror`-attribuut dat de placeholder toont.
- **Byte-identiteit:** t.o.v. v2.26 wijzigden uitsluitend `index.html` en `traffic_counter_help.html`; `over.html` is nieuw. Geen ander bestand aangeraakt.

## Backlog (ongewijzigd meegenomen)

- Engelse variant van `over.html`, als gewenst.
- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
