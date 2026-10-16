# Overdracht v3.11 — kwaliteitsteken zonder eigen regel

Jay, na v3.10: "We hebben in telrapport.html al erg weinig verticale ruimte in de
kolom, dus het kwaliteitslinkje zou geen nieuwe regel in mogen nemen."

## 1. Wat er veranderd is

In v3.10 had het kwaliteitsrapport een eigen regel in elke sessierij (*✓
kwaliteit* / *⚠ n aandachtspunten*). Elke rij werd daardoor 15 px hoger: 70 px
in plaats van 55 px in de test.

Nu staat er een teken **rechts op de eerste regel** van de rij, naast de datum en
de teller:
- *✓*, in het groen, als er geen aandachtspunten zijn;
- *⚠ n*, in het oranje, met het aantal aandachtspunten.

De tooltip zegt wat het is, bijvoorbeeld *kwaliteit: 1 aandachtspunt — klik voor
het rapport*. Een klik opent het paneel, net als in v3.10. De telling blijft
daarbij aan.

Het teken krimpt niet (`flex-shrink: 0`) en schuift naar rechts
(`margin-left: auto`), tegen de kolom met het aantal aan. De regels *geclusterd*
en de sessie-id blijven zoals ze waren.

Verder is er niets veranderd: het rapport, de controles en het paneel zijn
gelijk aan v3.10.

## 2. Tests

`logicatest.py` heeft twee tests meer (27):
- het teken staat op de eerste regel, met de uitleg in de tooltip;
- de rij is met het teken even hoog als zonder (55 px in de test).

Tegen v3.10 falen beide: het teken stond niet op de eerste regel, en de rij was
70 px tegen 55 px zonder. De bestaande
B-tests zoeken nu naar *✓* en *⚠ 1*.

Daarnaast bekeken in Chromium: de sessielijst met drie parkeertellingen (*⚠ 1*,
*⚠ 1*, *✓*), op gelijke hoogte met de regels zonder teken.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `makeSessionRow`: het teken in `.session-line1`; CSS van `.session-kwaliteit` |
| `traffic_counter_help.html` | *Kwaliteit per telling*: waar het teken staat |
| `index.html` | versie v3.11 |
| `_archief/overpass_rig/logicatest.py` | plek en hoogte van het teken |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

```
VALIDATIE
```
