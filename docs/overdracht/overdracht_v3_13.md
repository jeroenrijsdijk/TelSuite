# Overdracht v3.13 — hoofdstuk "Slim lopen bij parkeertellingen"

Jay: "Als een straat erg vol is, loop ik de straat twee keer. Soms tel ik heen en
terug, en tel ik twee keer de rechter-auto's. Als ik een rondje kan lopen, dan
loop ik die twee keer, de eerste keer tel ik rechts, de tweede ronde links. In
een hele wijk tel ik eerst de buitenkant en dan ga ik naar binnen-straten.
Kortom: vastigheden om te zorgen dat je efficiënt loopt en niks vergeet."

Na het voorstel (drie niveaus: handleiding, dekking per kant in pocket, route uit
de planning): "het hoofdstuk slim lopen is goed — het gaat er ook om dat mensen
vooraf even nadenken hoe ze het doen — zo'n hoofdstuk maakt hen daar alert op."

## 1. Wat er veranderd is

De handleiding heeft een nieuw hoofdstuk `#slim-lopen`, direct na *Methodiek*, en
staat in de inhoudsopgave onder Methodiek. Het geldt voor Pocket-parkeren,
Autoparkeren en Fietsparkeren.

- **Vooraf: vijf vragen.** Begin en eind; drukke en smalle straten; de rand
  (beide kanten of alleen de binnenkant, vastleggen bij de opdracht);
  doodlopende straten; past het in je tijdvak.
- **Eén kant per keer.** Bij heen en terug beide keren rechts tellen. Rechts is
  rechts in je looprichting; de parkeertelling zet de tik meteen aan de goede
  kant, bij Pocket doet de reconstructie dat achteraf.
- **Drie patronen, elk met een plaatje** (inline SVG, kleur alleen voor de
  eerste en de tweede doorgang):
  1. drukke straat, heen en terug;
  2. een rondje om een blok, twee keer met de klok mee: eerst rechts (de
     blokkant), dan links (de overkant);
  3. een wijk: begin op de rand waar een binnenstraat uitkomt, eerst de rand
     rond, dan elke binnenstraat heen en terug. Dat sluit zonder een meter
     extra.
- **Waarom dit altijd past.** Elke straat twee keer, steeds rechts: er is altijd
  een route die elke kant één keer telt en uitkomt waar je begon (eulercircuit).
  Blokrondjes als alternatief. Straten die je in één keer telt: bij een oneven
  aantal op een kruispunt loop je ergens dubbel; valt dat op een smalle straat,
  tel die dan als een drukke.
- **Onderweg en na afloop.** Na het keren eerst een paar passen; kijk op de kaart
  voor je stopt (pocket: knop *Kaart*; parkeertelling: zandgele straten op de
  mini-kaart); loop een volgende keer dezelfde route.

**Verwijzingen.** De methodiekregel over het gebied (parkeren), de sectie
*Parkeren* van pocket en de veldtips van de parkeertelling verwijzen naar het
hoofdstuk.

**Eén tip aangepast.** De veldtip *Looprichting* van de parkeertelling zei:
"Loop de route in één richting — bij een U-vormige route is een nieuwe sessie
voor de terugweg nauwkeuriger." Dat spreekt het nieuwe hoofdstuk tegen (heen en
terug in één telling). Nu: "Keer je, loop dan eerst een paar passen en wacht op
de groene pijl voordat je weer tikt." De kant volgt uit de looprichting, en die
draait na een keerpunt bij; de groene pijl is daar al het teken voor. Jay: als
er toch een reden was voor een nieuwe sessie, zet de oude zin terug.

**Opmaak.** Eén regel eigen CSS na het gedeelde stijlblok (dat blijft
ongemoeid; `valideer.py` staat er vijf toe en verbiedt `style=""` met opmaak):
`figure{margin:1em 0}`, anders laat de standaard inspringing van `<figure>`
(40 px) op een telefoon weinig over; de SVG vult de kolom tot 36em; `.samen`
houdt een kleurlabel bij zijn woord en haakjes.

**Hoe de plaatjes gemaakt zijn.** Met een klein Python-script (coördinaten,
pijlpunten midden op elk stuk). Het script staat niet in de repo; de SVG is met
de hand te lezen en te wijzigen. Kleuren: blauw `#1f6fb2` (eerste doorgang),
oranje `#d9822b` (tweede), weg `#e4e4e4`, huizen `#c9c9c9`.

## 2. Wat niet (backlog)

Niveau 2 en 3 uit het voorstel staan in de stand van zaken, §5 *Slim lopen*:
- dekking per straatkant in de dekkingskaart van pocket-parkeren;
- een route uit telplanning (eulercircuit, met een koppeling via kortste paden
  voor straten die in één keer geteld worden).

Volgorde: eerst niveau 2.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter_help.html` | hoofdstuk `#slim-lopen` met drie SVG's; inhoudsopgave; drie verwijzingen; veldtip *Looprichting* |
| `index.html` | versie v3.13 |
| `_archief/overpass_rig/valideer.py`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

Bekeken in Chromium op 390 en 1000 px breed: geen horizontale scroll, plaatjes
over de volle breedte van de tekstkolom, bijschriften leesbaar.

```
valideer.py           ALLES OK — 2 verwachte bestanden gewijzigd; gedeelde blokken OK;
                      documentatiepagina's kaal (figuurstijl in de eigen regel na het gedeelde blok)
SVG                   3 plaatjes goed gevormd (XML)
laadtest.py           47/47
hersteltest.py        133/133
statictest.py         24/24
opruimtest.py         139/139
logicatest.py         30/30
robuusttest.py        87/87
gpkgtest.py           80/80
functests             alle 16 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
