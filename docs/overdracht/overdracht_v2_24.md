# TrafficCounterSuite v2.24 — Overdracht

Deze release repareert een **verkeerde modus-codering** in `parkeer_reconstructie.html`. Aanleiding: in QGIS bleken er `type=ped` (voetgangers) tikken in de laag `tikken — parkeren` te zitten. Dat zijn loop-tellingen, geen parkeerresultaten — ze waren onterecht als `modus=parkeren` weggeschreven.

**Oorzaak (twee fallbacks van de parkeren-erfenis van de reconstructor):**
1. `kiesProfiel()` viel terug op het `pocket-parkeren`-profiel zodra geen enkel profiel de sessie herkende (bv. een oudere pocket-telling zonder modus-veld).
2. `bouwZipBlob()` schreef `r.modus || 'parkeren'` — een lege modus werd hard `'parkeren'`.

Samen stempelden ze elke telling met een lege modus als parkeren, ook voetgangers-tellingen (`type=ped`).

Alleen `parkeer_reconstructie.html` is gewijzigd; alle andere bestanden zijn byte-identiek aan v2.23.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `parkeer_reconstructie.html` | ✦ bijgewerkt | Modus wordt nu correct afgeleid: (A) elk profiel draagt zijn eigen `modus` (`wandelProfiel` geeft `opts.modus` mee; `pocket-parkeren`/`auto` krijgen `modus:'parkeren'`); (B) nieuwe `profielUitTypes()` leidt bij een lege/onbekende modus het profiel af uit de **type-woordenschat**; (C) `kiesProfiel()` gebruikt die inferentie i.p.v. blind `pocket-parkeren`, met **`simpel`** als neutrale terugval; (D) `bouwZipBlob()` schrijft `(S.profiel.modus) || r.modus` weg i.p.v. `r.modus || 'parkeren'`, en stempelt de reconstructie-versie nu als `v2.24`. Versielabel in de header → `v2.24`. |

**Schema:** geen kolomwijziging. Alleen de *waarde* in de bestaande `modus`-kolom wordt nu correct gevuld. Geen KNIME-impact op de structuur; wel klopt de modus voortaan.

### Woordenschat → modus
| Types | modus |
|---|---|
| `car` / `truck` / `moto` / `bike` / `ped` | transect |
| `stilstaand` / `tegemoet` / `meelopend` | winkelstraat |
| `bezet` / `leeg` / `vrij` / `goed` / `fout` / `spec` | parkeren |
| vrije tekst (objecten) | simpel |

---

## Validatie

- **`node --check`** schoon; **HTML-tagbalans** schoon.
- **Byte-identiteit:** sinds v2.23 wijzigde uitsluitend `parkeer_reconstructie.html`.
- **Functietest (Node-sandbox):** `profielUitTypes()` levert `transect` voor ped/car/bike, `winkelstraat` voor stilstaand/tegemoet, `pocket-parkeren` voor bezet/leeg én goed/fout/leeg/spec, en `null` (→ `simpel`-terugval) voor vrije tekst. De herken-lus draait eerst, dus een sessie mét geldige modus behoudt die; alleen lege/onbekende modi worden uit de inhoud afgeleid.

---

## Effect

- **Vanaf nu** krijgt elke reconstructie de juiste modus in `_sessie.csv` — een voetgangers-telling wordt `transect`, niet `parkeren`.
- Een echte parkeertelling (`app_type=auto`, of `modus=parkeren`) blijft ongewijzigd `parkeren`.
- **Bestaande** al-verkeerd-gelabelde ZIP's blijven fout tot ze opnieuw gereconstrueerd of omgelabeld worden — zie het losse `relabel_modus.py` (leidt de modus uit de woordenschat af en herschrijft `_sessie.csv`, niet-destructief naar een uitvoermap).

## Backlog (ongewijzigd meegenomen)

- Parkeren uit pocket halen (eigen modus/tool).
- %bezet per dag×uur-cel (vraagt tik-met-tijd-én-categorie → schema/KNIME).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- QGIS: optionele join op `_straten.csv`/`_bezocht.csv` (bezetting per weglijn) + GPS-sporen.
