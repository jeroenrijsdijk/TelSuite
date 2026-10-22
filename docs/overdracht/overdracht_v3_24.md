# Overdracht v3.24 — een Engelse introductie

Jay: "Schrijf maar een engelse over.html". Dit stond in de backlog als *Engelse
variant van `over.html`*.

## 1. Wat er is

- **`about.html` (nieuw).** De vertaling van `over.html`, met dezelfde opbouw:
  - wat het is en voor wie;
  - in het kort;
  - de drie stappen;
  - de GIS-alinea;
  - de links onderaan.
- **Dezelfde kale stijl** (`valideer.py`: `about.html` staat in `KAAL`, groep
  *kale stijl* nu vijf bestanden).
- **Dezelfde screenshots** (`screenshot-*.jpg`, in dezelfde map), met de
  plaatshouder als ze ontbreken.
- **Erbij voor Engelse lezers.** Eén alinea dat de meeste schermen Nederlands
  zijn, en dat de voorpagina, het startscherm van pocket en de
  ZIP-referentie ook Engels zijn. De links onderaan zeggen welke pagina
  Nederlands is.
- **Metadata:**
  - titel "What is telonline.org? Traffic counting in your browser" (55
    tekens);
  - description van 139 tekens, met "traffic counting" (de afspraak voor SEO);
  - canonical;
  - Open Graph met `en_US` en als alternatief `nl_NL`;
  - JSON-LD `AboutPage` met `inLanguage: en`.
- **Over en weer.** Beide pagina's hebben `<link rel="alternate" hreflang="nl|en">`,
  en bovenaan een taallink: *English* op `over.html`, *Nederlands* op
  `about.html`.
- **Voorpagina.** "Wat is dit?" gaat naar `about.html` als de voorpagina Engels
  is, en naar `over.html` als hij Nederlands is (`setLanguage`). In de HTML
  staat `about.html`, omdat de voorpagina zonder script Engels is.
- **Sitemap:** `about.html` erbij (15 adressen).

## 2. Niet veranderd

- **De indeling van `over.html` volgt de voorpagina nog niet** (backlog sinds
  v2.69). `about.html` volgt `over.html`, zodat de twee gelijk blijven. Pas ze
  later samen aan.
- **De kop van de handleiding.** Jay paste de bovenste kop al aan. Boven de
  inhoudsopgave staat nog een tweede kop "Traffic Counter Help", met daaronder
  "Contents". In de backlog genoteerd.
- **Kleine fouten verbeterd in de vertaling, niet in het Nederlandse
  origineel:** "handleding" en "niet de op de rijbaan".

## 3. Tests

`robuusttest.py` deel D: de voorpagina linkt in het Engels naar `about.html` en
in het Nederlands naar `over.html` (2 tests erbij, nu 89). Titel, description,
canonical, sitemap en de kale stijl van `about.html` controleert `valideer.py`.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `about.html` | nieuw |
| `over.html` | `hreflang` en de taallink *English* |
| `index.html` | "Wat is dit?" per taal; versie v3.24 |
| `sitemap.xml` | `about.html` |
| `_archief/overpass_rig/robuusttest.py`, `valideer.py`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py            ALLES OK — 3 verwachte bestanden (about.html nieuw, over.html, index.html);
                       kale stijl 5 bestanden OK; about.html titel 55, description 139; sitemap 15 adressen
robuusttest.py         89/89 (deel D: de introductie per taal)
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
