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

Draaien vanuit de repo-root (geen npm nodig):

    node _archief/passantensim/batch.js         # 1000 rondes per regel, ~4 min
    node _archief/passantensim/batch.js 200     # snel

De uitvoer is Markdown op stdout. Commit geen uitvoer.

Waarheid: de doorsnedestroom in het midden van elk vak, beide richtingen samen
(Jay). De parameters staan in `SIMKERN.STANDAARD`, met uitleg per regel. De
trefkans (overkant, groepjes, drukte) is een aanname: die komt alleen uit een
ijking met Static.
