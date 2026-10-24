#!/usr/bin/env python3
"""Validatie per release: JS-syntax, HTML-tagbalans, byte-identiteit t.o.v. de vorige.

De tagbalans wordt vergeleken met de vorige release, niet met nul. Nieuwe
afwijking telt als fout; verdwenen ruis als verbetering. De enige bekende ruis
(een losse </div> in traffic_counter.html) is in v2.73 opgeruimd.
"""
import io, os, re, subprocess, sys, hashlib
from html.parser import HTMLParser

# De twee mappen. Op GitHub (tests.yml) zet de workflow ze via de omgeving.
OUD_DIR = os.environ.get('VALIDEER_OUD', '/home/claude/suite')
NIEUW_DIR = os.environ.get('VALIDEER_NIEUW', '/home/claude/build')
# Een PR zonder nieuw versienummer (alleen documentatie, tests of opmaak) heeft
# geen eigen RELEASE en VERWACHT-sets. Met VALIDEER_ZONDER_RELEASE=1 slaan de
# release-controles over: welke bestanden er veranderden, het releasenummer en
# de overdracht. Alle andere controles blijven. tests.yml zet hem zelf als
# index.html hetzelfde nummer houdt.
ZONDER_RELEASE = os.environ.get('VALIDEER_ZONDER_RELEASE') == '1'
# Per release bijwerken. RELEASE moet overeenkomen met index.html, de stand van
# zaken en de naam van de overdracht; zie de sectie 'releasenummer' onderaan.
RELEASE = 'v3.33'
# v3.33: Ordenen wordt Archief, met een Overzicht (kaart, tabel, catalogus.csv).
VERWACHT_GEWIJZIGD = {'index.html', 'telarchief.html', 'over.html', 'about.html', 'privacy.html',
                      'traffic_counter_help.html', 'zip_format_reference.html'}
VERWACHT_VERWIJDERD = set()

# Interne pagina's: niet in de sitemap, geen eisen aan titel en description
NIET_IN_SITEMAP = {'snap_methodology.html', 'snaptrace.html', 'winkelstraat_rekenrig.html'}

# v3.3: documentatiepagina's in kale HTML, met hetzelfde stijlblok
KAAL = ['traffic_counter_help.html', 'over.html', 'about.html', 'privacy.html', 'verantwoording.html']   # about.html sinds v3.24

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Balans(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.fouten = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.fouten.append('sluit </%s> zonder open' % tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.fouten.append('niet gesloten: <%s>' % self.stack.pop())
            if self.stack:
                self.stack.pop()
        else:
            self.fouten.append('sluit </%s> zonder open' % tag)


def balans(pad):
    b = Balans()
    b.feed(io.open(pad, encoding='utf-8').read())
    rest = [t for t in b.stack if t not in ('html', 'body', 'head')]
    return (tuple(b.fouten), tuple(rest))


def js_uit(pad):
    """Alleen echte scripts: JSON-LD en andere niet-JS types overslaan."""
    s = io.open(pad, encoding='utf-8').read()
    stukken = []
    for attrs, body in re.findall(r'<script([^>]*)>(.*?)</script>', s, re.S | re.I):
        if 'src=' in attrs:
            continue
        m = re.search(r'type\s*=\s*["\']([^"\']+)', attrs, re.I)
        if m and m.group(1).strip().lower() not in (
                'text/javascript', 'application/javascript', 'module'):
            continue
        stukken.append(body)
    return '\n;\n'.join(stukken)


fouten = 0
html = sorted(f for f in os.listdir(NIEUW_DIR) if f.endswith('.html'))

print('== JS-syntax (node --check) ==')
for f in html:
    js = js_uit(os.path.join(NIEUW_DIR, f))
    if not js.strip():
        print('  %-28s (geen inline JS)' % f)
        continue
    tmp = '/tmp/%s.js' % f.replace('.html', '')
    io.open(tmp, 'w', encoding='utf-8').write(js)
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    if r.returncode == 0:
        print('  %-28s OK' % f)
    else:
        print('  %-28s FOUT\n%s' % (f, r.stderr[:800]))
        fouten += 1

print('\n== HTML-tagbalans (t.o.v. vorige release) ==')
for f in html:
    oudpad = os.path.join(OUD_DIR, f)
    nieuw = balans(os.path.join(NIEUW_DIR, f))
    if not os.path.exists(oudpad):
        print('  %-28s %s (nieuw bestand)' % (f, 'OK' if nieuw == ((), ()) else 'RUIS ' + str(nieuw)))
        if nieuw != ((), ()):
            fouten += 1
        continue
    oud = balans(oudpad)
    if nieuw == oud:
        print('  %-28s %s' % (f, 'OK' if nieuw == ((), ()) else 'ongewijzigde ruis'))
    elif nieuw == ((), ()):
        # v2.73: ruis die verdwijnt is een verbetering, geen afwijking
        print('  %-28s OK (ruis opgelost, was %s)' % (f, oud))
    else:
        print('  %-28s AFWIJKING oud=%s nieuw=%s' % (f, oud, nieuw))
        fouten += 1

print('\n== byte-identiteit t.o.v. vorige release ==')
gewijzigd = set()
nieuw_bestand = set()
for f in html:
    oudpad = os.path.join(OUD_DIR, f)
    if not os.path.exists(oudpad):
        nieuw_bestand.add(f)
        print('  nieuw:     %-28s %d bytes' % (f, os.path.getsize(os.path.join(NIEUW_DIR, f))))
        continue
    a = open(oudpad, 'rb').read()
    b = open(os.path.join(NIEUW_DIR, f), 'rb').read()
    if hashlib.md5(a).hexdigest() != hashlib.md5(b).hexdigest():
        gewijzigd.add(f)
        print('  gewijzigd: %-28s %+d bytes' % (f, len(b) - len(a)))
gewijzigd |= nieuw_bestand
onverwacht = gewijzigd - VERWACHT_GEWIJZIGD
ontbrekend = VERWACHT_GEWIJZIGD - gewijzigd
if ZONDER_RELEASE:
    print('  geen release: %d bestand(en) gewijzigd, niet vergeleken met VERWACHT_GEWIJZIGD' % len(gewijzigd))
else:
    if onverwacht:
        print('  FOUT onverwacht gewijzigd: %s' % sorted(onverwacht)); fouten += 1
    if ontbrekend:
        print('  FOUT niet gewijzigd terwijl verwacht: %s' % sorted(ontbrekend)); fouten += 1
    if not onverwacht and not ontbrekend:
        print('  precies de %d verwachte bestanden gewijzigd, de rest byte-identiek'
              % len(VERWACHT_GEWIJZIGD))

verwijderd = {f for f in os.listdir(OUD_DIR) if f.endswith('.html')} - set(html)
for f in sorted(verwijderd):
    print('  verwijderd: %s' % f)
if not ZONDER_RELEASE and verwijderd != VERWACHT_VERWIJDERD:
    print('  FOUT verwijderd %s, verwacht %s' % (sorted(verwijderd), sorted(VERWACHT_VERWIJDERD)))
    fouten += 1

print('\n== gedeelde blokken byte-identiek ==')


def blok(pad, start, eind):
    s = io.open(pad, encoding='utf-8').read()
    i = s.index(start)
    j = s.index(eind, i) + len(eind)
    return hashlib.md5(s[i:j].encode()).hexdigest()[:8]


groepen = [
    ('HIGHWAY_RE', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                    'pocket_count.html', 'telreconstructie.html', 'snaptrace.html'],
     "var HIGHWAY_RE = '", "corridor';"),
    ('OVP-blok', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                  'pocket_count.html', 'telreconstructie.html', 'telrapport.html',
                  'telplanning.html'],   # telplanning sinds v3.9
     '/* ---- Overpass-antwoord classificeren (v2.49)',
     'function ovpBackoffMs(n) { return Math.min(500 * Math.pow(2, Math.max(0, n - 1)), 8000); }'),
    ('leesTegels', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                    'pocket_count.html'],
     '/* ---- Tegel-cache LEZEN (v2.49)', '  });\n}'),
    ('fetch-discipline', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'],
     '/* ---- fetch-discipline (v2.49)', '\n// Verwerk een netwerk'),
    ('overpassFetch', ['telrapport.html', 'telreconstructie.html'],
     '/* ---- overpassFetch: gedeeld transport (v2.50)', '  tryOnce();\n}'),
    ('RECON-kern', ['telreconstructie.html'],
     'var RECON = (function () {', '\n})();'),
    ('MATCHER', ['telreconstructie.html'],
     'var MATCHER = (function () {', '\n})();'),
    ('OSMCACHE', ['telreconstructie.html'],
     'var OSMCACHE = (function () {', '\n})();'),
    ('splitWayIntoSegments', ['telreconstructie.html', 'pocket_count.html', 'telrapport.html'],   # telrapport sinds v3.21
     'function splitWayIntoSegments(geom) {', '\n}'),
    # v2.72: doortellen na herstel, gedeeld door de drie parkeer-apps
    ('hervatSessie', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'],
     '/* ── Doortellen na herstel (v2.72) ──', '/* ── einde gedeeld blok doortellen ── */'),
    # v2.77: ZIP bewaren met bevestiging, gedeeld door de drie parkeer-apps; sinds v3.22 ook Static
    ('bewaarZip', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                   'traffic_counter.html'],
     '/* ── ZIP bewaren (v2.77) ──', '/* ── einde gedeeld blok ZIP bewaren ── */'),
    ('cacheWaysInTiles', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                          'pocket_count.html'],
     '// Bewaar ways per tegel',   # v3.20: vanaf het commentaar, met _tileCov en tegelsVanWeg
     '  } catch (e) { /* cache is best-effort: nooit het tellen verstoren */ }\n}'),
    # v3.4: GPX-tijd in echte UTC, gedeeld door de drie parkeer-apps
    ('GPX-tijd', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'],
     '/* ── GPX-tijd (v3.4) ── */', '/* ── einde gedeeld blok GPX-tijd ── */'),
    # v3.8: noodkopie met één eigenaar, gedeeld door de vijf veld-apps
    ('noodkopie', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                   'pocket_count.html', 'traffic_counter.html'],
     '/* ── Noodkopie: één venster schrijft (v3.8)', '/* ── einde gedeeld blok noodkopie ── */'),
    ('noodkopie-haken', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'],
     '/* ── Noodkopie: haken parkeer-apps (v3.8) ── */', '/* ── einde haken noodkopie ── */'),
    # v3.22: één herstelmelding voor de vijf veld-apps, met de haken van de parkeer-apps
    ('herstelmelding', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                        'pocket_count.html', 'traffic_counter.html'],
     '/* ── Herstelmelding (v3.22)', '/* ── einde gedeeld blok herstelmelding ── */'),
    ('herstel-haken', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html'],
     '/* ── Herstelmelding: haken parkeer-apps (v3.22) ── */', '/* ── einde haken herstelmelding ── */'),
    # v3.30: de SHA-256 van de ZIP na het opslaan, met een mail-knop
    ('vingerafdruk', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                      'pocket_count.html', 'traffic_counter.html'],
     '/* ── Vingerafdruk (v3.30)', '/* ── einde gedeeld blok vingerafdruk ── */'),
    # v3.29: één regel bij de ZIP-knop over delen (je plek; thuis je huis)
    ('deelwaarschuwing', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                          'pocket_count.html', 'traffic_counter.html'],
     '/* ── Deelwaarschuwing (v3.29)', '/* ── einde gedeeld blok deelwaarschuwing ── */'),
    # v3.27: oude tegels uit de cache, in elk bestand dat de tegelcache gebruikt
    ('tegels opruimen', ['parkeertelling.html', 'fietsparkeren.html', 'capaciteitstelling.html',
                         'pocket_count.html', 'telreconstructie.html'],
     '/* ── Tegels opruimen (v3.27)', '/* ── einde gedeeld blok tegels opruimen ── */'),
    # v3.14: planning als link, inpakken en uitpakken
    ('planlink', ['telplanning.html', 'parkeertelling.html', 'fietsparkeren.html', 'pocket_count.html'],
     '/* ── Planning als link (v3.14) ──', '/* ── einde gedeeld blok planlink ── */'),
    # v3.19: het geplande gebied vooraf in de tegelcache, in de apps die een planning-link openen
    ('gebied vooraf', ['parkeertelling.html', 'fietsparkeren.html', 'pocket_count.html'],
     '/* ── Gebied vooraf ophalen (v3.19)', '/* ── einde gedeeld blok gebied vooraf ── */'),
    # v3.33: de clusterbol (taart per soort) van telrapport, ook op de kaart van Archief
    ('clusterbol', ['telrapport.html', 'telarchief.html'],
     '/* ── Clusterbol (v2.61)', "       + cijfer + '\">' + total + '</div></div>';\n}"),
    # v3.3: de kale stijl van de documentatiepagina's
    ('kale stijl', KAAL,
     '/* ── kale stijl (v3.3)', '/* ── einde kale stijl ── */'),
]
for naam, bestanden, a, z in groepen:
    h = {blok(os.path.join(NIEUW_DIR, f), a, z) for f in bestanden}
    ok = len(h) == 1
    print('  %-18s %d bestanden  %s  %s' % (naam, len(bestanden),
                                            list(h)[0] if ok else sorted(h),
                                            'OK' if ok else 'DRIFT'))
    if not ok:
        fouten += 1

print('\n== documentatiepagina\'s kaal ==')
# v3.3: één <style>, dat begint met het gedeelde blok; daarna hooguit een paar
# regels die de pagina functioneel nodig heeft. Geen Google Fonts, geen style=""
# behalve een kleur in een kleurstaal of een verborgen plaatshouder.
for f in KAAL:
    s = io.open(os.path.join(NIEUW_DIR, f), encoding='utf-8').read()
    stijlen = re.findall(r'<style>\s*(.*?)</style>', s, re.S)
    rest = stijlen[0].split('/* ── einde kale stijl ── */', 1)[-1].strip() if stijlen else ''
    los = [x for x in re.findall(r'style="([^"]*)"', s)
           if not re.fullmatch(r'background:[^;]+(;border:2px solid [^;]+)?|background:none;border:2px solid [^;]+|display:none', x)]
    problemen = []
    if len(stijlen) != 1 or not stijlen[0].startswith('/* ── kale stijl (v3.3)'):
        problemen.append('%d <style>-blokken, of niet beginnend met het gedeelde blok' % len(stijlen))
    if len(rest.splitlines()) > 5:
        problemen.append('%d regels eigen CSS na het gedeelde blok' % len(rest.splitlines()))
    if re.search(r'(@import|<link)[^;>]*fonts\.googleapis', s):   # privacy.html noemt het domein wel
        problemen.append('Google Fonts')
    if los:
        problemen.append('style="" met opmaak: %s' % los[:3])
    print('  %-26s %s' % (f, 'FOUT ' + '; '.join(problemen) if problemen else 'OK'))
    fouten += len(problemen)

print('\n== gedeelde constanten (waarde) ==')
# Constanten die per bestand een eigen naam dragen maar dezelfde waarde moeten
# hebben. Geen blok-md5 zoals hierboven: de namen verschillen (SIDE_OFFSET_M in
# de veld-apps, OFFSET_M in telrapport en de reconstructor). Precies één
# declaratie per bestand, anders is de controle zelf niet te vertrouwen.
constanten = [
    ('zijde-offset', [('parkeertelling.html', 'SIDE_OFFSET_M'),
                      ('fietsparkeren.html', 'SIDE_OFFSET_M'),
                      ('capaciteitstelling.html', 'SIDE_OFFSET_M'),
                      ('telreconstructie.html', 'OFFSET_M'),
                      ('telrapport.html', 'OFFSET_M')]),
    # v3.19: verversafstand van het wegennet (pocket heeft een eigen: SNAP_ROAD_VERVERS_M)
    ('verversafstand', [('parkeertelling.html', 'ROAD_CACHE_DIST'),
                        ('fietsparkeren.html', 'ROAD_CACHE_DIST'),
                        ('capaciteitstelling.html', 'ROAD_CACHE_DIST')]),
    # v3.22: kleur per voertuigtype in Static gelijk aan telrapport
    ('typekleuren', [('traffic_counter.html', 'TYPE_KLEUR'),
                     ('telrapport.html', 'SS_TYPE_COLOR')]),
]
for naam, plekken in constanten:
    waarden = {}
    for f, var in plekken:
        s = io.open(os.path.join(NIEUW_DIR, f), encoding='utf-8').read()
        hits = re.findall(r'\b(?:var|let|const)\s+' + var + r'\s*=\s*([^;\n]+);', s)
        if len(hits) != 1:
            print('  %-18s FOUT %s: %d declaraties van %s' % (naam, f, len(hits), var))
            fouten += 1
            continue
        waarden[f] = hits[0].strip()
    ok = len(set(waarden.values())) == 1 and len(waarden) == len(plekken)
    print('  %-18s %d bestanden  %s  %s' % (naam, len(plekken),
                                            sorted(set(waarden.values())),
                                            'OK' if ok else 'DRIFT ' + str(waarden)))
    if not ok:
        fouten += 1

print('\n== releasenummer ==')
# Het nummer onderaan index.html is wat je op de telefoon ziet. Het moet gelijk
# zijn aan RELEASE, hoger dan in de vorige release, en de stand van zaken en de
# overdracht moeten hetzelfde nummer dragen. Vergeten op te hogen valt zo op.
def versie_op_index(map_):
    pad = os.path.join(map_, 'index.html')
    if not os.path.exists(pad):
        return []
    return re.findall(r'<div class="versie">(v\d+\.\d+)</div>', io.open(pad, encoding='utf-8').read())

def als_getal(v):
    return tuple(int(x) for x in v[1:].split('.'))

nieuw_v, oud_v = versie_op_index(NIEUW_DIR), versie_op_index(OUD_DIR)
if ZONDER_RELEASE:
    # Geen release: het nummer blijft wat het was, en verder is er niets te toetsen.
    if nieuw_v != oud_v:
        print('  FOUT VALIDEER_ZONDER_RELEASE, maar index.html ging van %s naar %s' % (oud_v, nieuw_v))
        fouten += 1
    else:
        print('  geen release: index.html houdt %s' % (nieuw_v[0] if nieuw_v else '?'))
else:
    if nieuw_v != [RELEASE]:
        print('  FOUT index.html toont %s, verwacht precies [%s]' % (nieuw_v, RELEASE))
        fouten += 1
    else:
        print('  index.html          %s' % RELEASE)
    if oud_v and als_getal(oud_v[0]) >= als_getal(RELEASE):
        print('  FOUT niet opgehoogd: vorige release toonde al %s' % oud_v[0])
        fouten += 1
    elif oud_v:
        print('  vorige release      %s' % oud_v[0])
    stand = io.open(os.path.join(NIEUW_DIR, 'OVERDRACHT_STAND_VAN_ZAKEN.md'), encoding='utf-8').read()
    if ('**Laatste release: %s.**' % RELEASE) in stand:
        print('  stand van zaken     %s' % RELEASE)
    else:
        print('  FOUT stand van zaken noemt niet "Laatste release: %s."' % RELEASE)
        fouten += 1
    overdracht = 'overdracht_%s.md' % RELEASE.replace('.', '_')
    if os.path.exists(os.path.join(NIEUW_DIR, overdracht)):
        print('  overdracht          %s' % overdracht)
    else:
        print('  FOUT %s ontbreekt' % overdracht)
        fouten += 1

print('\n== versiestempel reconstructor ==')
# v2.74: RECON_VERSIE in telreconstructie.html is de release waarin de
# reconstructor voor het laatst veranderde. Veranderd bestand -> stempel gelijk
# aan RELEASE; onveranderd -> stempel niet hoger dan RELEASE.
# v3.6: de <head> telt niet mee. Een andere titel of description verandert de
# reconstructor niet, en de stempel komt in elke gereconstrueerde ZIP.
def recon_stempel(map_):
    pad = os.path.join(map_, 'telreconstructie.html')
    if not os.path.exists(pad):
        return None, None
    tekst = io.open(pad, encoding='utf-8').read()
    zonder_kop = re.sub(r'<head>.*?</head>', '<head></head>', tekst, count=1, flags=re.S)
    return zonder_kop, re.findall(r"^var RECON_VERSIE = '(v\d+\.\d+)';$", tekst, re.M)
t_nieuw, st_nieuw = recon_stempel(NIEUW_DIR)
t_oud, _ = recon_stempel(OUD_DIR)
if t_nieuw is not None:
    if len(st_nieuw) != 1:
        print('  FOUT verwacht precies één RECON_VERSIE, gevonden %s' % st_nieuw); fouten += 1
    elif t_nieuw != t_oud and ZONDER_RELEASE:
        print('  FOUT telreconstructie.html is gewijzigd zonder release; RECON_VERSIE moet mee met een nieuw nummer'); fouten += 1
    elif t_nieuw != t_oud and st_nieuw[0] != RELEASE:
        print('  FOUT telreconstructie.html is gewijzigd, maar RECON_VERSIE = %s (verwacht %s)' % (st_nieuw[0], RELEASE)); fouten += 1
    elif als_getal(st_nieuw[0]) > als_getal(RELEASE):
        print('  FOUT RECON_VERSIE %s is hoger dan de release %s' % (st_nieuw[0], RELEASE)); fouten += 1
    else:
        print('  RECON_VERSIE %s (%s)' % (st_nieuw[0], 'bijgewerkt in deze release' if t_nieuw != t_oud else 'ongewijzigd bestand'))

print('\n== privacyverklaring dekt alle externe domeinen ==')
# v2.75: elk extern domein dat een pagina aanspreekt, moet in privacy.html staan
# (als <span class="domein">). Een nieuwe dienst zonder vermelding is een fout:
# dan belooft de verklaring minder dan de site doet.
# Uitgezonderd: alleen links of verwijzingen, geen verzoek vanuit de browser.
GEEN_VERZOEK = {'telonline.org', 'schema.org', 'www.openstreetmap.org', 'open-meteo.com',
                'github.com'}   # v3.4: link naar de broncode in verantwoording.html
priv_pad = os.path.join(NIEUW_DIR, 'privacy.html')
if not os.path.exists(priv_pad):
    print('  FOUT privacy.html ontbreekt'); fouten += 1
else:
    priv = io.open(priv_pad, encoding='utf-8').read()
    vermeld = set(re.findall(r'<span class="domein">([a-z0-9.-]+)</span>', priv))
    gebruikt = {}
    for f in sorted(x for x in os.listdir(NIEUW_DIR) if x.endswith('.html')):
        for host in re.findall(r'https://([a-zA-Z0-9{}.-]+)', io.open(os.path.join(NIEUW_DIR, f), encoding='utf-8').read()):
            host = re.sub(r'^\{[a-z]\}\.', '', host.lower()).rstrip('.')
            if not host or '.' not in host or host in GEEN_VERZOEK:
                continue
            gebruikt.setdefault(host, set()).add(f)
    ontbreekt = {h: b for h, b in gebruikt.items() if not any(h == v or h.endswith('.' + v) for v in vermeld)}
    for h in sorted(ontbreekt):
        print('  FOUT %s (in %s) staat niet in privacy.html' % (h, ', '.join(sorted(ontbreekt[h]))))
    fouten += len(ontbreekt)
    if not ontbreekt:
        print('  %d externe domeinen in de code, alle vermeld (%d vermeldingen)' % (len(gebruikt), len(vermeld)))
    # Nog in te vullen plekken: waarschuwing, geen fout (Jay levert de gegevens aan)
    for k in re.findall(r'data-invullen="([a-z]+)"', priv):
        print('  LET OP privacy.html: "%s" nog invullen vóór het online gaat' % k)

print('\n== titel, description, canonical (publieke pagina\'s) ==')
# v3.6: elke publieke pagina (alles behalve NIET_IN_SITEMAP, bovenaan) heeft
#  - een <title> van hooguit 65 tekens;
#  - een meta description van 70 tot en met 160 tekens;
#  - een canonical op https://telonline.org/<bestand> (index.html: https://telonline.org/);
#  - als er een og:title is: gelijk aan de titel zonder " | telonline.org".
# Gemeten in tekens na het omzetten van entiteiten (&amp; telt als één teken).
class Kop(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titel, self.meta, self.links, self._in_titel, self.klaar = None, {}, {}, False, False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'body': self.klaar = True
        if self.klaar: return
        if tag == 'title': self._in_titel, self.titel = True, ''
        elif tag == 'meta':
            sleutel = a.get('name') or a.get('property')
            if sleutel and sleutel not in self.meta: self.meta[sleutel] = a.get('content', '')
        elif tag == 'link' and a.get('rel') == 'canonical': self.links['canonical'] = a.get('href', '')
    def handle_endtag(self, tag):
        if tag == 'title': self._in_titel = False
    def handle_data(self, data):
        if self._in_titel and not self.klaar: self.titel += data

TITEL_MAX, DESC_MIN, DESC_MAX = 65, 70, 160
for f in sorted(set(html) - NIET_IN_SITEMAP):
    k = Kop(); k.feed(io.open(os.path.join(NIEUW_DIR, f), encoding='utf-8').read())
    titel = (k.titel or '').strip()
    desc = k.meta.get('description', '').strip()
    canon = k.links.get('canonical', '')
    verwacht = 'https://telonline.org/' + ('' if f == 'index.html' else f)
    problemen = []
    if not titel: problemen.append('geen <title>')
    elif len(titel) > TITEL_MAX: problemen.append('titel %d tekens (max %d)' % (len(titel), TITEL_MAX))
    if not desc: problemen.append('geen meta description')
    elif not DESC_MIN <= len(desc) <= DESC_MAX: problemen.append('description %d tekens (%d-%d)' % (len(desc), DESC_MIN, DESC_MAX))
    if canon != verwacht: problemen.append('canonical %r, verwacht %r' % (canon, verwacht))
    og = k.meta.get('og:title')
    if og is not None and og.strip() != re.sub(r' \| telonline\.org$', '', titel):
        problemen.append('og:title %r wijkt af van de titel' % og)
    print('  %-26s %s' % (f, ('FOUT ' + '; '.join(problemen)) if problemen
                          else 'OK  titel %2d, description %3d' % (len(titel), len(desc))))
    fouten += len(problemen)

print('\n== sitemap en robots.txt ==')
# Sinds 10 okt 2026 (na v3.3). De sitemap noemde na de verhuizing nog rvmk.nl,
# en dat bestand gaat met elke release-ZIP mee naar de server. Elk adres moet op
# telonline.org staan, naar een bestand in de release wijzen en één keer
# voorkomen ('/' is index.html). Een pagina die er niet in staat is een
# waarschuwing: zet hem in de sitemap, of bovenaan in NIET_IN_SITEMAP als hij intern is.
sm_pad = os.path.join(NIEUW_DIR, 'sitemap.xml')
if not os.path.exists(sm_pad):
    print('  FOUT sitemap.xml ontbreekt'); fouten += 1
else:
    import xml.etree.ElementTree as ET
    try:
        ET.parse(sm_pad)
        locs = re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', io.open(sm_pad, encoding='utf-8').read())
    except ET.ParseError as e:
        print('  FOUT sitemap.xml is geen geldige XML: %s' % e); fouten += 1
        locs = []
    voor = fouten
    paden = []
    for u in locs:
        m = re.fullmatch(r'https://telonline\.org/([^?#]*)', u)
        if not m:
            print('  FOUT %s staat niet op https://telonline.org/' % u); fouten += 1
            continue
        f = m.group(1) or 'index.html'
        if not os.path.exists(os.path.join(NIEUW_DIR, f)):
            print('  FOUT %s: %s zit niet in de release' % (u, f)); fouten += 1
        paden.append(f)
    dubbel = sorted({f for f in paden if paden.count(f) > 1})
    if dubbel:
        print('  FOUT dubbel in de sitemap: %s' % ', '.join(dubbel)); fouten += 1
    if fouten == voor and locs:
        print('  sitemap.xml         %d adressen, alle op telonline.org en in de release' % len(locs))
    for f in sorted(set(html) - set(paden) - NIET_IN_SITEMAP):
        print('  LET OP %s staat niet in de sitemap (of hoort in NIET_IN_SITEMAP)' % f)
rb_pad = os.path.join(NIEUW_DIR, 'robots.txt')
if not os.path.exists(rb_pad):
    print('  FOUT robots.txt ontbreekt'); fouten += 1
elif not re.search(r'(?mi)^Sitemap:\s*https://telonline\.org/sitemap\.xml\s*$', io.open(rb_pad, encoding='utf-8').read()):
    print('  FOUT robots.txt verwijst niet naar https://telonline.org/sitemap.xml'); fouten += 1
else:
    print('  robots.txt          verwijst naar de sitemap')

print('\n%s' % ('ALLES OK' if fouten == 0 else '%d PROBLEMEN' % fouten))
sys.exit(1 if fouten else 0)
