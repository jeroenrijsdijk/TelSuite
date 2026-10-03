# Overdracht v2.77 — parkeer-apps volgen de opruimregel

Op verzoek van Jay het backlogpunt uit v2.76 opgepakt: de parkeer-apps wisten
de noodkopie ook als de ZIP niet was opgeslagen. Ze volgen nu dezelfde regel
als pocket en Static.

---

## 1. Wat er misging (v2.76 en eerder)

De export van parkeertelling, fietsparkeren en capaciteit deed na Stop:

```
deelvenster voltooid     -> kopie wissen
deelvenster geannuleerd  -> download-link starten, en kopie wissen
deelvenster mislukt      -> download-link starten, en kopie wissen
```

Bij annuleren of mislukken werd de kopie dus altijd gewist, ook als die
download-link niets opleverde. Op de iPhone is dat onzeker: de link wordt
gestart buiten een tik, na het inpakken van kaart en ZIP. Daarbij startte er
een download die niemand gevraagd had, terwijl je net "annuleren" had getikt.

## 2. Wat er nu gebeurt

| situatie | noodkopie | wat je ziet |
|---|---|---|
| deelvenster voltooid | weg | statusregel *ZIP opgeslagen · &lt;naam&gt;* |
| geen deelvenster (desktop) | weg na de download | idem |
| deelvenster geannuleerd of mislukt | **blijft** | *ZIP niet opgeslagen — tik op ⬇ Download ZIP …*; geen ongevraagde download |

**Opnieuw proberen werkt nu ook op de iPhone.** De knop *⬇ Download ZIP*
pakte tot nu toe alles opnieuw in (kaart, comprimeren) voordat het deelvenster
openging. Daarbij kan het tikgebaar verlopen, en dan weigert het deelvenster
opnieuw. Nu onthoudt de app de laatst gemaakte ZIP met een sleutel: sessie-id,
aantal vermeldingen, aantal GPS-punten, en bij capaciteit het aantal
terreinen. Is die sleutel na Stop onveranderd, dan biedt de knop dezelfde ZIP
**meteen** aan, binnen dezelfde tik.

Door de sessie-id in de sleutel krijg je nooit de ZIP van een vorige sessie,
ook niet als die toevallig evenveel tikken had. De test controleert dat.

Bijeffect: opnieuw exporteren levert nu hetzelfde bestand op. Voorheen kreeg
elke export een nieuwe eindtijd in `_sessie.csv`.

De losse knoppen voor CSV, GPX en kaart zijn ongewijzigd. Dat zijn
tussenexports; ze raken de noodkopie niet.

## 3. Hoe het gebouwd is

- **Nieuw gedeeld blok** `zipSleutel()` + `bewaarZip()`, byte-identiek in de
  drie apps en bewaakt in `valideer.py` (groep `bewaarZip`). De
  deelvenster-logica stond eerder drie keer los in `exportZip()`.
- `exportZip()`: bovenaan een snelle route die dezelfde ZIP opnieuw aanbiedt
  (alleen na Stop, bij dezelfde sleutel). Onderaan roept hij `bewaarZip()`
  aan in plaats van de oude `finalizeExport`-code.
- `csvDownloaded` en `kaartDownloaded` gaan alleen nog op `true` na een
  bevestigde opslag. Daardoor waarschuwt de browser bij het sluiten van de
  pagina als de ZIP nog niet is opgeslagen, en slaat het vangnet bij
  scherm-uit de kopie nog op.
- Niet veranderd: op Android opent nog steeds het deelvenster (pocket en
  Static kiezen daar een gewone download). Dat staat los van de opruimregel.

## 4. Tests

`opruimtest.py`, nu **52 tests**:

- De iPhone-scenario's B, C en D slaan de parkeer-apps niet meer over.
- In B wordt ook gecontroleerd dat er na annuleren geen download start.
- Nieuw deel F:
  - de statusregel zegt *niet opgeslagen*;
  - opnieuw via de knop geeft hetzelfde bestand, zonder opnieuw in te pakken
    (gemeten door `generateAsync` te tellen);
  - de statusregel meldt daarna *opgeslagen*;
  - een nieuwe sessie met evenveel tikken krijgt een nieuwe ZIP.

Op v2.76 gedraaid geeft de test **15 fouten**. Daaronder één die alleen de
teller van `generateAsync` zag: v2.76 pakte opnieuw in en kwam toevallig op
exact dezelfde bestandsgrootte uit. Een vergelijking op naam en grootte was
dus niet genoeg geweest.

## 5. Veldtest

`VELDTEST_3.0.md` stap 4 heeft twee punten erbij:

1. Verschijnt het deelvenster na Stop? Dat vertelt ons of het tikgebaar het
   inpakken overleeft op jouw iPhone. Zo niet, dan tik je *⬇ Download ZIP*.
2. Annuleer het deelvenster eens: er start geen download, de statusregel meldt
   het, en na herladen is de herstelmelding er.

Het draaiboek wijst nu naar v2.77, ook in het project.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | gedeeld blok `bewaarZip`, snelle route in `exportZip()` |
| `traffic_counter_help.html` | alinea bij *Download ZIP* |
| `index.html` | versie v2.77 |
| `_archief/overpass_rig/opruimtest.py` | parkeer-apps in B–D, nieuw deel F; 26 → 52 tests |
| `_archief/overpass_rig/valideer.py` | groep `bewaarZip`, `RELEASE` |
| `VELDTEST_3.0.md`, rig-`README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt; het backlogpunt is weg |

## 7. Validatie

```
valideer.py        ALLES OK — 5 verwachte bestanden gewijzigd; 12 groepen gedeelde blokken OK (nieuw: bewaarZip)
opruimtest.py      52/52   (op v2.76: 15 FOUT)
hersteltest.py     133/133
laadtest.py        46/46
statictest.py      24/24
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
