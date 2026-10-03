# Overdracht v2.57 — TL;DR bovenaan over.html

Eén bestand, één blok. `over.html`, +1.156 bytes. Geen nieuwe CSS, geen nieuwe
klassen (26 voor en na).

## Plaats

Tussen het "Voor wie is dit?"-blok en de kop **De werkwijze — drie stappen**.
De haastige lezer krijgt zo het hele verhaal vóór de lange versie; wie doorleest
verliest niets, want de drie stappen eronder zeggen hetzelfde uitgebreider.

## Inhoud

Een tweede `info-block` met de kopregel *In het kort — tellen → ZIP →
reconstrueren → kaart*, drie opsommingsregels (tellen, nabewerken, bekijken) en
een afsluitende regel over geen installatie, geen account, geen upload, plus de
QGIS-route.

## Drie keuzes in de formulering

- **Geen tijdsduur.** Geen "in vijf minuten geteld". Ik weet niet hoe lang een
  typische sessie duurt en een verzonnen getal is erger dan geen getal.
- **"Niet uitpakken" staat erin.** Dat is de eerste fout die iemand met een ZIP
  maakt, en hij staat verderop pas in stap 1.
- **De reconstructie is een stap, geen optie.** In stap 2 noem je 'm zelf "warm
  aanbevolen"; in een TL;DR is "optioneel" hetzelfde als "sla over".

## Opmaak

Hergebruikt `info-block`, `body-text` en de bestaande `ul` / `li`-opmaak binnen
dat blok. Alleen twee inline `style`-attributen voor marge en één kleinere
afsluitregel, in dezelfde trant als de bestaande inline-stijlen op deze pagina.
Er staan nu twee `info-block`s onder elkaar; als dat visueel te veel van
hetzelfde is, is een randkleur of wat extra witruimte de kleinste ingreep.

## Validatie

```
HTML-tagbalans over.html, voor en na    identiek, geen openstaande tags
CSS-klassenverzameling voor/na          identiek (26)
byte-identiteit                         alleen over.html
JS-syntax, gedeelde blokken             ongewijzigd, alles OK
```

## Nog open voor over.html

De drie screenshots ontbreken nog; de pagina toont zolang een nette placeholder.
Een Engelse variant staat op de backlog.
