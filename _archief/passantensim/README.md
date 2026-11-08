# Passantensimulatie (okt 2026)

Kalibratie van *Passanten per uur* (winkelstraat) met een simulatie waarin de
waarheid bekend is. Gaat niet online (`_archief` heeft `export-ignore`).

- `sim_kern.js`: de kern, `SIMKERN`. Puur JavaScript, geen DOM, geen Node.
  Eén straat, voetgangers als stuksgewijs rechte lijnen in (t, x), één lopende
  teller die de straat één keer afloopt, Pocket nagedaan (routepunten,
  `_bezocht`, tik op het vak van het dichtstbijzijnde routepunt). Uitvoer: de
  waarheid per vak en de CSV-rijen voor `PASSANTEN.sessie`. Herhaalbaar via
  het zaadje. Later te plakken in een HTML-pagina met een canvas.
- `batch.js`: Monte Carlo. Rekent met het échte blok `PASSANTEN` en de échte
  Garwood-marge uit `passanten.html`, ongewijzigd, via `vm`.

- `simulatieronde.html` in de suite-root (sinds v3.46 op telonline.org; tot
  dan `simkijker.html` hier, nov 2026): één ronde als tijd-wegdiagram, tot op de
  voetganger (Jay: "Iets waardoor ik vertrouwen krijg in de resultaten").
  Elke lijn een voetganger, elke ontmoeting gezien of gemist (met kans en
  worp), elke tik naar het vak waar hij telt; per vak de rekensom van
  Passanten naast de waarheid, en F over de zaadjes 1 tot 400 ter
  vergelijking. Trefkans 95% voor iedereen. Schakelaar drukte (Jay: "veel of
  weinig passanten"): weinig 300–600, gemengd 300–1.600, veel 1.200–1.600
  per uur in het midden. Onderaan 1.000 rondes (Jay: "doe eens een stuk of 1000
  simulaties, en maak een scatter plot van werkelijk vs geteld"): werkelijk
  tegen geteld, per ronde en per vak; klik op een stip en die ronde (en dat
  vak) gaat open. Rekent bij elke drukte opnieuw, in een paar seconden.
  Schakelaar "geteld als" (Jay: "passages per meter per uur [...] kun je die
  ook laten zien in de grafieken"): Passanten per uur, of p/m·u zoals
  telrapport (n_tellingen ÷ lengte ÷ duur_sec, met de terugval van v3.17);
  dan is de lijn werkelijk = k × p/m·u, k in meters. Ook in de vakkentabel
  en de rekensom.
  Drukte "een week" (standaard; Jay: "een mix van druk en rustig - zeg maar
  50-3000 passanten. Met uiteraard de meeste aandacht voor de aantallen die op
  een normale week zich voordoen"): lognormaal tussen 50 en 3.000, mediaan
  600 (het meetkundig gemiddelde van Jay's zes winkelstraattellingen),
  spreiding 0,75 in ln; de teller niet langzamer dan 0,8 m/s. In sim_kern:
  `qMediaan`, `qSpreiding`, `tempoMin` (standaard uit; dezelfde zaadjes geven
  zonder die drie dezelfde rondes). Onder de wolken een tabel per
  drukteklasse: F en k per klasse, en hoe goed één factor overal past.
  Het aantal rondes is in te stellen: 200 tot 10.000 (Jay: "Kun je het aantal
  van 1000 simulaties instelbaar maken?"); 10.000 rekent in zo'n 15 s. Eén zelfstandige pagina (ook als
  artifact), met een kopie van `sim_kern.js` en van het blok `PASSANTEN`:
  `node _archief/passantensim/kijkercheck.js [--bijwerken]` controleert of die
  kopieën nog gelijk zijn (en vervangt ze). `run()` geeft daarvoor ook de
  voetgangers, alle ontmoetingen (met kans en worp) en de gps-punten terug;
  dat trekt geen extra toevalsgetallen, dus dezelfde zaadjes geven dezelfde
  rondes als voorheen.

Draaien vanuit de repo-root (geen npm nodig):

    node _archief/passantensim/batch.js         # 1000 rondes per regel, ~4 min
    node _archief/passantensim/batch.js 200     # snel

De uitvoer is Markdown op stdout. Commit geen uitvoer.

Waarheid: de doorsnedestroom in het midden van elk vak, beide richtingen samen
(Jay). De parameters staan in `SIMKERN.STANDAARD`, met uitleg per regel. De
trefkans (overkant, groepjes, drukte) is een aanname: die komt alleen uit een
ijking met Static.
