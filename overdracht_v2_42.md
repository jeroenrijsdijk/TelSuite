# TrafficCounterSuite v2.42 — Overdracht

**Volledigheids-melding in telrapport**: per sessie in de zijbalk staat nu "X/Y geclusterd" — direct zichtbaar of elke getelde tik ook echt op de clusterkaart staat. Alleen `telrapport.html` wijzigt; de rest byte-identiek aan v2.41.

## Aanleiding (methodiek-controle)

Op verzoek de hele clustering-keten doorgelicht. Bevinding: de systematiek is correct (elk kwalificerend punt telt precies één keer, geen dubbeltelling), maar het way-gebaseerde clusterpad (auto/fiets) neemt alleen `snapped='1'`-tikken op, plus rijen met geometrie en numerieke marker. Ongesnapte tikken staan wél als vervaagde ⚠-stip op de kaart, maar niet in de cluster-totalen.

Voor gereconstrueerde ZIP's is dit geen issue (de reconstructor zet `snapped` default op `'1'`, dus alles clustert); voor rauwe auto/fiets-ZIP's kan er een gat zitten. Om dat gat elke keer expliciet te maken — zodat je conclusies op een volledige kaart baseert — is deze melding toegevoegd.

## Wat is toegevoegd

- **`clusterDekking(sid)`** — read-only helper die de filters van `drawClusters` spiegelt en per sessie `{totaal, geplaatst, buiten}` teruggeeft:
  - way-pad (auto/fiets, transect/pocket mét wayData): telt `telData`-rijen (al gesnapt-gefilterd) die óók geometrie + numerieke marker hebben;
  - gap-pad (transect/pocket zonder wayData): telt de getekende stippen;
  - `totaal` = `n_waarnemingen` (het echte aantal), `buiten` = totaal − geplaatst.
  Bevat een comment dat 'ie bij wijziging in `drawClusters` moet meelopen.
- **Sessie-rij** toont nu een regel `✓ X/Y geclusterd` (compleet) of `⚠ X/Y geclusterd · Z buiten` (amber) met een tooltip die uitlegt dat de Z-tikken ongesnapt/buiten het netwerk zijn en als vervaagde ⚠-stippen zichtbaar zijn.

Zo zie je in één oogopslag of de clusterkaart volledig is, zonder badges op te tellen.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon.
- **Functietest (geïsoleerd):** auto 8/10 (2 ongesnapt), 10/10 (compleet), 9/10 (1 way zonder geometrie), pocket 12/12 (gap-pad) — alle correct.
- **Byte-identiteit:** t.o.v. v2.41 wijzigde uitsluitend `telrapport.html`.

## Methodiek-conclusie (ter naslag)

- Systematiek clustering: correct, geen dubbeltelling, elk kwalificerend punt één keer.
- Gereconstrueerde ZIP's: elk geteld punt zit in een cluster.
- Rauwe auto/fiets-ZIP's: ongesnapte tikken buiten de clusters (wél als ⚠-stip zichtbaar) — nu expliciet gemeld per sessie.
- Niets verdwijnt spoorloos: worst case = vervaagde ⚠-stip; `n_waarnemingen` blijft het volledige aantal.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen; eventueel zijde-offset op de kaartstippen.
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
