# Overdracht v2.68 — versienummer op index.html

Op verzoek van Jay staat het versienummer nu zichtbaar op het startscherm. Het
gaat mee met elke update.

---

## 1. Wat er is

- Onderaan `index.html`, onder de link naar de handleiding: `v2.68`, klein, in
  Share Tech Mono, in de gedempte kleur van de help-link. Het is taalneutraal,
  dus er hoeft niets in de NL/EN-woordenlijst.
- `valideer.py` controleert het releasenummer op vier plekken. Een vergeten
  ophoging laat de validatie falen.

## 2. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `index.html` | klasse `.versie` (9 regels CSS) en één regel HTML |
| `_archief/overpass_rig/valideer.py` | constante `RELEASE` en een sectie *releasenummer* |
| `OVERDRACHT_STAND_VAN_ZAKEN.md` | werkafspraak toegevoegd (§3), release-tabel |
| `README.md` | één zin bij Ontwikkelen |

Alle andere HTML-bestanden zijn byte-identiek aan v2.67.

## 3. Hoe het bijgehouden blijft

Eén nummer, vier plekken:

| plek | vorm |
|---|---|
| `valideer.py` | `RELEASE = 'v2.68'` — de bron |
| `index.html` | `<div class="versie">v2.68</div>` |
| `OVERDRACHT_STAND_VAN_ZAKEN.md` | `**Laatste release: v2.68.**` |
| overdracht | bestandsnaam `overdracht_v2_68.md` |

`valideer.py` faalt in drie gevallen:

- `index.html` toont een ander nummer dan `RELEASE`, of het staat er niet
  precies één keer;
- het nummer is niet hoger dan in de vorige release;
- de stand van zaken of de overdracht draagt een ander nummer.

Getest met vier opzettelijke fouten: index niet opgehoogd, index met een
ander nummer, stand van zaken vergeten, overdracht ontbreekt. Alle vier gevangen.

Gevolg voor het werkproces: `index.html` staat voortaan in **elke** release bij
de gewijzigde bestanden. Dat is de bedoeling.

## 4. Waarom alleen index.html

Het nummer in elke tool zetten zou betekenen dat bij elke release alle vijftien
HTML-bestanden veranderen. Dan zegt de byte-identiteitscontrole niets meer: die
is juist waardevol omdat alleen de bedoelde bestanden mogen wijzigen.

**Let op bij het testen op de telefoon.** Het nummer op het startscherm zegt dat
`index.html` vers is. Het zegt niets over `pocket_count.html` of een andere tool:
Safari kan die nog uit zijn cache halen. Wil je zeker weten dat een tool vers
is, herlaad die tool dan zelf.

## 5. Terloops gezien, niet aangeraakt

- De pocket-kaart op het startscherm zegt "Pocket — three modes" / "drie
  modi". Pocket heeft er sinds de parkeermodus vier.
- De reconstructor schrijft nog oude versiemarkeringen (`v2.18` in de log,
  `v2.24` in `_sessie.csv`). Staat al op de backlog. Die zouden later aan
  hetzelfde `RELEASE`-nummer kunnen hangen.

## 6. Validatie

```
valideer.py                       ALLES OK — alleen index.html gewijzigd
  releasenummer                   index v2.68 · vorige release geen nummer · stand v2.68 · overdracht_v2_68.md
  negatieftests                   niet opgehoogd / ander nummer / stand vergeten / overdracht mist -> alle vier FOUT
functests                         alle 13 groen
check_encoding.py                 alles geldige UTF-8
```
