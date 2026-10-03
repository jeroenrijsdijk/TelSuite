# Overdracht v2.58 — kopmetadata voor over.html en de handleiding

Drie bestanden, samen +3.328 bytes. **Geen zichtbare tekst gewijzigd** — dat is
apart gecontroleerd door de body van voor en na te ontdoen van tags en te
vergelijken.

| Bestand | Verschil | Wat |
|---|---|---|
| `index.html` | +39 | `@id` op het WebApplication-knooppunt |
| `over.html` | +1.447 | Open Graph + JSON-LD `AboutPage` |
| `traffic_counter_help.html` | +1.842 | `lang`, title, description, canonical, Open Graph + JSON-LD `TechArticle` |

---

## 1. Twee dingen die gewoon fout stonden

**De handleiding was aangemerkt als Engels.** `<html lang="en">` op een pagina
die overwegend Nederlands is (745 Nederlandse tegen 94 Engelse signaalwoorden in
de body). Dat is niet alleen een zoekkwestie: een schermlezer las die pagina met
een Engelse uitspraak voor. Nu `lang="nl"`.

**De handleiding had geen enkele metadata.** Alleen een `<title>`, en die luidde
nog "Traffic Counter — Help" — de naam van vóór de rebrand in v2.34. Geen
description, geen canonical, niets. Terwijl dit samen met `over.html` je enige
echte tekstpagina is; de veldapps zijn apps waar weinig te citeren valt.

## 2. Wat er nu staat

`over.html` en de handleiding hebben dezelfde behandeling als `index.html` al
had: title, description, canonical, Open Graph en structured data. De types
volgen wat er werkelijk op de pagina staat — `AboutPage` voor de uitleg over de
suite, `TechArticle` voor de handleiding. Geen `HowTo` of `FAQPage`: daar staat
geen bijbehorende zichtbare inhoud tegenover, en structured data die niet matcht
met de pagina is precies wat je niet wilt.

**De drie pagina's verwijzen nu naar één app-knooppunt.** `index.html` heeft
`"@id": "https://telonline.org/#app"` gekregen; `over.html` en de handleiding
verwijzen daarnaar in hun `about`. Daarmee is het één samenhangende beschrijving
van één applicatie in plaats van drie losse beschrijvingen die toevallig op
elkaar lijken.

## 3. Eén ding dat ik heb laten staan

De kop ín de handleiding zegt nog **"Traffic Counter Help"** en daarboven
"traffic counter - count and report". Dat is zichtbare tekst en daarmee jouw
tekst, dus die heb ik niet aangeraakt — maar hij spreekt de nieuwe `<title>`
tegen en draagt de naam van vóór de rebrand. Eén regel werk als je wilt; zeg maar
wat de kop moet worden.

## 4. Nog niet gedaan

`zip_format_reference.html` heeft ook alleen een `<title>` en is wél een serieuze
tekstpagina — technische documentatie is precies wat AI-zoekmachines graag
aanhalen. Datzelfde blok erop is tien minuten. Stond niet in de opdracht, dus
niet gedaan.

Daarnaast blijven `robots.txt` en `sitemap.xml` jouw kant op: zonder sitemap
moet een crawler je subpagina's maar zien te vinden vanaf de homepage.

## 5. Validatie

```
JSON-LD geparsed met json.loads       3/3 geldig (WebApplication, AboutPage, TechArticle)
kopvolledigheid                       alle drie: lang, title, description, canonical, OG, JSON-LD
zichtbare tekst voor/na               ongewijzigd in alle drie
HTML-tagbalans, vergeleken met v2.57  geen afwijking
byte-identiteit                       precies 3 bestanden gewijzigd
gedeelde blokken byte-identiek        6 groepen OK
```

## 6. Waarop dit gebaseerd is

Google's documentatie zegt dat er geen aanvullende eisen of speciale
optimalisaties zijn om in AI Overviews of AI Mode te verschijnen, en dat er geen
nieuwe machine-leesbare bestanden of speciale schema's voor nodig zijn. Wat telt
is crawlbaarheid, inhoud als zichtbare tekst, interne links, en structured data
die overeenkomt met de zichtbare pagina. Dat is precies wat deze release doet —
niets meer.

Wat bewust **niet** is gedaan: `llms.txt`. Ahrefs vond in juni 2026 over
137.000 domeinen dat 97% van de llms.txt-bestanden in mei 2026 nul verzoeken
kreeg, en Google zegt expliciet dat het bestand de zichtbaarheid niet helpt en
niet schaadt.
