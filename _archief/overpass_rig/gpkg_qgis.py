#!/usr/bin/env python3
"""v3.1 — opent een GeoPackage uit telrapport in QGIS (zonder scherm) en meldt
wat QGIS ervan maakt: per laag geldig of niet, aantal objecten, het soort
opmaak, de categorieën met hun kleur, het taartdiagram en de labels. Met een
tweede argument rendert hij de kaart ook naar een PNG.

Wordt aangeroepen door gpkgtest.py, met de Python waarin PyQGIS draait:
    python3.12 _archief/overpass_rig/gpkg_qgis.py bestand.gpkg [kaart.png]
Uitvoer: één regel JSON op stdout.
"""
import json, os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qgis.core import (QgsApplication, QgsVectorLayer, QgsMapSettings, QgsMapRendererSequentialJob,
                       QgsRectangle, QgsCoordinateReferenceSystem, QgsProject)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor

app = QgsApplication([], False)
app.initQgis()
pad = sys.argv[1]
uit = {'qgis': app.version() if hasattr(app, 'version') else '', 'lagen': {}}
from qgis.core import Qgis
uit['qgis'] = Qgis.QGIS_VERSION

lagen = {}
for naam in ['waarnemingen', 'clusters', 'wegvakken', 'route', 'sessies', 'export_info']:
    l = QgsVectorLayer(pad + '|layername=' + naam, naam, 'ogr')
    if not l.isValid():
        uit['lagen'][naam] = {'geldig': False}
        continue
    r = l.renderer()
    info = {'geldig': True, 'aantal': l.featureCount(), 'crs': l.crs().authid(),
            'opmaak': r.type() if r else None, 'labels': l.labelsEnabled()}
    if r and r.type() == 'categorizedSymbol':
        info['veld'] = r.classAttribute()
        info['categorieen'] = [[c.value(), c.label(), c.symbol().color().name()] for c in r.categories()]
    d = l.diagramRenderer()
    if d:
        ds = d.diagramSettings()[0]
        info['diagram'] = {'soort': d.rendererName(), 'velden': list(ds.categoryAttributes),
                           'kleuren': [c.name() for c in ds.categoryColors]}
    uit['lagen'][naam] = info
    lagen[naam] = l

if len(sys.argv) > 2:
    volgorde = [lagen[n] for n in ['clusters', 'waarnemingen', 'route', 'wegvakken'] if n in lagen]
    for l in volgorde:
        QgsProject.instance().addMapLayer(l)
    # Inzoomen op de telling zelf (stippen, bollen, route), niet op het hele
    # opgehaalde wegennet: dat is wat je na "zoom naar laag" wilt zien.
    ext = QgsRectangle()
    for l in [lagen[n] for n in ['waarnemingen', 'clusters', 'route'] if n in lagen] or volgorde:
        ext.combineExtentWith(l.extent())
    ext.scale(1.4)
    ms = QgsMapSettings()
    ms.setLayers(volgorde)
    ms.setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:3857'))
    ms.setOutputSize(QSize(1400, 1000))
    ms.setOutputDpi(96)
    ms.setBackgroundColor(QColor('#f2efe9'))
    from qgis.core import QgsCoordinateTransform
    tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'), ms.destinationCrs(), QgsProject.instance())
    ms.setExtent(tr.transformBoundingBox(ext))
    job = QgsMapRendererSequentialJob(ms)
    job.start(); job.waitForFinished()
    uit['png'] = job.renderedImage().save(sys.argv[2], 'PNG')

print(json.dumps(uit))
