# Telonline Verkeerstellingen — stand van zaken

**Laatste release: v3.1.** Telrapport bewaart de kaart als GeoPackage met opmaak voor QGIS (`overdracht_v3_1.md`). 3.0 was de in het veld geteste v2.77; sinds 3.0 maakt GitHub per release automatisch een ZIP (zie §3).

---

## 1. Wat het is

Suite van single-file HTML-tools voor Nederlandse verkeers- en parkeertellingen, op **telonline.org**. Alles draait in de browser, geen install, geen account. Veldwerk op iPhone/Safari; verwerking op desktop.

**Werkwijze in drie stappen:** tellen → ZIP → (optioneel) reconstrueren → presenteren in telrapport. Daarnaast QGIS als alternatief eindpunt.

### Bestanden in de suite
| Bestand | Rol |
|---|---|
| `index.html` | startscherm (tweetalig NL/EN), ingedeeld naar wat je telt (v2.69) |
| `over.html` | publieke introductiepagina (NL) |
| `traffic_counter.html` | Static — telpost vanaf vast punt; noodopslag + doortellen sinds v2.72; export in suitevorm sinds v2.73 (`<sid>_sta.zip`); Engelstalig |
| `parkeertelling.html` | autoparkeren, lopend traject |
| `fietsparkeren.html` | fietsparkeren |
| `capaciteitstelling.html` | parkeercapaciteit |
| `pocket_count.html` | Pocket — 4 sub-modi (simpel/transect/winkelstraat/parkeren); parkeren heeft een eigen ingang `#parkeren` (v2.69) |
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

### Aparte tak: `gpx_snap.html`
Sinds v2.65 **geen deel meer van de suite**. Gaat verder als eigen tak (startpunt = de stand van v2.64, byte-identiek), met zijn eigen tests (`functest_gpxsnap.js`, `functest_grofspoor.js`, `functest_osrm.js`, `meet_grofspoor.js`). De tak draagt een kopie van de rekenkern van `telreconstructie.html`; de suite kijkt niet naar de tak. De afhankelijkheid loopt één kant op: de tak mag de suite volgen, niet andersom.

> Het archief is volledig omgezet (sept 2026); nieuwe data komt alleen nog in het huidige formaat binnen. Zou er toch nog een oude ZIP opduiken: eerst `relabel_modus.py`, dan `voeg_modusletter_toe.py`.

---

## 2. Afspraken die vastliggen

**Zijde-offset van 4 meter** (waarom je veilig op het fietspad kunt blijven lopen): een parkeertik wordt eerst naar de wegas gesnapt — dat haalt je loopafstand eraf — en daarna 4 m haaks opzij gezet, naar de kant die je hebt aangegeven. `parkeertelling.html` doet dit **live** bij elke tik (`SIDE_OFFSET_M = 4`, via `snapToRoad()` + `offsetPoint()`); de kant komt uit de kanteling van de telefoon. `pocket_count.html` doet dit **niet** — daar is links/rechts alleen een label (ring om de stip) en blijft het coördinaat rauwe GPS. `telreconstructie.html` past het voor beide alsnog toe (`OFFSET_M = 4`), waarbij pocket de zijde afleidt uit het links/rechts-label en auto/fiets de veld-`zijde` als grondwaarheid houdt. Gevolg: een **ongereconstrueerde** pocket-parkeertelling staat in telrapport als GPS-wolk, een parkeertelling ernaast in nette rijtjes.

De 4 staat in **vijf** bestanden: `SIDE_OFFSET_M` in de drie parkeer-apps (live plaatsing), `OFFSET_M` in `telreconstructie.html` en in `telrapport.html` (de correctietool: een versleepte tik landt ook 4 m uit de as). Sinds v2.66 bewaakt `valideer.py` dat de waarde overal gelijk is; elke declaratie verwijst in zijn commentaar naar die controle. Vier zichtbare teksten noemen de 4 m ook (kop van de reconstructor, handleiding, ZIP-referentie, commentaar in telrapport) — die zijn niet bewaakt en moeten bij een wijziging met de hand mee.

**Welk coördinaat op de telrapport-kaart staat** (vastgelegd v2.60, test `functest_coordinaten.js`): auto/fiets/capaciteit-vakken → `lat_marker`/`lon_marker` · pocket → `tikPositie()` (marker indien aanwezig, anders `lat`/`lon`) · transect → `lat`/`lon` (dit profiel krijgt ook na reconstructie geen markerkolom) · standstill → GPS uit de metakop · capaciteitsterrein → POLYGON uit `_netwerk.csv`, label op `poly.getCenter()`. Clusterbollen staan altijd op het zwaartepunt van hun groep en tonen sinds v2.61 de typeverdeling als taartdiagram (vaste puntvolgorde uit `APP_CONFIG.types`, totaal in een donutgat, vlak onder 26 px; een gecombineerd cluster van meerdere sessies houdt zijn diagonale tweekleur). Groepen zonder geometrie krijgen **geen** marker; de sessierij meldt het.

**Reconstructie verandert de `sessie_id` niet.** Alleen de bestandsnaam wordt `<sessie_id>_recon.zip`; de leden binnenin houden hun originele namen. Origineel en reconstructie dragen dus dezelfde identiteit — telrapport ziet ze als één sessie en laadt er één. Sinds v2.59 is dat de gereconstrueerde. Het onderscheid zit in de kolom `reconstructie` in `_sessie.csv`, niet in de naam. **Relevant voor KNIME**: joinen op `sessie_id` gooit origineel en reconstructie op één hoop.

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

**Carto-sleutel** staat in drie bestanden: `telrapport.html`, `telplanning.html` en `telreconstructie.html`. Eén sleutel, drie plekken om aan te passen als hij vervalt — plus `gpx_snap.html` in de aparte tak.

**Geen externe matcher in de suite.** Sinds v2.65 stuurt geen enkele suite-tool een spoor naar een externe dienst; OSRM leeft alleen nog in de gpx-tak.

**`hopClass` begrenst de matcher op twee hops**: 0 = zelfde way, 1 = buur, 2 = buur-van-buur, daarboven `Infinity` — die overgang bestaat niet. Bij sprongen groter dan ~60 m in een stratennet zijn dat er al snel drie, en dan blijft de Viterbi-kolom leeg en herstart de matcher met alleen emissiekosten (de *stuksgewijze backtrack*). Het klapt niet, maar is op dat punt gedegradeerd tot "dichtstbijzijnde way" — zonder dat je dat aan de uitvoer ziet. De gpx-tak vangt dat sinds v2.63 af met tussenpunten (hoge `acc`, dus vlakke emissie: steiger, geen waarneming). **`telreconstructie.html` heeft die opvang niet.** Voor lopende sessies is dat zelden een probleem; voor de geplande post-hoc reconstructie van autoritten wel, want op rijsnelheid zijn sprongen van 60 m+ de regel.

**Highway-voorkeur per profiel** (werkt sinds v2.67; beschreven in v2.18 maar kwam tot v2.67 nooit aan in de matcher): `auto` geeft de rijbaan voorrang boven fiets- en voetpaden, `fiets` omgekeerd. Het is een extra term in de emissiekost: −2 voor geprefereerd, +4 voor vermeden. Met acc 5 m trekt een geprefereerde weg tot ruim 17 m afstand; verder weg wint de weg waar je op staat. Is er alleen het vermeden type, dan wordt dat alsnog gekozen. De wandelprofielen en pocket-parkeren zijn neutraal en rekenen exact als vóór v2.67 (300 willekeurige gevallen, byte-gelijk). Een recon-ZIP draagt in `_reconstructie_log.csv` de regel `highway_voorkeur`; **ontbreekt die regel, dan is de ZIP van vóór v2.67** en is de voorkeur niet toegepast.

**Noodopslag en doortellen** (v2.71 getoetst, v2.72 compleet; `hersteltest.py`: harde crash zonder enige afsluit-gebeurtenis, nep-Overpass zodat er echt gesnapt wordt). **Alle vijf veld-apps** slaan de telling bij elke tik op in `localStorage` en bij scherm-uit/app-wissel nog eens: parkeertelling, fietsparkeren, capaciteit (`<app>_sessie`, wegennet apart in `<app>_sessie_netwerk`), pocket (`pocket_sessie`, alle vier de modi) en sinds v2.72 Static (`static_sessie`, plus een hartslag elke 10 s). Na herladen komt een herstelmelding met **Doortellen**, Download en Verwijder. Doortellen gaat verder in dezelfde telling: zelfde sessie-id (parkeer-apps), zelfde starttijd, alles in één ZIP; de onderbreking is een gat in het GPS-spoor. **Static telt de onderbreking niet mee**: de tijd tussen de laatste hartslag en Doortellen gaat als `Interruption`-regel in de CSV en valt buiten `Observed duration` en de uurfactor (anders trekt een pauze de intensiteit per uur omlaag); zonder onderbreking is de export ongewijzigd. Een nieuwe telling starten terwijl er een herstelde klaarstaat, vraagt eerst bevestiging (alle apps). Pocket bewaart het wegennet en de snap-trace niet in de noodopslag: na herstel zonder doortellen ontbreken `_netwerk.csv` en `_snap_trace.csv`. Grenzen: GPS-punten na de laatste tik/hartslag gaan bij een harde crash verloren; de opslag is ~5 MB voor heel telonline.org en een volle opslag stopt de noodkopie zonder melding (~0,5 kB per tik met GPS-punt in parkeertelling, ~0,3 kB in pocket).

**Opruimen na de export** (v2.76, `opruimtest.py`): de noodkopie verdwijnt **zodra de ZIP aantoonbaar is opgeslagen, en niet eerder**. Aantoonbaar = het iOS-deelblad is voltooid (de share-belofte slaagt), of de download is aan de browser overgedragen (desktop/Android). Geannuleerd of gebaar verlopen: de kopie blijft, en de tool biedt de telling de volgende keer weer aan. Na de bevestiging schrijft niets de kopie opnieuw weg (pocket: `exportAfgerond`; Static: `geexporteerd` blokkeert `bewaarStatic`). In pocket geldt *Sluiten* op het voorbeeldscherm ook als bevestiging (ongewijzigd sinds v2.11). De parkeer-apps volgen sinds v2.77 dezelfde regel (gedeeld blok `bewaarZip`, bewaakt): geannuleerd deelvenster → geen ongevraagde download, kopie blijft, statusregel *ZIP niet opgeslagen*, en de ZIP-knop biedt dezelfde ZIP opnieuw aan zonder opnieuw in te pakken (sleutel: sessie-id + aantallen, dus nooit de ZIP van een vorige sessie). Ze schrijven het wegennet alleen nog weg tijdens een lopende sessie, en Stop annuleert een wachtende fetch. Blijvend en bedoeld: taal, tellernaam, kantelmodus, en de wegennet-cache in IndexedDB (openbare OSM-data; legen via telreconstructie of de websitegegevens).

**Voorpagina: ingedeeld naar wat je telt** (v2.69). Drie groepen: *Verkeer tellen — wat komt er langs* (stroom: stilstaand, pocket in beweging), *Parkeren tellen — wat staat er* (toestand: pocket-parkeren eerst, dan parkeertelling, fietsparkeren, capaciteit) en *Achter je bureau* (planning, reconstructie, rapport, compact onderaan). Een nieuwe tool krijgt een plek in de groep die past bij de vraag, niet bij hoe hij gebouwd is. De kaartteksten zeggen wanneer je welke kiest, vooral binnen parkeren. Pocket-parkeren is **geen eigen tool**: de kaart linkt naar `pocket_count.html#parkeren`. Via die ingang gedraagt pocket zich als parkeer-app en verschijnt het keuzemenu met vier modi **nooit** (v2.70): meteen het parkeerscherm; Terug gaat naar de voorpagina; na Stop en het voorbeeldscherm een verse parkeertelling. Bij een onderbroken telling of als er geen voorbeeldscherm komt (geen GPS-spoor), blijft van het keuzescherm alleen de Parkeren-knop over. Het verbergen gebeurt met de klasse `.pk-ingang` op `<html>`, gezet in `<head>` vóór de eerste weergave, zodat het menu ook niet even zichtbaar is.

**Rekenkern**: `RECON`, `MATCHER` en `OSMCACHE` staan binnen de suite alleen nog in `telreconstructie.html`; `splitWayIntoSegments` byte-identiek in `telreconstructie.html` en `pocket_count.html`. Bewaakt door `valideer.py` (de groepen met één bestand blijven staan als ankercontrole). De gpx-tak draagt een kopie op de stand van v2.64 — hoe die kopie de suite volgt is nog niet besloten (zie backlog). Sinds v2.67 wijkt `MATCHER` af van die kopie (vijfde parameter); de tak geeft geen voorkeur mee, dus daar verandert het gedrag niet als hij de nieuwe versie overneemt.

**Gedeelde Overpass-blokken** (houd byte-identiek, controleer met md5 na elke multi-file wijziging): `ovpKeur`-blok in 6 bestanden, `overpassFetch`-transport in telrapport + telreconstructie, `startRoadFetch`-discipline in de drie parkeer-apps. Pocket houdt een eigen ingang (`snapStartFetch`) omdat zijn discipline verweven is met de fid-volgordeguard en de trace-events, maar draait op hetzelfde model. Regressietests in `_archief/overpass_rig/`.

**Overpass-antwoorden worden geclassificeerd** (v2.49, gedeeld blok `ovpKeur`, byte-identiek in 6 bestanden): `ok` / `leeg` / `oud` / `limiet` / `fout`. Een leeg gebied is een geldig antwoord en wordt niet opnieuw bevraagd. Een rate-limit — ook als Overpass die als HTTP 200 met `remark` in de body stuurt — leidt tot 30s stilte zonder mirror-hop. Alle apps delen nu één backoff-model (`ovpBackoffMs`, 500·2ⁿ⁻¹, max 8s).

**Handoff "Direct reconstrueren"**: ZIP-blob via IndexedDB store `handoff` → `telreconstructie.html?handoff=1`. Knop aanwezig in alle vier veld-apps die door de reconstructor gaan.

---

## 3. Werkwijze in de samenwerking

- **Round-trip:** Jay bewerkt bestanden handmatig en levert ze terug; Claude integreert en valideert. Een regel context bij teruggave ("ik heb secties X en Y aangeraakt") maakt het sneller.
- **Validatie elke release:** inline JS extraheren → `node --check`; HTML-tagbalans; functionele test waar zinvol; **byte-identiteit** (alleen de bedoelde bestanden mogen wijzigen).
- **Elke release** krijgt een `overdracht_vX_Y.md` en een volledige ZIP. Sinds v3.0 maakt GitHub die ZIP zelf: na de merge naar `main` ziet `.github/workflows/release.yml` het nieuwe nummer in `index.html` en maakt een release met tag, `telsuite-<versie>.zip` en de overdracht als tekst. Wat niet in de ZIP gaat (ontwikkelspul en `planningen/.htaccess`) staat in `.gitattributes`.
- **Laadtest bij wijzigingen aan de opstart van een pagina** (sinds v2.69): `laadtest.py` laadt elke pagina echt in Chromium en faalt op elke JS-fout bij het opstarten. `node --check` en de tagbalans zagen de dode herstelfunctie van pocket niet.
- **Versienummer ophogen bij elke release** (sinds v2.68, op verzoek van Jay): het staat zichtbaar onderaan `index.html` (`<div class="versie">`). Eén nummer op vier plekken: `RELEASE` in `valideer.py`, `index.html`, "Laatste release" hier, en de naam van de overdracht. `valideer.py` faalt als één ervan afwijkt of als het nummer niet hoger is dan in de vorige release. Daardoor staat `index.html` voortaan in élke release bij de gewijzigde bestanden.
- **Additief werken**: bestaande logica byte-identiek laten waar mogelijk.
- Ontwerp eerst bespreken bij niet-triviale keuzes; terse goedkeuring = go.

---

## 4. Nog te doen door Jay (buiten de code)

0. **GeoPackage in QGIS 4 bekijken (v3.1)** — in telrapport een paar tellingen laden, *bewaar kaart als GeoPackage (QGIS)*, het bestand in QGIS 4 slepen en alle lagen kiezen. Verwacht: stippen in de kleuren van telrapport, clusterbollen als taartdiagram met een wit cijfer, gekleurde wegvakken en een gestreept GPS-spoor, elk met een legenda. Getest is tegen QGIS 3.34; QGIS 4 kon hier niet. Wijkt iets af (vooral de cijfers in de bollen: vet en wit?), dan een schermafbeelding.
0a. **Planningmap afschermen (v2.75), vóór het online zetten** — een wachtwoordbestand maken buiten de webroot en het volledige pad invullen bij `AuthUserFile` in `planningen/.htaccess`. Controle in een privévenster: `https://telonline.org/planningen/planning_list.php` moet om een wachtwoord vragen. Vraagt hij niets, dan leest de server geen `.htaccess` en is de map open. Zolang het pad niet klopt, geeft de map een 500-fout (dicht, niet open) en meldt telplanning dat.
0b. **Contactgegevens in `privacy.html` invullen** — het gele veld bij *Je rechten en contact* (naam en e-mailadres van de beheerder). `valideer.py` meldt het zolang het er staat.
1. **Screenshots voor `over.html`** — nog niet geleverd. Drie bestanden, exact deze namen, naast `over.html`:
   `screenshot-tellen.jpg` · `screenshot-nabewerken.jpg` · `screenshot-telrapport.jpg`
   Zolang ze ontbreken toont de pagina een nette placeholder met de verwachte bestandsnaam. (PNG kan, vergt dan een `src`-aanpassing.)
2. **KNIME aanpassen** op het nieuwe `sessie_id`-formaat (met modus-letter).
3. **Testen in het veld** van de recente toevoegingen: audio-feedback en dekkingskaart in pocket parkeren, en de automatische ZIP-download na Stop in de drie parkeer-apps.
4. **Testen in het veld van v2.49**: herhaald gebied (hoort nul Overpass-verzoeken te kosten), nieuw gebied, gebied zonder OSM-wegen, slecht bereik. Let vooral op of straatnamen in `_netwerk.csv` compleet blijven — dat is de gevoeligste plek van de cache-route. Zie `overdracht_v2_49.md` §9.
5. **Server**: `gpx_snap.html` hoort niet meer bij de suite. Blijft hij op telonline.org staan (als losse tool), of verhuist hij? Hij had al geen links vanuit de suite, dus weghalen breekt niets.
6. **KNIME**: `snap_path` in `snap_trace.csv` begint sinds v2.49 met `bron:fetch|` / `bron:tegel|` / `bron:leeg|`, en de `event`-kolom kent twee nieuwe waarden (`tegelcache`, `fetch_leeg`). Vrije-tekstkolommen, dus formeel geen schemawijziging — maar een node die op de exacte vorm parst moet mee.
7. **KNIME: Static heeft sinds v2.73 een ZIP in suitevorm** — `<sid>.zip` (sid eindigt op `_sta`) met `_sessie.csv` (pocket-kolommen + `lat;lon;nauwkeurigheid;straat;plaats;notities;actieve_duur_s;uurfactor`, `app_type` = `standstill`), `_telregels.csv` (`sessie_id;nr;tijdstip;type;richting;lat;lon;nauwkeurigheid`, tijdstip mét datum), `_onderbrekingen.csv` (alleen na doortellen) en het oude leesbare overzicht als `_overzicht.csv`. Wie Static nu nog in KNIME inleest via het overzicht, kan dat blijven doen; de nieuwe bestanden maken Static een gewone sessie. Voor uurintensiteiten `actieve_duur_s` of `uurfactor` gebruiken, niet eind − start.

---

## 5. Backlog (niets besloten)

**Klein / afgebakend**
- Kop van de handleiding zegt nog "Traffic Counter Help" (naam van vóór de rebrand in v2.34) en spreekt de nieuwe `<title>` tegen. Zichtbare tekst, dus Jay's keuze.
- Hetzelfde metadatablok op `zip_format_reference.html`; dat heeft nu alleen een `<title>`.
- `robots.txt` en `sitemap.xml` op de server (Jay's kant).
- Reconstructiescript een losse kaart-PNG naast de `_recon.zip` laten schrijven (afgesproken bij v2.55, nu `_kaart.png` niet meer in de verzameling meegaat).
- `probeBbox` leren omgaan met verzamelingen; nu is het bbox-filter daar fail-open en doet het dus niets.
- Besluiten over het losse transect-formaat (`*_trn.zip`): geen enkele app maakt het nog (pocket's transect-modus `_pkt_t` verving het), maar telrapport leest het wel. Liggen er nog `_trn`-ZIP's in het archief? Zo nee: sectie uit de referentie én de leescode in telrapport eruit.
- Terugvalcode voor oude formats opruimen (telrapport r.998/1044/1736/1872/2090, telplanning r.885). Die op r.1872 haalt geometrie via Overpass op als `_netwerk.csv` ontbreekt — een van de laatste netwerkverzoeken in de suite, en alleen voor ZIP's die niet meer bestaan. Wel met een expliciete melding erbij, zodat een niet-omgezette ZIP luid faalt in plaats van stil.
- Tegenstrijdig commentaar in `capaciteitstelling.html`: `exportZip()` zegt dat `_terrein.csv` een eigen schema heeft (osm_id+osm_type, geen zijde), terwijl `buildTerreinCsvString()` bewust dezelfde header als `_capaciteit.csv` schrijft. Eén van de twee moet weg.
- `zoekTerreinen` in `capaciteitstelling.html` ontdubbelen op afstand tot het vorige zoekcentrum: vuurt nu één Overpass-verzoek per kaartpan, zonder cache.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>` voor consistentie (Jay's keuze — hij schreef die sectie zelf).
- Engelse variant van `over.html`.


**Lessen uit de gpx-tak die terug kunnen**
- Verdichten (steigerpunten, v2.63) voor `telreconstructie.html` — nodig zodra de autorit-reconstructie gebouwd wordt (`hopClass` breekt boven twee hops).
- Ketting-breuken zichtbaar maken (plekken waar de matcher herstart met `back = null`) — geldt voor de reconstructor net zo goed.
- Synchronisatiebeleid voor de rekenkern-kopie in de tak: meelopen met de suite, bewust bevriezen, of een controle in de tak die de afwijking alleen meldt.

**Meetkunde (vraagt veldtest)**
- Fetch-radius en verversafstand losser zetten. Nu radius 300 m en verversen op 150 m, dus 69% van elke fetch is al bekend gebied. Radius 300 / verversen op 220 m scheelt een derde van de verzoeken; radius 500 / verversen op 350 m halveert ze tegen 19% meer bytes. Voor Overpass tellen verzoeken zwaarder dan bytes.
- Gebied vooraf ophalen vanuit `telplanning.html`, zodat de cache gevuld is vóór je de deur uitgaat en het veldwerk met nul verzoeken telt.

**Uitrollen als het bevalt**
- Audio-feedback (nu alleen pocket parkeren) naar andere tel-modi.
- Dekkingskaart (nu alleen pocket parkeren) naar andere tel-modi; eventueel links/rechts-stippen uit elkaar trekken.

**Na de reparatie van v2.67**
- Oude auto- en fietsreconstructies (vóór v2.67) opnieuw draaien of laten staan? Herkenbaar aan het ontbreken van `highway_voorkeur` in de log. Het verschil zit alleen waar een fietspad of voetpad binnen ~17 m van de rijbaan ligt.

**Groter / vraagt ontwerp**
- **Autorit-reconstructie — geparkeerd** (v2.67: Jay telt zelden vanuit de auto). De highway-voorkeur, het grootste obstakel, is sinds v2.67 opgelost. Wat nog ontbreekt: een tijdspoort plus verdichten, een rit-profiel met herkenning, en bij lange ritten een corridor-fetch en een ruimtelijke index. Analyse en volgorde in `overdracht_v2_66.md` §4.
- Zijde-offset live in pocket-parkeren? De ingrediënten zijn er (de gesnapte positie en de wegrichting kent pocket al), zo'n vijftien regels. Twee bezwaren: het voegt `lat_marker`/`lon_marker`/`zijde` toe aan het rauwe pocket-schema en vraagt dus KNIME-afstemming, én "links" is bij pocket relatief aan de looprichting, die de app op het moment van tikken minder zeker kent dan de reconstructor achteraf uit de hele route — precies de reden dat de reconstructor bestaat. Winst is vooral cosmetisch: ongereconstrueerde pocket-parkeertellingen zien er in telrapport dan net zo uit als parkeertellingen.
- "Save as .png" in telrapport: het kaartbeeld exporteren. De knop is triviaal, het plaatje niet. Tegels zijn niet CORS-schoon (`L.tileLayer` zet geen `crossOrigin`), vectoren zitten in vijf SVG-panes, labels zijn acht `divIcon`-varianten. Drie routes: handgetekend canvas zonder ondergrond (patroon van de veld-apps), eigen tegel-compositor (~150 regels, geen afhankelijkheid), of `html2canvas` van een CDN. Voorstel: tegel-compositor met automatische terugval naar zonder-ondergrond bij een SecurityError. Eerst de CORS-test draaien op OSM/CARTO/PDOK; de bronvermelding moet sowieso in de PNG gebakken worden.
  *v3.1:* voor het rapportpad is er nu de GeoPackage voor QGIS (daar zitten ondergrond, schaalstok en PDF-export al in). Een PNG uit telrapport blijft nuttig voor het snelle plaatje.
- **GeoPackage stap 2: QGIS-project in de GeoPackage** (tabel `qgis_projects`): ondergrond, laagvolgorde, RD New, ingezoomd op de telling, en een printopmaak met titel, legenda, schaalstok en noordpijl. Eerst een proef: hoe vindt QGIS de lagen terug als het project in hetzelfde bestand zit en je dat bestand verplaatst?
- **GeoPackage: capaciteitsterreinen en Static** als eigen lagen (`terreinen`, `telposten`). Nu meldt de export dat ze niet meegaan.
- QGIS-loader (`telonline_qgis_loader.py`) op QGIS 4 testen (Qt6, opgeschoonde Python-API); eventueel dezelfde stijlsjablonen gebruiken als de GeoPackage-export, zodat de opmaak op één plek bestaat.
- Parkeren uit pocket halen naar een eigen tool. Sinds v2.69 heeft het een eigen ingang op de voorpagina (`#parkeren`), wat het grootste deel van de wens dekt. Een echte afsplitsing loont pas als parkeren een eigen kant op gaat (bijv. de zijde-offset live), want dan moeten GPS, snap, fetch-discipline en noodopslag in twee bestanden gelijk blijven.
- `over.html` volgt de nieuwe indeling van de voorpagina nog niet (v2.69). De handleiding is in v2.74 bijgewerkt.
- Volle opslag wordt niet gemeld: `setItem` faalt stil in een `try/catch`, en vanaf dat moment is er geen noodkopie meer. Een zichtbare waarschuwing ("noodopslag vol, download tussendoor") in alle vier de apps.
- Wegennet-cache (IndexedDB) ruimt oude tegels nooit op; TTL bepaalt alleen of een tegel vers genoeg is. Automatisch opruimen van tegels ouder dan bijvoorbeeld 90 dagen, in de gedeelde blokken (`leesTegels`/`OSMCACHE`). Privacy en opslagruimte.
- `hersteltest.py` is soms wisselvallig: 1 FOUT in 1 van 4 runs bij v2.75, op ongewijzigde apps. Vaste wachttijden (250 ms per GPS-stap, 1,2 s op een ZIP) vervangen door wachten tot een voorwaarde klopt, en de uitvoer van elke run bewaren.
- Google Fonts zelf hosten: haalt Google uit de lijst met derden in de privacyverklaring (v2.75). Optioneel.
- Veld-apps melden niet als een planning niet geladen kan worden (bijv. geweigerd door de afscherming): de geplande wegen verschijnen dan gewoon niet. Via telplanning op hetzelfde toestel speelt dit niet, want de login geldt dan al.
- Static is Engelstalig, terwijl de andere veld-apps Nederlands zijn en voorpagina en pocket tweetalig (audit v2.72; de andere drie auditpunten zijn in v2.73 opgelost).
- Pocket vraagt het scherm-aan-slot één keer aan bij de start, maar niet opnieuw als je de app even verlaat (de browser geeft het slot dan vrij). Op het parkeerscherm na een directe ingang vraagt de eerste tik het wel opnieuw; een algemene oplossing is `visibilitychange` → opnieuw aanvragen.
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten (proeftuin bestaat).
- %bezet per dag×uur-cel — vraagt tik-met-tijd-én-categorie; schema/KNIME-afstemming nodig.
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` (bezetting per weglijn).

---

## 6. Releases v2.32 → v3.1 in één oogopslag

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
| v2.58 | Kopmetadata: `over.html` en handleiding op hetzelfde niveau als `index.html` |
| v2.59 | Vier fixes: vastloper op lege telling · `_recon` wint bij een paar · weekprofiel-knop bovenaan · ruimte voor de sessielijst |
| v2.60 | Eerlijker coördinaten in telrapport: clusterzwaartepunt, polygoon-zwaartepunt, geen verzonnen fallback |
| v2.61 | Clusterbol als taartdiagram; shift-klik op een cluster isoleert die telling |
| v2.62 | Nieuwe losse tool `gpx_snap.html`: GPX-spoor op het OSM-netwerk leggen *(nu aparte tak)* |
| v2.63 | `gpx_snap.html`: ondergrondkiezer (OSM/Carto) + verdunnen en verdichten voor grove sporen *(nu aparte tak)* |
| v2.64 | `gpx_snap.html`: OSRM als tweede matcher, naast de eigen Viterbi *(nu aparte tak)* |
| v2.65 | `gpx_snap.html` en zijn tests uit de suite, verder als aparte tak; `valideer.py` controleert voortaan ook verwijderde bestanden |
| v2.66 | `README.md` opnieuw geschreven als plattegrond; FileReader-shim in `functest_verzameling.js` (weer groen op Node 22); zijde-offset in vijf bestanden gekoppeld en bewaakt; analyse autorit-reconstructie |
| v2.67 | Highway-voorkeur van de profielen werkt eindelijk: auto blijft op de rijbaan, fiets op het fietspad; log-regel `highway_voorkeur` |
| v2.68 | Versienummer zichtbaar onderaan `index.html`; `valideer.py` bewaakt dat het meegaat |
| v2.69 | Voorpagina in drie groepen (verkeer · parkeren · bureau), pocket-parkeren met eigen ingang; **pocket-sessieherstel werkte niet** (opstartfout) — gerepareerd; nieuwe `laadtest.py` |
| v2.70 | Parkeer-ingang van pocket toont nooit het keuzemenu: Terug → voorpagina, na opslaan verse telling, bij herstel alleen de Parkeren-knop |
| v2.71 | **Pocket bewaarde geen GPS-route zolang er geen wegennet was** (start, Overpass onbereikbaar) — gerepareerd; nieuwe `hersteltest.py`: crash-herstel van alle veld-apps getoetst |
| v2.72 | **Static krijgt noodopslag** (+ scherm-aan); **doortellen na herstel** in alle vijf veld-apps; Static telt onderbrekingen niet mee in duur en uurfactor; nieuwe telling bij herstelmelding vraagt eerst |
| v2.73 | **Static-export in suitevorm** (`_sessie`/`_telregels`/`_onderbrekingen` + leesbaar `_overzicht`, sid `…_sta`); **telrapport leest Static-ZIP's** (nieuw én v2.18–v2.72) en neemt stilstaand mee in verzamelingen; reconstructor weigert stilstaand; branding-restant uit Static weg |
| v2.74 | Release-kandidaat voor 3.0: handleiding bijgewerkt (voorpagina, herstel & doortellen, Static-export, reconstructie); versiestempel reconstructor = release waarin hij veranderde (bewaakt); veldtest-draaiboek `VELDTEST_3.0.md` |
| v2.75 | **Privacyverklaring** `privacy.html` (NL/EN), gekoppeld vanaf voorpagina en `over.html`; voorpaginazin eerlijk ("je tellingen" blijven op je toestel, kaart/wegennet/straatnaam zien waar je telt); **planningmap afgeschermd** met wachtwoord (`.htaccess`), telplanning meldt 401/500 leesbaar; `valideer.py`: elk extern domein moet in de privacyverklaring staan |
| v2.76 | **Noodopslag weg na de download**: pocket schreef hem na Stop + Sluiten bij de eerstvolgende app-wissel opnieuw weg (heropenen bood een al gedownloade telling aan); parkeer-apps lieten het wegennet van de sessie staan; Static hield zijn kopie tot je Static weer opende, en **wiste een niet-opgeslagen afgeronde telling** als het deelblad geannuleerd was. Nu: weg zodra de ZIP bevestigd is opgeslagen, blijft als dat niet lukte. Privacyverklaring noemt de wegennet-cache. Nieuwe `opruimtest.py` |
| v2.77 | **Parkeer-apps volgen de opruimregel**: geannuleerd deelvenster wist de noodkopie niet meer en start geen ongevraagde download; ZIP-knop biedt dezelfde ZIP opnieuw aan binnen de tik (belangrijk op de iPhone); gedeeld blok `bewaarZip` |
| **v3.0** | **Veldtest groen op iPhone en Android → v2.77 wordt 3.0**, byte-identiek op het versienummer na. Nieuw: GitHub maakt per versie automatisch een release met `telsuite-<versie>.zip` |
| v3.1 | **Kaart bewaren als GeoPackage voor QGIS**: waarnemingen, clusterbollen (taartdiagram), wegvakken en GPS-spoor, met de opmaak van telrapport ingebouwd (`layer_styles`); wat je ziet gaat mee; sql.js via cdnjs; nieuwe `gpkgtest.py` (ook tegen QGIS 3.34) |

---

## 7. Methodiek-conclusie telrapport (ter naslag)

Op verzoek doorgelicht: de clustering is **zuiver** — elk kwalificerend punt telt precies één keer, geen dubbeltelling. Bij **gereconstrueerde** ZIP's zit elk geteld punt in een cluster. Bij **rauwe** auto/fiets-ZIP's kunnen ongesnapte tikken buiten de clusters vallen; die zijn wél zichtbaar als vervaagde ⚠-stip, en `n_waarnemingen` blijft het volledige aantal. Sinds v2.42 meldt elke sessie zelf "X/Y geclusterd", dus je ziet direct of de kaart volledig is voordat je conclusies trekt.
