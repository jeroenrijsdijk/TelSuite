# Overdracht v3.58 — Passanten: dagkrommen met gewone uren

Jay: "Kun je de code nog zo aanpassen dat de .csv normale uren heeft, (dus 1 is
01:00 tot 01:59)? Dus de code aanpassen en de csv omschrijven. De UurCorr in de
header mag Uur worden."

## 1. Code

- **`leesDagkrommen`**: het uur is het klokuur, 0 tot 23. 9 is 9:00–9:59.
- **Uur 24** geeft nu een melding: "is geen 0 tot 23 (9 = 9:00–9:59)". In v3.57
  liep het van 1 tot 24, met 24 = 0:00 van de volgende dag.
- **De kopregel** wordt niet gelezen, dus `Uur` en `UurCorr` mogen allebei.
- **Al geladen krommen** (in de browser bewaard) blijven goed: daar staan de
  uren al als klokuur in.
- De tooltip van de knop en de handleiding (rij Klik op een stuk) volgen.

## 2. De CSV van Jay

- Omgeschreven naar de kop `Uur;1;2;3;4;5;6;7` en de rijen 0 tot en met 23.
- Rij 1 tot en met 23 zijn ongewijzigd.
- De oude rij 24 van dag *d* (0:00 van dag *d* + 1) is rij 0 van dag *d* + 1
  geworden. In zijn cijfers alleen 0,26 van vrijdagnacht, nu zaterdag 0:00.
- De dagtotalen zijn gelijk gebleven.
- **De CSV staat niet in de repo.** Hij is aan Jay gegeven, buiten de repo.

## 3. Tests

**`passantentest.py`: 114.**

- De zelfgemaakte kromme heeft nu de kop `Uur;1;…;7` en de rijen 0–23.
- Rij 0 van maandag wordt maandag 0:00.
- Een uur 24 wordt geweigerd.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `leesDagkrommen` (uur 0–23), het commentaar en de tooltip van de knop |
| `traffic_counter_help.html` | het formaat van de CSV |
| `index.html` | versie v3.58 |
| `_archief/overpass_rig/passantentest.py` | zie §3 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
passantentest.py      114/114
volledige ronde lokaal: zie de PR
```
