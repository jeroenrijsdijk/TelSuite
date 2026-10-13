# Overdracht v3.7 — weekprofiel: tabel, betrouwbaarheid, koppeling

Jay over het weekprofiel in telrapport (klik op een link na het inladen):
"zou je deze tabel op datum kunnen sorteren, nieuwste bovenaan, zou je de tijd
altijd in seconden kunnen weergeven, en kun je de weekdag erbij zetten? Zie je
zelf ook nog mogelijke verbeteringen?" Daarna, over mijn voorstellen: "Ik vind
al je suggesties goed, dus ga."

## 1. Wat er veranderd is

**De tabel "Tellingen op dit segment"**

| was | nu |
|---|---|
| gesorteerd op de datum als tekst ("01-07-2026"), dus op dag van de maand | nieuwste bovenaan, op het moment van het eerste bezoek aan dit segment |
| "01-07-2026" | "wo 01-07-2026 14:05": weekdag zoals in het diagram, en het tijdstip |
| "1.2 min" boven de minuut | altijd seconden: "72 s" |
| aparte kolom *visits* | in *aanwezig*: "72 s · 2×" (alleen bij meer dan één bezoek) |
| — | tooltip op p/m·u met de 95%-marge |
| — | rij lichter als de waarde onzeker is |

**Het diagram**: de tooltip van een cel geeft de tijd in seconden en de
95%-marge. Een onzekere cel staat lichter.

**Koppeling**
- Klik op een rij: de cellen waarin die telling meetelt, krijgen een witte rand.
- Klik op een cel: de tabel toont alleen de tellingen in die cel; de ∑-rij
  verdwijnt zolang.
- Nog een keer klikken zet alles terug. Er is één selectie tegelijk.

Onder de tabel staat een regel uitleg. De handleiding heeft twee nieuwe
alinea's in *Drukte & weekprofiel*.

## 2. De 95%-marge

Een telling van k tikken is een Poisson-waarneming. De marge is het exacte
(Garwood-)interval op het verwachte aantal:
- ondergrens: de λ waarvoor P(X ≥ k) = 2,5%;
- bovengrens: de λ waarvoor P(X ≤ k) = 2,5%.

Gedeeld door segmentlengte × uren geeft dat de marge in p/m·u.

- `poissonCdf` rekent in log-ruimte. Dat klopt ook voor grote aantallen: bij
  1000 tikken gaat `exp(-λ)` anders naar nul.
- `poissonMarge` zoekt de grenzen met bisectie (60 stappen). Getoetst aan scipy
  (`chi2.ppf`) voor k = 0, 1, 2, 5, 50 en 1000: gelijk tot op 0,002.
- Hoe groot de marge naar verhouding is, hangt alleen af van k, niet van de
  meetduur.

| tikken | tijd (45 m) | p/m·u | 95%-marge |
|---|---|---|---|
| 2 | 23 s | 7.0 | 0.8 – 25 |
| 8 | 22 s | 29 | 13 – 57 |
| 50 | 44 s | 91 | 68 – 120 |

**Onzeker** betekent: minder dan 5 tikken, én de marge loopt over een
klassegrens. Valt de hele marge in één klasse, dan is de waarde niet onzeker.
Een voorbeeld is lang gemeten en vrijwel niets geteld: 1 tik in 120 s geeft een
marge van 0 tot 3,7, dus zeker Rustig.

In een cel kan het aantal tikken een breuk zijn, omdat bezoeken over een
uurgrens naar rato worden verdeeld. Voor de marge wordt het afgerond.

## 3. Wat niet

- **Tellerkolom.** Ik had hem voorgesteld, maar hij heeft hier geen zin. Het
  weekprofiel bestaat alleen voor pocket-tellingen (die met `_bezocht.csv`), en
  pocket legt geen tellernaam vast. De kolom zou altijd leeg zijn.
- **Hoe de waarden zelf berekend worden**, het poolen van tikken en tijd, is
  ongewijzigd. Alleen de weergave en de marge zijn nieuw.

## 4. Tests

`functest_segmenttabel.js` is nieuw en heeft 23 tests:
- **A. tabel:** de volgorde (ook over jaargrenzen heen), weekdag en tijd, de
  seconden, "· 2×" en de ∑-rij;
- **B. marge:** zes referentiewaarden van scipy, en de tooltip;
- **C. onzeker:** 2 tikken wel; 1 tik in 120 s niet, want hij valt helemaal
  in Rustig; 17 tikken niet;
- **D. koppeling:** de cellen per rij, ook over een uurgrens heen; elke gemeten
  cel heeft een `data-cel`; een onzekere cel is lichter; de tooltip staat in
  seconden;
- **E.** een ander segment en een verborgen sessie tellen niet mee.

Tegen de oude telrapport faalt de test, zoals bedoeld. Daarnaast is het in
Chromium nagelopen, met 15 nagebootste tellingen:
- een klik op een rij zet een rand om zijn cel;
- een klik op een cel laat 3 van de 15 rijen staan en verbergt de ∑-rij;
- nog een keer klikken zet alles terug;
- geen JS-fouten.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `poissonCdf`, `poissonMarge`, `pmhMarge`; tabel en cellen; `weekprofielKlik`; CSS |
| `traffic_counter_help.html` | tabel en betrouwbaarheid in *Drukte & weekprofiel* |
| `index.html` | versie v3.7 |
| `_archief/overpass_rig/functest_segmenttabel.js` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py        ALLES OK — 3 verwachte bestanden gewijzigd; 14 groepen gedeelde blokken OK; 14 publieke pagina's OK
functests          alle 15 groen (nieuw: functest_segmenttabel.js 23/23)
weekprofiel        in Chromium: rij- en celklik, geen JS-fouten
laadtest.py        47/47
statictest.py      24/24
opruimtest.py      52/52
hersteltest.py     133/133
gpkgtest.py        80/80
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
