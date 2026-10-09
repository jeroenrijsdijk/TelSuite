#!/usr/bin/env python3
"""v3.1 — opent een GeoPackage uit telrapport in QGIS (zonder scherm) en meldt
wat QGIS ervan maakt: per laag geldig of niet, aantal objecten, het soort
opmaak, de categorieën met hun kleur, het taartdiagram en de labels. Met een
tweede argument rendert hij de kaart ook naar een PNG.

v3.2 — staat er een project in (qgis_projects), dan kopieert hij het bestand
naar een andere map (zelfde naam), opent het project daar en meldt: CRS,
lagenboom, geldigheid en id's, standaardbeeld, de opmaak (onderdelen, schaal,
kaartbeeld, legenda). Met een derde argument exporteert hij de opmaak als PNG.
Hernoemd openen wordt ook geprobeerd en gemeld (bekende beperking van QGIS).

Wordt aangeroepen door gpkgtest.py, met de Python waarin PyQGIS draait:
    python3.12 _archief/overpass_rig/gpkg_qgis.py bestand.gpkg [kaart.png [opmaak.png]]
Uitvoer: één regel JSON op stdout.
"""
import json, os, shutil, sqlite3, sys, tempfile
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
    if l.labelsEnabled() and l.labeling():
        ls = l.labeling().settings()
        info['label'] = {'veld': ls.fieldName, 'expressie': ls.isExpression, 'html': ls.format().allowHtmlFormatting()}
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

# ── v3.2: het project in de GeoPackage
RD_PUNTEN = [[51.85, 4.30], [53.2, 6.56], [50.85, 5.69], [52.37, 4.89], [51.44, 3.57]]
from qgis.core import (QgsCoordinateTransform, QgsPointXY, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemLabel, QgsLayoutExporter)
wgs, rdcrs = QgsCoordinateReferenceSystem('EPSG:4326'), QgsCoordinateReferenceSystem('EPSG:28992')
naar_rd = QgsCoordinateTransform(wgs, rdcrs, QgsProject.instance())
uit['rd_punten'] = [[naar_rd.transform(QgsPointXY(lo, la)).x(), naar_rd.transform(QgsPointXY(lo, la)).y()] for la, lo in RD_PUNTEN]
db = sqlite3.connect(pad)
heeft = db.execute("select count(*) from sqlite_master where name='qgis_projects'").fetchone()[0]
namen = [r[0] for r in db.execute('select name from qgis_projects')] if heeft else []
db.close()
if namen:
    data = QgsRectangle()
    for n in ['waarnemingen', 'clusters', 'route']:
        if n in lagen: data.combineExtentWith(lagen[n].extent())
    data_rd = naar_rd.transformBoundingBox(data)
    QgsProject.instance().clear()
    elders = tempfile.mkdtemp()
    kopie = os.path.join(elders, os.path.basename(pad)); shutil.copy(pad, kopie)
    pr = QgsProject.instance()
    pj = {'namen': namen, 'gelezen': pr.read('geopackage:' + kopie + '?projectName=' + namen[0])}
    pj['crs'] = pr.crs().authid()
    pj['boom'] = [[n.name(), n.isVisible()] for n in pr.layerTreeRoot().findLayers()]
    pj['groepen'] = [g.name() for g in pr.layerTreeRoot().findGroups()]
    pj['lagen'] = {l.id(): {'naam': l.name(), 'geldig': l.isValid(), 'bron': l.source(), 'aanbieder': l.providerType(),
                            'opmaak': (l.renderer().type() if l.type() == 0 and l.renderer() else None),
                            'diagram': bool(l.diagramRenderer()) if l.type() == 0 else None}
                   for l in pr.mapLayers().values()}
    v = pr.viewSettings().defaultViewExtent()
    pj['beeld_bevat_data'] = v.contains(data_rd)
    lay = pr.layoutManager().layoutByName('A4 liggend')
    if lay:
        items = [i for i in lay.items() if hasattr(i, 'uuid')]
        soort = lambda k: [i for i in items if isinstance(i, k)]
        m = soort(QgsLayoutItemMap)[0]
        lg = soort(QgsLayoutItemLegend)
        pj['opmaak'] = {'kaarten': len(soort(QgsLayoutItemMap)), 'legendas': len(lg), 'schaalstokken': len(soort(QgsLayoutItemScaleBar)),
                        'plaatjes': len(soort(QgsLayoutItemPicture)), 'labels': sorted(l.text() for l in soort(QgsLayoutItemLabel)),
                        'schaal': round(m.scale()), 'kaart_crs': m.crs().authid(), 'kaart_bevat_data': m.extent().contains(data_rd),
                        'legenda': [n.name() for n in lg[0].model().rootGroup().findLayers()] if lg else [],
                        'legenda_gekoppeld': all(n.layer() is not None for n in lg[0].model().rootGroup().findLayers()) if lg else False}
        if len(sys.argv) > 3:
            st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 110
            pj['opmaak']['png'] = QgsLayoutExporter(lay).exportToImage(sys.argv[3], st) == QgsLayoutExporter.Success
    else:
        pj['opmaak'] = None
    # Hernoemd: bekende beperking, alleen melden.
    QgsProject.instance().clear()
    anders = os.path.join(elders, 'hernoemd.gpkg'); os.rename(kopie, anders)
    QgsProject.instance().read('geopackage:' + anders + '?projectName=' + namen[0])
    pj['hernoemd_geldig'] = sum(1 for l in QgsProject.instance().mapLayers().values() if l.providerType() == 'ogr' and l.isValid())
    uit['project'] = pj

print(json.dumps(uit))
