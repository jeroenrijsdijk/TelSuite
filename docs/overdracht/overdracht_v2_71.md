# Overdracht v2.71 — noodopslag getoetst, en pocket vergat de GPS-route

Jays vraag: blijft de data van een telling bewaard bij een onderbreking of als
de browser sluit? Dat is voor alle vijf veld-apps getoetst met een nieuwe test,
onder de zwaarste omstandigheid: een harde crash. Daarbij kwam een fout in
pocket boven die al veel langer bestond, en die is gerepareerd.

---

## 1. Uitkomst in het kort

| app | na crash | ZIP na herstel |
|---|---|---|
| parkeertelling | alle tikken + GPS-spoor terug, herstelmelding | gelijk aan zonder onderbreking |
| fietsparkeren | idem | gelijk |
| capaciteitstelling | idem (straatmodule getest; terreinmodule zit in dezelfde opslag) | gelijk |
| pocket, alle 4 modi | alle tikken + GPS-route terug, herstelmelding (sinds v2.69) | gelijk, behalve `_netwerk.csv` en `_snap_trace.csv` (bewust niet bewaard) |
| **Static** | **niets** — de app slaat niets op | — |

"Gelijk" betekent: elk bestand, regel voor regel. Alleen het tijdstip van
exporteren telt niet mee, want dat verschilt per keer: `eind_tijd` in
`_sessie.csv` en de tijd in de kop van de GPX.

## 2. Gevonden en gerepareerd: pocket bewaarde geen route zonder wegennet

**Wat er gebeurde.** Bij elke GPS-fix bepaalt pocket eerst op welke weg je
loopt. Is er nog geen wegennet, dan schrijft hij een regel `no_network` in de
snap-trace. Bij die ene aanroep van `traceWrite()` ontbrak één argument. De
lijst met alternatieven kwam daardoor als `undefined` binnen, en `alts.map()`
gaf een fout. Die fout brak de hele GPS-afhandeling af, en dat gebeurde vóór
`routeLog.push()`. Zolang er geen wegennet was, werd er dus **geen enkel
routepunt** bewaard.

**Wanneer dat speelde:**

- aan het begin van elke sessie, tot het eerste Overpass-antwoord binnen was
  (seconden). De eerste meters ontbreken in `_gps.csv`;
- **de hele sessie**, als Overpass niet bereikbaar was: geen mobiel internet,
  of beide endpoints plat. Dan was `_gps.csv` leeg, er was geen route op de
  kaart en de reconstructor had niets om mee te werken.

De tikken zelf werden wel bewaard, alleen zonder route eromheen.

**Reparatie.** Het ontbrekende argument is toegevoegd. Daarnaast maakt
`traceWrite()` een ontbrekende lijst voortaan leeg in plaats van te crashen.
Een fout in de diagnose mag nooit veldgegevens kosten.

Alle andere aanroepen van `traceWrite()` zijn nageteld; die hebben het juiste
aantal argumenten.

**Gevolg voor bestaande data.** Pocket-sessies die zonder bereikbaar Overpass
zijn geteld, hebben een lege of korte `_gps.csv`. Dat is niet te herstellen,
want de punten zijn nooit opgeslagen.

## 3. Wat de test precies doet (`hersteltest.py`)

Per app en per pocket-modus:

1. telling starten in Chromium met nagebootste, bewegende GPS en 12 tikken.
   Overpass is geblokkeerd, dus er is geen wegennet;
2. direct na de laatste tik de opslag bevriezen. Dat is een harde crash: geen
   `pagehide`, geen `visibilitychange`, niets;
3. de ZIP maken zoals de app dat zonder onderbreking doet (referentie);
4. een nieuwe browser met alleen die bevroren opslag: laden, controleren dat de
   herstelmelding er is, en de ZIP maken uit de herstelde telling;
5. beide ZIP's bestand voor bestand en regel voor regel vergelijken.

Op v2.70 gedraaid geeft hij 8 fouten: vier keer "0 GPS-punten" en vier keer de
JS-fout. Op v2.71 zijn alle 81 tests groen, met vijf meldingen `BEKEND`:
viermaal de snap-trace in pocket en eenmaal Static.

## 4. Gemeten grenzen

- **Opslagruimte:** ongeveer 5,1 miljoen tekens voor heel telonline.org.
- **Per tik met GPS-punt:** ~0,55 kB in parkeertelling, ~0,27 kB in pocket.
  Een lange sessie van 1500 tikken is dus ~1 MB, ruim binnen de grens.
- **Onbekend:** de omvang van het opgeslagen wegennet in de parkeer-apps. Dat
  was in de test geblokkeerd.
- **Schrijftijd:** minder dan 1 ms per tik bij 100 tikken, lineair oplopend.

## 5. Wat de test niet dekt, en wat Jay moet weten

- **Na een harde crash** zijn de GPS-punten na de laatste tik weg. Bij
  scherm-uit of app-wissel worden ze wel bewaard.
- **Herstel betekent downloaden, niet doortellen.** Een per ongeluk herladen
  pagina splitst een straat in twee ZIP's.
- **Volle opslag wordt niet gemeld.** Vanaf dat moment is er stil geen
  noodkopie meer.
- **Safari:**
  - in een privévenster verdwijnt de opslag zodra de tab sluit;
  - Safari kan websitegegevens wissen van een site die je ruim een week niet
    hebt bezocht. Download een herstelde telling dus snel.
- **Nieuwe telling starten** terwijl de herstelmelding er staat, wist de oude
  zonder te vragen (backlog sinds v2.70).

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `pocket_count.html` | één argument in de `no_network`-aanroep; vangnet in `traceWrite()` |
| `index.html` | versie v2.71 |
| `_archief/overpass_rig/hersteltest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md` (rig), `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py                       ALLES OK — index.html en pocket_count.html gewijzigd
hersteltest.py                    81/81 (+5 BEKEND); op v2.70: 8 FOUT
laadtest.py                       40/40
functests                         alle 13 groen
check_encoding.py                 alles geldige UTF-8
```

## 8. Backlog, nieuw

- Static noodopslag (grootste gat).
- Waarschuwing bij volle opslag, in alle vier de apps met noodopslag.
- Doortellen na herstel.
