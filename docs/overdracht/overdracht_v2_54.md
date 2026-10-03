# Overdracht v2.54 — de referentie sluit weer aan op de code

Eén bestand: `zip_format_reference.html`, +10.671 bytes. Plus een nieuwe test die
dit voortaan bewaakt.

---

## 1. Drie foute kopregels gecorrigeerd

| Bestand | Stond er | Klopt |
|---|---|---|
| `_straten.csv` (fiets) | `…;wrak;bezet;vrij;bezettingsgraad_pct;eerste;laatste` | `…;wrak;totaal;eerste;laatste` |
| `_sessie.csv` (pocket) | `…;app_type;type;n_waarnemingen` | `…;n_waarnemingen;modus;richting_a;richting_b` |
| `_telregels.csv` (pocket) | `…;gps_stab;gps_level` | `…;gps_level;richting;snelheid` |

Die eerste was de gevaarlijkste: `bezet` / `vrij` / `bezettingsgraad_pct` bestaan
in een fietstelling niet — dat zijn auto-kolommen. Er is geen bezettingsgraad
omdat fietsen geteld worden en niet tegen een capaciteit gelegd. In plaats
daarvan staat er `totaal`, de som van de vier typekolommen.

Bij pocket zijn `richting` en `snelheid` toegelicht, want ze gedragen zich per
modus anders: `transect` vult `richting` met het richtinglabel, `parkeren` met
`links` / `rechts`, `winkelstraat` laat `richting` leeg maar vult `snelheid` met
de loopsnelheid in m/s op het moment van de tik, en `simpel` laat beide leeg.

## 2. Twee hoofdtabellen die nergens beschreven stonden

De auto/fiets/capaciteit-`_telregels.csv` — zestien kolommen — had geen enkel
blok. Nu wel, met nadruk op het punt waar we het eerder over hadden: **twee
coördinatenparen per rij.** `lat_gps` / `lon_gps` is waar de telefoon was,
`lat_marker` / `lon_marker` het punt op straat, ~4 m naar de getelde kant.
Verder `zijde` (`L` / `R` / `N` bij vlak houden), `snapped`, en wat de vier
`hdg_`-kolommen precies zijn.

Hun `_gps.csv` had ook geen blok en heeft echt andere kolommen dan de
pocket-variant: `hdg_gps`, `hdg_kompas`, `hdg_fused`, `gesnapped`,
`kompas_bevroren` in plaats van `segment_index` / `straat`.

De kopregel is byte-identiek over de drie parkeer-apps, dus fiets en capaciteit
verwijzen naar het auto-blok in plaats van het te herhalen.

## 3. Reconstructiesectie: de kopregels erbij

De sectie beschreef wél wat er verandert, maar toonde nergens een kopregel.
Juist daar zitten **vier** schema's:

- `_sessie.csv` na reconstructie — één kolom erbij, `reconstructie`. Dat is de
  betrouwbare test voor "deze ZIP is gereconstrueerd"; de `_recon` in de
  bestandsnaam is conventie, dit is data.
- `_telregels.csv` in drie vormen, gekozen op profiel: wandel (twee varianten,
  met en zonder `richting`), pocket-parkeren, en auto/fiets.

Het belangrijkste punt daarbij: **lees op kolomnaam, nooit op positie.** De
auto-variant herordent namelijk — `lat_gps` / `lon_gps` staan er vóór
`lat_marker` / `lon_marker`, terwijl het rauwe bestand ze andersom heeft.
`recon_status` is de enige kolom die alle drie de vormen delen.

Ook toegevoegd: een kopregel en voorbeeld voor `_segmentsamenvatting.csv`
(tidy-long, één rij per segment × richting × categorie), en twee ontbrekende
regels in de reconstructietabel: `_bezocht_origineel.csv` en
`_reconstructie_log.csv`.

## 4. Ontbrekende ZIP-leden genoemd

`_kaart.png` en `.gpx` zitten in de drie parkeer-apps maar stonden in geen enkele
bestandslijst. Nu wel. `_snap_trace.csv` (pocket) en `_reconstructie_log.csv`
staan er alleen als **diagnostiek**, met één regel erbij dat ze niet voor
verwerking bedoeld zijn en dat hun kolommen met de snap-engine meebewegen. Zoals
afgesproken niet uitgeschreven.

## 5. Nieuwe test: `_archief/overpass_rig/test_zipref.py`

Trekt elke kopregel uit elk `csv-sample`-blok en elke header-string uit de zes
apps, en vergelijkt beide kanten op. Dat is precies de controle die ik nu met de
hand deed.

Drie soorten uitzonderingen, allemaal expliciet benoemd in het bestand:
- **diagnostiek** — bewust niet beschreven
- **bouwsteen** — een string die het begin is van een beschreven kopregel
  (`telreconstructie` stelt zijn wandel-header samen uit `basis` + `kwal`; de
  test bouwt hem net zo op)
- **alleen nog leesbaar** — zie hieronder

Draaien vanuit de suite-map:

```
python3 _archief/overpass_rig/test_zipref.py
```

Uitkomst nu: `REFERENTIE SLUIT AAN OP DE CODE`.

---

## 6. Wat de test aan het licht bracht en ik niet heb opgelost

**Geen enkele tool in de suite produceert nog `_trn.zip`.** Het losse
transect-formaat is vervangen door pocket's transect-modus (`_pkt_t.zip`).
`traffic_counter.html` is de statische telpost en schrijft een heel ander
bestand (`sep=;`, secties). `telrapport.html` heeft nog wel leescode voor
`app_type=transect`.

Dat is dus opnieuw een oud formaat — maar anders dan de passages die we in v2.53
schrapten weet ik hier niet of jouw archief ook op dit punt is omgezet. De
retrofit-scripts die je noemde (`relabel_modus.py`, `voeg_modusletter_toe.py`)
zetten geen `_trn` om naar pocket. Daarom heb ik de transect-sectie laten staan
en de test geleerd dat die kopregel bewust alleen nog leesbaar is, met de reden
erbij.

Twee mogelijkheden, jouw keuze:
- **Liggen er nog `_trn`-ZIP's** die je in telrapport laadt → sectie blijft, maar
  dan hoort er een regel bij dat er geen app meer is die ze maakt.
- **Zijn ze er niet meer** → de hele transect-sectie eruit, net als in v2.53, en
  dan kan de leescode in telrapport op dezelfde stapel als de andere
  terugvaltakken uit het vorige overdrachtsdocument.

---

## 7. Validatie

```
JS-syntax (node --check)                  15/15 OK
HTML-tagbalans, vergeleken met v2.53      geen afwijking
byte-identiteit                           alleen zip_format_reference.html
gedeelde blokken byte-identiek            6 groepen OK
test_zipref.py                            referentie sluit aan op de code
functionele tests                         34 + 18 + 16 + 9 OK
```
