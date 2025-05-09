from pyproj import CRS, Transformer
from shapely.geometry import Polygon
import re

def dms_str_to_decimal(dms_str: str) -> float:
    """
    Convert a DMS string like 28°13'30.28" (no hemisphere) to decimal degrees,
    assuming positive (East or North).
    If you need West/South, prefix with '-' (e.g. "-117°09'12.00\"").
    """
    # Extract degrees, minutes, seconds, and optional leading sign
    m = re.match(r'^\s*([\-+]?)(\d+)[°:\s]+(\d+)[\'\s]+([\d\.]+)"?\s*$', dms_str)
    if not m:
        raise ValueError(f"Cannot parse DMS string: {dms_str!r}")
    sign, deg, mins, secs = m.groups()
    dd = float(deg) + float(mins) / 60 + float(secs) / 3600
    if sign == '-':
        dd = -dd
    return dd

def compute_area_m2(dms_lon, dms_lat):
    """
    dms_lon: list of 4 longitude DMS strings (e.g. ["28°13'30.28\"", ...])
    dms_lat: list of 4 latitude  DMS strings (e.g. ["26°57'42.46\"", ...])

    Returns: area in square meters.
    """
    if len(dms_lon) != 4 or len(dms_lat) != 4:
        raise ValueError("Need exactly 4 longitude and 4 latitude values.")

    # 1. Convert all to decimal degrees
    pts_dd = []
    for lon_str, lat_str in zip(dms_lon, dms_lat):
        lon = dms_str_to_decimal(lon_str)
        lat = dms_str_to_decimal(lat_str)
        pts_dd.append((lat, lon))

    # 2. Determine UTM zone from polygon centroid
    centroid_lat = sum(lat for lat,lon in pts_dd) / 4
    centroid_lon = sum(lon for lat,lon in pts_dd) / 4
    utm_zone = int((centroid_lon + 180) / 6) + 1
    utm_crs = CRS.from_proj4(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs")

    # 3. Build transformer from WGS84 → UTM
    transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

    # 4. Project points to meters
    projected = [transformer.transform(lon, lat) for lat, lon in pts_dd]

    # 5. Compute polygon area
    poly = Polygon(projected)
    return abs(poly.area)

if __name__ == "__main__":
    # Replace these with your exact four readings from the sheet:
    longitudes = [
        "28°13'30.28\"",
        "28°13'41.59\"",
        "28°13'32.53\"",
        "28°13'21.35\"",
    ]
    latitudes = [
        "26°57'42.46\"",
        "26°57'26.23\"",
        "26°57'21.83\"",
        "26°57'38.45\"",
    ]

    area_m2 = compute_area_m2(longitudes, latitudes)
    print(f"Total area: {area_m2:,.2f} m²")
