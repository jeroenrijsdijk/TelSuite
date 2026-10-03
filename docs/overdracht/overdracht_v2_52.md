# Overdracht v2.52 — `_capaciteit.csv` en `_netwerk.csv` beschreven

Eén bestand: `zip_format_reference.html`, +3.422 bytes. Alleen inhoud, geen
nieuwe CSS en geen nieuwe klassen (gecontroleerd: de klassenverzameling voor en
na is identiek).

Beide bestanden hadden al een blok, maar de beschrijving klopte niet met wat
`capaciteitstelling.html` werkelijk wegschrijft. Ik heb de bouwers gelezen en de
tekst daarop gebaseerd.

---

## 1. Wat er niet klopte

**`_capaciteit.csv`**

| Stond er | Klopt niet omdat |
|---|---|
| voorbeeld met `zijde=nvt` | `buildStratenCsvString()` schrijft `L+R` — een capaciteitstelling telt beide trottoirbanden van de straat samen. `nvt` hoort bij `_terrein.csv`, waar een terrein geen zijde heeft. |
| "Multiple rows per `osm_way_id` — one per `soort`" | De aggregatie gaat per **straatnaam**, niet per way. `nameMap[naam]` is de sleutel; `osm_way_id` is `Object.keys(r.wayIds)[0]`, dus de eerste way die onder die naam langskwam. Een straat die in OSM uit acht ways bestaat levert één rij per soort, met één willekeurige van die acht in de kolom. Wie daarop joint verliest rijen. |
| — | De verzamelrijen voor niet-gesnapte tikken ontbraken volledig: `naam=(niet gesnapped)` met een lege `osm_way_id`, één per soort. Zonder die rijen lijkt het bestand rijen kwijt te zijn ten opzichte van `n_waarnemingen`. |

**`_netwerk.csv` — capaciteitsvariant**

De twee bestaande noten klopten, maar er ontbrak het meeste: geen `sessie_id`-
kolom, `lon lat`-volgorde, het sluiten van de ring bij open polygonen,
ontdubbeling op way-id, het overslaan van ways met minder dan twee punten, dat
het bestand het **hele** opgehaalde netwerk bevat (dus rijen zonder telling —
geen fout), en dat het bestand helemaal wordt weggelaten als er niets is in
plaats van als kop-alleen-bestand.

---

## 2. Wat er nu staat

`_capaciteit.csv` heeft acht noten, met het voorbeeld uitgebreid tot drie rijen
zodat de `(niet gesnapped)`-rij zichtbaar is. De kern:

- één rij per (`naam` × `soort`), geaggregeerd op straatnaam
- `osm_way_id` is een **representant**, geen sleutel — join op `naam`, of via
  `_netwerk.csv`
- `capaciteit` = aantal tikken, één tik is één plek
- een soort met nul telt krijgt géén rij
- `zijde` is altijd `L+R`; per zijde staat in `_telregels.csv`
- de `capaciteit`-kolom sommeert altijd tot `n_waarnemingen` in `_sessie.csv`
- tijdstempels omsluiten die ene groep, niet de hele straat
- het `_cap`-merk zit alleen in de ZIP-naam; `sessie_id` is `YYYYMMDD_HHMMSS_xyz`

`_netwerk.csv` heeft zeven noten en een voorbeeld van drie rijen: een gewone
LINESTRING, een POLYGON-parkeerterrein, en een way zonder highway-tag zodat de
lege kolom zichtbaar is.

---

## 3. Eén noot bij `_terrein.csv`

Niet gevraagd, wel toegevoegd, omdat de bestaande tekst "identical schema"
misleidend kan werken: `capaciteit` betekent daar iets anders. Een terrein wordt
ingevoerd als een **aantal** plekken per soort en die aantallen worden gesommeerd
(`r.capaciteit += parseInt(e.n)`), terwijl een straat één tik per plek telt
(`r[e.type]++`). Zelfde kolom, andere eenheid. Dat is precies het soort verschil
waar een KNIME-som stilletjes op misgaat.

---

## 4. Los aandachtspunt in de code

In `capaciteitstelling.html` staat bij `exportZip()` het commentaar:

> Terrein heeft een eigen schema (osm_id+osm_type, geen zijde)

Dat is achterhaald. `buildTerreinCsvString()` schrijft bewust dezelfde header als
`_capaciteit.csv`, inclusief `zijde`, en zegt dat zelf ook in zijn eigen
commentaarblok. Twee commentaren die elkaar tegenspreken, waarvan er één de
lezer op het verkeerde been zet. Niet aangeraakt in deze release omdat het puur
commentaar is en jij misschien weet welke van de twee de bedoeling was — maar
het is de moeite waard om op te ruimen zodra je toch in dat bestand bent.

---

## 5. Validatie

```
JS-syntax (node --check)                     15/15 OK
HTML-tagbalans, vergeleken met v2.51         geen afwijking
byte-identiteit                              alleen zip_format_reference.html
CSS-klassen voor/na                          identiek, geen nieuwe klassen
gedeelde blokken byte-identiek               6 groepen OK
functionele tests (Overpass + tikPositie)    34 + 18 + 16 + 9 OK
```

De inhoud is afgeleid uit `buildStratenCsvString()`, `buildTerreinCsvString()` en
`buildNetwerkCsvString()` in `capaciteitstelling.html`. Wijzigt een van die drie,
dan loopt dit blok mee achter — er is geen test die de referentie tegen de code
houdt. Dat zou kunnen (kopregels vergelijken), maar dat is een eigen klusje.
