# Overdracht v3.6 — SEO-ronde

Jay's opdracht: "SEO-ronde telonline.org na 3.0. Alleen `<head>` en één `<h1>`;
geen functionele wijzigingen." Hij stelde de titels en descriptions zelf op.

## 1. Wat er veranderd is

**Negen tools**: een Nederlandse titel, een meta description en een canonical.

| bestand | titel (tekens) | description (tekens) |
|---|---|---|
| `traffic_counter.html` | Verkeer tellen vanaf een vast punt (50) | 147 |
| `pocket_count.html` | Lopend tellen: verkeer en passanten met GPS (59) | 144 |
| `parkeertelling.html` | Parkeertelling: geparkeerde auto's tellen (57) | 148 |
| `fietsparkeren.html` | Fietsparkeertelling: gestalde fietsen tellen (60) | 146 |
| `capaciteitstelling.html` | Parkeercapaciteit in kaart brengen (50) | 143 |
| `telplanning.html` | Telplanning: tellingen voorbereiden (51) | 152 |
| `telreconstructie.html` | Telreconstructie: tellingen op de juiste straat (63) | 152 |
| `telrapport.html` | Telrapport: drukte per wegvak op de kaart (57) | 141 |
| `zip_format_reference.html` | ZIP-formaat: technische referentie (50) | 138 |

Elke titel eindigt op " | telonline.org"; de tekens tellen dat mee.

**`over.html`**: de titel is "Wat is telonline.org? — Online verkeerstellingen".
De og:title was al gelijk.

**`capaciteitstelling.html`**: de zichtbare `<h1>` "Mapping Capacity Only" is
"Parkeercapaciteit".

## 2. Waar ik van de opdracht afweek, en waarom

1. **Versie v3.6, niet 3.0.1.** Online stond al v3.5. Een lager nummer zou
   `valideer.py` afwijzen. En `release.yml` leest alleen `vX.Y`, dus bij
   `v3.0.1` was er geen release gekomen.
2. **De sitemap en `robots.txt` waren al klaar** (10 oktober). De sitemap heeft
   14 adressen: de tien uit de opdracht, `/` voor de voorpagina, en de
   handleiding, de privacyverklaring en de verantwoording. Ingediend bij Google
   Search Console; Bing kan de sitemap uit Search Console overnemen. Verder:
   - de voorpagina blijft `/` in de sitemap en in de canonical, niet
     `index.html`, want `/` is het adres dat Google moet tonen;
   - de opdracht noemde elf pagina's; met die lijst waren de handleiding, de
     privacyverklaring en de verantwoording uit de sitemap gevallen.
3. **Drie pagina's buiten de tien haalden de nieuwe controle niet.** Ingekort,
   ter beoordeling:

   | pagina | was | nu |
   |---|---|---|
   | `index.html`, titel | Online Traffic Counting — Vehicle & Parking Surveys \| telonline.org (67) | Traffic Counting — Vehicle & Parking Surveys \| telonline.org (60) |
   | `over.html`, description | "telonline.org (Telonline Verkeerstellingen) is een gratis, …" (184) | zonder "(Telonline Verkeerstellingen)" (154) |
   | `verantwoording.html`, titel | Een telling met telonline.org beoordelen — toelichting voor juristen (68) | Een telling beoordelen: toelichting voor juristen \| telonline.org (65) |
   | `verantwoording.html`, description | "… bij een verkeers- of parkeertelling vastlegt …" (166) | "… bij een telling vastlegt …" (146) |

   De og:title van de voorpagina en de verantwoording volgen de nieuwe titel.
   Bij `over.html` staat dezelfde description ook in og:description en de
   JSON-LD; die zijn meegegaan.
4. **og:title**: van de tien pagina's had alleen `over.html` er een, en die
   klopte al. Er zijn geen Twitter-tags.

## 3. Bewust niet aangeraakt

- **Pocket via `#parkeren`.** `pocket_count.html` zet zijn tabtitel dan zelf op
  "Pocket Parkeren". Dat is een functie (sinds v2.70). Zoekmachines zien het
  adres zonder `#parkeren` en lezen dus de nieuwe titel.
- **Taal van de pagina.** `traffic_counter.html` en `zip_format_reference.html`
  zijn Engelstalig (`lang="en"`) en hebben nu een Nederlandse titel en
  description. Dat is Jay's keuze voor de vindbaarheid in Nederland.
- **Zichtbare tekst.** De rest van de zichtbare tekst is ongewijzigd, ook de
  Engelse `<h1>` van parkeertelling en fietsparkeren.

## 4. Nieuwe controle in `valideer.py`

Sectie *titel, description, canonical*. Elke publieke pagina, dat is alles
behalve `NIET_IN_SITEMAP`:

- `<title>` hooguit 65 tekens;
- meta description 70 tot en met 160 tekens;
- canonical `https://telonline.org/<bestand>` (`index.html`: `https://telonline.org/`);
- als er een og:title is: gelijk aan de titel zonder " | telonline.org".

Gemeten na het omzetten van entiteiten (`&amp;` is één teken), alleen in de
`<head>`. `NIET_IN_SITEMAP` staat nu bovenaan; de sitemapcontrole gebruikt
dezelfde set.

Getest met een te lange titel, een ontbrekende canonical en een afwijkende
og:title. Alle drie gevonden.

**Versiestempel van de reconstructor.** `RECON_VERSIE` staat in elke
gereconstrueerde ZIP en betekent: de reconstructor is in deze release veranderd.
`valideer.py` eiste een nieuwe stempel zodra `telreconstructie.html` ook maar
iets veranderde, dus ook bij alleen een nieuwe titel. Die controle slaat nu de
`<head>` over. De stempel blijft `v2.74`. Getest: een wijziging in de code van de
reconstructor eist nog steeds een nieuwe stempel.

De byte-identiteit van gedeelde code (`HIGHWAY_RE`, de Overpass-blokken,
`MATCHER`/`RECON`, `hervatSessie`, `bewaarZip`, `GPX-tijd`, …) hangt aan ankers in
de code, niet aan `<head>` of `<h1>`. Alle 14 groepen blijven gelijk.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| de negen tools | titel, description, canonical |
| `capaciteitstelling.html` | ook de `<h1>` |
| `over.html` | titel, description (ingekort) |
| `index.html` | titel en og:title, versie v3.6 |
| `verantwoording.html` | titel, og:title, description |
| `_archief/overpass_rig/valideer.py` | nieuwe controle, release v3.6 |
| `CLAUDE.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | de regels voor de `<head>` |

## 6. Validatie

```
valideer.py        ALLES OK — 12 verwachte bestanden gewijzigd; 14 groepen gedeelde blokken OK; 14 publieke pagina's: titel, description, canonical OK
functests          alle 14 groen
laadtest.py        47/47
statictest.py      24/24
opruimtest.py      52/52
hersteltest.py     133/133
gpkgtest.py        80/80
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
