#!/usr/bin/env python3
"""Houdt zip_format_reference.html tegen de exportcode.

Twee kanten op:
  1. elke kopregel in de referentie moet letterlijk in een app voorkomen
  2. elke kopregel in de code moet in de referentie staan, tenzij bewust
     overgeslagen (diagnostiek) of alleen nog leesbaar (geen producerende tool)

Draaien vanuit de suite-map:  python3 _archief/overpass_rig/test_zipref.py
"""
import io, os, re, sys

HIER = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.abspath(os.path.join(HIER, '..', '..'))

APPS = ['traffic_counter.html', 'parkeertelling.html', 'fietsparkeren.html',
        'capaciteitstelling.html', 'pocket_count.html', 'telreconstructie.html']
REF = 'zip_format_reference.html'

# Bewust niet beschreven: diagnostiek. De kolommen veranderen met de
# snap-engine en zijn niet bedoeld voor verwerking.
DIAGNOSTIEK = ['sessie_id;seq;tijdstip;event;']

# Beschreven in de referentie maar door geen enkele app meer gebouwd. Het losse
# transect-formaat (*_trn.zip) is vervangen door pocket's transect-modus
# (*_pkt_t.zip); telrapport leest het nog. De sectie blijft tot besloten is of
# het archief ook hier is omgezet.
ALLEEN_NOG_LEESBAAR = ['sessie_id;nr;tijdstip;type;richting;lat;lon;nauwkeurigheid']


def lees(naam):
    with io.open(os.path.join(SUITE, naam), encoding='utf-8') as f:
        return f.read()


def is_kop(regel):
    return (regel.startswith('sessie_id;') or regel.startswith('osm_way_id;')) \
        and not re.search(r'\d\.\d', regel)


def ref_kopregels():
    """(titel, kopregel) voor ELKE kopregel in elk csv-sample-blok."""
    uit = []
    for titel, sample in re.findall(
            r'<div class="csv-title">(.*?)</div>\s*<div class="csv-sample">(.*?)</div>',
            lees(REF), re.S):
        titel = re.sub(r'<[^>]*>', '', titel).strip()
        for regel in sample.split('\n'):
            regel = regel.strip()
            if is_kop(regel):
                uit.append((titel, regel))
    return uit


def code_kopregels():
    uit = {}
    for f in APPS:
        s = lees(f)
        for h in set(re.findall(r"'((?:sessie_id|osm_way_id);[^']{5,300})'", s)):
            uit.setdefault(h.replace('\\n', ''), []).append(f)
    # telreconstructie stelt de wandel-kopregel samen: basis + (';richting;'|';') + kwal.
    # Die staat dus nergens als één string; hier bouwen we 'm net zo op.
    s = lees('telreconstructie.html')
    b = re.search(r"var basis\s*=\s*'([^']+)'", s)
    k = re.search(r"var kwal\s*=\s*'([^']+)'", s)
    if b and k:
        for sep in (';richting;', ';'):
            uit.setdefault(b.group(1) + sep + k.group(1), []).append(
                'telreconstructie.html (samengesteld)')
    return uit


fouten = 0
ref = ref_kopregels()
code = code_kopregels()
ref_koppen = {k for _, k in ref}

print('== kopregels in de referentie die de code niet kent ==')
for titel, kop in ref:
    if kop in code:
        print('  OK   %-44s %s' % (titel[:44], ', '.join(code[kop])))
    elif kop in ALLEEN_NOG_LEESBAAR:
        print('  ---  %-44s geen producerende tool meer, alleen lezen' % titel[:44])
    else:
        print('  FOUT %-44s %s' % (titel[:44], kop[:110]))
        fouten += 1

print('\n== kopregels in de code die de referentie niet beschrijft ==')
for kop, bestanden in sorted(code.items()):
    if kop in ref_koppen:
        continue
    if any(kop.startswith(d) for d in DIAGNOSTIEK):
        print('  ---  diagnostiek, bewust overgeslagen: %s' % kop[:66])
        continue
    # Een string die het begin is van een beschreven kopregel is een bouwsteen
    # (telreconstructie stelt zijn walk-header samen uit basis + kwal).
    if any(k.startswith(kop + ';') for k in ref_koppen):
        print('  ---  bouwsteen van een beschreven kopregel: %s' % kop[:66])
        continue
    print('  FOUT niet beschreven (%s): %s' % (', '.join(bestanden), kop[:110]))
    fouten += 1

print('\n%s' % ('REFERENTIE SLUIT AAN OP DE CODE' if fouten == 0 else '%d PROBLEMEN' % fouten))
sys.exit(1 if fouten else 0)
