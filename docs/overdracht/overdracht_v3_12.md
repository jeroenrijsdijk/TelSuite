# Overdracht v3.12 — "geclusterd" alleen als er iets buiten valt

Jay: "Nogmaals een taak om ruimte te winnen in de kolom: 44/44 geclusterd hoef je
niet weer te geven, doe dat alleen als niet alle punten in een cluster zitten.
Scheelt ook weer ruimte."

## 1. Wat er veranderd is

In de sessielijst van telrapport stond onder elke telling *✓ 44/44 geclusterd*
(sinds v2.42). Die regel staat er nu alleen nog als er tikken buiten een cluster
vallen: *⚠ 41/44 geclusterd · 3 buiten*, in het oranje, met de bekende tooltip.
Zitten alle tikken in een cluster, dan is er geen regel. Een rij is dan een regel
lager: 42 px in plaats van 55 px in de test.

**Bijwerking.** Bij een capaciteitstelling kan er ook een melding staan dat
terreinen geen geometrie hebben. Tot nu toe overschreef de regel *✓ n/n
geclusterd* die melding. Nu is hij zichtbaar als alle tikken geclusterd zijn.
Vallen er tikken buiten een cluster, dan gaat de melding over de clustering voor,
zoals voorheen.

De handleiding beschrijft de regel nu bij de sessielijst.

## 2. Tests

`logicatest.py` heeft drie tests meer (30):
- een telling waarvan alle tikken geclusterd zijn, heeft geen regel *geclusterd*;
- een telling met een tik buiten een cluster houdt *⚠ 4/5 geclusterd · 1 buiten*;
- de volledige rij is een regel lager (42 tegen 55 px).

Tegen v3.11 faalt de eerste, want daar staat *✓ 4/4 geclusterd*, en de derde,
want daar zijn beide rijen even hoog.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `makeSessionRow`: de regel alleen bij `dk.buiten > 0` |
| `traffic_counter_help.html` | sessielijst: wanneer de regel er staat |
| `index.html` | versie v3.12 |
| `_archief/overpass_rig/logicatest.py` | drie tests |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

```
valideer.py           ALLES OK — 3 verwachte bestanden gewijzigd; gedeelde blokken OK
logicatest.py         30/30
robuusttest.py        87/87
opruimtest.py         139/139
hersteltest.py        133/133
laadtest.py           47/47
statictest.py         24/24
gpkgtest.py           80/80
functests             alle 16 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
