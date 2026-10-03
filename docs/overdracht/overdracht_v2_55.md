# Overdracht v2.55 — verzamel-ZIP: de kaart in één handeling terug

Eén bestand: `telrapport.html`, +8.958 bytes. Nieuwe knop in de Kaart-groep:
**bewaar kaart als verzamel-ZIP**. Terugladen gaat via de gewone dropzone, geen
tweede knop.

---

## 1. Waarom dit goedkoop was

`loadZip` bewaart bij elke telling het originele bestand: `originalFile[sid] =
file`, oorspronkelijk voor de correctietool. De ZIP's staan dus al in het
geheugen. Er hoefde niets opnieuw geserialiseerd te worden; ze worden opnieuw
ingepakt.

## 2. Vorm: geneste ZIP's

`TelVerzameling_<jjjjmmdd>.zip` bevat per telling een `<sessie_id>.zip` plus één
`verzameling.json`.

Niet samenvoegen tot één platte ZIP, en daar is een harde reden voor: `loadZip`
zoekt zijn bestanden met `Object.keys(F).find(k => k.endsWith(suf))` en pakt de
**eerste** treffer. Vijf tellingen in één platte ZIP zou vier `_sessie.csv`'s
onzichtbaar maken. Genest houdt bovendien elk lid een zelfstandige, herlaadbare
telling waar de correctietool gewoon op werkt.

## 3. Correcties gaan mee

Zoals afgesproken. Heeft een telling correcties, dan worden `_telregels.csv` en
`_straten.csv` in het lid vervangen door `buildTelregelsCsv(sid)` en
`buildStratenCsv(sid, origineleStratenTekst)` — hetzelfde pad als
`exportOneCorrectedZip`, inclusief het meegeven van de originele stratentekst
zodat de naam-mapping bij de her-aggregatie intact blijft. Alle andere leden
worden als `uint8array` overgenomen, dus GPX en andere binaire bestanden blijven
byte-identiek.

**Gevolg, met opzet:** de leden zijn niet meer gelijk aan je bronbestanden. De
verzameling is de huidige staat van je kaart, niet een archiefkopie. Bewaar je
originele ZIP's dus zelf.

`_kaart.png` gaat er niet in. Wat is weggelaten staat per telling in het manifest
onder `weggelaten`, zodat het zichtbaar blijft in plaats van stil te verdwijnen.

## 4. Het manifest

```json
{
  "formaat": "telonline-verzameling",
  "versie": 1,
  "gemaakt": "2026-09-14T11:20:03",
  "tellingen": [
    { "sid": "...", "bestand": "....zip", "bron": "..._car.zip",
      "app_type": "auto", "correcties": 3, "weggelaten": ["..._kaart.png"] }
  ],
  "weergave": {
    "midden": {"lat": ..., "lon": ...}, "zoom": 17, "basemap": "positron",
    "zichtbaar": {"<sid>": true}, "stippen": {"goed": true, ...},
    "clusters": true, "capaciteitscontouren": false
  }
}
```

**De laadvolgorde is het subtiele deel.** Sessiekleuren komen uit
`SESSION_COLOR_PALETTE[SESSION_COLOR_IDX++]`, dus ze hangen aan de volgorde van
binnenkomst. Zonder vaste volgorde zou je dezelfde kaart in andere kleuren
terugkrijgen. `tellingen` is daarom een array en die volgorde wordt bij het laden
aangehouden.

Een verzameling met een hoger `versie`-nummer dan deze telrapport kent, wordt
niet geweigerd: je krijgt een melding en wat onbekend is wordt overgeslagen.

## 5. Laden

`loadFile` pakt een ZIP nu één keer uit en kijkt dan pas wat het is. Zit er een
`verzameling.json` in, dan gaat hij naar `loadVerzameling`; anders naar `loadZip`,
met de al uitgepakte JSZip erbij zodat hij niet twee keer wordt ontleed.

De weergave wordt **niet** direct hersteld maar geparkeerd in
`_verzamelingHerstel` en aan het eind van `ingestFiles` toegepast — na alle
per-telling `fitBounds` en na het eventuele bbox-herstel. Anders zou de laatste
telling het kaartbeeld meteen weer overschrijven.

Volgorde van herstellen: basemap, stippen, zichtbaarheid per telling,
capaciteitscontouren, clusters, en als laatste midden en zoom.

## 6. Twee dingen om te weten

**Het bewaarde kaartbeeld wint van het bbox-filter.** Laad je een verzameling met
het bbox-vinkje aan, dan krijg je het bewaarde beeld, niet het bevroren
filterbeeld. Een bewaarde kaart is een expliciete keuze, een bevroren filterbeeld
niet.

**Het bbox-filter zelf werkt niet op verzamelingen.** `probeBbox` zoekt
`_netwerk.csv` in de ZIP en vindt die niet in een verzameling (de leden zijn
`.zip`'s). Hij geeft dan `null` terug, en het filter is fail-open: het bestand
wordt geladen. Dat is het bestaande, bewuste gedrag — een telling wordt nooit
stil weggelaten — maar het betekent wel dat filteren op een verzameling niets
doet. Als je dat wilt, moet `probeBbox` de leden gaan aflopen; dat is een eigen
klusje en niet gratis.

## 7. Validatie

```
JS-syntax (node --check)                    15/15 OK
HTML-tagbalans, vergeleken met v2.54        geen afwijking
byte-identiteit                             alleen telrapport.html
gedeelde blokken byte-identiek              6 groepen OK
test_zipref.py                              referentie sluit aan op de code
functest_verzameling.js (nieuw)             26/26 OK
overige functionele tests                   34 + 18 + 16 + 9 OK
```

De nieuwe test draait de echte `exportVerzameling` / `loadVerzameling` /
`pasVerzamelingWeergaveToe` met een echte JSZip en een nagemaakte kaart, en
controleert de round-trip: volgorde, weggelaten `_kaart.png`, ingeschreven
correcties, byte-identiek binair lid, de volledige weergavestaat, en de twee
randgevallen (lege kaart, origineel kwijt).

Hij heeft één afhankelijkheid die de andere tests niet hebben:

```
npm install jszip
node _archief/overpass_rig/functest_verzameling.js
```

**Wat de test niet dekt:** of het in de browser prettig voelt. Laad je paar
parkeertellingen, zet ze zoals je ze wilt hebben, bewaar, ververs de pagina en
sleep het bestand terug. Let vooral op of de sessiekleuren dezelfde zijn — dat is
de gevoeligste aanname in het ontwerp.

## 8. Backlog

Toegevoegd:
- Reconstructiescript een losse kaart-PNG naast de `_recon.zip` laten schrijven,
  nu `_kaart.png` niet meer in de verzameling meegaat.
- `probeBbox` leren omgaan met verzamelingen, zodat het bbox-filter ook daar werkt.

Verder ongewijzigd t.o.v. v2.54.
