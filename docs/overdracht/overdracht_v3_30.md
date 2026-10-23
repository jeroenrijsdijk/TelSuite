# Overdracht v3.30 — vijf losse eindjes en Jay's deeltekst

Jay vroeg na v3.29: "Hebben we nu nog kleine losse eindjes?" Ik gaf er vijf, elk
met een advies. Jay: "Je mag de 5 punten repareren." Over het transect-formaat:
"Nee, mag eruit." Tijdens het werk kwam er nog een tekst bij: "Dat is geen mooi
nederlands. Vervang het maar door: 'Begint je opname bij huis? Deel de zip dan
niet zomaar met iedereen'".

De CSV-kolommen veranderen niet en er komt geen bestand in de ZIP bij.

## 1. Oswald in de kaartlabels van telrapport

- **Tot nu toe:** de clusterbollen, de nummers en het capaciteitslabel vroegen
  om `Oswald`, maar telrapport laadde het lettertype niet. Er stond dus een
  reserveletter.
- **Nu:** `<link href="fonts/fonts.css" rel="stylesheet">` in de kop, zoals in
  de andere tools.
- **Bekeken:** de bollen naast elkaar met en zonder Oswald, van 6 tot 1419
  tikken. Oswald is smaller, dus de cijfers passen ruimer in het gat. Het
  capaciteitslabel met drie cijfers ook.
- **Test:** `lettertypetest.py` nam telrapport tot nu toe niet mee. Nu wel:
  telrapport linkt `fonts.css` en laadt Oswald zonder verzoek aan Google.

## 2. Het losse transect-formaat (`_trn`) is weg

Geen app maakt het nog; pocket's transect-modus (`_pkt_t`) verving het. Jay
heeft zulke ZIP's niet meer.

- **telrapport:** deze onderdelen zijn verwijderd:
  - `loadTransectZip`, met de Overpass-terugval;
  - `APP_CONFIG.transect` en `TYPES_TRANSECT`;
  - de transect-tak in `showClusterDetail`;
  - de soort *Transect* in de sessielijst;
  - `hasTransect`;
  - `transect` in de GeoPackage-labels.

  De voorwaarden `appType === 'transect' || appType === 'pocket'` zijn nu
  `appType === 'pocket'`. De reservekleur van een losse clusterbol komt uit
  `SS_TYPE_COLOR`. Dat zijn dezelfde kleuren, en het is de gedeelde constante
  `typekleuren`.
- **Een `_trn.zip` (app_type `transect`)** geeft nu een melding: *"een los
  transect-bestand (_trn). Dat formaat leest telrapport sinds v3.30 niet meer.
  Tel een transect met pocket (Transect); die ZIP leest telrapport wel."* Hij
  komt niet op de kaart. Andere ZIP's in dezelfde keuze laden gewoon.
- **Blijft:** pocket's transect-modus (`pocket:transect`, `MODUS_META.transect`).
  De bestandsnaamherkenning in `reconBasis` kent `_trn` ook nog. Dat is
  onschuldig, en zo komt er een melding in plaats van stilte.
- **Referentie:**
  - de sectie *Move and Count* (`*_trn.zip`) is weg;
  - de rij `_trn` in de tabel met bestandsnamen en de rij in het overzicht
    zijn weg;
  - er staat nu een alinea *No more `_trn`*;
  - het CSS-kleurtje `--c-transect` is weg.

  `test_zipref.py` kent geen *alleen nog leesbaar* meer.

## 3. De kop van het veiligheidsblok

In de handleiding is *Denk aan je eigen veiligheid* nu een `<h4>`, zoals de
andere tussenkopjes in de methodiek. Tot nu toe was het een `<h1>`. De zin
eronder is ongewijzigd.

## 4. De legenda van de GeoPackage bij veel tellingen

Onder *GPS-spoor* staat per telling een regel (v3.26). Bij veel tellingen liep
de legenda daardoor uit het A4-vak.

- **De regel:** passen er meer dan `GPKG_LEGENDA_MAX` (20) regels in de legenda,
  dan wordt het GPS-spoor één regel. Er wordt geteld over waarnemingen,
  spoor, wegvakken en capaciteit.
  - De 20 is gemeten in de opmaak van v3.28: 16 regels en 4 laagnamen vulden
    140 van de 180 mm.
  - Het spoor krijgt dan één stijl (`singleSymbol`). De kleur per telling komt
    uit het veld `kleur`, met dezelfde doorzichtigheid
    (`set_color_part("kleur", 'alpha', 179)`).
  - De laag heet dan *GPS-spoor (n tellingen)*.
  - De regel per telling (dag, tijden, code) staat dan niet in de legenda. De
    tabel `sessies` heeft hem nog.
- **Bekeken:** de opmaak in QGIS 3.34, met de drempel op 5. Er staat één regel
  *GPS-spoor (3 tellingen)*, en de sporen op de kaart houden hun kleur.

## 5. De vingerafdruk bij de export

Uit `verantwoording.html` (v3.4), bewijswaarde punt 1.

- **Nieuw gedeeld blok `vingerafdruk`** in de vijf veld-apps:
  `vingerafdruk(blob, naam)` rekent met WebCrypto de SHA-256 van precies de
  ZIP. De regel staat onder de deelwaarschuwing:
  - *Vingerafdruk (SHA-256) van <naam>: <code>* in Share Tech Mono;
  - een link *✉ Mail deze code naar jezelf* (`mailto:`), met de naam, de code,
    het tijdstip en hoe je controleert (`certutil -hashfile … SHA256` en
    `shasum -a 256 …`);
  - in het Nederlands of het Engels, net als de deelwaarschuwing;
  - één regel: een volgende ZIP vervangt hem.

  Waarom een mail: een mail aan jezelf draagt de tijd van de mailserver. Wie
  later dezelfde code uit het bestand berekent, laat zien dat de ZIP sinds dat
  moment niet is veranderd. Er is geen server voor nodig.
- **Waar het wordt aangeroepen:**
  - in `bewaarZip`, het gedeelde blok van de parkeer-apps en Static, bij elke
    poging tot opslaan;
  - in pocket bij het openen van het voorbeeldscherm, met `lastZipBlob`.
- **Zonder `crypto.subtle`** (een pagina via http) komt er geen regel, en geen
  fout.
- **`verantwoording.html`:**
  - bij de zwakke plek *Het bestand is achteraf te bewerken* staat nu dat de
    app de vingerafdruk toont, en wat de mail dan bewijst;
  - bij *Wat een beoordelaar kan nagaan*, punt 2, staat nu hoe je de code
    narekent.

## 6. De deelwaarschuwing in Jay's woorden

| waar | tekst |
|---|---|
| veld-apps | *Begint je opname bij huis? Deel de zip dan niet zomaar met iedereen.* |
| Static | *Tel je vanuit huis? Deel de zip dan niet zomaar met iedereen.* |
| telreconstructie | *Begint je opname bij huis? Deel de zip dan niet zomaar met iedereen.* |
| telrapport | *Begint een opname bij huis? Deel de verzameling of GeoPackage dan niet zomaar met iedereen.* |
| Engels (pocket) | *Does your recording start at home? Then don't share the ZIP with just anyone.* / *Counting from home? …* |

Static, telrapport en de Engelse regel zijn afgeleid van Jay's zin. Voor Static
past "opname bij huis" niet, want Static telt op één plek. `RECON_VERSIE` wordt
v3.30, omdat telreconstructie veranderde (de regel van `valideer.py`).

## 6b. De topregel van telreconstructie

Jay: "de topregel van telreconstructie is nogal technisch … die regel mag weg. Of
je mag er iets leukers voor verzinnen". De regel was een opsomming van wat er
in v2.23 en v2.24 bijkwam ("Herfetch · hersnap · richtingslaag · …"), met twee
kapotte `&middot;`'s erin. Nu staat er: *Zet elke tik achteraf op de goede straat
en aan de goede kant, met je hele route erbij.* Dat is wat de voorpagina en
`over.html` er ook over zeggen.

## 7. Tests

- **`vingerafdruktest.py`** (nieuw, 24):
  - in de vijf veld-apps is de code de SHA-256 van het gedownloade bestand,
    nagerekend met `hashlib`;
  - de regel staat onder de deelwaarschuwing, met naam en code;
  - de mail-link heeft de naam, de code en de controle;
  - in Static vervangt een tweede ZIP de regel;
  - pocket in het Engels;
  - zonder `crypto.subtle` komt er geen regel en geen fout.
- **`gpkgtest.py`** 101 (was 93), deel E2:
  - met de drempel op 5 is het spoor één stijl met de kleur uit `kleur`, en
    heet de laag *GPS-spoor (3 tellingen)*;
  - met de gewone drempel blijft het een categorie per telling;
  - in QGIS zijn de stijl, de kleur uit het veld en de legenda bekeken, met de
    opmaak als PNG.
- **`gpkg_qgis.py`** meldt bij een enkelvoudige stijl of de kleur uit een veld
  komt.
- **`onderhoudtest.py`** 34 (was 31), deel D: een `_trn.zip` geeft de melding
  en laadt niet; de pocket-ZIP ernaast laadt wel.
- **`lettertypetest.py`** 46 (was 43): telrapport doet mee.
- **`deeltest.py`** (25): de nieuwe teksten.
- **`functest_coordinaten.js`** 28 (was 29) en **`functest_taartbol.js`** 23
  (was 24): zonder het losse transect.
- **`test_zipref.py`**: zonder *alleen nog leesbaar*.
- **`valideer.py`**: groep `vingerafdruk` (5 bestanden). Het blok
  `bewaarZip` (4) en het blok `deelwaarschuwing` (5) zijn mee veranderd en
  nog steeds byte-identiek.

## 8. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | Oswald; `_trn` weg en een melding; legenda samenvatten (`GPKG_LEGENDA_MAX`, `lijnPerKleur`); deelregel |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `traffic_counter.html` | blok `vingerafdruk`, aanroep in `bewaarZip`; deeltekst |
| `pocket_count.html` | blok `vingerafdruk`, aanroep in `showPreview`; deeltekst |
| `telreconstructie.html` | deeltekst; topregel; `RECON_VERSIE` v3.30 |
| `zip_format_reference.html` | `_trn` weg; legenda in de GeoPackage |
| `traffic_counter_help.html` | kop veiligheid; legenda bij veel tellingen |
| `verantwoording.html` | de vingerafdruk |
| `index.html` | versie v3.30 |
| `_archief/overpass_rig/vingerafdruktest.py` | nieuw |
| `gpkgtest.py`, `gpkg_qgis.py`, `onderhoudtest.py`, `lettertypetest.py`, `deeltest.py`, `functest_coordinaten.js`, `functest_taartbol.js`, `test_zipref.py`, `valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 9. Validatie

```
valideer.py            ALLES OK — 11 verwachte bestanden; gedeelde blokken OK, nieuw: vingerafdruk (5);
                       bewaarZip (4) en deelwaarschuwing (5) byte-identiek; RECON_VERSIE v3.30
vingerafdruktest.py    24/24 (nieuw)
gpkgtest.py            101/101 (QGIS 3.34 deel G meegedraaid, samengevatte opmaak als PNG bekeken)
onderhoudtest.py       34/34   lettertypetest.py 46/46   deeltest.py 25/25
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
