# Overdracht v3.29 — waarschuwen bij het delen van een ZIP

Jay: "Als mensen een telling doen vanuit huis, en ze leveren de .zip aan
derden, verraden ze de plek van hun woning. Dat is een waarschuwing waard."
Voorstel: alleen waarschuwen, op drie plekken. Jay: "akkoord".

Er verandert niets aan de data of het ZIP-schema.

## 1. Wat een ZIP over je plek zegt

- **Static.** Het overzicht bevat de gemiddelde GPS-plek op 6 decimalen
  (enkele meters) en de straat met huisnummer ("Voorstraat 12"). Wie vanuit
  zijn raam telt, zet zijn adres in de ZIP.
- **Lopende tellingen** (pocket, parkeertelling, fietsparkeren, capaciteit).
  Het GPS-spoor loopt van Start tot Stop. Het zit in `_gps.csv`, de GPX en
  `_kaart.png`, en sinds v3.28 ook in de `_recon.zip`. Wie bij de voordeur
  begint, zet zijn huis in de ZIP.
- **De tellernaam** staat in de ZIP als hij is ingevuld.
- **Telrapport.** De verzameling en de GeoPackage nemen de routes mee.

## 2. Wat er is

- **Eén regel onder de knop waarmee je de ZIP bewaart.** De regel is altijd
  dezelfde, klein en zonder iets weg te klikken: een melding die je moet
  wegtikken, leer je blind weg te tikken.
  - Veld-apps: *"ⓘ Deel je deze ZIP, dan deel je je route en je plek. Begon je
    thuis, dan staat je huis erin."*
  - Static: *"… dan deel je je plek en adres. Tel je vanuit huis, dan staat je
    huis erin."*
- **Gedeeld blok `deelwaarschuwing`.** Het staat in de vijf veld-apps:
  `DEEL_TEKST` (Nederlands en Engels) en `deelWaarschuwing(onder, metAdres)`.
  - De app geeft het element waaronder de regel komt.
  - De taal volgt `<html lang>`. Opnieuw aanroepen werkt de tekst bij, en zet
    er geen tweede regel bij.
  - De regel neemt de tekstkleur over, met 70% dekking. Zo past hij op lichte
    en donkere achtergronden.
- **Waar de regel staat:**
  - parkeertelling, fietsparkeren, capaciteitstelling: onder *Download ZIP*,
    bij het laden;
  - Static: onder *Download ZIP*, met adres;
  - pocket: in het voorbeeldscherm onder de kop met *ZIP opslaan*, telkens als
    dat scherm opent, in de taal van dat moment.
- **Telreconstructie:** een vaste regel onder *Herschreven ZIP downloaden*.
  Dat was niet genoemd in het voorstel, maar het is ook een ZIP om te delen.
  Volgens de regel van `valideer.py` gaat `RECON_VERSIE` daardoor naar v3.29.
- **Telrapport:** een vaste regel onder *bewaar kaart als verzamel-ZIP* en
  *GeoPackage*.
- **Privacyverklaring:**
  - nieuw kopje *Een ZIP delen*: wat erin staat, en "start en stop dan een
    eindje van huis";
  - in het Engelse deel *Sharing a ZIP*.
- **Handleiding:** nieuwe sectie *Een ZIP delen* (`#delen`) onder Algemeen,
  in de inhoudsopgave en met een link naar de privacyverklaring.

## 3. Bewust niet

- **Begin en eind van het spoor weglaten** (zoals de privacyzone van Strava).
  Dat verandert de data: bezocht, aanwezigheid, p/m·u, en dus wat KNIME
  binnenkrijgt. Als het ooit nodig is, dan als aparte deelversie naast de
  echte ZIP. In de backlog.
- **Static afronden.** De plek is daar de meting zelf. Alleen het huisnummer
  weglaten helpt weinig, want de coördinaat wijst het huis toch aan.

## 4. Tests

**`deeltest.py`** (nieuw, 25 tests):
- **De vier apps met een vaste knop:**
  - de regel staat direct onder de knop en is zichtbaar;
  - de tekst klopt (Static met adres);
  - er is één regel, ook na een tweede aanroep;
  - op 360 px schuift niets zijwaarts.
- **Pocket:**
  - geen regel zolang er niets te bewaren is;
  - in het voorbeeldscherm in het Nederlands, en na de taalknop in het Engels.
- **Telreconstructie en telrapport:** de regel staat op de goede plek.
- **Privacyverklaring en handleiding:** de nieuwe stukken staan erin.

**`valideer.py`:** groep `deelwaarschuwing` (5 bestanden).

**Zelf bekeken:** schermafdrukken van alle plekken (parkeertelling, Static,
pocket, telrapport) op telefoonbreedte.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `pocket_count.html`, `traffic_counter.html` | blok `deelwaarschuwing` en de aanroep |
| `telreconstructie.html` | regel onder de downloadknop; `RECON_VERSIE` v3.29 |
| `telrapport.html` | regel onder verzameling en GeoPackage |
| `privacy.html` | *Een ZIP delen* (NL), *Sharing a ZIP* (EN) |
| `traffic_counter_help.html` | sectie *Een ZIP delen* |
| `index.html` | versie v3.29 |
| `_archief/overpass_rig/deeltest.py` | nieuw |
| `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — 10 verwachte bestanden; gedeelde blokken OK, nieuw: deelwaarschuwing (5 bestanden);
                       RECON_VERSIE v3.29; documentatiepagina's kaal
deeltest.py            25/25 (nieuw)
alle overige browsertests en de 20 functests groen; test_zipref en check_encoding OK
```
