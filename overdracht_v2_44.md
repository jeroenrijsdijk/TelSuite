# TrafficCounterSuite v2.44 — Overdracht

**"Reconstrueren"-knop in pocket** — de meest gebruikte module heeft nu ook de directe doorstuur-knop, in aanvulling op de drie parkeer-apps uit v2.43. Alleen `pocket_count.html` wijzigt; de rest byte-identiek aan v2.43.

## Waar de knop zit

Pocket heeft geen knoppenpaneel zoals de parkeer-apps, maar toont na Stop een **preview-overlay** ("Telling afgerond") met een kaartje van de telling. Daar is de knop geplaatst, tussen "⇓ ZIP opslaan" en "✕ Sluiten":

`⇓ ZIP opslaan` · `↻ Reconstrueren` · `✕ Sluiten`

Dat is precies het juiste moment: je ziet net je telling en kunt met één tik door naar de reconstructie. Stijl volgt `#preview-save`, met de blauwe accentkleur (#1f5fbf) die de reconstructie-knop elders in de suite ook heeft.

## Hoe het werkt

`openReconstructie()` gebruikt **`lastZipBlob`/`lastZipName`** — exact dezelfde bron als `savePreviewZip()`, dus geen hercompressie en gegarandeerd dezelfde ZIP als je zou opslaan. Van daaruit loopt het via de handoff uit v2.43: blob in IndexedDB (store `handoff`) → `parkeer_reconstructie.html?handoff=1` → reconstructor pikt 'm op en wist de overdracht.

Geen blob beschikbaar → nette melding ("stop eerst de telling"). Doorsturen mislukt → melding met het advies de ZIP op te slaan en handmatig te slepen. Geen stille fouten.

## Geverifieerd

- `stuurNaarReconstructie` (uit v2.43) en de nieuwe `openReconstructie` staan in **hetzelfde inline script-blok** (pocket heeft er maar één), dus de functies zien elkaar — expliciet gecontroleerd, want pocket's structuur verschilt van de parkeer-apps.
- **`node --check`** + **HTML-tagbalans** schoon.
- Alle onderdelen aanwezig: knop in de preview-header, CSS, handler, juiste blob-bron, verzender; de cache-deling uit v2.43 is intact (2 aanroepen).
- **Byte-identiteit:** t.o.v. v2.43 wijzigde uitsluitend `pocket_count.html`.

## Stand van de reconstructie-knop

| App | Knop | Plek |
|---|---|---|
| parkeertelling | ✓ | onder de ZIP-knop |
| fietsparkeren | ✓ | onder de ZIP-knop |
| capaciteitstelling | ✓ | onder de ZIP-knop |
| pocket (alle 4 submodi) | ✓ | preview-overlay na Stop |
| traffic_counter (static) | — | exporteert één CSV, gaat niet door de reconstructor |

De gedeelde tegelcache (v2.43) draait in alle vier de veld-apps.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen naar de andere tel-modi.
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
