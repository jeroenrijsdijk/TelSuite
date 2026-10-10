# Overdracht v3.4 — toelichting voor juristen, GPX-tijden in UTC

Jay: "Als iemand telonline.org heeft gebruikt, en de gedane telling wordt
onderdeel van een juridische procedure, dan wil ik een verhaaltje hebben dat je
kunt laten lezen aan de rechter." En daarna: "Je hoeft het document niet aan te
passen op de tellers, alleen op de lezers. Dat is de jurist die zoekt naar wat
de app telt en wat de app ermee doet. Beschrijf de sterke en zwakke plekken. Het
alternatief is een papiertje waarop geturfd is."

---

## 1. Nieuw: `verantwoording.html`

Een kale pagina (zelfde stijlblok als de handleiding) voor wie een telling
beoordeelt: rechter, advocaat, adviseur. Ongeveer 1700 woorden.

| deel | inhoud |
|---|---|
| inleiding | voor wie, de maatstaf (turven op papier); representativiteit hangt af van de opzet, niet van het hulpmiddel |
| In het kort | een mens telt, de app noteert; tijd en GPS per tik, route; gegevens blijven bij de teller; ZIP is achteraf te bewerken; code is openbaar |
| Wat de app vastlegt | sessienummer, tijden, teller (niet gecontroleerd), per tik tijd/soort/positie; tabel per soort telling (Static, parkeren, pocket); positie, route en plek op de straat |
| Wat er daarna gebeurt | noodkopie op het toestel, ZIP, reconstructie (nieuw bestand, aantallen en tijden ongewijzigd, `handmatig`), telrapport (`manually_corrected`) |
| Sterke punten | aanwezigheid, tijd per waarneming, plaats per waarneming, de data zegt zelf waar ze onzeker is, openbare code |
| Zwakke plekken | menselijke waarneming, ongedaan maken laat geen spoor, klok van de telefoon, GPS-nauwkeurigheid, koppeling aan een straat, Static heeft geen route, geen versienummer in het bestand, achteraf te bewerken, oude GPX-tijden |
| Wat een beoordelaar kan nagaan | originele ZIP vragen, hoe bewaard, aantallen vergelijken, route op de kaart, nauwkeurigheid, correcties zoeken |

"Opgesteld door de maker van telonline.org", zonder naam (Jay). Gelinkt vanuit
de lijst onderaan `over.html` en de bestandentabel in de handleiding; staat in de
sitemap.

**Elke bewering is in de code nagelopen.** Wat daarbij bleek en in de tekst staat:

- De tijd per tik komt van de klok van de telefoon, als lokale tijd zonder
  tijdzone (`new Date()`).
- De positie van een tik is de laatst ontvangen GPS-positie (`currentLat`,
  `lastLat`); `maximumAge` 2 à 3 s.
- De parkeer-apps zetten de telknoppen uit bij een nauwkeurigheid boven 25 m
  (`GPS_THRESHOLD`, met 3 s marge). Pocket telt ook zonder GPS.
- `_gps.csv` krijgt een punt per 5 m verplaatsing; de GPX van de parkeer-apps
  krijgt elk punt.
- Static bepaalt één positie bij de start (beste fix binnen 30 s) en heeft geen
  route; wel een hartslag per 10 s voor onderbrekingen.
- Ongedaan maken haalt de tik weg (`pop`/`splice`); er blijft niets van over.
- De veld-apps schrijven geen versienummer in de ZIP; alleen de reconstructie
  stempelt (`reconstructie`).

## 2. GPX-tijden in echte UTC

De drie parkeer-apps schreven in het GPX-bestand de lokale tijd met een `Z`
erachter: `2026-10-10T09:54:12Z` voor een punt van 09:54:12 Nederlandse tijd.
Een GPS-programma leest dat als UTC, dus één uur (winter) of twee uur (zomer) te
laat. De tijd in de GPX-kop was wel echte UTC. De CSV-bestanden waren altijd goed.

Nu:

- Een routepunt krijgt naast `ts` (lokaal, zoals altijd) een veld `utc`, uit
  **hetzelfde** `Date`-object. `timestamp(d)` neemt daarvoor een optionele datum;
  zonder argument werkt hij als voorheen.
- De GPX schrijft `utc`. Een punt uit een noodkopie van vóór v3.4 heeft alleen
  `ts`; dat rekent de browser om naar UTC. Alleen in het dubbele uur bij de
  overgang naar wintertijd is die omrekening niet eenduidig; nieuwe punten
  hebben dat probleem niet.
- `utcTijd` en `gpxTijd` staan als gedeeld blok in de drie apps
  (`/* ── GPX-tijd (v3.4) ── */`), bewaakt door `valideer.py`.
- Geen schemawijziging: de CSV's zijn ongewijzigd; KNIME leest de GPX niet.
  De handleiding en de ZIP-referentie noemen de UTC-tijden.

Getest: `functest_gpxtijd.js` (nieuw, 31 tests) knipt de functies uit de drie
apps en draait ze in de tijdzone Europe/Amsterdam: zomer- en wintertijd, een
punt uit een oude noodkopie, een onleesbare tijd. Daarnaast in Chromium met
nagebootste GPS: in alle drie de apps is elke GPX-tijd precies de lokale tijd
van dat punt, omgerekend naar UTC.

## 3. Branches op GitHub

Jay vroeg of ik de oude branches opruim. Tien branches van al samengevoegde PR's
stonden er nog; hun laatste commit was steeds precies wat er is samengevoegd.
Verwijderen vanuit de Claude-omgeving wordt geweigerd (geen schrijfrecht op dat
deel van de GitHub-API). Wat werkt:

- **Eenmalig**: op GitHub onder *Branches* de oude verwijderen, of op elke
  samengevoegde PR de knop *Delete branch*.
- **Voortaan vanzelf**: *Settings → General → Pull Requests → Automatically
  delete head branches*. Dan verdwijnt de branch bij elke merge.

## 4. Backlog: bewijswaarde

In de stand van zaken, in volgorde van nut:

1. **Vingerafdruk bij de export** (Jay: later): de SHA-256 van de ZIP tonen,
   met een knop om die naar jezelf te mailen. Daarmee is aantoonbaar dat de ZIP
   sinds dat moment niet veranderd is.
2. **`n_ongedaan` en `app_versie`** in `_sessie.csv`, als kolommen achteraan.
   Schemawijziging, dus eerst KNIME.
3. **Consistentiecheck** in telrapport.

Bij elk daarvan: de zwakke plekken in `verantwoording.html` bijwerken.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `verantwoording.html` | nieuw |
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | GPX-tijd in UTC: `timestamp(d)`, gedeeld blok, `utc` per routepunt |
| `over.html`, `traffic_counter_help.html` | link naar de verantwoording; handleiding noemt GPX in UTC |
| `zip_format_reference.html` | GPX-tijden in UTC sinds v3.4 |
| `index.html` | versie v3.4 |
| `sitemap.xml` | `verantwoording.html` erbij |
| `_archief/overpass_rig/functest_gpxtijd.js` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md` | groep `GPX-tijd`, kale stijl in vier pagina's, `github.com` als link zonder verzoek, release v3.4 |
| `CLAUDE.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py        ALLES OK — 8 verwachte bestanden gewijzigd (1 nieuw); 14 groepen gedeelde blokken OK; 4 pagina's kaal; sitemap 14 adressen
functests          alle 14 groen (nieuw: functest_gpxtijd.js 31/31)
GPX in Chromium    3 apps, elke tijd = lokale tijd omgerekend naar UTC, geen JS-fouten
test_zipref.py     referentie sluit aan op de code
laadtest.py        47/47
statictest.py      24/24
opruimtest.py      52/52
hersteltest.py     133/133 (de GPX na herstel is gelijk aan zonder onderbreking)
gpkgtest.py        80/80
check_encoding.py  alles geldige UTF-8
```
