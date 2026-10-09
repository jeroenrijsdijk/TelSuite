#!/usr/bin/env python3
"""Vergelijkt de tekst van twee HTML-bestanden, woord voor woord (v3.3).

Bedoeld voor opmaakwijzigingen: andere tags, andere CSS, dezelfde woorden.
Telt mee: alle tekst in <title> en <body>, ook verborgen tekst. Telt niet mee:
<script>, <style>, witruimte, en de tekens in --negeer (standaard · — ( )),
die bij het omzetten als scheiding tussen losse onderdelen kunnen ontstaan.

    python3 tekstgelijk.py oud.html nieuw.html [--negeer "·—()*"]

Uitvoer: OK met het aantal woorden, of de eerste verschillen met context.
Exitcode 0 als gelijk, 1 als niet.
"""
import difflib, sys
from html.parser import HTMLParser

STANDAARD_NEGEER = '·—()'


class Tekst(HTMLParser):
    OVERSLAAN = {'script', 'style'}
    # binnen een regel: deze tags scheiden geen woorden; alle andere wel
    INLINE = {'a', 'abbr', 'b', 'code', 'em', 'i', 'kbd', 'mark', 'samp', 'small',
              'span', 'strong', 'sub', 'sup', 'u'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.delen, self.diepte = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.OVERSLAAN:
            self.diepte += 1
        if tag not in self.INLINE:
            self.delen.append(' ')

    def handle_endtag(self, tag):
        if tag in self.OVERSLAAN and self.diepte:
            self.diepte -= 1
        if tag not in self.INLINE:
            self.delen.append(' ')

    def handle_data(self, data):
        if not self.diepte:
            self.delen.append(data)


def woorden(pad, negeer):
    p = Tekst()
    p.feed(open(pad, encoding='utf-8').read())
    tekst = ''.join(p.delen)
    for t in negeer:
        tekst = tekst.replace(t, ' ')
    return tekst.split()


def vergelijk(oud, nieuw, negeer=STANDAARD_NEGEER):
    """Geeft (gelijk, n_oud, n_nieuw, verschillen) terug."""
    a, b = woorden(oud, negeer), woorden(nieuw, negeer)
    verschillen = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != 'equal':
            ctx = ' '.join(a[max(0, i1 - 6):i1])
            verschillen.append((op, ctx, ' '.join(a[i1:i2]), ' '.join(b[j1:j2])))
    return not verschillen, len(a), len(b), verschillen


def main(argv):
    args = [x for x in argv if x != '--negeer']
    negeer = STANDAARD_NEGEER
    if '--negeer' in argv:
        negeer = argv[argv.index('--negeer') + 1]
        args.remove(negeer)
    oud, nieuw = args[:2]
    gelijk, na, nb, verschillen = vergelijk(oud, nieuw, negeer)
    if gelijk:
        print(f'OK  {nieuw}: {na} woorden, gelijk aan {oud}')
        return 0
    print(f'VERSCHIL  {oud} ({na} woorden) <> {nieuw} ({nb} woorden), {len(verschillen)} plek(ken):')
    for op, ctx, x, y in verschillen[:20]:
        print(f'  [{op}] na "…{ctx}": oud «{x}»  nieuw «{y}»')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
