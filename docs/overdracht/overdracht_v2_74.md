# Overdracht v2.74 — release-kandidaat voor 3.0

Afgesproken route naar 3.0:

1. veldtest-draaiboek;
2. handleiding bijwerken;
3. versiestempel van de reconstructor aan de release koppelen;
4. Jay test op de iPhone;
5. wat daaruit komt repareren, en dat wordt 3.0.

Deze release doet stap 1 tot en met 3.

---

## 1. Veldtest-draaiboek: `VELDTEST_3.0.md`

Ongeveer 40 minuten buiten en 10 minuten achter de computer. Het draaiboek dekt
wat de automatische tests niet kunnen zien: Safari op een echte iPhone, echte
GPS, echt Overpass, en de cache.

| blok | wat |
|---|---|
| 0 | voorbereiding: openstaande tellingen eerst downloaden, websitegegevens wissen, v2.74 onderaan de voorpagina |
| 1 | Static: scherm blijft aan, herladen → Continue, Safari wegvegen → Continue, END → vier CSV's met `Interruptions;2` |
| 2 | pocket-parkeren via de eigen ingang: nooit het menu, beginschermicoon, wegvegen → Doortellen, Sluiten → verse telling, Terug → voorpagina |
| 3 | pocket in vliegtuigmodus: `_gps.csv` gevuld (de reparatie van v2.71) |
| 4 | parkeertelling: wegvegen, Start vraagt eerst, Doortellen, één ZIP; daarna een korte ronde fietsparkeren of capaciteit |
| 5 | telrapport (Static-ZIP nieuw en oud, verzameling heen en terug), reconstructor (log met highway-voorkeur en `v2.74`, fietspad, weigering van Static) |

Bij elke stap staat wat je hoort te zien. Een afwijking noteer je met tool,
stap, tijd en zo mogelijk een schermafbeelding.

## 2. Handleiding (`traffic_counter_help.html`)

**Inleiding**

- De indeling van de voorpagina: *Verkeer tellen*, *Parkeren tellen*, *Achter
  je bureau*.
- Een link naar Pocket-parkeren.

**Static** (Engelstalig, zoals de tool)

- *CSV export* heet nu *Export (ZIP)* en beschrijft de vier bestanden.
- Nieuwe sectie *Interruptions & continuing*: de herstelbalk, waarom
  onderbrekingen niet meetellen, en dat het scherm aan blijft.

**Parkeer-apps**

- *Crash recovery* noemt Doortellen en de bevestiging bij Start.

**Pocket**

- Keuzescherm: een kaart *Onderbroken telling*.
- Parkeren: een kaart *Eigen ingang op de voorpagina*, met de tip om hem als
  icoon op het beginscherm te zetten.

**Telrapport**

- Static laadt in drie vormen en gaat mee in verzamelingen.

**Algemeen** (nieuw)

- *Onderbreking, herstel & doortellen* voor alle vijf de tools, inclusief de
  grenzen: GPS na de laatste tik, privévenster, de week van Safari, 5 MB.
- *Telreconstructie in het kort*: wegtype-voorkeur, versiestempel, weigering
  van Static. De handleiding had nog geen sectie over de reconstructor.

**Bestanden**

- Nieuwe omschrijvingen voor Static en pocket (die stond nog als "één-knops").
- `planning_delete.php` staat erbij.
- De lijst met externe diensten klopt nu: CARTO, PDOK en Open-Meteo stonden
  er niet in.

Alle ankers in de inhoudsopgave verwijzen naar een bestaande sectie; dat is
nagekeken. Het blok "Built by me and Claude" onderaan de handleiding is wél
netjes omsloten en bedoeld. Dat is blijven staan.

## 3. Versiestempel van de reconstructor

**Het probleem.** Er stonden twee bevroren stempels die elkaar tegenspraken:
`_sessie.csv` schreef `reconstructie` = `v2.24`, en de log schreef
`reconstructie_versie;v2.18`.

**De oplossing.** Nu is er één constante, `RECON_VERSIE`, voor beide. Die geeft
**de release waarin de reconstructor voor het laatst veranderde**. Waarom niet
altijd het nieuwste releasenummer: dan zou `telreconstructie.html` elke release
veranderen, en zegt de byte-identiteitscontrole niets meer.

`valideer.py` bewaakt dit:

- is `telreconstructie.html` gewijzigd, dan moet `RECON_VERSIE` gelijk zijn aan
  `RELEASE`;
- anders mag de stempel niet hoger zijn dan `RELEASE`;
- er moet precies één declaratie zijn.

Telrapport kijkt alleen óf de kolom `reconstructie` gevuld is. De nieuwe waarde
verandert daar dus niets. Oudere recon-ZIP's houden `v2.24`. De ZIP-referentie
beschrijft beide.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter_help.html` | zie §2 |
| `telreconstructie.html` | `RECON_VERSIE`, gebruikt in `_sessie.csv` en de log |
| `zip_format_reference.html` | betekenis van de stempel `reconstructie` |
| `index.html` | versie v2.74 |
| `VELDTEST_3.0.md` | nieuw |
| `_archief/overpass_rig/valideer.py` | controle op de versiestempel, `RELEASE` |
| `_archief/overpass_rig/functest_hwvoorkeur.js` | +4 tests: één stempel, gebruikt in log en sessie, geen bevroren waarden meer |
| `README.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt; veldtest is Jays punt 0 in §4 |

## 5. Validatie

```
valideer.py        ALLES OK — 4 verwachte HTML-bestanden gewijzigd; RECON_VERSIE v2.74 (bijgewerkt in deze release)
laadtest.py        40/40
hersteltest.py     133/133
statictest.py      24/24
functests          alle 13 groen (functest_hwvoorkeur nu 22)
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
