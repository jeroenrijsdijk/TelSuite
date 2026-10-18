# Overdracht v3.15 — geen planningen meer op de server

Jay, na de veldtest van v3.14: "Ok, dat is getest en het werkt. We hoeven de .json
niet meer op te slaan op de server." Op de vraag wat er dan met *Maak Telling*
moest gebeuren (zonder server bleef alleen een download over die nergens werd
ingelezen): "Weg, alleen de link."

## 1. Wat er veranderd is

**Telplanning.**
- *Maak Telling* is weg: geen download van de JSON en geen opslag op de server.
  `exportPlanning` is verwijderd; `maakPlanning` maakt de planning voor de link.
- *Opdrachten* is weg: de knop, het paneel, de CSS en de functies `loadOpdrachten`,
  `startOpdracht`, `verwijderOpdracht`, `planningServerMelding` en `escHtml`
  (die alleen daar werd gebruikt).
- *Deel als link* is de hoofdknop: de gevulde knop onderaan de zijbalk, die vroeger
  *Maak Telling* was. Hij staat aan zodra er wegen geselecteerd zijn.

**Veld-apps.** Parkeertelling, fietsparkeren en pocket lezen een planning alleen
nog uit de link (`#plan=…`). Een oude link met `?plan=/planningen/…` laadt niets:
geen planning, geen fout, en geen verzoek naar de server.

**Repo.**
- `planningen/` is weg: `planning_list.php`, `planning_save.php`,
  `planning_delete.php` en `.htaccess`. Er staat geen PHP meer in de repo.
- `.gitattributes`: de regel `planningen/.htaccess export-ignore` is weg.
- `.gitignore` houdt `planningen/` en `planning_*.json` buiten git: oude
  planningen kunnen tellernamen bevatten.
- `site.yml`: alleen het commentaar is bijgewerkt. De controle op een
  `.htaccess`/`.htpasswd` in de inhoud blijft.

**Documentatie.**
- **Handleiding:**
  - *Wat doet de telplanning?* en *Sessiegegevens* (was *Maak Telling*) zijn
    bijgewerkt;
  - *Planning als link* zegt dat dit de enige weg is, en dat je de mail bewaart
    als je de opdracht later nog eens wilt geven;
  - *Opdrachten starten vanuit de app* is weg, ook uit de inhoudsopgave;
  - bij de serverbestanden staan geen planningen meer.
- **Privacyverklaring** (NL/EN, bijgewerkt 18 oktober 2026): op de server
  alleen serverlogs; een planning gaat als link; tot oktober 2026 stonden
  planningen op de server, en dat is gestopt.
- **ZIP-referentie:** de link is de enige route.
- **README, `CLAUDE.md`, `docs/ONTWIKKELEN.md`:**
  - geen backend en geen PHP meer;
  - controlestap 5 (`php -l`) is vervallen;
  - de regel over het planning-endpoint is vervangen.

## 2. Nog te doen door Jay

**De map op de server opruimen.** De opgeslagen planningen (`planning_*.json`,
met tellernamen) zijn nooit via git op de server gekomen. Ze blijven daar dus
staan, ook na de deploy.
1. In Plesk → Bestanden: `httpdocs/planningen` helemaal verwijderen.
2. Controle: `https://telonline.org/planningen/planning_list.php` geeft 404.
3. Stond er nog een *Password-Protected Directory* op `/planningen`: die mag ook weg.

Ik weet niet zeker of de Git-deploy van Plesk de PHP-scripts zelf weghaalt als ze
uit de branch `site` verdwijnen. Stap 1 regelt het in elk geval.

## 3. Wat niet

**Een link terug openen in telplanning**, om een planning aan te passen of
opnieuw te gebruiken. Telplanning zou dan `#plan=` lezen, net als de apps; het
blok `planlink` kan dat al. Het staat op de backlog. Nu teken je opnieuw.

## 4. Tests

- **`planlinktest.py`, deel D** is herschreven: *zonder server* in plaats van
  *de server-route blijft werken*. Het test:
  - geen Maak Telling, geen Opdrachten en geen paneel;
  - *Deel als link* is gevuld;
  - een link maken werkt nog;
  - een oude server-link in de parkeertelling en in pocket laadt niets en
    geeft geen fout;
  - geen enkel verzoek naar `/planningen/`.

  Samen 44 tests. Tegen v3.14 faalt deel D: Maak Telling en Opdrachten bestaan
  daar nog.
- **`laadtest.py`, deel D** (de opdrachtenlijst bij een afgeschermde map, v2.75)
  is vervallen.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | Maak Telling, Opdrachten en het opslaan op de server weg; Deel als link is de hoofdknop |
| `parkeertelling.html`, `fietsparkeren.html`, `pocket_count.html` | alleen nog `#plan=`, geen `?plan=` |
| `traffic_counter_help.html`, `privacy.html`, `zip_format_reference.html` | zonder server |
| `index.html` | versie v3.15 |
| `planningen/` | verwijderd (drie PHP-scripts, `.htaccess`) |
| `.gitattributes`, `.gitignore`, `.github/workflows/site.yml` | `planningen/` |
| `README.md`, `CLAUDE.md`, `docs/ONTWIKKELEN.md` | geen backend |
| `_archief/overpass_rig/planlinktest.py`, `laadtest.py` | deel D |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

Het gedeelde blok `planlink` is ongewijzigd (md5 `81a1ed9e`).

## 6. Validatie

Bekeken in Chromium: de zijbalk van telplanning met *Deel als link* als gevulde
hoofdknop onderaan.

```
valideer.py           ALLES OK — 8 verwachte bestanden gewijzigd; groep planlink ongewijzigd (81a1ed9e) en OK
planlinktest.py       44/44 (deel D nieuw)
laadtest.py           45/45 (deel D vervallen)
functest_planlink.js  29/29
hersteltest.py        133/133
statictest.py         24/24
opruimtest.py         139/139
logicatest.py         30/30
robuusttest.py        87/87
gpkgtest.py           80/80
functests             alle 17 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
