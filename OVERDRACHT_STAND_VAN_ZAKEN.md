# Telonline Verkeerstellingen — stand van zaken

**Laatste release: v2.57.** Dit document is het startpunt voor een nieuwe sessie: wat er staat, welke afspraken vastliggen, wat er nog open is, en wat er nog van Jay's kant moet gebeuren. De losse `overdracht_v2_XX.md`-bestanden bevatten de details per release.

---

## 1. Wat het is

Suite van single-file HTML-tools voor Nederlandse verkeers- en parkeertellingen, op **telonline.org**. Alles draait in de browser, geen install, geen account. Veldwerk op iPhone/Safari; verwerking op desktop.

**Werkwijze in drie stappen:** tellen → ZIP → (optioneel) reconstrueren → presenteren in telrapport. Daarnaast QGIS als alternatief eindpunt.

### Bestanden in de suite
| Bestand | Rol |
|---|---|
| `index.html` | startscherm (tweetalig NL/EN) |
| `over.html` | publieke introductiepagina (NL) |
| `traffic_counter.html` | Static — telpost vanaf vast punt |
| `parkeertelling.html` | autoparkeren, lopend traject |
| `fietsparkeren.html` | fietsparkeren |
| `capaciteitstelling.html` | parkeercapaciteit |
| `pocket_count.html` | Pocket — 4 sub-modi (simpel/transect/winkelstraat/parkeren) |
| `telreconstructie.html` | nabewerking (hersnap, richting, handmatige correctie) |
| `telrapport.html` | kaartvisualisatie + analyse |
| `telplanning.html` | planning & dekking vooraf |
| `traffic_counter_help.html` | handleiding (NL, deels EN-mix) |
| `zip_format_reference.html` | technische ZIP-documentatie (EN) |
| `snap_methodology.html`, `snaptrace.html`, `winkelstraat_rekenrig.html` | interne reference/rig-tools, bewust niet gelinkt |

### Losse tools (buiten de suite, in outputs)
| Script | Doel |
|---|---|
| `telonline_qgis_loader.py` | laadt map met ZIP's recursief in QGIS: één laag per telptype, netwerklaag, GPS-route. Stippen op de **gecorrigeerde** markerpositie. Gepubliceerd op telonline.org. |
| `relabel_modus.py` | **klaar** — het archief is omgezet; bewaard voor het geval er ooit nog een oude ZIP opduikt. |
| `voeg_modusletter_toe.py` | **klaar** — idem. |
| `recon_qgis_loader.py` | oude naam van de QGIS-loader — vervangen door `telonline_qgis_loader.py`. |

> Het archief is volledig omgezet (sept 2026); nieuwe data komt alleen nog in het huidige formaat binnen. Zou er toch nog een oude ZIP opduiken: eerst `relabel_modus.py`, dan `voeg_modusletter_toe.py`.

---

## 2. Afspraken die vastliggen

**Naamconventie ZIP's**
`_car` → auto/parkeren · `_fts` → fiets/parkeren · `_cap` → capaciteit · `_trn` → transect · `_pkt_<s|t|w|p>` → pocket (simpel/transect/winkelstraat/parkeren).

**Modus-letter zit in de `sessie_id`**, niet alleen in de bestandsnaam (Route A). Daardoor overleeft hij reconstructie automatisch. Gevolg: het formaat van de KNIME-joinsleutel is gewijzigd.

**Type-woordenschat → modus** (voor ZIP's met lege/foute modus):
fiets/brommer/breed/wrak → fiets-parkeren · car/truck/moto/bike/ped → transect · stilstaand/tegemoet → winkelstraat · bezet/leeg/goed/fout/spec → parkeren · vrije tekst → simpel.
Eén fiets-woord volstaat om de hele sessie als fietstelling te markeren. Naam-markers winnen van inhoud.

**OSM-netwerk**: gedeelde `HIGHWAY_RE` (16 typen) in alle fetchende apps, plus `tunnel=building_passage`. Twee Overpass-endpoints (hoofdserver + private.coffee) — meer vrije, sleutelloze wereldwijde instanties bestaan niet. Elk antwoord wordt op ouderdom gekeurd (`OSM_MAX_LAG_DAGEN = 7`); te oud → volgende mirror.

**GPS-positie versus wegpositie**: telrapport tekent tikken op `lat_marker/lon_marker` (de positie op de weg) waar die kolom bestaat, anders op `lat/lon`. Geldt sinds v2.51 in álle laders, inclusief pocket. Rauwe parkeer-ZIP's dragen de live 4 m-offset in `lat_marker`; gereconstrueerde de routeconsistente positie. Wandelprofielen (transect/winkelstraat/simpel) kennen geen markerkolom. Clusters groeperen op `wayId|segIdx|zijde`, zodat links en rechts gescheiden blijven.

**Verzamel-ZIP** (v2.55): `TelVerzameling_<jjjjmmdd>.zip` met per telling een geneste `<sessie_id>.zip` plus `verzameling.json`. Genest, niet samengevoegd — `loadZip` pakt de eerste treffer per achtervoegsel, dus platte samenvoeging zou tellingen onzichtbaar maken. Correcties worden in de leden geschreven; `_kaart.png` gaat er niet in. De laadvolgorde in het manifest is bindend, want sessiekleuren hangen aan de volgorde van binnenkomst.

**Kaartafbeelding** (`_kaart.png`) zit **alleen** in parkeertelling/fietsparkeren/capaciteitstelling, niet in pocket/static.

**Gedeelde tegelcache**: veld-apps schrijven opgehaald netwerk in hetzelfde tegelformaat als de reconstructor (IndexedDB `telsuite_osm`). Een tegel gaat pas de cache in als hij **volledig** gedekt is (raster 8×8) — anders zou de reconstructor een half gevulde tegel als compleet lezen en stil wegen missen. Sinds v2.49 **lezen** de veld-apps de cache ook: alles-of-niets per fetch-cirkel, TTL 14 dagen (reconstructor houdt 60), schemaversie 2 (tegels dragen ook de straatnaam; oudere tegels tellen als misser en genezen zichzelf).

**Gedeelde Overpass-blokken** (houd byte-identiek, controleer met md5 na elke multi-file wijziging): `ovpKeur`-blok in 6 bestanden, `overpassFetch`-transport in telrapport + telreconstructie, `startRoadFetch`-discipline in de drie parkeer-apps. Pocket houdt een eigen ingang (`snapStartFetch`) omdat zijn discipline verweven is met de fid-volgordeguard en de trace-events, maar draait op hetzelfde model. Regressietests in `_archief/overpass_rig/`.

**Overpass-antwoorden worden geclassificeerd** (v2.49, gedeeld blok `ovpKeur`, byte-identiek in 5 bestanden): `ok` / `leeg` / `oud` / `limiet` / `fout`. Een leeg gebied is een geldig antwoord en wordt niet opnieuw bevraagd. Een rate-limit — ook als Overpass die als HTTP 200 met `remark` in de body stuurt — leidt tot 30s stilte zonder mirror-hop. Alle apps delen nu één backoff-model (`ovpBackoffMs`, 500·2ⁿ⁻¹, max 8s).

**Handoff "Direct reconstrueren"**: ZIP-blob via IndexedDB store `handoff` → `telreconstructie.html?handoff=1`. Knop aanwezig in alle vier veld-apps die door de reconstructor gaan.

---

## 3. Werkwijze in de samenwerking

- **Round-trip:** Jay bewerkt bestanden handmatig en levert ze terug; Claude integreert en valideert. Een regel context bij teruggave ("ik heb secties X en Y aangeraakt") maakt het sneller.
- **Validatie elke release:** inline JS extraheren → `node --check`; HTML-tagbalans; functionele test waar zinvol; **byte-identiteit** (alleen de bedoelde bestanden mogen wijzigen).
- **Elke release** krijgt een `overdracht_v2_XX.md` en een volledige ZIP.
- **Additief werken**: bestaande logica byte-identiek laten waar mogelijk.
- Ontwerp eerst bespreken bij niet-triviale keuzes; terse goedkeuring = go.

---

## 4. Nog te doen door Jay (buiten de code)

1. **Screenshots voor `over.html`** — nog niet geleverd. Drie bestanden, exact deze namen, naast `over.html`:
   `screenshot-tellen.jpg` · `screenshot-nabewerken.jpg` · `screenshot-telrapport.jpg`
   Zolang ze ontbreken toont de pagina een nette placeholder met de verwachte bestandsnaam. (PNG kan, vergt dan een `src`-aanpassing.)
2. **KNIME aanpassen** op het nieuwe `sessie_id`-formaat (met modus-letter).
3. **Testen in het veld** van de recente toevoegingen: audio-feedback en dekkingskaart in pocket parkeren, en de automatische ZIP-download na Stop in de drie parkeer-apps.
4. **Testen in het veld van v2.49**: herhaald gebied (hoort nul Overpass-verzoeken te kosten), nieuw gebied, gebied zonder OSM-wegen, slecht bereik. Let vooral op of straatnamen in `_netwerk.csv` compleet blijven — dat is de gevoeligste plek van de cache-route. Zie `overdracht_v2_49.md` §9.
5. **KNIME**: `snap_path` in `snap_trace.csv` begint sinds v2.49 met `bron:fetch|` / `bron:tegel|` / `bron:leeg|`, en de `event`-kolom kent twee nieuwe waarden (`tegelcache`, `fetch_leeg`). Vrije-tekstkolommen, dus formeel geen schemawijziging — maar een node die op de exacte vorm parst moet mee.

---

## 5. Backlog (niets besloten)

**Klein / afgebakend**
- Reconstructiescript een losse kaart-PNG naast de `_recon.zip` laten schrijven (afgesproken bij v2.55, nu `_kaart.png` niet meer in de verzameling meegaat).
- `probeBbox` leren omgaan met verzamelingen; nu is het bbox-filter daar fail-open en doet het dus niets.
- Besluiten over het losse transect-formaat (`*_trn.zip`): geen enkele app maakt het nog (pocket's transect-modus `_pkt_t` verving het), maar telrapport leest het wel. Liggen er nog `_trn`-ZIP's in het archief? Zo nee: sectie uit de referentie én de leescode in telrapport eruit.
- Terugvalcode voor oude formats opruimen (telrapport r.998/1044/1736/1872/2090, telplanning r.885). Die op r.1872 haalt geometrie via Overpass op als `_netwerk.csv` ontbreekt — een van de laatste netwerkverzoeken in de suite, en alleen voor ZIP's die niet meer bestaan. Wel met een expliciete melding erbij, zodat een niet-omgezette ZIP luid faalt in plaats van stil.
- Twee bevroren versiestempels in `telreconstructie.html` die elkaar tegenspreken: `_sessie.csv` schrijft `reconstructie=v2.24` (r.1802), het log schrijft `reconstructie_versie=v2.18` (r.1820). Raakt KNIME, dus jouw sign-off.
- Tegenstrijdig commentaar in `capaciteitstelling.html`: `exportZip()` zegt dat `_terrein.csv` een eigen schema heeft (osm_id+osm_type, geen zijde), terwijl `buildTerreinCsvString()` bewust dezelfde header als `_capaciteit.csv` schrijft. Eén van de twee moet weg.
- `zoekTerreinen` in `capaciteitstelling.html` ontdubbelen op afstand tot het vorige zoekcentrum: vuurt nu één Overpass-verzoek per kaartpan, zonder cache.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>` voor consistentie (Jay's keuze — hij schreef die sectie zelf).
- Engelse variant van `over.html`.

**Meetkunde (vraagt veldtest)**
- Fetch-radius en verversafstand losser zetten. Nu radius 300 m en verversen op 150 m, dus 69% van elke fetch is al bekend gebied. Radius 300 / verversen op 220 m scheelt een derde van de verzoeken; radius 500 / verversen op 350 m halveert ze tegen 19% meer bytes. Voor Overpass tellen verzoeken zwaarder dan bytes.
- Gebied vooraf ophalen vanuit `telplanning.html`, zodat de cache gevuld is vóór je de deur uitgaat en het veldwerk met nul verzoeken telt.

**Uitrollen als het bevalt**
- Audio-feedback (nu alleen pocket parkeren) naar andere tel-modi.
- Dekkingskaart (nu alleen pocket parkeren) naar andere tel-modi; eventueel links/rechts-stippen uit elkaar trekken.

**Groter / vraagt ontwerp**
- Parkeren uit pocket halen naar een eigen modus/tool (parkeren = toestand, geen stroom).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten (proeftuin bestaat).
- %bezet per dag×uur-cel — vraagt tik-met-tijd-én-categorie; schema/KNIME-afstemming nodig.
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` (bezetting per weglijn).

---

## 6. Releases v2.32 → v2.48 in één oogopslag

| Versie | Kern |
|---|---|
| v2.32 | Carto API-key toegevoegd; verouderd Fastly-domein gemoderniseerd |
| v2.33 | Jay's herschreven `over.html` + handleiding ingepast (2 markup-fixes) |
| v2.34 | Rebrand rvmk.nl → telonline.org, productnaam "Telonline Verkeerstellingen" |
| v2.35 | Engelse docs dragen het domein i.p.v. de NL productnaam |
| v2.36 | `building_passage` geharmoniseerd over alle fetchende apps |
| v2.37 | Audio-feedback (klik) in pocket parkeren |
| v2.38 | Dekkingskaart in pocket parkeren (netwerk + route + tik-stippen) |
| v2.39 | Tik-toon per status (bezet 440 Hz / vrij 392 Hz); dunnere stiprand |
| v2.40 | Knoppenbalk pocket parkeren naar flex (geen overlap meer) |
| v2.41 | Automatische ZIP-download na Stop in de drie parkeer-apps |
| v2.42 | Volledigheidsmelding "X/Y geclusterd" per sessie in telrapport |
| v2.43 | "Direct reconstrueren"-knop + gedeelde OSM-tegelcache |
| v2.44 | Reconstrueren-knop ook in pocket (preview-overlay) |
| v2.45 | Reconstructie-uitleg in gebruikerstaal + hernoeming naar `telreconstructie.html` |
| v2.46 | Capaciteitscontouren + labels standaard uit bij opstarten |
| v2.47 | Overpass-mirror → private.coffee; QGIS-loaderlink ingevuld |
| v2.48 | Verse-data-garantie: elk Overpass-antwoord op ouderdom gekeurd |
| v2.49 | Tegelcache wordt gelezen; Overpass-antwoorden geclassificeerd; één backoff-model |
| v2.50 | `telrapport.html` op het gedeelde Overpass-transport; `haalWayGeometrie()` |
| v2.51 | Pocket-parkeren tekent en clustert op de wegpositie; `zijde` splitst links/rechts |
| v2.52 | `_capaciteit.csv` en `_netwerk.csv` correct beschreven in de ZIP-referentie |
| v2.53 | Documentatie beschrijft alleen nog het huidige formaat; legacy-passages eruit |
| v2.54 | ZIP-referentie sluit weer aan op de exportcode; test bewaakt dat voortaan |
| v2.55 | Verzamel-ZIP: hele kaart bewaren en in één handeling terugladen |
| v2.56 | Verzamel-ZIP genoemd in `over.html` (stap 3) |
| v2.57 | TL;DR-blok bovenaan `over.html` voor de snelle passant |

---

## 7. Methodiek-conclusie telrapport (ter naslag)

Op verzoek doorgelicht: de clustering is **zuiver** — elk kwalificerend punt telt precies één keer, geen dubbeltelling. Bij **gereconstrueerde** ZIP's zit elk geteld punt in een cluster. Bij **rauwe** auto/fiets-ZIP's kunnen ongesnapte tikken buiten de clusters vallen; die zijn wél zichtbaar als vervaagde ⚠-stip, en `n_waarnemingen` blijft het volledige aantal. Sinds v2.42 meldt elke sessie zelf "X/Y geclusterd", dus je ziet direct of de kaart volledig is voordat je conclusies trekt.
