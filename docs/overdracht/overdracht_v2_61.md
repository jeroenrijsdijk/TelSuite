# Overdracht v2.61 — taartdiagram en shift-klik op clusters

Eén bestand: `telrapport.html`. Drie bijna-identieke stukken bol-HTML zijn
vervangen door één `clusterBolHtml()`, en die tekent nu een taart.

---

## 1. Wat er misging aan de oude bol

De vulkleur was `cfg.colors[dominant]` — de kleur van het **meest voorkomende**
type in het cluster. Bij een parkeertelling betekende dat "hier staat het meeste
goed geparkeerd" of "hier is het meeste leeg", en verder niets. Twaalf goed en
elf leeg gaf exact dezelfde groene bol als twaalf goed en nul leeg.

Terwijl die verhouding nu juist de telling ís.

## 2. Wat er nu staat

Een `conic-gradient` per type, met het totaal in een donutgat. Drie keuzes die
het leesbaar houden:

**Vaste puntvolgorde uit `APP_CONFIG.types`**, niet gesorteerd op aantal. Zo ziet
dezelfde straat er elke keer hetzelfde uit en kun je twee bollen naast elkaar
vergelijken. Voor auto is dat dus altijd goed → fout → leeg → spec, met de
kleuren die de losse stippen ook al hebben.

**Het cijfer staat in een gat, niet over de punten heen.** Wit op de lichtgrijze
`leeg`-punt (#94a3b8) is anders niet te lezen. Het gat heeft de
achtergrondkleur van de app, dus ook op de luchtfoto blijft het cijfer staan.

**Onder 26 px blijft de bol vlak**, precies zoals vroeger, met het cijfer erop.
Taartpunten van een paar pixels zijn mush, en een diagram dat je niet kunt
aflezen liegt meer dan het vertelt. Een cluster met één type krijgt om dezelfde
reden gewoon zijn eigen kleur.

## 3. Eén uitzondering die blijft

Een gecombineerd cluster van twee of meer sessies houdt zijn diagonale
tweekleur. Die zegt "hier liggen tellingen van verschillende dagen over elkaar",
en dat is een andere boodschap dan de typeverdeling. Bij één sessie krijgt die
bol wél de taart.

## 4. En passant: drie keer dezelfde HTML weg

De bol werd op drie plekken opgebouwd — `makePtClusterMarker`, het gap-pad en
het segment-pad van `drawClusters` — met drie net iets verschillende kopieën van
hetzelfde blokje CSS. Eén schaduw hier, een andere randdikte daar. Dat is nu één
functie met opties, en de kleine verschillen die er waren (geen schaduw op het
segment-pad, dikkere rand op de gecombineerde bol) zitten in die opties.

## 5. Validatie

```
nieuwe test functest_taartbol.js   24/24 OK
  puntvolgorde                     uit APP_CONFIG, niet op aantal; nul-types eruit;
                                   onbekend type achteraan met neutrale kleur
  taart vs vlak                    drempel 26px, één type blijft vlak
  de punten zelf                   aansluitend, laatste exact op 100 (geen haarlijn),
                                   ook bij derden
  tweekleur                        bgStyle wint, dan ook geen donutgat
  alle telsoorten                  fiets, auto, pocket, transect
  randgevallen                     leeg counts-object, onbekend appType, gat ≥ 14px
byte-identiteit                    alleen telrapport.html
alle overige tests                 29 + 20 + 11 + 22 + 16 + 9 + 34 + 18 + 26 + 16 OK
```

De test draait de echte `clusterBolHtml` headless, met de echte `APP_CONFIG`
uit het bestand — dus als je ooit een type of kleur toevoegt, loopt de test mee.

**Wat de test niet ziet:** of het oogt. Vooral de drempel van 26 px en de
gatgrootte (52% van de bol) zijn smaak. Beide staan als constante bovenin
`clusterBolHtml`; `PIE_MIN_PX` hoger zetten geeft minder maar duidelijkere
taarten.

## 6. Eén vraag die open blijft

Voor een parkeertelling toont de taart nu de **typeverdeling** (goed / fout /
leeg / spec). Omdat `leeg` een eigen punt is, lees je de bezetting daar
impliciet in af. Wil je liever een strikte **bezet-versus-vrij**-taart in twee
kleuren — waarbij goed, fout en spec samen "bezet" worden — dan is dat een
andere keuze, en die kan naast de huidige bestaan. Zeg maar of je dat ergens
wilt kunnen omschakelen.

---

# Deel 2 — shift-klik op een cluster isoleert die telling

## 7. Wat het doet

Shift-klik op een clusterbol zet alle andere geladen tellingen uit. Nogmaals
shift-klikken op dezelfde selectie zet alles weer aan, zodat één handeling ook de
weg terug is. Shift-klikken op een ánder cluster wisselt de selectie in plaats van
alles terug te zetten — dat is wat je wilt als je tellingen langs elkaar legt.

Zonder shift verandert er niets: de klik opent het detailpaneel zoals altijd.

## 8. De solo-logica bestond al

Rechtsklik op een sessierij deed dit al, maar de logica zat inline in de
contextmenu-handler. Die is eruit gelicht naar `soloSessies(sids)`, zodat de
kaart en de lijst nu dezelfde schakelaar gebruiken. De contextmenu-handler is
daarmee vier regels.

`soloSessies` neemt een **lijst**, want een gecombineerd cluster kan tellingen
van meerdere dagen bevatten. Shift-klik daarop isoleert die hele groep in plaats
van willekeurig één ervan te kiezen.

## 9. Twee dingen die makkelijk misgaan

**De box-zoom van Leaflet start op shift+mousedown**, niet op click. Alleen de
klik afvangen is dus te laat: je krijgt een zoomkader over je kaart terwijl de
selectie ook nog gebeurt. Alle drie de clusterpaden hebben daarom een
`mousedown`-blokkade die alléén bij ingedrukte shift toeslaat — gewoon slepen
blijft werken.

**Niemand vindt een sneltoets vanzelf.** De clustertooltip krijgt er een dimmed
regel bij: "shift-klik: alleen deze telling". Alleen als er twee of meer
tellingen geladen zijn, want bij één is het een lege belofte en dan is het ruis
bij elke hover.

## 10. Validatie van deel 2

```
nieuwe test functest_shiftsolo.js   27/27 OK
  soloSessies                       isoleren, terugschakelen, groep isoleren,
                                    wisselen tussen tellingen, onbekende sid, lege lijst
  clusterShiftSolo                  zonder shift niet afgehandeld, met shift wel,
                                    event zonder originalEvent klapt niet
  box-zoom                          geblokkeerd bij shift, ongemoeid zonder
  tooltip-hint                      pas vanaf twee tellingen, inhoud blijft voorop
  bedrading                         alle drie de clusterpaden, lijst gebruikt
                                    dezelfde schakelaar, geen tweede kopie meer
byte-identiteit                     alleen telrapport.html
alle overige tests                  24 + 29 + 20 + 11 + 22 + 16 + 9 + 34 + 18 + 26 + 16 OK
```

**Wat de test niet ziet:** of de shift-klik in de browser inderdaad geen
zoomkader oplevert. Dat is de enige plek waar ik op Leaflets interne gedrag
gok — even proberen op een kaart met meerdere tellingen.

## 11. Voor de hand liggend vervolg

De losse tik-stippen en de weglijnen kennen deze sneltoets nog niet. Daar zou
hij net zo logisch zijn, en het is nu drie regels per plek. Bewust niet gedaan:
je vroeg om het cluster, en ik wil niet ongevraagd overal shift-gedrag inbouwen
voordat je het cluster-gedrag in de praktijk prettig vindt.
