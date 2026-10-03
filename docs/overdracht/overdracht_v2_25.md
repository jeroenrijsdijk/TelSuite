# TrafficCounterSuite v2.25 — Overdracht

Deze release werkt **`zip_format_reference.html`** bij met twee nieuwe secties, zodat de codering- en naamconventies op één canonieke plek staan. Alleen de reference wijzigt; alle andere bestanden zijn byte-identiek aan v2.24.

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `zip_format_reference.html` | ✦ bijgewerkt | Twee secties toegevoegd vóór de Overview-tabel: **"Filename markers & survey-type coding"** en **"Reconstructed ZIPs"**. |

## Wat is toegevoegd

**Filename markers & survey-type coding.** Vastgelegd hoe de telmode van een sessie bepaald wordt, in volgorde van gezag: de naam-marker → `app_type` in `_sessie.csv` → (bij ontbrekende/foute modus) de type-woordenschat van de tikken. Twee tabellen:
- markers → app_type/modus/types: `_car`→auto/parkeren, `_fts`→fiets/parkeren, `_cap`→capaciteit, `_trn`→transect, `_pkt`→pocket.
- type-woordenschat → modus: fiets/brommer/breed/wrak→fiets-parkeren; car/truck/moto/bike/ped→transect; stilstaand/tegemoet/meelopend→winkelstraat; bezet/leeg/vrij/goed/fout/spec→parkeren; vrije tekst→simpel.
- Bijzondere gevallen: één fiets-woord markeert de hele sessie als fiets; `_pkt` met uitsluitend `ped` onder `parkeren`→`simpel`; al-`simpel` blijft `simpel`; naam wint van inhoud.

**Reconstructed ZIPs.** Wat `parkeer_reconstructie.html` toevoegt/wijzigt: `_sessie.csv` krijgt `modus` + `reconstructie`-versiestempel; `_netwerk.csv` wordt gesnapte geometrie met segment-kolommen (+`_netwerk_origineel.csv`); `_straten.csv` wordt herbouwd voor auto/parkeren (+`_straten_origineel.csv`, v2.23+); wandel-recon voegt `_segmentsamenvatting.csv` toe (v2.20+); `_telregels.csv` krijgt marker/zijde/richting/recon_status. Plus de legacy-noot over de oude `parkeren`-fallback en `relabel_modus.py`.

## Validatie

- **HTML-tagbalans** schoon.
- **Byte-identiteit:** sinds v2.24 wijzigde uitsluitend `zip_format_reference.html`.
- Beide nieuwe secties gerenderd in de bestaande opmaak (summary-section + tabellen).

## Bijbehorend (buiten de suite)

- `relabel_modus.py` — omlabel-script voor bestaande archieven (naam-markers + woordenschat, droogloop-standaard, niet-destructief).
- QGIS: `recon_qgis_loader.py` (tikken per telptype), en de plakkerigheid-proeftuin (`plakkerigheid_winkelstraat_prototype.html`).

## Backlog (ongewijzigd meegenomen)

- Parkeren uit pocket halen (eigen modus/tool).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport porten.
- %bezet per dag×uur-cel (tik-met-tijd-én-categorie → schema/KNIME).
- QGIS-loader: optionele join op `_straten.csv`/`_bezocht.csv` + GPS-sporen.
