# Telonline Verkeerstellingen — stand van zaken

**Laatste release: v3.29.** Waarschuwen bij het delen van een ZIP (Jay: "Als mensen een telling doen vanuit huis, en ze leveren de .zip aan derden, verraden ze de plek van hun woning"): één regel onder de ZIP-knop in de vijf veld-apps (gedeeld blok `deelwaarschuwing`, Static noemt het adres), de reconstructor en telrapport; *Een ZIP delen* in de privacyverklaring en de handleiding (`overdracht_v3_29.md`). v3.28: capaciteit in de GeoPackage, kaartje in de `_recon.zip`, introductie herschikt. v3.27: het wegennet van pocket in de noodkopie, oude tegels weg. Open: Static op de weg (§5). Tests op GitHub bij elke PR sinds na v3.18.

---

## 1. Wat het is

Suite van single-file HTML-tools voor Nederlandse verkeers- en parkeertellingen, op **telonline.org**. Alles draait in de browser, geen install, geen account. Veldwerk op iPhone/Safari; verwerking op desktop.

**Werkwijze in drie stappen:** tellen → ZIP → (optioneel) reconstrueren → presenteren in telrapport. Daarnaast QGIS als alternatief eindpunt.

### Bestanden in de suite
| Bestand | Rol |
|---|---|
| `index.html` | startscherm (tweetalig NL/EN), ingedeeld naar wat je telt (v2.69) |
| `over.html` | publieke introductiepagina (NL) |
| `about.html` | dezelfde introductie in het Engels (sinds v3.24); `hreflang` over en weer |
| `traffic_counter.html` | Static — telpost vanaf vast punt; noodopslag + doortellen sinds v2.72; export in suitevorm sinds v2.73 (`<sid>_sta.zip`); Nederlands en in de huisstijl van de parkeer-apps sinds v3.22 |
| `parkeertelling.html` | autoparkeren, lopend traject |
| `fietsparkeren.html` | fietsparkeren |
| `capaciteitstelling.html` | parkeercapaciteit |
| `pocket_count.html` | Pocket — 4 sub-modi (simpel/transect/winkelstraat/parkeren); parkeren heeft een eigen ingang `#parkeren` (v2.69) |
| `telreconstructie.html` | nabewerking (hersnap, richting, handmatige correctie) |
| `telrapport.html` | kaartvisualisatie + analyse |
| `telplanning.html` | planning & dekking vooraf; een planning gaat als link naar de telapp (v3.14; sinds v3.15 de enige weg) |
| `traffic_counter_help.html` | handleiding (NL, deels EN-mix); kale HTML sinds v3.3, net als `over.html` en `privacy.html` |
| `zip_format_reference.html` | technische ZIP-documentatie (EN) |
| `verantwoording.html` | toelichting voor juristen: wat een telling vastlegt, sterke en zwakke plekken (v3.4); meenemen bij elke wijziging in wat de apps vastleggen |
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

**Gedeelde tegelcache**: veld-apps schrijven opgehaald netwerk in hetzelfde tegelformaat als de reconstructor (IndexedDB `telsuite_osm`). Sinds v3.20 is dat **schema 3**: elke weg draagt zijn knooppunten (alle apps halen op met `out body geom`), een weg hoort bij elke tegel die een segment raakt, en uit de cache komen alleen de wegen binnen de fetch-cirkel. Een tegel gaat pas de cache in als hij **volledig** gedekt is (raster 8×8; sinds v3.20 telt een cel pas als hij helemaal binnen een cirkel ligt) — anders zou de reconstructor een half gevulde tegel als compleet lezen en stil wegen missen. Sinds v2.49 **lezen** de veld-apps de cache ook: alles-of-niets per fetch-cirkel, TTL 14 dagen (reconstructor houdt 60), schemaversie 2 (tegels dragen ook de straatnaam; oudere tegels tellen als misser en genezen zichzelf). Sinds v3.19 **vult een planning-link de cache vooraf** (blok `gebied vooraf` in parkeertelling, fietsparkeren en pocket): alle tegels die een fetch-cirkel langs de geplande straten kan raken, in één bbox-verzoek, hele tegels dus meteen compleet; tegels jonger dan 7 dagen worden overgeslagen. Sinds v3.27 **ruimt de cache zichzelf op** (blok `tegels opruimen` in de vier veld-apps met cache en de reconstructor): tegels ouder dan 90 dagen gaan eruit, hooguit één keer per dag, vijf seconden na het openen.

**Carto-sleutel** staat in drie bestanden: `telrapport.html`, `telplanning.html` en `telreconstructie.html`. Eén sleutel, drie plekken om aan te passen als hij vervalt — plus `gpx_snap.html` in de aparte tak.

**Geen externe matcher in de suite.** Sinds v2.65 stuurt geen enkele suite-tool een spoor naar een externe dienst; OSRM leeft alleen nog in de gpx-tak.

**`hopClass` begrenst de matcher op twee hops**: 0 = zelfde way, 1 = buur, 2 = buur-van-buur, daarboven `Infinity` — die overgang bestaat niet. Bij sprongen groter dan ~60 m in een stratennet zijn dat er al snel drie, en dan blijft de Viterbi-kolom leeg en herstart de matcher met alleen emissiekosten (de *stuksgewijze backtrack*). Het klapt niet, maar is op dat punt gedegradeerd tot "dichtstbijzijnde way" — zonder dat je dat aan de uitvoer ziet. De gpx-tak vangt dat sinds v2.63 af met tussenpunten (hoge `acc`, dus vlakke emissie: steiger, geen waarneming). **`telreconstructie.html` heeft die opvang niet.** Voor lopende sessies is dat zelden een probleem; voor de geplande post-hoc reconstructie van autoritten wel, want op rijsnelheid zijn sprongen van 60 m+ de regel.

**Highway-voorkeur per profiel** (werkt sinds v2.67; beschreven in v2.18 maar kwam tot v2.67 nooit aan in de matcher): `auto` geeft de rijbaan voorrang boven fiets- en voetpaden, `fiets` omgekeerd. Het is een extra term in de emissiekost: −2 voor geprefereerd, +4 voor vermeden. Met acc 5 m trekt een geprefereerde weg tot ruim 17 m afstand; verder weg wint de weg waar je op staat. Is er alleen het vermeden type, dan wordt dat alsnog gekozen. De wandelprofielen en pocket-parkeren zijn neutraal en rekenen exact als vóór v2.67 (300 willekeurige gevallen, byte-gelijk). Een recon-ZIP draagt in `_reconstructie_log.csv` de regel `highway_voorkeur`; **ontbreekt die regel, dan is de ZIP van vóór v2.67** en is de voorkeur niet toegepast.

**Noodopslag en doortellen** (v2.71 getoetst, v2.72 compleet; `hersteltest.py`: harde crash zonder enige afsluit-gebeurtenis, nep-Overpass zodat er echt gesnapt wordt). **Alle vijf veld-apps** slaan de telling bij elke tik op in `localStorage` en bij scherm-uit/app-wissel nog eens: parkeertelling, fietsparkeren, capaciteit (`<app>_sessie`, wegennet apart in `<app>_sessie_netwerk`), pocket (`pocket_sessie`, alle vier de modi) en sinds v2.72 Static (`static_sessie`, plus een hartslag elke 10 s). Na herladen komt de herstelmelding met **Doortellen**, Download ZIP en Weggooien; sinds v3.22 één gedeeld blok in alle vijf (`herstelmelding`, `herstelmeldingtest.py`), met de vraag bij Weggooien en bij een nieuwe telling in het blok, en zonder Doortellen bij een afgeronde Static-telling. Doortellen gaat verder in dezelfde telling: zelfde sessie-id (parkeer-apps), zelfde starttijd, alles in één ZIP; de onderbreking is een gat in het GPS-spoor. **Static telt de onderbreking niet mee**: de tijd tussen de laatste hartslag en Doortellen gaat als `Interruption`-regel in de CSV en valt buiten `Observed duration` en de uurfactor (anders trekt een pauze de intensiteit per uur omlaag); zonder onderbreking is de export ongewijzigd. Een nieuwe telling starten terwijl er een herstelde klaarstaat, vraagt eerst bevestiging (alle apps). Pocket bewaart sinds v3.27 ook het wegennet (`pocket_sessie_netwerk`, met knooppunten voor de aansluitingen): een herstelde telling geeft dezelfde ZIP als een telling zonder onderbreking, op `_snap_trace.csv` na (diagnose, bewust niet bewaard). Bij een volle opslag wijkt het netwerk voor de tikken. Grenzen: GPS-punten na de laatste tik/hartslag gaan bij een harde crash verloren; de opslag is ~5 MB voor heel telonline.org; een volle opslag geeft sinds v3.9 een melding (~0,5 kB per tik met GPS-punt in parkeertelling, ~0,3 kB in pocket).

**Opruimen na de export** (v2.76, `opruimtest.py`): de noodkopie verdwijnt **zodra de ZIP aantoonbaar is opgeslagen, en niet eerder**. Aantoonbaar = het iOS-deelblad is voltooid (de share-belofte slaagt), of de download is aan de browser overgedragen (desktop/Android). Geannuleerd of gebaar verlopen: de kopie blijft, en de tool biedt de telling de volgende keer weer aan. Na de bevestiging schrijft niets de kopie opnieuw weg (pocket: `exportAfgerond`; Static: `geexporteerd` blokkeert `bewaarStatic`). In pocket geldt *Sluiten* op het voorbeeldscherm ook als bevestiging (ongewijzigd sinds v2.11). De parkeer-apps volgen sinds v2.77 dezelfde regel (gedeeld blok `bewaarZip`, bewaakt): geannuleerd deelvenster → geen ongevraagde download, kopie blijft, statusregel *ZIP niet opgeslagen*, en de ZIP-knop biedt dezelfde ZIP opnieuw aan zonder opnieuw in te pakken (sleutel: sessie-id + aantallen, dus nooit de ZIP van een vorige sessie). Ze schrijven het wegennet alleen nog weg tijdens een lopende sessie, en Stop annuleert een wachtende fetch. Blijvend en bedoeld: taal, tellernaam, kantelmodus, en de wegennet-cache in IndexedDB (openbare OSM-data; legen via telreconstructie of de websitegegevens).

**Eén venster schrijft de noodkopie** (v3.8, `opruimtest.py` deel G). Een telling kan in twee vensters openstaan (op de iPhone opent een beginschermicoon vaak een nieuw tabblad). Tot v3.8 schreef een oud venster zijn afgebroken stand terug zodra het verborgen werd, ook nadat een ander venster de telling had doorgeteld en opgeslagen; Static overschreef elke 10 s een telling die elders liep. Nu, in het gedeelde blok `noodkopie` (byte-identiek in de vijf veld-apps, bewaakt): de kopie draagt het id van het schrijvende venster (`venster`) en van de telling (`telling`); alleen de eigenaar schrijft, en Start en Doortellen maken een venster eigenaar. Een hersteld venster dat niet doortelt, schrijft niet. Na bevestigd opslaan of bewust weggooien gaat het telling-id op de lijst `telsuite_afgesloten` (laatste 30); zo'n telling wordt nooit meer weggeschreven of hersteld. Doortellen weigert als de kopie sinds het herstel veranderde. Een venster dat buitenspel staat, legt stil (GPS, klok, schermslot) en toont `#kopie-elders` met *Opnieuw laden*; het controleert bij elke schrijfpoging, bij `storage`, `pageshow` en zichtbaar worden. Telling-id: `sessionId` (parkeer-apps), `sessieId` (Static), en bij pocket sinds v3.10 het sessie-id, dat vanaf Start vastligt (v3.8/v3.9: de starttijd; een kopie van toen wordt ook onder die starttijd nagekeken). Alleen in de browser, niet in de ZIP: geen schemawijziging. Eén kopie per app blijft: twee lopende tellingen van dezelfde app in twee vensters kan niet; wie later start, wint. Sinds v3.9 vangt `kopieSchrijf` een mislukte `setItem` (opslag vol) zelf af: de vorige kopie blijft staan en `#kopie-vol` verschijnt bovenin (neemt geen tikken af) tot wegschrijven weer lukt. Start en Doortellen roepen `navigator.storage.persist()` aan. De voorpagina leest de kopieën van alle vijf de apps en toont ze onder *Nog niet opgeslagen* (afgesloten, lege en kapotte niet).

**Voorpagina: ingedeeld naar wat je telt** (v2.69). Drie groepen: *Verkeer tellen — wat komt er langs* (stroom: stilstaand, pocket in beweging), *Parkeren tellen — wat staat er* (toestand: pocket-parkeren eerst, dan parkeertelling, fietsparkeren, capaciteit) en *Achter je bureau* (planning, reconstructie, rapport, compact onderaan). Een nieuwe tool krijgt een plek in de groep die past bij de vraag, niet bij hoe hij gebouwd is. De kaartteksten zeggen wanneer je welke kiest, vooral binnen parkeren. Pocket-parkeren is **geen eigen tool**: de kaart linkt naar `pocket_count.html#parkeren`. Via die ingang gedraagt pocket zich als parkeer-app en verschijnt het keuzemenu met vier modi **nooit** (v2.70): meteen het parkeerscherm; Terug gaat naar de voorpagina; na Stop en het voorbeeldscherm een verse parkeertelling. Bij een onderbroken telling of als er geen voorbeeldscherm komt (geen GPS-spoor), blijft van het keuzescherm alleen de Parkeren-knop over. Het verbergen gebeurt met de klasse `.pk-ingang` op `<html>`, gezet in `<head>` vóór de eerste weergave, zodat het menu ook niet even zichtbaar is.

**Rekenkern**: `RECON`, `MATCHER` en `OSMCACHE` staan binnen de suite alleen nog in `telreconstructie.html`; `splitWayIntoSegments` byte-identiek in `telreconstructie.html` en `pocket_count.html`. Bewaakt door `valideer.py` (de groepen met één bestand blijven staan als ankercontrole). De gpx-tak draagt een kopie op de stand van v2.64 — hoe die kopie de suite volgt is nog niet besloten (zie backlog). Sinds v2.67 wijkt `MATCHER` af van die kopie (vijfde parameter); de tak geeft geen voorkeur mee, dus daar verandert het gedrag niet als hij de nieuwe versie overneemt.

**Gedeelde Overpass-blokken** (houd byte-identiek, controleer met md5 na elke multi-file wijziging): `ovpKeur`-blok in 7 bestanden (sinds v3.9 ook telplanning), `overpassFetch`-transport in telrapport + telreconstructie, `startRoadFetch`-discipline in de drie parkeer-apps. Pocket houdt een eigen ingang (`snapStartFetch`) omdat zijn discipline verweven is met de fid-volgordeguard en de trace-events, maar draait op hetzelfde model. Regressietests in `_archief/overpass_rig/`.

**Overpass-antwoorden worden geclassificeerd** (v2.49, gedeeld blok `ovpKeur`, byte-identiek in 7 bestanden; telplanning sinds v3.9): `ok` / `leeg` / `oud` / `limiet` / `fout`. Een leeg gebied is een geldig antwoord en wordt niet opnieuw bevraagd. Een rate-limit — ook als Overpass die als HTTP 200 met `remark` in de body stuurt — leidt tot 30s stilte zonder mirror-hop. Alle apps delen nu één backoff-model (`ovpBackoffMs`, 500·2ⁿ⁻¹, max 8s).

**Documentatiepagina's zijn kaal** (v3.3, op verzoek van Jay: "veel css en kleurtjes voor een pakket dat toch een beetje voor verkeerskundigen is"). Handleiding, `over.html` en `privacy.html` zijn gewone HTML met één gedeeld stijlblok (`/* ── kale stijl (v3.3)` … `einde kale stijl ── */`), byte-identiek in alle drie, en zonder Google Fonts. Kleur alleen waar die iets uitlegt: kleurstalen (`class="kleur"`, `rond`) met hun kleur in `style`. `valideer.py` bewaakt het blok en dat er geen opmaak terugsluipt (losse `style=""`, extra `<style>`, Google Fonts). Nieuwe stukken tekst dus als `<h3>`/`<h4>`/`<p>`/`<ul>`/`<table>`, niet als kaartje. De tools houden Oswald.

**Telplanning: wegen ophalen** (v3.9, `robuusttest.py` deel E). Na het tekenen van een contour staat midden op de kaart een melding met verstreken tijd en ontvangen kB. Per server een tijdslimiet (`OPHAAL_TIMEOUT_MS`, 45 s; de query zelf 25 s), daarna de volgende server. Elk antwoord gaat door `ovpKeur`: een antwoord met een `remark` is afgebroken en wordt **niet** gebruikt, ook niet als er wegen in zitten (een halve planning valt anders niet op). Leeg gebied: melding *Geen wegen gevonden*, de tweede server wordt niet gevraagd. Lukt het bij geen server: een melding met de reden per server, een advies en *Opnieuw*.

**Pocket-id vast vanaf Start** (v3.10, `logicatest.py` deel A). Pocket maakte zijn `sessie_id` tot v3.10 bij Stop, met de tijd van dat moment; nu bij Start (`pocketStam = genSid(startTime)`), met de moduscode erachter bij het inpakken (`pocketSid()`). Het id gaat mee in de noodkopie (`sessieId`) en Doortellen houdt het vast, dus een telling die twee keer wordt ingepakt heeft één id. Een kopie van vóór v3.10 (zonder id) krijgt het uit de starttijd, met letters die ook uit de starttijd volgen (`stamUitStart`), zodat twee vensters op hetzelfde id uitkomen. Formaat en bestandsnamen zijn ongewijzigd; KNIME gebruikt `_sessie.csv` alleen als lijst (Jay, 16 okt). Binnen de suite leest niets de tijd uit het id.

**Planning als link** (v3.14, `functest_planlink.js`, `planlinktest.py`). *Deel als link* in telplanning zet de planning achter het `#` van de link: `parkeertelling.html#plan=1.<data>`, `fietsparkeren.html#plan=…`, `pocket_count.html#parkeren&plan=…`. `<data>` = base64url(deflate-raw(JSON)), met per weg de geometrie als polyline (Google, 1e5, ±1 m). Het deel na `#` gaat niet naar de server: niets op de server, alleen langs de mail of app. De `1` is de formaatversie; een hogere versie geeft een melding. Gedeeld blok `planlink` (byte-identiek in telplanning en de drie apps, md5-groep in `valideer.py`); de apps maken er weer het JSON-object van zoals de server het levert, dus de bestaande laadcode is gebleven. Teltype heeft een derde waarde, `pocket`; `PLANLINK_APP` in het blok zegt welke app bij welk teltype hoort. Pocket toont de planning alleen ter oriëntatie: een regel boven de telvakken en paarse lijnen op de *Kaart*; in de ZIP komt niets. Sinds v3.15 is de link de enige weg: *Maak Telling* (download + opslaan op de server), *Opdrachten* en `planningen/` met de PHP-scripts zijn weg, en de apps lezen `?plan=` niet meer (Jay: "We hoeven de .json niet meer op te slaan op de server"; de download ging mee weg, want niets las hem in). Telplanning waarschuwt boven 6000 tekens (mailprogramma's). Valkuil die in handleiding en dialoog staat: een link uit de Gmail-app of WhatsApp opent vaak in een ingebouwde browser met eigen opslag, en daar vindt Safari een onderbroken telling niet.

**Kwaliteitsrapport per telling** (v3.10, `functest_kwaliteit.js`, `logicatest.py` deel B). Telrapport rekent bij het inladen per telling zes controles uit, uit de bestanden die al in de ZIP zitten (`kwaliteitRapport`, constanten in `KW`): *Aantallen* (`n_waarnemingen` = regels in `_telregels` = som in `_straten`), *Tijd* (elke tik tussen start en eind, 60 s marge), *GPS-spoor* (een gat = > 60 s zonder punt én > 50 m sprong; tikken in een gat zijn een aandachtspunt; Static: de onderbrekingen), *Positie* (elke tik een GPS-positie), *Nauwkeurigheid* (mediaan ≤ 15 m, hooguit 20% boven 20 m; Static: de ene fix) en *Op de route* (elke tik binnen 50 m van het spoor op zijn tijdstip). Oordelen: ok, let op (telt als aandachtspunt), info, n.v.t. **De apps loggen een GPS-punt pas na 5 m verplaatsing**: stilstaan geeft geen punten. Daarom telt een gat alleen met een sprong, en is "verse fix" niet uit de ZIP af te leiden (in het voorstel aan Jay stond die nog; vervangen door *Positie* en de tikken in een gat). De routecontrole gebruikt de rauwe GPS-kolommen (`lat_gps`/`lon_gps`, of `lat`/`lon`); correctie en reconstructie verschuiven alleen de marker. In beeld: rechts op de eerste regel van de sessierij een *✓* of *⚠ n* (sinds v3.11; in v3.10 een eigen regel, maar de kolom heeft weinig verticale ruimte), uitleg in de tooltip, een klik opent het paneel. Niet in de GeoPackage: eerst kijken hoe het bevalt (mijn voorstel; Jay maakte geen bezwaar).

**Telrapport per stuk** (v3.21, `stukkentest.py`). Fiets- en autotellingen staan in telrapport per stuk van een weg, niet per hele weg. Het knippen is `splitWayIntoSegments`, byte-identiek in telreconstructie, pocket en telrapport: stukken van gelijke lengte zo dicht mogelijk bij 40 m, een weg korter dan 60 m blijft heel. Dezelfde weg geeft dus overal dezelfde sleutels `way:stuk`. Een `_recon` levert zijn stukken zelf (`segment_index` in `_netwerk.csv` en `_telregels.csv`); bij een origineel knipt telrapport en deelt hij elke tik in naar de plek van zijn marker langs de weg (`stukVanTik`, dezelfde rekensom als `segIdxFor` in de reconstructor). De aantallen per stuk komen uit de telregels (`telPerStuk`), niet uit `_straten.csv`; voor auto bezet = goed + fout + spec, vrij = leeg. Gelopen stukken zonder tikken: uit `_bezocht.csv` (recon) of het GPS-spoor (origineel), gestreept. De correctietool rekent na elke verplaatsing het stuk en de kleuren opnieuw uit (`naCorrectie`). Pocket werkte al zo. Later (schema, eerst KNIME): parkeertelling en fietsparkeren schrijven `segment_index` zelf.

**Handoff "Direct reconstrueren"**: ZIP-blob via IndexedDB store `handoff` → `telreconstructie.html?handoff=1`. Knop aanwezig in alle vier veld-apps die door de reconstructor gaan.

---

## 3. Werkwijze in de samenwerking

- **Round-trip:** Jay bewerkt bestanden handmatig en levert ze terug; Claude integreert en valideert. Een regel context bij teruggave ("ik heb secties X en Y aangeraakt") maakt het sneller.
- **Validatie elke release:** inline JS extraheren → `node --check`; HTML-tagbalans; functionele test waar zinvol; **byte-identiteit** (alleen de bedoelde bestanden mogen wijzigen).
- **Elke release** krijgt een `overdracht_vX_Y.md` en een volledige ZIP. Sinds v3.0 maakt GitHub die ZIP zelf: na de merge naar `main` ziet `.github/workflows/release.yml` het nieuwe nummer in `index.html` en maakt een release met tag, `telsuite-<versie>.zip` en de overdracht als tekst. Wat niet in de ZIP gaat (ontwikkelspul en `planningen/.htaccess`) staat in `.gitattributes`.
- **Laadtest bij wijzigingen aan de opstart van een pagina** (sinds v2.69): `laadtest.py` laadt elke pagina echt in Chromium en faalt op elke JS-fout bij het opstarten. `node --check` en de tagbalans zagen de dode herstelfunctie van pocket niet.
- **Versienummer ophogen bij elke release** (sinds v2.68, op verzoek van Jay): het staat zichtbaar onderaan `index.html` (`<div class="versie">`). Eén nummer op vier plekken: `RELEASE` in `valideer.py`, `index.html`, "Laatste release" hier, en de naam van de overdracht. `valideer.py` faalt als één ervan afwijkt of als het nummer niet hoger is dan in de vorige release. Daardoor staat `index.html` voortaan in élke release bij de gewijzigde bestanden.
- **Additief werken**: bestaande logica byte-identiek laten waar mogelijk.
- **Live zetten gaat vanzelf** (10 okt 2026): elke push naar `main` → `.github/workflows/site.yml` zet de inhoud van de release-ZIP op de branch `site` → Plesk ("Deploy using Git", webhook) zet die in `httpdocs`. Een merge naar `main` staat dus meteen online, ook zonder versienummer. Alleen documentatie of tests: `site` verandert niet. Serverbestanden (`planningen/.htaccess`, de planningen) staan nooit in `site`. Met de hand opnieuw: *Actions → Site → Run workflow*. **Plesk ruimt niet op**: bij de overstap van `main` naar `site` bleven `CLAUDE.md`, `docs/` en `_archief/` online staan tot Jay ze weghaalde. Verdwijnt er ooit een bestand uit de suite, haal het dan ook met de hand van de server.
- **Tests op GitHub** (19 okt 2026, Jay: "Testen op github, kun je dat nu maken"): bij elke PR naar `main` en na elke merge draait `.github/workflows/tests.yml` `valideer.py`, alle functests, `test_zipref.py`, `check_encoding.py` en elke browsertest in een eigen job. De controle **alles groen** vat het samen; pas mergen als die groen is. `valideer.py` vergelijkt met de vorige stand van `main`; zonder nieuw versienummer slaan de release-controles over. Nieuwe tests doen vanzelf mee als ze `functest*.js` of `<naam>test.py` heten. Bibliotheken en Chromium staan alleen op de runner (`.github/actions/testopzet`), op `ubuntu-24.04`. Faalt een browsertest, dan staan zijn FOUT-regels als melding bij de controle (`.github/scripts/meldingen.sh`). De runner draait in UTC, de Claude-omgeving in Europe/Amsterdam: de eerste run ving zo een test die 09:30 verwachtte (`logicatest` A5, nu uit de tijdzone van de browser). Verplicht maken kan in *Settings → Branches* (Jay's keuze).
- **Branches opruimen** (v3.4): na de merge kan de branch weg. Vanuit de Claude-omgeving lukt verwijderen niet; GitHub doet het zelf met *Settings → General → Automatically delete head branches*.
- **Sitemap en robots.txt** (10 okt 2026, na v3.3, zonder eigen release): de sitemap noemde na de verhuizing nog rvmk.nl, en gaat met elke release-ZIP mee naar de server. Nu: 13 openbare pagina's op telonline.org, zonder datums (niets bij te houden), en een `robots.txt` die naar de sitemap wijst. `valideer.py` controleert het; een nieuwe openbare pagina moet erin, een interne in `NIET_IN_SITEMAP`. telonline.org is aangemeld in Google Search Console, met de sitemap erbij (Jay, 10 okt).
- Ontwerp eerst bespreken bij niet-triviale keuzes; terse goedkeuring = go.

---

## 4. Nog te doen door Jay (buiten de code)

Opgeruimd op 21 oktober 2026.

**Afgerond.**
- Op 21 oktober (Jay: "het gaat soepel allemaal"):
  - de telling van de S25 is opgeslagen;
  - de veldtest van v2.49 (tegelcache) is geslaagd;
  - de veldtest van v3.23 (GPS middelen in Static) is geslaagd.
- Eerder:
  - de veldtest van v3.9 (16 oktober);
  - de planningmap op de server is opgeruimd (18 oktober);
  - Plesk volgt de branch `site` (10 oktober).
- De KNIME-notitie over Static is vervallen: Static draait niet in KNIME (Jay, v3.22). Het formaat staat in `zip_format_reference.html`.

**Nog open.**
1. **Screenshots voor `over.html`.** Drie bestanden, met precies deze namen, naast `over.html`: `screenshot-tellen.jpg`, `screenshot-nabewerken.jpg` en `screenshot-telrapport.jpg`. Zolang ze ontbreken, toont de pagina een nette plaatshouder met de verwachte bestandsnaam. PNG kan ook, maar dan moet `src` mee.
2. **KNIME.** Twee punten:
   - het `sessie_id`-formaat met de modusletter;
   - `snap_path` in `snap_trace.csv` begint sinds v2.49 met `bron:fetch|`, `bron:tegel|` of `bron:leeg|`, en de kolom `event` kent `tegelcache` en `fetch_leeg`. Het zijn vrije-tekstkolommen, dus formeel geen schemawijziging. Een node die op de exacte vorm parst, moet wel mee.
3. **Server.** `gpx_snap.html` hoort niet meer bij de suite. Blijft hij als losse tool op telonline.org staan, of verhuist hij? Er linkt niets naartoe, dus weghalen breekt niets.
4. **Veldtest v3.19** (pocket-parkeren; alleen pocket schrijft de bron van het netwerk in `_snap_trace.csv`):
   - met een planning: open de link thuis. Boven de telvakken staat dan *gebied klaar*, en na het lopen staat in `_snap_trace.csv` na het begin alleen `tegelcache`, geen `fetch`;
   - zonder planning, in een stuk dat je nog niet eerder liep: een derde minder `fetch`-regels per kilometer dan voor v3.19;
   - snappen: meer verkeerde straten of niet-gesnapte tikken dan vroeger? Dan terug naar 150 m (één getal per app). Valt de test goed uit, dan kan 500/350 later nog (§5, *Meetkunde*).
5. **Veldtest pocket-parkeren:** de audio-feedback en de dekkingskaart. Het automatisch downloaden van de ZIP na Stop is sinds v3.18 op de S25 getest.

---

## 5. Backlog (niets besloten)

**Klein / afgebakend**
- ~~Kop van de handleiding~~ — aangepast door Jay (de bovenste kop). Boven de inhoudsopgave staat nog een tweede kop "Traffic Counter Help", met daaronder "Contents". Zichtbare tekst, dus Jay's keuze.
- ~~Reconstructiescript een kaart-PNG bij de `_recon.zip`~~ — gedaan in v3.28: `<sid>_kaart.png` in de ZIP (Jay's keuze), netwerk, spoor en tikken, zonder ondergrond.
- Besluiten over het losse transect-formaat (`*_trn.zip`): geen enkele app maakt het nog (pocket's transect-modus `_pkt_t` verving het), maar telrapport leest het wel. Liggen er nog `_trn`-ZIP's in het archief? Zo nee: sectie uit de referentie én de leescode in telrapport eruit.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>` voor consistentie (Jay's keuze — hij schreef die sectie zelf). Sinds de duidelijkere koppen (na v3.16) valt hij nog meer op dan de hoofdstukken.
- Overpass-terugval voor het losse transect-formaat (`_trn`, telrapport `loadTransectZip`) gaat mee met het besluit over `_trn` hierboven; v3.17 liet hem staan.
- ~~Pocket: netwerk ook na Doortellen in de ZIP~~ — gedaan in v3.27: het netwerk staat in de noodkopie. De Overpass-terugval in telrapport blijft, voor oudere pocket-ZIP's en na een volle opslag.
- **Ingebouwde browser van een app** (uit v3.18). Op Android opent een link uit sommige apps in een WebView (`; wv)` in de user-agent): geen ZIP-download, en de noodkopie staat in de opslag van die app, niet in Chrome. v3.18 laat in de parkeer-apps alleen de kopie staan. Nog open: (1) een waarschuwingsbalk bij het openen, met *Kopieer link*, in alle vijf de veld-apps (nieuw gedeeld blok, tweetalig zoals *Noodopslag vol*); (2) pocket en Static: een download in een WebView niet als opgeslagen tellen, en *Sluiten* in het voorbeeldscherm van pocket dan niet laten bevestigen. Pas oppakken als het in het veld voorkomt.
- Ook kaal maken? `zip_format_reference.html` en `snap_methodology.html` hebben nog de oude opmaak (Jay's keuze; v3.3 deed alleen de drie pagina's voor gebruikers).
- ~~Engelse variant van `over.html`~~ — gedaan in v3.24: `about.html`.
- **Bewijswaarde van een telling** (uit `verantwoording.html`, v3.4), in volgorde van nut:
  1. *Vingerafdruk bij de export* (Jay: later): SHA-256 van de ZIP tonen, met een knop "mail deze code naar mezelf". Daarmee is aantoonbaar dat de ZIP sinds dat moment niet veranderd is. WebCrypto, geen server.
  2. *Ongedaan maken tellen* (`n_ongedaan`) en *versienummer* (`app_versie`) in `_sessie.csv`, als kolommen achteraan. Schemawijziging: eerst KNIME.
  3. ~~*Consistentiecheck* in telrapport~~ — gedaan in v3.10 als kwaliteitsrapport per telling (zie §2): aantallen in alle bestanden gelijk, elke tik binnen de sessietijd en op de route rond zijn tijdstip. Zie ook het *gezondheidsrapport per telling* bij de ideeën na v3.8.
  `verantwoording.html` noemt het kwaliteitsrapport sinds v3.10. Bij 1 en 2 de zwakke plekken daar ook bijwerken.


**Ideeën na v3.8** (15 okt 2026)

*Kwaliteit*
- ~~**Tests op GitHub bij elke PR.**~~ Gedaan (19 okt 2026): `.github/workflows/tests.yml`, zie §3. `hersteltest` was in de eerste runs op GitHub groen; of hij daar ooit vals alarm geeft (hieronder), moet blijken.
- **"Klaar voor het veld?"**: een korte controle vóór je naar buiten gaat:
  - werkt de GPS, en hoe nauwkeurig?
  - mag het kompas?
  - blijft het scherm aan?
  - hoeveel opslagruimte is er (`navigator.storage.estimate()`)?
  - werkt het deelvenster?
  - staat er nog een onderbroken telling?

  Nu ontdek je zulke dingen pas buiten.

*Logica*: beide punten (pocket-id bij Start, gezondheidsrapport) zijn gedaan in v3.10.

*Interface*
- ~~**Eén herstelmelding voor alle apps**~~ — gedaan in v3.22 (gedeeld blok `herstelmelding`).

*Slim lopen* (Jay, 17 okt 2026; niveau 1, het hoofdstuk in de handleiding, is gedaan in v3.13)
- **Niveau 2: dekking per kant in pocket-parkeren.** Pocket snapt de GPS al tijdens het tellen op de OSM-weg en kent de looprichting. De dekkingskaart (knop *Kaart*) kan dan per straatkant tonen of je er al langs liep met die kant rechts: "wat heb je nog niet geteld". Haken: zonder auto's tik je niet, dus welke kant je telde is alleen af te leiden (rechts, behalve in een smalle straat); en pocket kent alleen het netwerk rond waar je liep, niet het hele gebied. Levert ook de toestand per straatkant waar niveau 3 op voortbouwt.
- **Niveau 3: route uit de planning.** In telplanning per straat kiezen: beide kanten apart (standaard), in één keer, of niet. Telplanning rekent de route uit en toont hem met pijlen, nummers, afstand en tijd. Algoritme: elke straat die twee keer gelopen wordt, is twee gerichte kanten, dus de graaf is in balans en er is altijd een eulercircuit (Hierholzer, met de rand of de blokken als eerste rondjes). Straten in één keer: de knopen met een oneven aantal daarvan koppelen via kortste paden (min-cost perfect matching; exact met een bitmask-DP voor een handvol knopen), dan Hierholzer. Lastig is niet het algoritme maar de graaf: OSM is geen stoepennet (dubbele rijbanen, rotondes, fietspaden naast de weg, parkeerterreinen). Pocket leest sinds v3.14 een planning (paars op de *Kaart*), maar pocket hoort in je zak: de route is om vooraf te bekijken, niet om per bocht te navigeren. Eerst niveau 2.

*Groter, eerst bespreken*
- **Werken zonder bereik.** De veld-apps halen Leaflet en JSZip van een CDN. Herlaadt Safari een tabblad in het veld zonder bereik, dan laadt de pagina mogelijk niet, en kan hij dus ook niet herstellen. Een service worker die de veld-apps en hun bibliotheken bewaart, lost dat op. Wel goed bedenken hoe een nieuwe release dan binnenkomt (eerst het netwerk proberen voor de HTML). Niet als beginscherm-app installeerbaar maken: op de iPhone heeft zo'n app een eigen opslag, los van Safari, en dan vindt Safari de noodkopie niet meer.

**Lessen uit de gpx-tak die terug kunnen**
- Verdichten (steigerpunten, v2.63) voor `telreconstructie.html` — nodig zodra de autorit-reconstructie gebouwd wordt (`hopClass` breekt boven twee hops).
- Ketting-breuken zichtbaar maken (plekken waar de matcher herstart met `back = null`) — geldt voor de reconstructor net zo goed.
- Synchronisatiebeleid voor de rekenkern-kopie in de tak: meelopen met de suite, bewust bevriezen, of een controle in de tak die de afwijking alleen meldt.

**Meetkunde (vraagt veldtest)**
- ~~Fetch-radius en verversafstand losser zetten~~ — gedaan in v3.19: radius 300 / verversen op 220 m (Jay's keuze; pocket 250/170). Veldtest staat in §4. Als die goed uitvalt, kan 500/350 later nog: dat halveert de verzoeken tegen 19% meer bytes, maar maakt elke cirkel bijna drie keer zo groot.
- ~~Gebied vooraf ophalen~~ — gedaan in v3.19, niet vanuit telplanning maar in de veld-app zodra de link opent: de tegelcache staat in de browser van het toestel, en de planning gaat sinds v3.14 als link naar de telefoon.

**Uitrollen als het bevalt**
- Audio-feedback (nu alleen pocket parkeren) naar andere tel-modi.
- Dekkingskaart (nu alleen pocket parkeren) naar andere tel-modi; eventueel links/rechts-stippen uit elkaar trekken.

**Na de reparatie van v2.67**
- Oude auto- en fietsreconstructies (vóór v2.67) opnieuw draaien of laten staan? Herkenbaar aan het ontbreken van `highway_voorkeur` in de log. Het verschil zit alleen waar een fietspad of voetpad binnen ~17 m van de rijbaan ligt.

**Groter / vraagt ontwerp**
- ~~**Planningen zonder server**~~ — gedaan: v3.14 (de link) en v3.15 (server, *Maak Telling* en *Opdrachten* weg). Ook gedaan (v3.19): **een link terug openen in telplanning** (*Of: planning uit een link*, of `telplanning.html#plan=…`), met de omgeving grijs erbij.
- **Autorit-reconstructie — geparkeerd** (v2.67: Jay telt zelden vanuit de auto). De highway-voorkeur, het grootste obstakel, is sinds v2.67 opgelost. Wat nog ontbreekt: een tijdspoort plus verdichten, een rit-profiel met herkenning, en bij lange ritten een corridor-fetch en een ruimtelijke index. Analyse en volgorde in `overdracht_v2_66.md` §4.
- Zijde-offset live in pocket-parkeren? De ingrediënten zijn er (de gesnapte positie en de wegrichting kent pocket al), zo'n vijftien regels. Twee bezwaren: het voegt `lat_marker`/`lon_marker`/`zijde` toe aan het rauwe pocket-schema en vraagt dus KNIME-afstemming, én "links" is bij pocket relatief aan de looprichting, die de app op het moment van tikken minder zeker kent dan de reconstructor achteraf uit de hele route — precies de reden dat de reconstructor bestaat. Winst is vooral cosmetisch: ongereconstrueerde pocket-parkeertellingen zien er in telrapport dan net zo uit als parkeertellingen.
- "Save as .png" in telrapport: het kaartbeeld exporteren. De knop is triviaal, het plaatje niet. Tegels zijn niet CORS-schoon (`L.tileLayer` zet geen `crossOrigin`), vectoren zitten in vijf SVG-panes, labels zijn acht `divIcon`-varianten. Drie routes: handgetekend canvas zonder ondergrond (patroon van de veld-apps), eigen tegel-compositor (~150 regels, geen afhankelijkheid), of `html2canvas` van een CDN. Voorstel: tegel-compositor met automatische terugval naar zonder-ondergrond bij een SecurityError. Eerst de CORS-test draaien op OSM/CARTO/PDOK; de bronvermelding moet sowieso in de PNG gebakken worden.
  *v3.1:* voor het rapportpad is er nu de GeoPackage voor QGIS (daar zitten ondergrond, schaalstok en PDF-export al in). Een PNG uit telrapport blijft nuttig voor het snelle plaatje.
- ~~GeoPackage: capaciteitsterreinen als eigen laag~~ — gedaan in v3.28: laag `terreinen` (POLYGON, capaciteit per soort), in het project *Capaciteit*.
- **Deelversie van een ZIP** (uit v3.29, niet besloten): begin en eind van het GPS-spoor weglaten, zoals de privacyzone van Strava, voor wie vanuit huis start. Verandert bezocht, aanwezigheid en p/m·u, dus alleen als aparte ZIP naast de echte, nooit voor KNIME. Static afronden helpt niet: de plek is de meting. v3.29 waarschuwt alleen.
- **GeoPackage-opmaak:** bij veel tellingen loopt de legenda (GPS-spoor per telling) uit het A4-vak; dan twee kolommen of het spoor uit de legenda. Eventueel ook een A3-opmaak.
- QGIS-loader (`telonline_qgis_loader.py`) op QGIS 4 testen (Qt6, opgeschoonde Python-API); eventueel dezelfde stijlsjablonen gebruiken als de GeoPackage-export, zodat de opmaak op één plek bestaat.
- Parkeren uit pocket halen naar een eigen tool. Sinds v2.69 heeft het een eigen ingang op de voorpagina (`#parkeren`), wat het grootste deel van de wens dekt. Een echte afsplitsing loont pas als parkeren een eigen kant op gaat (bijv. de zijde-offset live), want dan moeten GPS, snap, fetch-discipline en noodopslag in twee bestanden gelijk blijven.
- ~~`over.html` en `about.html` volgens de voorpagina~~ — gedaan in v3.28: stap 1 in *Verkeer tellen* en *Parkeren tellen*, en een alinea over plannen vooraf met Telplanning.
- ~~Wegennet-cache ruimt oude tegels nooit op~~ — gedaan in v3.27: gedeeld blok `tegels opruimen`, tegels ouder dan 90 dagen, hooguit één keer per dag.
- ~~`hersteltest.py` is soms wisselvallig~~ — opgelost in v3.27. De oorzaak was het exporttijdstip in de kop van `_kaart.png` (een minuutgrens tussen de twee exports), niet de wachttijden; de test vergelijkt de kaart nu pixelrij voor pixelrij zonder de kop.
- ~~Google Fonts zelf hosten~~ — gedaan in v3.25: `fonts/`, Google uit de privacyverklaring.
- telrapport: de labels op de kaart (clusterbollen, nummers) vragen om Oswald, maar telrapport laadt hem niet en toont een reserveletter. Sinds v3.25 is het één regel (`<link href="fonts/fonts.css" rel="stylesheet">`), maar het verandert hoe de kaart eruitziet. Jay's keuze.
- ~~Static is Engelstalig~~ — gedaan in v3.22: Nederlands, in de huisstijl van de parkeer-apps. Het leesbare `_overzicht.csv` blijft Engels (telrapport leest het).
- **Static op de weg** (laag 2 van het voorstel bij v3.22, nog niet besloten). Na de GPS-fix het punt op de weg snappen (met de knip in stukken van v3.21); de richtingen uit het netwerk (de weg volgen tot de eerste kruising met een straat met een naam: "richting Gorsstraat"); welke knop welke richting is uit je positie ten opzichte van de as, met het kompas alleen als je te dicht op de as staat; bevestigen op een minikaartje met ⇄. In de export kolommen achteraan (`osm_way_id`, `segment_index`, A met of tegen de OSM-richting). Static draait niet in KNIME, dus het raakt alleen `zip_format_reference.html` en telrapport. Zie `overdracht_v3_22.md` §4.
- ~~Static: `GPS reliable` "Yes (< 25m)" tegen 20 m in de app~~ — opgelost in v3.23: de app middelt, en de grens is 15 m in app en overzicht.
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten (proeftuin bestaat).
- %bezet per dag×uur-cel — vraagt tik-met-tijd-én-categorie; schema/KNIME-afstemming nodig.
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` (bezetting per weglijn).

---

## 6. Releases v2.32 → v3.29 in één oogopslag

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
| v3.2 | **QGIS-project in de GeoPackage** (in QGIS 4 nagelopen door Jay: PDOK laadt, beeld en teksten goed, PDF netjes): RD New, PDOK BRT-A grijs (luchtfoto en OSM klaar), lagen in volgorde, printopmaak A4 liggend op een rond schaalgetal met legenda, schaalstok en noordpijl; je kiest de bestandsnaam bij het opslaan (het project onthoudt hem); sessielabels gerepareerd; `gpkgtest.py` 80 tests |
| v3.3 | **Kale documentatiepagina's**: handleiding, `over.html` en `privacy.html` in gewone HTML met één gedeeld stijlblok (96,7 → 76,4 kB voor de handleiding), tekst woord voor woord gelijk (nieuwe `tekstgelijk.py`); geen Google Fonts meer op die pagina's; op de telefoon geen zijwaarts schuiven meer; `valideer.py` bewaakt het stijlblok |
| v3.4 | **`verantwoording.html`**: toelichting voor juristen (wat de app vastlegt, wat er daarna mee gebeurt, sterke en zwakke plekken naast een turflijst, wat een beoordelaar kan nagaan), gelinkt vanuit `over.html` en de handleiding; **GPX-tijden in echte UTC** in de drie parkeer-apps (stonden als lokale tijd met een Z, één of twee uur mis); nieuwe `functest_gpxtijd.js` |
| v3.5 | **Contactadres** `verkeer@telonline.org` (privacyverklaring, `over.html`, verantwoording; GitHub-issues op `over.html` en in de README); GIS-alinea in `over.html` noemt de GeoPackage met kant-en-klaar QGIS-project |
| v3.6 | **SEO-ronde**: titels, meta descriptions en canonicals voor de negen tools (Nederlands) en de titel van `over.html`; `<h1>` van capaciteitstelling "Parkeercapaciteit"; titel van `index.html` en `verantwoording.html` en de description van `over.html` en `verantwoording.html` ingekort; nieuwe controle in `valideer.py` (titel ≤ 65, description 70–160, canonical, og:title) |
| v3.7 | **Weekprofiel**: tabel nieuwste bovenaan (sorteerde op de datumtekst), weekdag en tijd, seconden, visits in *aanwezig*; 95%-marge (exact Poisson, getoetst aan scipy) in de tooltips; onzeker = minder dan 5 tikken én marge over een klassegrens, lichter getoond; klik op rij ↔ cel; nieuwe `functest_segmenttabel.js` |
| v3.8 | **Noodkopie met één eigenaar**: een oud venster zet een afgebroken telling niet meer terug nadat een ander venster hem doortelde en opsloeg (gemeld door Jay); Static overschrijft geen lopende telling meer; opgeslagen of weggegooide tellingen op een lijst; Doortellen weigert een verouderde stand; het oude venster legt stil en meldt het; gedeeld blok `noodkopie` in de vijf veld-apps; `opruimtest.py` deel G (87 tests) |
| v3.9 | **Robuustheid**: melding bij volle noodopslag en `storage.persist()` (blok `noodkopie`); pocket vraagt het schermslot terug na een app-wissel; voorpagina toont *Nog niet opgeslagen* tellingen; telplanning: laadmelding zichtbaar (bleef verborgen), tijd en kB, tijdslimiet per server, `ovpKeur` (afgebroken antwoorden niet meer stil gebruikt), foutmelding met *Opnieuw*; privacyverklaring over de planningenmap; nieuwe `robuusttest.py` (87 tests) |
| v3.10 | **Logica**: pocket-id vast vanaf Start (was: tijd van Stop; een tweede keer inpakken gaf een ander id), ook na Doortellen; **kwaliteitsrapport per telling** in telrapport (aantallen, tijd, GPS-spoor, positie, nauwkeurigheid, op de route), regel in de sessielijst en paneel; verantwoording en ZIP-referentie bijgewerkt; nieuwe `functest_kwaliteit.js` (33) en `logicatest.py` (25) |
| v3.11 | Kwaliteitsrapport: teken (*✓* / *⚠ n*) rechts op de eerste regel van de sessierij in plaats van een eigen regel (Jay: weinig verticale ruimte in de kolom); `logicatest.py` meet dat de rij niet hoger wordt (27 tests) |
| v3.12 | Sessielijst in telrapport: *✓ n/n geclusterd* weg als alle tikken in een cluster zitten, *⚠ n/m geclusterd · k buiten* blijft (Jay: ruimte in de kolom; een volledige rij 42 tegen 55 px). Bijwerking: bij capaciteit verborg die regel een melding over terreinen zonder geometrie; die is nu zichtbaar. `logicatest.py` 30 tests |
| v3.13 | Handleiding: hoofdstuk **Slim lopen bij parkeertellingen** (Jay: "mensen vooraf laten nadenken hoe ze het doen"): vijf vragen vooraf, één kant per keer, drie patronen met een plaatje in SVG (drukke straat heen en terug, een rondje twee keer, een wijk met eerst de rand), waarom het altijd past (eulercircuit), onderweg en na afloop. Veldtip parkeertelling over keren aangepast: niet langer een nieuwe sessie voor de terugweg |
| v3.14 | **Planning als link** (Jay: "vanuit een mail of link een telling kunnen starten"): *Deel als link* in telplanning, planning achter het `#` (polyline + deflate-raw + base64url, formaatversie 1), niet via de server; parkeertelling, fietsparkeren en pocket lezen hem (gedeeld blok `planlink`); teltype *Pocket-parkeren*; pocket toont de opdracht boven de telvakken en de straten in paars op de *Kaart*, ook via *Opdrachten* (`?plan=…#parkeren`); handleiding, privacyverklaring, ZIP-referentie; nieuwe `functest_planlink.js` (29) en `planlinktest.py` (42) |
| v3.15 | **Geen planningen meer op de server** (Jay, na de veldtest van de link: "We hoeven de .json niet meer op te slaan op de server"): *Maak Telling* (download + opslaan) en *Opdrachten* weg uit telplanning, *Deel als link* is de hoofdknop; `planningen/` met de drie PHP-scripts en `.htaccess` uit de repo; de apps lezen `?plan=` niet meer; handleiding, privacyverklaring, ZIP-referentie, README, CLAUDE.md, ONTWIKKELEN bijgewerkt; `laadtest` deel D vervallen, `planlinktest` deel D test nu dat er niets meer naar `/planningen/` gaat (44) |
| v3.16 | Parkeertelling: **capaciteitscontouren standaard uit** (Jay: "Het kaartje is te druk om te lezen"), knop *capaciteit* in de kop van de kaart; `cap_netwerk.csv` pas opgehaald bij de eerste keer aanzetten, zonder bestand gaat de knop uit; handleiding bij *Mini-kaart & bearing*; `planlinktest` deel E (51) |
| — | Zonder versienummer (Jay): scheidingslijnen tussen de secties van de handleiding en `over.html`; h1 en h2 groter met een dikke lijn in de gedeelde kale stijl (alle vier de documentatiepagina's) |
| v3.17 | **Backlog opgeruimd**: Open Graph en TechArticle op `zip_format_reference.html`; de "terugvalcode" in telrapport en telplanning bleek niet dood (een pocket-ZIP na Doortellen kan zonder `_netwerk.csv` zijn; de Overpass-terugval vangt dat op) en kreeg eerlijk commentaar; fout commentaar over `_terrein.csv` in capaciteitstelling; `zoekTerreinen` met geheugen (geen verzoek binnen 150 m van een eerdere zoekplek, terreinen blijven staan, `ovpKeur`, niet doorvragen bij een rate-limit); bbox-filter kent verzamelingen (bbox van alle tellingen samen, laadt als geheel); nieuwe `functest_bbox.js` (11) en `onderhoudtest.py` (17) |
| v3.18 | **ZIP opslaan op Android** (Jay, veldtelling op de S25: "Zip niet opgeslagen", en ⬇ Download ZIP reageerde niet): het gedeelde blok `bewaarZip` gebruikt het deelvenster alleen nog op iOS, zoals `saveBlob` en pocket; Android en desktop krijgen een download. Chrome op Android deelt geen ZIP en weigerde, dus er kwam nooit een download. In een Android-WebView telt een download niet als opgeslagen: de noodkopie blijft. Handleiding bij *↓ Download ZIP* en *Planning als link*; nieuwe `opslaantest.py` (48) |
| — | Zonder versienummer (Jay: "Testen op github"): **tests op GitHub** bij elke PR en na elke merge (`.github/workflows/tests.yml`, opzet in `.github/actions/testopzet`): `valideer.py` tegen de vorige stand van `main`, de functests, `test_zipref`, `check_encoding` en elke browsertest in een eigen job; controle *alles groen*. `valideer.py` kreeg `VALIDEER_OUD`, `VALIDEER_NIEUW` en `VALIDEER_ZONDER_RELEASE`; `logicatest` A5 hing aan de tijdzone Amsterdam en rekent nu in die van de browser |
| v3.19 | **Slim lopen en planning** (Jay: 1A met omgeving, 2 automatisch, 3 radius 300/220): telplanning haalt een verstuurde planning terug uit de link (*Of: planning uit een link* of `#plan=`; velden en straten terug, de omgeving grijs erbij, de contour niet); een planning-link vult in de veld-app meteen de tegelcache voor het hele gebied (gedeeld blok `gebied vooraf`, één bbox-verzoek, `ovpKeur`, max. 30 tegels, regel *gebied klaar*); verversen op 220 m (pocket 170 m), bewaakt als gedeelde constante; privacyverklaring en handleiding; nieuwe `functest_gebied.js` (22) en `gebiedtest.py` (41) |
| v3.20 | **Tegelcache hersteld** (Jay, met een fietstelling en de reconstructie ervan): het gebied vooraf haalde op zonder knooppunten (`out tags geom`), dus geen aansluitingen voor pocket en de reconstructor; nu overal `out body geom`, tegelschema 3, oudere tegels tellen als misser (ook in de reconstructor). `leesTegels` geeft alleen de wegen binnen de cirkel (was: hele tegels, 1926 ways). `cacheWaysInTiles`: hele cellen, toewijzing per segment (`tegelsVanWeg`, ook in `gebiedBewaar` en de reconstructor), geen stil afbreken na wegschrijven. Parkeer-apps bewaren de knooppunten niet. Gevonden, niet in deze release: telrapport toont van een gereconstrueerde fiets-/autotelling alleen het eerste stuk per weg (v3.21). Nieuwe `functest_tegelcache.js` (13), `gebiedtest.py` deel F (51) |
| v3.21 | **Telrapport per stuk** voor fiets en auto (Jay koos B2: "Met vaste lengtes breng je er wat meer systeem in"): `splitWayIntoSegments` ook in telrapport (groep van drie), originelen geknipt en tikken ingedeeld naar hun plek langs de weg, `_recon` met zijn eigen stukken, aantallen per stuk uit de telregels, gelopen stukken zonder tikken gestreept, correctietool rekent stuk en kleur opnieuw uit en wisselt van zijde langs de hele weg. Jays telling: `_recon` 9/9 tikken in een cluster (was 5/9). Nieuwe `stukkentest.py` (21) |
| v3.22 | **Static in de familie en één herstelmelding** (Jay: "Taal: nederlands", "Maak Herstelmelding: één gedeeld blok voor alle vijf veld-apps"): Static Nederlands, huisstijl van de parkeer-apps (kop, statusbalk, Start/Stop, tellog), palet van telrapport (constante `typekleuren`), opslaan via `bewaarZip` (nu vier bestanden, haak `zipBewaard`), Start meteen na Stop; gedeeld blok `herstelmelding` in de vijf veld-apps (tekst, Doortellen, Download ZIP, Weggooien; vraag in het blok), `herstel-haken` met Weggooien voor de parkeer-apps. Overzicht in de ZIP blijft Engels. Handleiding: hoofdstuk Static in het Nederlands. Nieuwe `herstelmeldingtest.py` (103) |
| v3.23 | **Static middelt de GPS** (Jay: "De wachttijd mag niet te lang oplopen"; "grenzen van 8m en 15m. 3 minuten luisteren is prima"): tellen meteen, hooguit 3 minuten luisteren (eerder klaar bij ±4 m), gewogen gemiddelde over 2 minuten, uitschieters naar opgegeven afwijking én echte spreiding, eerlijke afwijking (30 s samenhang, ondergrens 3 m); niveaus nauwkeurig/redelijk/grof in een eigen regel; adres zodra redelijk, opnieuw na 15 m, 30 s pauze na een mislukt verzoek; straat als *Voorstraat 12*. Nieuwe `gpsmiddeltest.py` (39) |
| v3.24 | **Engelse introductie** `about.html` (Jay: "Schrijf maar een engelse over.html"): vertaling van `over.html`, kale stijl, `hreflang` en een taallink over en weer, in de sitemap; de voorpagina linkt "Wat is dit?" naar `about.html` (Engels) of `over.html` (Nederlands). `robuusttest.py` deel D (89) |
| v3.25 | **Lettertypen op de eigen server** (Jay: "google fonts zelf hosten zou ik willen, maar maakt dat het installeren bij anderen niet ingewikkelder?"; "ga"): `fonts/` met Oswald (variabel, Latijn en uitgebreid Latijn), Share Tech Mono, `fonts.css` en de licenties; 11 pagina's linken `fonts/fonts.css`; Google Fonts uit de privacyverklaring; `laadtest` gebruikt de lettertypen uit de repo, de CI installeert ze niet meer. Nieuwe `lettertypetest.py` (43) |
| v3.26 | **Opmaak GeoPackage** (Jay: "1. Tijdstippen van eerste en laatste tik. 2. De naam van de dag van de week naast de datum 3. het woordje "pocket" verwijderen achter het gps spoor. 4. De 3-letterige codering van de telling"): titel *Telrapport · donderdag 22-10-2026*; legenda GPS-spoor *do 22-10 · 13:41–14:05 · NYK* (zonder jaar, dat staat in de titel; anders liep de legenda van het A4). `gpkgSpoorLabel`; de tabel `sessies` houdt zijn `label`. `gpkgtest.py` (82) |
| v3.27 | **Pocket-netwerk in de noodkopie, oude tegels weg** (uit de lijst kleine klussen): pocket bewaart `snap.elements` met knooppunten onder `pocket_sessie_netwerk`, dus `_netwerk.csv` compleet na Doortellen en Download ZIP, hertoekenning over de hele route; bij volle opslag wijkt het netwerk voor de tikken; Overpass-terugval in telrapport blijft voor oude ZIP's. Gedeeld blok `tegels opruimen` (vijf bestanden): tegels ouder dan 90 dagen, één keer per dag; privacyverklaring bijgewerkt. `hersteltest` wisselvallig door het exporttijdstip in `_kaart.png`: kaart nu zonder kop vergeleken; pocket-delen wachten op het netwerk. `hersteltest.py` (157), `onderhoudtest.py` deel C (31) |
| v3.28 | **Capaciteit in de GeoPackage, kaartje in de `_recon.zip`, introductie herschikt** (uit de lijst kleine klussen; Jay over het kaartje: "Ondergrond is niet nodig. Netwerk en tikken is genoeg", en: in de ZIP): laag `terreinen` (POLYGON, één gesloten ring, capaciteit per soort, paars met het totaal in een cirkel), schrijver kent vlakken, geen melding meer; `kaartPng` in telreconstructie, `<sid>_kaart.png` in de ZIP (wit vlak, wegennet grijs, spoor oranje, tikken in hun kleur, kop en legenda, geen exporttijdstip), `RECON_VERSIE` v3.28; `over.html`/`about.html`: groepen van de voorpagina, plannen vooraf. `gpkgtest.py` (93), nieuwe `reconkaarttest.py` (16) |
| v3.29 | **Waarschuwen bij het delen van een ZIP** (Jay: "Als mensen een telling doen vanuit huis, en ze leveren de .zip aan derden, verraden ze de plek van hun woning. Dat is een waarschuwing waard"; "akkoord"): één regel onder de ZIP-knop, niets om weg te klikken; gedeeld blok `deelwaarschuwing` in de vijf veld-apps (NL/EN, Static met adres, pocket in het voorbeeldscherm), vaste regel in telreconstructie (`RECON_VERSIE` v3.29) en telrapport; *Een ZIP delen* in privacyverklaring (NL en EN) en handleiding (`#delen`). Geen privacyzone, geen afronding: in de backlog. Nieuwe `deeltest.py` (25) |

---

## 7. Methodiek-conclusie telrapport (ter naslag)

Op verzoek doorgelicht: de clustering is **zuiver** — elk kwalificerend punt telt precies één keer, geen dubbeltelling. Bij **gereconstrueerde** ZIP's zit elk geteld punt in een cluster. Bij **rauwe** auto/fiets-ZIP's kunnen ongesnapte tikken buiten de clusters vallen; die zijn wél zichtbaar als vervaagde ⚠-stip, en `n_waarnemingen` blijft het volledige aantal. Sinds v2.42 meldt elke sessie zelf "X/Y geclusterd", dus je ziet direct of de kaart volledig is voordat je conclusies trekt.
