# Overdracht v3.53 — Passanten: Wanneer tellen?

Jay: "Als ik al mijn winkelstraat tellingen in passanten.html laad, en ik klik
op een link, kun je dan doorrekenen wanneer er geteld moet worden op die
link?" Daarvoor: de tellingen zijn "om algemeen kennis en wijsheid te
verzamalen over de loopstromen". Op het voorstel (blokken van twee uur, per
straat of per stuk): "ik maak zelf een route op basis van de linkjes die ik
aanklik. Doe het gewoon op uurbasis".

## 0. De gedachte

- Een stuk heeft 168 vakjes (7 dagen × 24 uur), en per telling kom je er een
  paar minuten langs. Dat raster vul je nooit, en het hoeft niet: de dagcurve
  van het gebied geeft voor elk uur al een verwachting, op het niveau van dit
  stuk.
- Voor kennis over loopstromen telt dus niet "welk vakje is leeg", maar: **volgt
  dit stuk het ritme van het gebied?** Een stuk bij een halte of garage kan om
  vijf uur twee keer zo druk zijn als de curve zegt. Dat zie je alleen als je
  er om vijf uur bent geweest.
- Per dagtype (werkdag = ma–vr samen, zaterdag, zondag) en uur, zoals de
  dagcurve.

## 1. Wat je ziet

Onder het weekoverzicht van een stuk (klik op een stuk):

- **Een lijst van de drie uren die het meest opleveren**, met de reden, zoals:
  "werkdag 12:00–13:00: hier nog nooit geteld, in het gebied 21 tellingen;
  ≈ 9,4 tegemoetkomers per keer langs".
- **Een richtingadvies** als het stuk maar in één bekende richting gelopen is:
  "Alleen richting zuidwest gelopen. Loop hem ook richting noordoost". Richting
  A loopt zoals de lijn getekend is (`richtingVan`); `kompas` geeft een van de
  acht windstreken.
- **Een tabel** met een rij per dagtype en een vakje per uur (van het eerste
  tot het laatste uur waarop in het gebied geteld is):

  | vakje | betekenis |
  |---|---|
  | 1, 2, 3 (donker) | eerst tellen |
  | wit met rand | hier nog nooit geteld, in het gebied wel genoeg |
  | grijs, een getal | te weinig: het aantal tellingen |
  | 1,3 (lichtgroen) | volgt de curve: 1,3 keer wat de curve verwacht |
  | rood / blauw | hoger / lager: 1 ligt buiten de marge (95%) |
  | gearceerd | nergens genoeg geteld |

  Een vakje aanwijzen geeft de tellingen, minuten, tegemoetkomers, de
  verwachting, de marge en hoeveel tegemoetkomers je per keer langs mag
  verwachten.

## 2. De rekening (`dcPlan(key)`)

- **Verwacht**: Σ w · A[stuk|richting] · D[weekdag] · F[dagtype:uur] uit de
  schatting op alle stukken (`dcKern(null)`). Het niveau A is dat van dit stuk
  zelf, dus 1,0 = het ritme van het gebied.
- **Stand**:
  - **nooit**: 0 tellingen, en het gebied heeft daar genoeg (de regel van de
    dagcurve: `DC_MIN_TELLINGEN`, `DC_MIN_TIKKEN`);
  - **leeg**: 0 tellingen, en het gebied heeft daar te weinig;
  - **dun**: minder dan 2 tellingen of minder dan 10 tegemoetkomers. Met een
    verwachting telt die, niet wat geteld is: een stil uur is kennis, geen
    gebrek;
  - **gezien**: genoeg, maar niet te vergelijken (het stuk hangt niet samen
    met de rest, of het gebied heeft daar te weinig);
  - anders **volgt**, **hoger** of **lager**.
- **De marge** heeft twee delen, in het kwadraat opgeteld:
  1. die van de popup: Garwood op de tegemoetkomers, × `MARGE_BREED`
     (groepjes);
  2. de spreiding tussen tellingen: 1,96 · σ · √(Σ Eᵢ²) ÷ E, met Eᵢ wat per
     telling verwacht wordt. Gelijke tellingen geven σ ÷ √n.
- **σ (`dcSpreiding`)** komt uit de stippen van v3.52. Per stip is
  z = geteld ÷ verwacht (μ), en (z − 1)² is gemiddeld σ² + φ/μ, met
  φ = `MARGE_BREED`². Alleen vakjes met genoeg en minstens twee stippen, × n/(n − 1):
  de curve is op die stippen zelf geschat. Een keer per kern, gecachet.
- **Waarom die spreiding erin moet.** De eerste versie had hem niet. Op een
  gemaakte set zonder stuk met een eigen ritme stond werkdag 9 uur van het
  drukste stuk op "hoger" (2,0) en 13 uur op "lager" (0,5). Twee drukke of
  stille dagen lijken dan een eigen ritme. In de test (100 tellingen, elke
  telling × een lognormale dagfactor met σ 0,4):

  | | hoger of lager |
  |---|---|
  | zonder de spreiding in de marge | 72 van de 439 uren (16%) |
  | met de spreiding in de marge | 5 van de 439 (1%) |

  Op de gemaakte sets van 150 en 300 tellingen: 1–2%. σ gemeten: 0,40 in de
  test, waar 0,42 echt is; 0,54–0,61 op de sets, die met σ 0,6 lognormaal
  gemaakt zijn.
- **Per keer langs**: (Σ w · A ÷ passages) · F · gemiddelde D, het aantal
  tegemoetkomers dat je bij één keer langslopen mag verwachten.

## 3. De volgorde van het advies

1. **nooit**;
2. **dun**, de minste tellingen eerst;
3. **hoger of lager op maar 2 tellingen**: bevestigen;
4. **leeg**.

Binnen een groep gaat de kleinste onzekerheid van de vergelijking met de curve
eerst: φ/μ + σ²·(1 + 1/n), met μ per keer langs en n de tellingen in het gebied
op dat uur.

De eerste versie zette het drukste uur eerst. Dan kwam zondag 9 uur (3
tellingen in het gebied) boven werkdag 12 uur (21 tellingen), terwijl een
vergelijking met een curve uit 3 tellingen weinig zegt. Bij een spreiding van
±60% doet de drukte boven een paar tegemoetkomers per keer er nauwelijks toe;
hoe goed het gebied het uur kent wel. Zonder spreiding (σ = 0) beslist de
drukte weer, en dat staat ook in de test.

## 4. Code

- **`dcKern(filter)`**: het deel van `dagcurveVan` zonder stippen en marges:
  - de waarnemingen en de schatting;
  - de aantallen per vakje en per werkdag;
  - de schaal (`dagen`, `refK`, `basis`);
  - `van` en `tot`.

  `dagcurveVan` = kern + stippen + trekkingen. **Byte-gelijk:** `DAGCURVE` op 300
  tellingen is precies die van v3.52. `genoeg` is nu `dcGenoeg`.
- **`dcKernAlle()`**: `dcKern(null)` in `DCKERN`. `herbereken` leegt hem.
  - De eerste klik kost 50–85 ms op 150–300 tellingen.
  - Daarna 4–11 ms per stuk.
- **`dcSpreiding(kern)`**, **`dcPlan(key)`**: in het blok Dagcurve, dus ook in de
  rekentest.
- **Weergave**: `tekenPlan` (vanuit `openWeek`), `planUur`, `planWaarom`,
  `planTitel`, `richtingAdvies`, `kompas`, `#week-plan` en CSS `#plan-tabel`.
- Geen schemawijziging: niets in de CSV's.

## 5. Handleiding

In de rij *Klik op een stuk* van Passanten: *Wanneer tellen?* (sinds v3.53).
Wat de vakjes betekenen, de marge met de spreiding tussen dagen, de volgorde
van het advies en het richtingadvies.

## 6. Tests

- **`functest_dagcurve.js`: 63 (was 53).** Nieuw deel "v3.53":
  - zonder ruis: spreiding 0 en elke verhouding precies 1;
  - aantallen per uur zoals in het plan;
  - nooit en leeg;
  - de volgorde van het advies;
  - alleen toeval: σ < 0,1 en hooguit 5% hoger of lager;
  - dagfactoren: σ binnen 30%, hooguit 5% hoger of lager; zonder de spreiding
    meer dan 8% en meer dan twee keer zoveel;
  - een stuk met een eigen ritme (stuk 7, werkdag 16–17 uur × 3) staat op
    hoger;
  - met spreiding gaat het uur dat het gebied goed kent voor het drukkere uur
    dat het nauwelijks kent;
  - per keer langs.

  De rekentest knipt ook `poissonCdf`, `poissonMarge` en `MARGE_BREED` uit de
  pagina; `zet` leegt `DCKERN`.
- **`passantentest.py`: 100 (was 96).**
  - De Voorstraat: een rij per dagtype en een vakje per uur; zaterdag 13 uur
    heeft 2 tellingen (ook in de tooltip), werkdag 11 uur 1 telling (te
    weinig); het advies als lijst en gemarkeerd in de tabel; geen
    richtingadvies.
  - De Kerkstraat (één richting): de gelopen windstreek klopt met de geometrie,
    en het advies noemt de tegenovergestelde.

## 7. Open

- **Nog niet op echte tellingen gezien.** De volgorde van het advies, σ en het
  aantal stukken op hoger of lager zijn alleen op gemaakte sets nagerekend.
- **Niet gebouwd, genoemd:** het andersom, als kaart: kies dagtype en uur, en
  zie welke stukken het nodig hebben. Jay kiest zijn route zelf per stuk.

## 8. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `dcKern`, `dcGenoeg`, `dcKernAlle`, `dcSpreiding`, `dcPlan`; `#week-plan` met `tekenPlan`, `richtingAdvies`, `kompas`; CSS; `herbereken` leegt `DCKERN` |
| `traffic_counter_help.html` | *Wanneer tellen?* in de rij Klik op een stuk |
| `index.html` | versie v3.53 |
| `_archief/overpass_rig/functest_dagcurve.js`, `passantentest.py` | zie §6 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 9. Validatie

```
valideer.py              ALLES OK — de 3 verwachte bestanden
functest_dagcurve.js     63/63
passantentest.py         100/100
300 tellingen            DAGCURVE byte-gelijk aan v3.52
volledige ronde lokaal: zie de PR
```
