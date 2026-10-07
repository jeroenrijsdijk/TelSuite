# Veldtest vóór 3.0

> **Uitkomst (7 oktober 2026): alles groen, op iPhone en op Android.** Gedraaid
> op v2.77; er hoefde niets gerepareerd te worden. v2.77 is daarom ongewijzigd
> 3.0 geworden (zie `overdracht/overdracht_v3_0.md`). Dit draaiboek blijft staan
> als voorbeeld voor een volgende veldtest.

Doel: zien of wat sinds v2.64 gebouwd is ook op een echte iPhone werkt, in
Safari en buiten. De automatische tests draaien in Chromium met nagebootste GPS
en een nagebootst wegennet. Dit draaiboek dekt wat die niet kunnen zien.

Duur: ongeveer 30–40 minuten buiten, plus 10 minuten achter de computer.
Plek: een straat met geparkeerde auto's, bij voorkeur met een vrijliggend
fietspad in de buurt.

Noteer bij elke afwijking: welke tool, welke stap, wat je zag, hoe laat, en maak
zo mogelijk een schermafbeelding. Een afwijking is geen mislukking; daar is deze
ronde voor.

---

## 0. Voorbereiding (thuis, 5 min)

- [ ] v2.77 staat op telonline.org.
- [ ] Heb je nog een onderbroken telling in een van de tools? Open de tool en
      download hem eerst. De volgende stap wist ook de noodopslag.
- [ ] Safari: Instellingen → Safari → Geavanceerd → Websitegegevens →
      telonline.org verwijderen. Zo haal je verse bestanden op in plaats van
      oude uit de cache.
- [ ] Open telonline.org: onderaan de voorpagina staat **v2.77**.
- [ ] De voorpagina toont drie groepen: *Verkeer tellen*, *Parkeren tellen*,
      *Achter je bureau*. Pocket-parkeren staat bovenaan bij parkeren.

## 1. Static (8 min)

- [ ] Start. Het scherm blijft aan; laat de telefoon 2 minuten liggen zonder
      aanraken en kijk of hij niet op slot gaat.
- [ ] Tel ongeveer 1 minuut, een paar voertuigen per richting.
- [ ] Herlaad de pagina (vernieuwknop in de adresbalk). Je ziet een bruine balk
      met *Continue / Download / Discard*, en de tellers staan er nog.
- [ ] Wacht 1 minuut. Tik dan **Continue** en tel nog 1 minuut.
- [ ] Veeg Safari weg in de app-kiezer. Open Safari en de tool opnieuw. Weer de
      balk; tik **Continue**.
- [ ] Tik **END**. Het deelblad biedt `…_sta.zip` aan; bewaar hem in Bestanden.
      Verschijnt er geen deelblad, tik dan **Export CSV**. Noteer dat wel: het
      is precies wat deze test moet vinden.
- [ ] Open de ZIP in Bestanden. Hij bevat vier CSV's. In `_overzicht.csv`
      staat `Interruptions;2`, met de twee onderbrekingen eronder. De
      *Observed duration* is ongeveer de getelde tijd, zonder de pauzes.
- [ ] Open de tool opnieuw. Er is geen balk meer, want de telling is afgerond
      en geëxporteerd.

## 2. Pocket-parkeren via de eigen ingang (8 min)

- [ ] Tik op de voorpagina *Pocket — parkeren*. Je komt **meteen** op het
      parkeerscherm, zonder het menu met vier modi, ook niet heel even.
- [ ] Delen → Zet op beginscherm. Open de telling daarna via dat icoon: weer
      meteen parkeren.
- [ ] Tel een stukje straat. Het tikgeluid werkt vanaf de eerste tik.
- [ ] Veeg Safari weg en open via het icoon. Je ziet de herstelmelding met
      **Doortellen** en alleen de knop *Parkeren* eronder, geen vier modi.
- [ ] Tik **Doortellen**. De tellers in de vier vakken staan er nog; tel
      verder.
- [ ] **Stop & Download** → bewaar de ZIP → **Sluiten**. Je krijgt een lege,
      nieuwe parkeertelling, geen menu.
- [ ] Tik **‹ Terug**. Je komt op de voorpagina.

### 2b. Opruimen na opslaan (3 min, v2.76)

- [ ] Pocket (gewone kaart, *Simpel*): tel een paar tikken, **Stop &
      Download**, sla op via het deelblad, tik **Sluiten**. Wissel naar een
      andere app, kom terug en herlaad pocket. Er komt **geen**
      herstelmelding.
- [ ] Nog eens, maar **annuleer** het deelblad en sluit de tab. Open pocket
      opnieuw: nu **wel** een herstelmelding. Kies *Download*.

## 3. Pocket zonder internet (5 min)

- [ ] Zet de vliegtuigmodus aan. GPS blijft werken.
- [ ] Open pocket (gewone kaart), kies *Simpel*, loop ± 100 m en tik af en toe.
- [ ] Stop & Download.
- [ ] Vliegtuigmodus uit. In de ZIP bevat `_gps.csv` punten van de hele route.
      Vóór v2.71 was die leeg zonder internet.

## 4. Parkeertelling (auto) (8 min)

- [ ] Start, tel een stukje straat (goed/fout/leeg).
- [ ] Veeg Safari weg en open opnieuw. De herstelmelding verschijnt met
      **▶ Doortellen**.
- [ ] Tik eerst **Start**. De app vraagt of de herstelde telling weg mag; kies
      *Annuleren*. Alles staat er nog.
- [ ] Tik **▶ Doortellen**. GPS pakt weer op en de telknoppen worden actief.
      Tel verder.
- [ ] Stop. Eén ZIP met alle tikken; op de kaart loopt het spoor door met een
      sprong op de plek van de onderbreking.
- [ ] Verschijnt na Stop het deelmenu? Noteer ja of nee: dat vertelt of het
      tikgebaar het inpakken overleeft. Zo niet, dan staat er *ZIP niet
      opgeslagen*; tik **⬇ Download ZIP** en het deelmenu komt meteen.
- [ ] Nog een korte telling, Stop, en **annuleer** het deelmenu. Er start
      geen download, de statusregel zegt *ZIP niet opgeslagen*. Herlaad de
      pagina: de herstelmelding verschijnt. Download dan alsnog.

Fietsparkeren en capaciteit delen deze code (byte-identiek, bewaakt). Eén
korte ronde op één van beide is genoeg: start, tel, herlaad, doortellen, stop.

- [ ] Fietsparkeren of capaciteit: herstel en doortellen werken.

## 5. Achter de computer (10 min)

- [ ] **Telrapport**: laad alle ZIP's van vandaag tegelijk. De Static-telling
      verschijnt als punt, zonder melding. Klik erop: de uurintensiteit klopt
      ongeveer met wat je telde.
- [ ] Laad ook een oude Static-ZIP (`traffic_count_….zip`) als je die hebt.
      Die hoort ook te laden.
- [ ] Tik *bewaar kaart als verzamel-ZIP*, herlaad telrapport en laad die ZIP. De Static-telling komt terug.
- [ ] **Reconstructor**: laad de parkeertelling-ZIP en reconstrueer. In
      `_reconstructie_log.csv` staan `highway_voorkeur;actief (auto)…` en
      `reconstructie_versie;v2.74`.
- [ ] Heb je langs een vrijliggend fietspad geteld? Dan liggen de tikken in
      telrapport op de rijbaan, niet op het fietspad.
- [ ] Laad de Static-ZIP in de reconstructor. Je krijgt de melding "niets te
      reconstrueren".

---

## Na afloop

Stuur de afwijkingen, of "alles groen". Wat eruit komt repareren we, en dat
wordt 3.0.
