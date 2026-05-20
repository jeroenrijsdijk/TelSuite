#!/usr/bin/env python3
"""
build_bezocht.py — Upgrade pocket-ZIPs naar v2.3 segment-aware formaat.

Splitst per wegvak de OSM-geometrie in segmenten van ~40m (parametrisch,
deterministisch) en hangt aan elk GPS-punt, elk tap-punt en elke visit een
segment_index. Het resultaat:

    osm_way_id + segment_index → atomaire observatie-eenheid

In-place upgrade overschrijft binnen de ZIP:
    _netwerk.csv         één rij per segment, eigen sub-LINESTRING
    _gps.csv             extra kolom segment_index
    _telregels.csv       extra kolom segment_index
    _bezocht.csv         nieuwe rij per visit op (wayId, segIdx)

Idempotent: als _netwerk.csv al een segment_index-kolom heeft, wordt de ZIP
overgeslagen tenzij --force.

Gebruik:
    python build_bezocht.py FILE_OR_DIR [...]            # default in-place
    python build_bezocht.py FILE_OR_DIR [...] --side     # los _bezocht.csv ernaast
    python build_bezocht.py FILE_OR_DIR [...] --force    # forceer her-upgrade

Drempels (identiek aan pocket_count.html):
    SEGMENT_TARGET_M    40 m  — doellengte per segment
    SEGMENT_MIN_M       60 m  — wegen korter blijven heel
    GPS_SNAP_M          15 m  — max snap-afstand GPS-punt → wegvak
    TAP_SNAP_M          50 m  — max snap-afstand tap-punt → wegvak
    MAX_GAP_SEC         30 s  — gat dat een visit breekt
    MIN_VISIT_SEC        5 s  — visits korter dan dit vervallen
    MIN_VISIT_PTS        3 pt — visits met minder GPS-punten vervallen
"""

import argparse
import csv
import io
import math
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SEGMENT_TARGET_M = 40.0
SEGMENT_MIN_M    = 60.0
GPS_SNAP_M       = 15.0
TAP_SNAP_M       = 50.0
MAX_GAP_SEC      = 30
MIN_VISIT_SEC    = 5
MIN_VISIT_PTS    = 3


# ── WKT-parser (LINESTRING) ──────────────────────────────────────────────────

WKT_LINESTRING = re.compile(r'LINESTRING\s*\(\s*(.+?)\s*\)', re.IGNORECASE)

def parse_linestring(wkt):
    """LINESTRING (lon lat, lon lat, ...) → [(lat, lon), ...]"""
    m = WKT_LINESTRING.search(wkt or '')
    if not m:
        return []
    pts = []
    for chunk in m.group(1).split(','):
        parts = chunk.strip().split()
        if len(parts) >= 2:
            try:
                lon, lat = float(parts[0]), float(parts[1])
                pts.append((lat, lon))
            except ValueError:
                continue
    return pts


# ── Geometrie / segmentatie ──────────────────────────────────────────────────

def polyline_length_m(geom):
    """Totale lengte in meters van een polyline [(lat, lon), ...]"""
    if len(geom) < 2:
        return 0.0
    LAT_M = 111320.0
    LON_M = 111320.0 * math.cos(geom[0][0] * math.pi / 180.0)
    total = 0.0
    for i in range(1, len(geom)):
        dx = (geom[i][1] - geom[i-1][1]) * LON_M
        dy = (geom[i][0] - geom[i-1][0]) * LAT_M
        total += math.hypot(dx, dy)
    return total


def split_way_into_segments(geom):
    """
    Knipt een polyline in ~SEGMENT_TARGET_M segmenten.
    Returns: lijst sub-polylines (elk [(lat, lon), ...]) — minstens één.
    Identieke logica als JS splitWayIntoSegments in pocket_count.html.
    """
    if not geom or len(geom) < 2:
        return [list(geom or [])]
    LAT_M = 111320.0
    LON_M = 111320.0 * math.cos(geom[0][0] * math.pi / 180.0)
    cum = [0.0]
    for i in range(1, len(geom)):
        dx = (geom[i][1] - geom[i-1][1]) * LON_M
        dy = (geom[i][0] - geom[i-1][0]) * LAT_M
        cum.append(cum[-1] + math.hypot(dx, dy))
    total = cum[-1]
    if total < SEGMENT_MIN_M:
        return [list(geom)]
    N = max(1, round(total / SEGMENT_TARGET_M))
    if N == 1:
        return [list(geom)]
    seg_len = total / N
    result = []
    cur = [geom[0]]
    next_cut = seg_len
    done = 0
    for j in range(1, len(geom)):
        d_start, d_end = cum[j-1], cum[j]
        edge = d_end - d_start
        while done < N - 1 and d_end >= next_cut and edge > 0:
            t = (next_cut - d_start) / edge
            cut_lat = geom[j-1][0] + t * (geom[j][0] - geom[j-1][0])
            cut_lon = geom[j-1][1] + t * (geom[j][1] - geom[j-1][1])
            cur.append((cut_lat, cut_lon))
            result.append(cur)
            cur = [(cut_lat, cut_lon)]
            next_cut += seg_len
            done += 1
        cur.append(geom[j])
    result.append(cur)
    return result


def build_mini_segs(network, ref_lat, ref_lon):
    """
    Voor elke way: projecteer alle knopen naar lokale xy en sla per OSM-edge
    de cumulatieve afstand vanaf het begin van de way op. De segment_index
    wordt later bij snap-tijd afgeleid uit de exacte snap-positie, niet uit
    een edge-midpoint — dat handelt 2-knoop-ways correct af.

    Returns: lijst dicts met ax,ay,bx,by,wid,cum_start,edge_len,seg_len,n_seg,highway,name
    """
    LAT_M = 111320.0
    LON_M = 111320.0 * math.cos(ref_lat * math.pi / 180.0)
    mini = []
    for wid, info in network.items():
        geom = info['geometry']
        if len(geom) < 2:
            continue
        xy = [(p[1] * LON_M, p[0] * LAT_M) for p in geom]
        cum = [0.0]
        for k in range(1, len(xy)):
            cum.append(cum[-1] + math.hypot(xy[k][0]-xy[k-1][0], xy[k][1]-xy[k-1][1]))
        total = cum[-1]
        n_seg = 1 if total < SEGMENT_MIN_M else max(1, round(total / SEGMENT_TARGET_M))
        seg_len = total / n_seg if n_seg > 0 else total
        for i in range(len(xy) - 1):
            mini.append({
                'wid': wid,
                'ax': xy[i][0],   'ay': xy[i][1],
                'bx': xy[i+1][0], 'by': xy[i+1][1],
                'cum_start': cum[i],
                'edge_len':  cum[i+1] - cum[i],
                'seg_len':   seg_len,
                'n_seg':     n_seg,
                'highway':   info.get('highway', ''),
                'name':      info.get('name', '')
            })
    return mini


def snap_xy(plat, plon, ref_lat):
    """Project lat/lon naar lokale xy gebaseerd op ref_lat."""
    LAT_M = 111320.0
    LON_M = 111320.0 * math.cos(ref_lat * math.pi / 180.0)
    return (plon * LON_M, plat * LAT_M)


def snap_to_minis(px, py, candidates, max_dist):
    """
    Vind dichtstbijzijnde mini-segment in candidates, of None.
    Returns: (mini-dict, seg_idx) of (None, None) als niets binnen max_dist ligt.
    seg_idx wordt afgeleid uit de exacte snap-positie langs de way.
    """
    best_d = max_dist
    best   = None
    best_t = 0.0
    for m in candidates:
        ax, ay, bx, by = m['ax'], m['ay'], m['bx'], m['by']
        dx, dy = bx - ax, by - ay
        L2 = dx*dx + dy*dy
        if L2 == 0:
            t = 0.0
            d = math.hypot(px - ax, py - ay)
        else:
            t = max(0.0, min(1.0, ((px - ax)*dx + (py - ay)*dy) / L2))
            d = math.hypot(px - (ax + t*dx), py - (ay + t*dy))
        if d < best_d:
            best_d = d
            best   = m
            best_t = t
    if best is None:
        return None, None
    if best['n_seg'] <= 1 or best['seg_len'] == 0:
        seg_idx = 0
    else:
        snap_m = best['cum_start'] + best_t * best['edge_len']
        seg_idx = min(best['n_seg'] - 1, int(snap_m // best['seg_len']))
    return best, seg_idx


# ── ZIP-helpers ──────────────────────────────────────────────────────────────

def find_csv(zf, suffix):
    """Vind eerste bestand in ZIP eindigend op suffix."""
    for n in zf.namelist():
        if n.endswith(suffix):
            return n
    return None


def read_csv_dict(zf, name):
    """Lees CSV-bestand uit ZIP, return lijst van dicts (separator ;)."""
    with zf.open(name) as f:
        text = f.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text), delimiter=';')
    return list(reader)


def parse_iso_ts(s):
    """ISO 'YYYY-MM-DDTHH:MM:SS' → datetime (lokaal, geen tz)."""
    try:
        return datetime.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


def fmt_time(dt):
    return dt.strftime('%H:%M:%S') if dt else ''


# ── Visit-detectie ───────────────────────────────────────────────────────────

def build_visits(gps_points, taps):
    """
    gps_points: [(dt, lat, lon, wid, seg_idx, name)] — chronologisch
    taps:       [(dt, wid, seg_idx)] — chronologisch
    return: lijst visits met velden wid, seg_idx, name, t_start, t_end, n_pts, n_tel
    """
    visits = []
    cur = None
    for dt, lat, lon, wid, seg_idx, name in gps_points:
        if not wid:
            if cur:
                visits.append(cur); cur = None
            continue
        same_key = cur and cur['wid'] == wid and cur['seg_idx'] == seg_idx
        gap_too_big = cur and (dt - cur['t_end']).total_seconds() > MAX_GAP_SEC
        if cur is None or not same_key or gap_too_big:
            if cur:
                visits.append(cur)
            cur = {'wid': wid, 'seg_idx': seg_idx, 'name': name,
                   't_start': dt, 't_end': dt, 'n_pts': 1, 'n_tel': 0}
        else:
            cur['t_end'] = dt
            cur['n_pts'] += 1
            if name and not cur['name']:
                cur['name'] = name
    if cur:
        visits.append(cur)

    visits = [v for v in visits
              if (v['t_end'] - v['t_start']).total_seconds() >= MIN_VISIT_SEC
              and v['n_pts'] >= MIN_VISIT_PTS]

    # Tellingen toewijzen — taps gesorteerd, lineaire pass
    ti = 0
    for v in visits:
        while ti < len(taps) and taps[ti][0] < v['t_start']:
            ti += 1
        j = ti
        while j < len(taps) and taps[j][0] <= v['t_end']:
            if taps[j][1] == v['wid'] and taps[j][2] == v['seg_idx']:
                v['n_tel'] += 1
            j += 1
    return visits


# ── Eén ZIP verwerken ────────────────────────────────────────────────────────

class SkipReason(Exception):
    pass


def is_already_v23(zf, net_name):
    """Heeft _netwerk.csv al een segment_index-kolom? → v2.3"""
    try:
        with zf.open(net_name) as f:
            first = f.read(2000).decode('utf-8-sig', errors='replace')
        header = first.split('\n', 1)[0]
        return 'segment_index' in header.lower()
    except Exception:
        return False


def process_zip(path: Path, in_zip: bool, force: bool) -> str:
    with zipfile.ZipFile(path, 'r') as zf:
        sessie_name = find_csv(zf, '_sessie.csv')
        gps_name    = find_csv(zf, '_gps.csv')
        tel_name    = find_csv(zf, '_telregels.csv')
        net_name    = find_csv(zf, '_netwerk.csv')

        if not sessie_name: raise SkipReason('geen _sessie.csv')
        if not gps_name:    raise SkipReason('geen _gps.csv')
        if not net_name:    raise SkipReason('geen _netwerk.csv')

        if not force and is_already_v23(zf, net_name):
            raise SkipReason('al v2.3 (gebruik --force om opnieuw te doen)')

        sessie = read_csv_dict(zf, sessie_name)
        if not sessie:
            raise SkipReason('_sessie.csv is leeg')
        sm = sessie[0]
        sid = sm.get('sessie_id', '').strip()
        datum = sm.get('datum', '').strip()
        if not sid or not datum:
            raise SkipReason('sessie.csv mist sessie_id of datum')

        # Netwerk: eerste-rij-per-wayId (oude format) of v2.3 input (--force).
        # We hebben de FULLe geometry per way nodig voor segmentatie.
        # Bij --force op v2.3 input zou geometrie al gesplitst zijn — randgeval
        # dat we accepteren met de aanname dat eerste rij voldoende is.
        network = {}
        for row in read_csv_dict(zf, net_name):
            wid = (row.get('osm_way_id') or '').strip()
            geom = parse_linestring(row.get('geometrie_wkt') or '')
            if wid and geom and wid not in network:
                network[wid] = {
                    'geometry': geom,
                    'highway':  row.get('highway', ''),
                    'name':     row.get('straat') or row.get('osmName') or ''
                }
        if not network:
            raise SkipReason('_netwerk.csv leverde geen geldige geometrie')

        # Straatnaam-fallback uit telregels (oude pocket had naam alleen daar)
        name_for_wid = {}
        if tel_name:
            for row in read_csv_dict(zf, tel_name):
                wid = (row.get('osm_way_id') or '').strip()
                straat = (row.get('straat') or '').strip()
                if wid and straat and wid not in name_for_wid:
                    name_for_wid[wid] = straat
        for wid, info in network.items():
            if not info['name'] and wid in name_for_wid:
                info['name'] = name_for_wid[wid]

        # Reference-punt: eerste GPS-punt of eerste way
        ref_lat = ref_lon = None
        gps_rows = read_csv_dict(zf, gps_name)
        for r in gps_rows:
            try:
                ref_lat = float(r.get('lat', ''))
                ref_lon = float(r.get('lon', ''))
                break
            except ValueError:
                continue
        if ref_lat is None:
            first_geom = next(iter(network.values()))['geometry']
            ref_lat, ref_lon = first_geom[0]

        mini = build_mini_segs(network, ref_lat, ref_lon)
        if not mini:
            raise SkipReason('netwerk leverde geen bruikbare mini-segmenten')

        mini_by_wid = {}
        for m in mini:
            mini_by_wid.setdefault(m['wid'], []).append(m)

        # GPS-punten verwerken: globaal snappen binnen GPS_SNAP_M
        gps_points   = []
        gps_out_rows = []
        skipped_pts  = 0
        for r in gps_rows:
            ts = parse_iso_ts(r.get('tijdstip', ''))
            try:
                lat = float(r.get('lat', ''))
                lon = float(r.get('lon', ''))
            except ValueError:
                skipped_pts += 1; continue
            if ts is None:
                skipped_pts += 1; continue
            px, py = snap_xy(lat, lon, ref_lat)
            m, seg_idx = snap_to_minis(px, py, mini, GPS_SNAP_M)
            if m:
                wid = m['wid']
                name = m.get('name') or name_for_wid.get(wid, '')
            else:
                wid, seg_idx, name = '', 0, ''
            gps_points.append((ts, lat, lon, wid, seg_idx, name))
            gps_out_rows.append({
                'sessie_id':     sid,
                'tijdstip':      r.get('tijdstip', ''),
                'lat':           f'{lat:.6f}',
                'lon':           f'{lon:.6f}',
                'nauwkeurigheid': r.get('nauwkeurigheid', ''),
                'osm_way_id':    wid,
                'segment_index': str(seg_idx) if wid else '',
                'straat':        name
            })

        if not gps_points:
            raise SkipReason('geen geldige GPS-punten')

        # Tap-punten verwerken: prefer bestaande wayId, anders globaal binnen TAP_SNAP_M
        taps = []
        tel_out_rows = []
        if tel_name:
            for row in read_csv_dict(zf, tel_name):
                ts = parse_iso_ts(row.get('tijdstip', ''))
                existing_wid = (row.get('osm_way_id') or '').strip()
                try:
                    lat = float(row.get('lat', ''))
                    lon = float(row.get('lon', ''))
                    has_xy = True
                except ValueError:
                    lat = lon = 0.0
                    has_xy = False

                wid     = ''
                seg_idx = 0
                name    = (row.get('straat') or '').strip()

                if has_xy:
                    px, py = snap_xy(lat, lon, ref_lat)
                    if existing_wid and existing_wid in mini_by_wid:
                        m, si = snap_to_minis(px, py, mini_by_wid[existing_wid], TAP_SNAP_M)
                        if m:
                            wid, seg_idx = m['wid'], si
                            if not name: name = m.get('name') or name_for_wid.get(wid, '')
                    if not wid:
                        m, si = snap_to_minis(px, py, mini, TAP_SNAP_M)
                        if m:
                            wid, seg_idx = m['wid'], si
                            if not name: name = m.get('name') or name_for_wid.get(wid, '')
                elif existing_wid in network:
                    wid = existing_wid
                    seg_idx = 0

                if ts and wid:
                    taps.append((ts, wid, seg_idx))

                tel_out_rows.append({
                    'sessie_id':     row.get('sessie_id', sid),
                    'nr':            row.get('nr', ''),
                    'tijdstip':      row.get('tijdstip', ''),
                    'type':          row.get('type', ''),
                    'lat':           row.get('lat', ''),
                    'lon':           row.get('lon', ''),
                    'osm_way_id':    wid or existing_wid,
                    'segment_index': str(seg_idx) if wid else '',
                    'straat':        name
                })
            taps.sort(key=lambda x: x[0])

        visits = build_visits(gps_points, taps)

        # ── CSVs bouwen ──────────────────────────────────────────────────────

        # _netwerk.csv — één rij per segment
        net_lines = ['osm_way_id;segment_index;segment_count;highway;geometrie_wkt']
        seg_count_for = {}
        for wid, info in network.items():
            subs = split_way_into_segments(info['geometry'])
            seg_count_for[wid] = len(subs)
            for idx, sub in enumerate(subs):
                coords = ', '.join(f'{p[1]:.6f} {p[0]:.6f}' for p in sub)
                net_lines.append(';'.join([
                    wid, str(idx), str(len(subs)),
                    info.get('highway', ''),
                    f'LINESTRING ({coords})'
                ]))
        net_csv = '\n'.join(net_lines).encode('utf-8')

        # _gps.csv
        gps_lines = ['sessie_id;tijdstip;lat;lon;nauwkeurigheid;osm_way_id;segment_index;straat']
        for r in gps_out_rows:
            gps_lines.append(';'.join([
                r['sessie_id'], r['tijdstip'], r['lat'], r['lon'],
                r['nauwkeurigheid'], r['osm_way_id'], r['segment_index'], r['straat']
            ]))
        gps_csv_out = '\n'.join(gps_lines).encode('utf-8')

        # _telregels.csv
        tel_csv_out = None
        if tel_name:
            tel_lines = ['sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat']
            for r in tel_out_rows:
                tel_lines.append(';'.join([
                    r['sessie_id'], r['nr'], r['tijdstip'], r['type'],
                    r['lat'], r['lon'], r['osm_way_id'],
                    r['segment_index'], r['straat']
                ]))
            tel_csv_out = '\n'.join(tel_lines).encode('utf-8')

        # _bezocht.csv
        bez_lines = ['sessie_id;datum;osm_way_id;segment_index;segment_count;straat;'
                     'start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen']
        for v in visits:
            dur = int(round((v['t_end'] - v['t_start']).total_seconds()))
            sc  = seg_count_for.get(v['wid'], 1)
            bez_lines.append(';'.join([
                sid, datum, v['wid'], str(v['seg_idx']), str(sc), v['name'],
                fmt_time(v['t_start']), fmt_time(v['t_end']),
                str(dur), str(v['n_pts']), str(v['n_tel'])
            ]))
        bez_csv = '\n'.join(bez_lines).encode('utf-8')
        bezocht_name = f'{sid}_bezocht.csv'

    # ── Schrijven ────────────────────────────────────────────────────────────

    if in_zip:
        replacements = {net_name: net_csv, gps_name: gps_csv_out}
        if tel_csv_out is not None and tel_name:
            replacements[tel_name] = tel_csv_out
        additions = {bezocht_name: bez_csv}
        with zipfile.ZipFile(path, 'r') as zf:
            to_delete = {n for n in zf.namelist() if n.endswith('_bezocht.csv')}
        rewrite_zip(path, replacements, additions, to_delete)
    else:
        out_path = path.parent / bezocht_name
        out_path.write_bytes(bez_csv)

    extras = []
    if skipped_pts: extras.append(f'{skipped_pts} GPS-pt overgeslagen')
    n_segs = sum(seg_count_for.values())
    info_msg = (f'{len(visits)} visits, {len(taps)} tellingen, '
                f'{len(network)} wegen → {n_segs} segmenten')
    if extras: info_msg += '; ' + ', '.join(extras)
    return info_msg


def rewrite_zip(path: Path, replacements: dict, additions: dict, deletions: set):
    """
    Schrijf nieuwe ZIP op pad: bestaande inhoud minus deletions, met
    replacements (zelfde naam, nieuwe inhoud) en additions (nieuwe namen).
    """
    tmp = path.with_suffix('.zip.tmp')
    with zipfile.ZipFile(path, 'r') as src:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as dst:
            for item in src.namelist():
                if item in deletions or item in replacements or item in additions:
                    continue
                dst.writestr(item, src.read(item))
            for name, data in replacements.items():
                dst.writestr(name, data)
            for name, data in additions.items():
                dst.writestr(name, data)
    shutil.move(tmp, path)


# ── CLI ──────────────────────────────────────────────────────────────────────

def find_zips(paths):
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            yield from sorted(pp.rglob('*.zip'))
        elif pp.is_file() and pp.suffix.lower() == '.zip':
            yield pp


def main():
    ap = argparse.ArgumentParser(
        description='Upgrade pocket-ZIPs naar v2.3 segment-aware formaat.')
    ap.add_argument('paths', nargs='+', help='ZIP-bestand(en) of map(pen) met ZIPs')
    ap.add_argument('--side', action='store_true',
                    help='Schrijf alleen _bezocht.csv los naast de ZIP '
                         '(geen in-place upgrade)')
    ap.add_argument('--force', action='store_true',
                    help='Forceer upgrade, ook als ZIP al v2.3 lijkt')
    args = ap.parse_args()

    zips = list(find_zips(args.paths))
    if not zips:
        print('Geen ZIP-bestanden gevonden.', file=sys.stderr)
        sys.exit(1)

    in_zip = not args.side
    mode = 'in-place upgrade' if in_zip else 'los _bezocht.csv ernaast'
    print(f'Modus: {mode}\n')

    n_ok = n_skip = n_err = 0
    for z in zips:
        try:
            info = process_zip(z, in_zip, args.force)
            print(f'✓ {z.name}  {info}')
            n_ok += 1
        except SkipReason as e:
            print(f'– {z.name}  overgeslagen: {e}')
            n_skip += 1
        except Exception as e:
            print(f'✗ {z.name}  fout: {e}')
            n_err += 1

    print(f'\n{n_ok} verwerkt, {n_skip} overgeslagen, {n_err} fouten.')


if __name__ == '__main__':
    main()
