# Overdracht v3.3 — kale documentatiepagina's

Jay: "De handleiding mag een beetje minder mooi. Erg veel css en kleurtjes voor
een pakket dat toch een beetje voor verkeerskundigen is." Na het voorbeeld:
"we gaan het zo doen! Maak over.html en privacy.html ook maar 'kaal'."

De handleiding, `over.html` en `privacy.html` zijn nu gewone HTML: koppen,
alinea's, lijsten en tabellen, met één klein stijlblok dat in alle drie hetzelfde
is. **De tekst is woord voor woord gelijk** (zie §5). De tools zelf houden hun
huisstijl.

---

## 1. Wat er veranderd is

| pagina | was | nu | CSS was | CSS nu |
|---|---|---|---|---|
| `traffic_counter_help.html` | 96,7 kB | 76,4 kB | 9,3 kB | 0,9 kB |
| `over.html` | 18,3 kB | 10,9 kB | 6,0 kB | 0,9 kB |
| `privacy.html` | 9,3 kB | 7,8 kB | 2,3 kB | 1,1 kB |

- **Systeemletter** in plaats van Oswald en Share Tech Mono. Deze pagina's halen
  niets meer op bij Google Fonts. De tools doen dat nog, dus de regel in de
  privacyverklaring blijft kloppen.
- **Geen kaartjes, balken, gekleurde labels en kapitalen meer.** Wat eerder met
  CSS in kapitalen stond, staat er nu zoals het geschreven is: "belangrijk",
  niet "BELANGRIJK".
- **Kleur alleen waar die iets uitlegt:**
  - de stippen en ringen van de GPS-status (rond, gevuld of open);
  - de kleurstalen van de intensiteitsklassen en de dekking;
  - de links.
- **Op de telefoon** schoof de handleiding zijwaarts (532 px breed op een scherm
  van 390). Nu past de pagina. Alleen een tabel die echt te breed is (de
  bestandenlijst) schuift binnen zichzelf.

## 2. Hoe de onderdelen zijn omgezet

| was | wordt |
|---|---|
| hoofdstukbalk per tool (`.divider`) | `<h2>` en een regel met de link(s) naar de tool |
| sectiekop (`<h2>`) | `<h3>` (één niveau omlaag, onder het hoofdstuk) |
| kaartje met titel (`.card`, `.card-title`) | `<h4>` en de inhoud |
| keuzekaart (`.choice-label`) | `<p><strong>` |
| statusvoorbeeld | `<p><samp>` |
| inhoudsopgave met subkoppen | geneste lijst |
| bestandsrijen (`.file-row`) | tabel, de bestandsnaam in `<code>` |
| labeltjes (`.tag`) | `<b>`; naast elkaar met `·` ertussen |
| rij knoppen-links | links met `·` ertussen |
| CSV-kop in monoletter | `<code>` |
| kleurstaal / stip / ring | `<span class="kleur">`, rond met `rond`; ring = `background:none;border:2px solid …` |
| *over*: stapkaart | `<h3>Stap 1 — Tellen</h3>`, "(*warm aanbevolen*)" erachter |
| *over*: knoppen onderaan | lijst met links |
| *over*: "Built by JRI and Claude - Anthropic" | `<p><small>`; het sterretje-logo is weg |
| *privacy*: kop met terug-link | `<h1>` met de link eronder |
| *privacy*: Engelse deel (`<div lang="en">`) | `<section lang="en">` |

Alle andere classes en `style`-attributen zijn weg. Lege `<div>`/`<span>`-schillen
zijn uitgepakt.

## 3. Het gedeelde stijlblok

In alle drie byte-identiek, tussen `/* ── kale stijl (v3.3)` en
`/* ── einde kale stijl ── */` (hier ingekort):

```css
body{font:16px/1.55 system-ui,…;max-width:46em;margin:2em auto;padding:0 1em;color:#222;background:#fff}
h1,h2,h3,h4{line-height:1.25}h2{margin-top:2.5em;padding-bottom:.2em;border-bottom:1px solid #bbb}h4{margin-bottom:.3em}
table{display:block;overflow-x:auto;border-collapse:collapse;margin:.6em 0}td,th{border:1px solid #ccc;…}
code,samp,kbd{font-family:ui-monospace,Consolas,monospace;font-size:.92em}code,samp,a{overflow-wrap:break-word}img{max-width:100%;height:auto}
.kleur{display:inline-block;width:.8em;height:.8em;…}.rond{border-radius:50%}td:has(>.kleur){white-space:nowrap}
```

Drie keuzes die niet vanzelf spreken:

- **`table{display:block;overflow-x:auto}`.** Een tabel die niet past, schuift
  binnen zichzelf, en niet de hele pagina. De cellen breken gewoon af; alleen
  onbreekbare inhoud (lange bestandsnamen) laat hem schuiven. Eerst geprobeerd:
  `overflow-wrap:anywhere` op `code`. Dan perst de tabel de bestandsnamen tot
  twee letters breed, een letter per regel.
- **`overflow-wrap:break-word` op `code`, `samp` en links.** De CSV-kop
  (`sessie_id;datum;…`) en de lange link naar de QGIS-loader breken af aan de
  rand. In een tabel heeft dit geen effect, zie hierboven.
- **`td:has(>.kleur)`.** Houdt een stip en zijn naam ("● Groen") op één regel.
  Dat vervangt de oude class `nowrap`.

`privacy.html` heeft daarna nog drie eigen regels: `.domein` (monoletter, grijs,
op een eigen regel), `.invullen` (geel, totdat de contactgegevens erin staan) en
`.tabel`.

## 4. Wat bewust bleef

- **De `<head>` is byte voor byte gelijk**: titel, Open Graph, JSON-LD,
  canonical. Alleen het `<style>`-blok (met de `@import` van Google Fonts) is
  vervangen.
- **Alle 49 id's**, en dus alle 49 ankers ernaartoe (vanuit de andere pagina's
  en binnen de handleiding). `<section lang="nl">` in de handleiding.
- **Privacy**:
  - `<span class="domein">` (13×), waarop `valideer.py` de domeinen controleert;
  - `data-invullen="contact"`;
  - het Engelse deel met `lang="en"`.
- **De plaatshouder voor de screenshots** in `over.html`. De `onerror` van het
  plaatje is ongewijzigd: die verbergt het plaatje en toont het element erna.
  Dat is nu een verborgen `<p>`: "📷 · screenshot-tellen.jpg · Plaats dit
  bestand naast over.html".
- **Jay's eigen keuzes in de tekst**, niet aangeraakt:
  - de NL/EN-mix in de koppen;
  - de twee `<h1>`'s bovenaan de handleiding;
  - de oude naam "Traffic Counter Help";
  - de `<h1>` van het veiligheidsblok (staat in de backlog);
  - de tekens ▢ … ▫▫ in `over.html`.

## 5. Zelfde tekst: hoe gecontroleerd

Nieuw in de rig: **`tekstgelijk.py`**. Het vergelijkt de woorden van twee
HTML-bestanden.

- Telt mee: alle tekst in `<title>` en `<body>`, ook verborgen tekst.
- Telt niet mee: script, stijl en witruimte.
- `· — ( )` tellen niet mee. Die ontstaan bij het omzetten als scheiding tussen
  wat eerder losse vakjes waren.

| pagina | woorden | toegevoegd | weg |
|---|---|---|---|
| handleiding | 8130, gelijk | 6× `·` (labels, linkrijen) | — |
| over | 965, gelijk | 6× `·`, 3× `—` (stapkoppen), `( )` om "warm aanbevolen" | het sterretje-logo `*` |
| privacy | 713, gelijk | — | — |

Daarnaast nagelopen in Chromium:

- geen JS-fouten;
- op 390 px breed geen zijwaarts schuiven;
- de drie plaatshouders verschijnen als de screenshots ontbreken;
- een anker (`#pocket-transect`) springt naar de goede plek.

De omzetting zelf was een eenmalig script (BeautifulSoup). Het staat niet in de
repo: voortaan is dit gewone HTML die je met de hand bewerkt.

## 6. `valideer.py`

- Nieuwe groep **`kale stijl`**: het stijlblok moet in de drie pagina's
  byte-identiek zijn.
- Nieuwe controle **"documentatiepagina's kaal"**. Per pagina:
  - één `<style>`, dat begint met het gedeelde blok;
  - daarna hooguit vijf eigen regels;
  - geen Google Fonts (`@import` of `<link>`; het domein noemen in de tekst mag);
  - geen `style=""`, behalve een kleur in een kleurstaal of een verborgen
    plaatshouder.

  Getest door een losse `style="color:red"` in te voegen; die wordt gevonden.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter_help.html`, `over.html`, `privacy.html` | kaal |
| `index.html` | versie v3.3 |
| `_archief/overpass_rig/tekstgelijk.py` | nieuw: tekst woord voor woord vergelijken |
| `_archief/overpass_rig/valideer.py`, `README.md` | groep `kale stijl`, controle "kaal", release v3.3 |
| `CLAUDE.md`, `docs/ONTWIKKELEN.md` | huisstijl: tools Oswald, documentatiepagina's kaal |
| `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py        ALLES OK — 4 verwachte bestanden gewijzigd; 13 groepen gedeelde blokken OK; 3 pagina's kaal
tekstgelijk.py     handleiding 8130, over 965, privacy 713 woorden gelijk
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
laadtest.py        46/46
statictest.py      24/24
opruimtest.py      52/52
hersteltest.py     133/133
gpkgtest.py        80/80
check_encoding.py  alles geldige UTF-8
```
