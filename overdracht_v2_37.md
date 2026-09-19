# TrafficCounterSuite v2.37 — Overdracht

Proef: **audio-feedback (een klikje) bij een tik in de parkeren-submodus van `pocket_count`**. Bewust beperkt tot alleen die submodus, zodat Jay kan uitproberen of het bevalt vóór het breder gaat. Alleen `pocket_count.html` wijzigt; de rest byte-identiek aan v2.36.

## Wat is toegevoegd

Een zelfstandige Web-Audio-helper `klik(freq, dur)` (net vóór `adjustParkeer`):
- **Geen geluidsbestand / geen CDN** — de klik wordt in code gesynthetiseerd (triangle-oscillator, snelle attack + decay ~30 ms). Blijft binnen de single-file-filosofie.
- **iOS Safari-proof** — de audio-context wordt bij de eerste tik ontgrendeld (`resume()` binnen de tik-gesture, Apple's autoplay-eis). Faalt stil als Web Audio niet beschikbaar is.
- **Twee onderscheidende tonen** in `adjustParkeer`: een korte hoge tik (1100 Hz) bij +1 (tellen), en een lagere toon (560 Hz) bij −1 (ongedaan maken, alleen als er echt iets teruggedraaid wordt). Zo hoor je zonder te kijken óók *wat* er gebeurde.

Aan/uit via `var GELUID = true;` bovenaan het blok.

## Waarom audio hier (context)

De apps geven nu een trilling (`navigator.vibrate`), maar **iOS Safari ondersteunt de Vibration API niet** — op de iPhone doet die trilling niets. Audio vult dat gat op het doelapparaat. De trilling blijft staan (werkt op Android); de klik komt ernaast.

## Bewust NIET gedaan (afwachten of Jay het fijn vindt)

- Alleen de **parkeren**-submodus; niet de andere pocket-submodi of de losse tel-apps.
- **Geen UI-schakelaar** — voorlopig een code-flag (`GELUID`). Een echte instelling in het scherm is de logische vervolgstap als het bevalt.
- **Geen iOS-mute-override** — staat de telefoon op stil (fysieke schakelaar), dan speelt Web Audio niet af. De (wat hacky) truc om dat te negeren is bewust achterwege gelaten; aparte keuze.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- Geverifieerd: 3 `klik`-verwijzingen (definitie + tik + undo); de klik zit uitsluitend in het parkeren-blok.
- **Byte-identiteit:** t.o.v. v2.36 wijzigde uitsluitend `pocket_count.html`.

## Als het bevalt — vervolgstappen (backlog)

- Klik ook in de andere pocket-submodi (simpel/transect/winkelstraat) en eventueel de tel-apps.
- UI-schakelaar voor geluid (i.p.v. de code-flag).
- Eventueel per-actie geluiden verder uitwerken (bv. een fout-buzz).
- Beslissing over de iOS-mute-override.

## Backlog (ongewijzigd)

- `parkeer_reconstructie.html` → `telreconstructie.html` (bestand + verwijzingen).
- Overpass fallback-helper in `telrapport.html`; mirrornaam `overpass.kumi.systems` → `overpass.private.coffee`.
- `over.html`: `__volgt__`-placeholder invullen met de QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding (optioneel).
- Parkeren uit pocket halen; plakkerigheid-kernel naar telrapport; %bezet dag×uur; QGIS-loader joins.
