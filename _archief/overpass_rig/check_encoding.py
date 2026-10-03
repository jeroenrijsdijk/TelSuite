#!/usr/bin/env python3
"""Vindt bestanden die geen geldige UTF-8 zijn.

Aanleiding: shell-heredocs sneuvelden af en toe op de eerste byte van een
multibyte-teken ("Eén" -> E\xa9n). De rest van het bestand blijft dan leesbaar,
dus het valt pas op als iets het bestand strikt probeert te lezen.

Draaien vanuit de suite-map:  python3 _archief/overpass_rig/check_encoding.py
"""
import os, sys

BINAIR = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.gpx', '.pdf', '.woff', '.woff2'}
HIER = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.abspath(os.path.join(HIER, '..', '..'))

slecht = []
for root, dirs, files in os.walk(SUITE):
    for f in files:
        p = os.path.join(root, f)
        if os.path.splitext(f)[1].lower() in BINAIR:
            continue
        b = open(p, 'rb').read()
        try:
            b.decode('utf-8')
        except UnicodeDecodeError as e:
            rel = os.path.relpath(p, SUITE)
            ctx = b[max(0, e.start - 22):e.start + 22].decode('utf-8', 'replace')
            slecht.append((rel, e.start, ctx))

for rel, pos, ctx in slecht:
    print('  FOUT %-40s byte %d  %r' % (rel, pos, ctx))
print('\n%s' % ('ALLES GELDIGE UTF-8' if not slecht else '%d BESTANDEN KAPOT' % len(slecht)))
sys.exit(1 if slecht else 0)
