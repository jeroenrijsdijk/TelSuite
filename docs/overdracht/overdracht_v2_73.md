# Overdracht v2.73 — Static in suitevorm, telrapport leest Static-ZIP's

Drie punten uit de Static-audit van v2.72, op verzoek van Jay:

- **punt 1**: telrapport leest de ZIP van Static;
- **punt 3**: het exportformaat van Static trekken we recht;
- **punt 4**: het losse branding-blok gaat weg.

Punt 2, Engelstalig, blijft op de backlog.

---

## 1. Samenvatting

| | vóór | nu |
|---|---|---|
| ZIP van Static | `traffic_count_<tijd>.zip` met één leesbare CSV | `<sid>.zip`: `_sessie`, `_telregels`, (`_onderbrekingen`), `_overzicht` |
| sessie-id | geen (telrapport verzon `ss_<starttijd>`) | `<jjjjmmdd>_<uummss>_<xxx>_sta`, vast vanaf Start, overleeft herstel |
| tijd per tik | `HH:MM:SS` | `2026-09-23T14:32:11`, zelfde vorm als pocket |
| telrapport + Static-ZIP | "Geen sessie.csv gevonden", eerst uitpakken | leest de nieuwe ZIP, de oude ZIP en de losse CSV |
| verzameling | stilstaand-tellingen vielen eruit (geen origineel) | gaan mee, ook uit een losse CSV |
| reconstructor + Static | probeerde een profiel te kiezen | nette melding: vaste plek, niets te reconstrueren |
| onderaan Static | los blok "Built with AI by Claude - Anthropic" + losse `</div>` | weg, met de bijbehorende CSS |

## 2. De nieuwe ZIP van Static

```
20260923_143205_kqd_sta.zip
├── 20260923_143205_kqd_sta_sessie.csv
├── 20260923_143205_kqd_sta_telregels.csv
├── 20260923_143205_kqd_sta_onderbrekingen.csv   (alleen na doortellen)
└── 20260923_143205_kqd_sta_overzicht.csv        (het leesbare formaat van vóór v2.73)
```

**`_sessie.csv`** heeft eerst de tien kolommen van pocket, met `app_type`,
`modus` en `type` op `standstill`, `standstill` en `verkeer`. Daarna volgen
`lat;lon;nauwkeurigheid;straat;plaats;notities;actieve_duur_s;uurfactor`.

- `actieve_duur_s` en `uurfactor` tellen zonder onderbrekingen; eind − start
  telt ze wel mee.
- De notities worden ontdaan van `;` en regeleinden.

**`_telregels.csv`** heeft de kop die al beschreven stond voor het oude
transect-formaat: `sessie_id;nr;tijdstip;type;richting;lat;lon;nauwkeurigheid`.

- `tijdstip` bevat nu datum en tijd.
- `richting` is `a` of `b`; de labels staan in `_sessie`.
- De telpositie staat op elke regel, zodat het bestand op zichzelf leesbaar is.
- Tikken uit een noodopslag van v2.72 hebben alleen een klokttijd. Die krijgen
  de startdatum, en een dag erbij als de klok terugspringt (een telling over
  middernacht).

**`_onderbrekingen.csv`**: `sessie_id;nr;van;tot;duur_s`, één regel per gat.

**`_overzicht.csv`** is byte voor byte de tekst die Static voorheen exporteerde.
Alle vier de bestanden komen uit dezelfde stand op hetzelfde moment. De test
controleert dat ze onderling kloppen: totalen per type en richting, de duur en
de factor.

**Waarom het overzicht blijft.** Excel-gebruik, bestaande KNIME-lezers, en
telrapport, dat het leest. Zo is er één weergavecode voor oud en nieuw.

`zip_format_reference.html` beschrijft het formaat; `test_zipref.py` controleert
dat de referentie klopt met de code. In de tabel met bestandsmerken staat nu
ook `_sta`.

## 3. Telrapport

- `loadZip` zoekt eerst een CSV met de banner `Traffic Count Export`. Vindt hij
  die, dan is het Static:
  - de `sessie_id` komt uit `_sessie.csv` (nieuw formaat);
  - zonder `_sessie.csv` (ZIP van v2.18–v2.72) synthetiseert telrapport er een
    uit de starttijd, zoals vroeger.
- `loadStandStillCsv` en de nieuwe ZIP-route gebruiken allebei
  `toonStandStill()`, het oude laadpad maar dan zonder het bestand zelf te
  lezen.
- **Verzamelingen.** Een stilstaand-telling bewaart nu haar origineel. Komt ze
  uit een losse CSV, dan pakt telrapport die CSV in een ZIP. Daardoor gaat ze
  mee in een verzameling en laadt ze daaruit terug. Voorheen viel ze er stil
  uit.

## 4. Reconstructor

Bij `app_type` = `standstill` volgt een gebruikersfout:

> Dit is een stilstaand-telling (Static): één vaste plek, geen route. Er valt
> niets te reconstrueren — open hem direct in telrapport.

De oude Static-ZIP's hebben geen `_telregels.csv` en gaven al de melding
"ZIP mist telregels".

## 5. KNIME

Dit is een schemawijziging voor Static en staat daarom in de stand van zaken,
§4 punt 7. Wie Static via het overzicht inleest, kan dat blijven doen. De nieuwe
bestanden maken Static een gewone sessie, met datum per tik. Gebruik voor
uurintensiteiten `actieve_duur_s` of `uurfactor`.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter.html` | sessie-id, datum per tik, ZIP in suitevorm, branding-restant + CSS weg |
| `telrapport.html` | Static-ZIP's herkennen, `toonStandStill()`, origineel bewaren voor verzamelingen |
| `telreconstructie.html` | weigering van stilstaand-tellingen |
| `zip_format_reference.html` | Static-sectie herschreven, `_sta` in de merkentabel |
| `index.html` | versie v2.73 |
| `_archief/overpass_rig/statictest.py` | nieuw, 24 tests |
| `_archief/overpass_rig/hersteltest.py` | leest het overzicht uit de nieuwe ZIP |
| `_archief/overpass_rig/functest_coordinaten.js` | de GPS-afscherming van stilstaand zit nu in `toonStandStill()`; de test kijkt daar |
| `_archief/overpass_rig/valideer.py` | verdwenen tagbalans-ruis telt als verbetering, niet als afwijking |
| `README.md` (rig en root), `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py        ALLES OK (tagbalans traffic_counter: de bekende ruis is weg)
statictest.py      24/24 — export, drie vormen in telrapport, verzameling heen en terug, reconstructor
hersteltest.py     133/133
laadtest.py        40/40
functests          alle 13 groen (functest_coordinaten volgt de verhuizing naar toonStandStill)
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
