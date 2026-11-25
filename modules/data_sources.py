"""NOAA Coral Reef Watch (ERDDAP) and OBIS v3 retrieval.

Safety rules: HTTPS only, fixed hosts, timeouts, response-size cap, numeric-only
query values, no silent fallback to fake data. Failures raise DataUnavailable.
"""
import io
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import numpy as np
import pandas as pd
import requests

ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/NOAA_DHW.csv"
OBIS = "https://api.obis.org/v3/occurrence"
TIMEOUT = (5, 25)
MAX_BYTES = 5_000_000
HEADERS = {"User-Agent": "Neythal-hackathon-prototype/0.1"}
CHL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdMH1chla8day_R2022NRT.csv"
OW = "https://services2.coastalresilience.org/arcgis/rest/services/OceanWealth/Ocean_Wealth/MapServer/"
WDPA = ("https://services5.arcgis.com/FDIcdEEqy1cBDX8N/ArcGIS/rest/services/"
        "The_World_Database_on_Protected_Areas/FeatureServer/0/query")
ALLOWED_PREFIXES = (ERDDAP, OBIS, CHL, OW, WDPA)


class DataUnavailable(Exception):
    """Raised when a source cannot supply usable data. http=True means the server answered with an error."""

    def __init__(self, message, http=False):
        super().__init__(message)
        self.http = http


def _get(url: str) -> bytes:
    if not url.startswith(ALLOWED_PREFIXES):
        raise DataUnavailable("Blocked: unexpected host.")
    try:
        with requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True) as r:
            r.raise_for_status()
            body = r.raw.read(MAX_BYTES + 1, decode_content=True)
    except requests.HTTPError as exc:
        raise DataUnavailable(f"Server refused the request ({exc.response.status_code}).", http=True) from None
    except requests.RequestException as exc:
        raise DataUnavailable(f"Could not reach the server ({type(exc).__name__}).") from None
    if len(body) > MAX_BYTES:
        raise DataUnavailable("Response too large; refused.")
    return body


def _coord(value, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
        raise DataUnavailable("Invalid coordinate.")
    return float(value)


def _meta(source, observed, units, coverage, latency, limits, url, synthetic=False):
    return {"Source": source, "Observation period": observed,
            "Retrieved (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "Units": units, "Spatial coverage": coverage, "Data latency": latency,
            "Limitations": limits, "Link": url, "synthetic": synthetic}


def _parse_noaa(body: bytes, prefix: str = "CRW_"):
    try:
        df = pd.read_csv(io.BytesIO(body), skiprows=[1])
        df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    except (ValueError, KeyError, pd.errors.ParserError):
        return None
    cols = [c for c in df.columns if c.startswith(prefix)]
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=cols, how="all").dropna(subset=["time"]).sort_values("time")
    return df if len(df) else None


def fetch_noaa_series(lat: float, lon: float) -> dict:
    lat, lon = _coord(lat, -90, 90), _coord(lon, -180, 180)
    now = datetime.now(timezone.utc)
    iso = lambda d: f"({(now - timedelta(days=d)):%Y-%m-%d}T12:00:00Z)"
    # Three time-window syntaxes: ERDDAP is strict, so try each until one works.
    windows = ["(last-89):1:(last)", f"{iso(93)}:1:{iso(4)}", f"{iso(97)}:1:{iso(8)}"]
    for t in windows:
        q = ",".join(f"{v}[{t}][({lat:.3f})][({lon:.3f})]"
                     for v in ("CRW_SST", "CRW_SSTANOMALY", "CRW_DHW"))
        try:
            df = _parse_noaa(_get(f"{ERDDAP}?{quote(q, safe='[]():,.-')}"))
        except DataUnavailable as exc:
            if not exc.http:
                raise
            continue
        if df is not None:
            last = df["time"].max()
            lag = (now - last.to_pydatetime()).days
            meta = _meta(
                "NOAA Coral Reef Watch, daily 5 km (ERDDAP dataset NOAA_DHW)",
                f"{df['time'].min():%Y-%m-%d} to {last:%Y-%m-%d}",
                "SST and anomaly in °C; DHW in °C-weeks",
                f"Single 5 km pixel near {df['latitude'].iloc[0]:.2f}°N, {df['longitude'].iloc[0]:.2f}°E",
                f"Newest value is {lag} day(s) older than retrieval time",
                "One pixel, not the whole region. Missing values are not zero. "
                "Near-real-time product; a refresh does not make it live.",
                "https://coralreefwatch.noaa.gov/product/5km/")
            return {"df": df, "meta": meta}
    raise DataUnavailable("NOAA returned no usable data (service down, or no ocean pixel).")


def fetch_obis(wkt: str, size: int = 500) -> dict:
    size = max(1, min(int(size), 1000))
    fields = "scientificName,decimalLatitude,decimalLongitude,date_year,datasetName,basisOfRecord"
    body = _get(f"{OBIS}?{urlencode({'geometry': wkt, 'size': size, 'fields': fields})}")
    try:
        data = json.loads(body)
    except ValueError:
        raise DataUnavailable("OBIS returned unreadable data.") from None
    rows = data.get("results") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise DataUnavailable("OBIS returned no records for this area.")
    df = pd.DataFrame(rows)
    for c in ("scientificName", "decimalLatitude", "decimalLongitude"):
        if c not in df:
            raise DataUnavailable("OBIS response was missing expected fields.")
    df["decimalLatitude"] = pd.to_numeric(df["decimalLatitude"], errors="coerce")
    df["decimalLongitude"] = pd.to_numeric(df["decimalLongitude"], errors="coerce")
    df = df.dropna(subset=["scientificName", "decimalLatitude", "decimalLongitude"])
    years = pd.to_numeric(df.get("date_year"), errors="coerce").dropna()
    period = f"{int(years.min())} to {int(years.max())}" if len(years) else "Not stated"
    meta = _meta("OBIS API v3 (occurrence records)", period, "Occurrence records (count)",
                 "Bounding box of the selected region",
                 "Depends on each contributing dataset",
                 f"Showing {len(df)} of {data.get('total', 'unknown')} records. Occurrence is not "
                 "abundance; sampling effort is uneven; absence of a record means nothing.",
                 "https://obis.org")
    return {"df": df, "meta": meta}


def fetch_chlorophyll(lat: float, lon: float) -> dict:
    """NASA MODIS-Aqua chlorophyll-a (8-day, 4 km) via NOAA CoastWatch: a water-quality indicator."""
    lat, lon = _coord(lat, -90, 90), _coord(lon, -180, 180)
    now = datetime.now(timezone.utc)
    iso = lambda d: f"({(now - timedelta(days=d)):%Y-%m-%d}T00:00:00Z)"
    for t in ("(last-23):1:(last)", f"{iso(200)}:1:{iso(12)}"):
        for alt in ("[(0.0)]", ""):  # some versions have an altitude axis, some do not
            q = f"chlorophyll[{t}]{alt}[({lat:.3f})][({lon:.3f})]"
            try:
                df = _parse_noaa(_get(f"{CHL}?{quote(q, safe='[]():,.-')}"), "chlorophyll")
            except DataUnavailable as exc:
                if not exc.http:
                    raise
                continue
            if df is not None:
                df = df[df["chlorophyll"] > 0]
                if df.empty:
                    continue
                last = df["time"].max()
                meta = _meta(
                    "NASA MODIS-Aqua chlorophyll-a, 4 km, 8-day composite, via NOAA CoastWatch "
                    "(erdMH1chla8day_R2022NRT)",
                    f"{df['time'].min():%Y-%m-%d} to {last:%Y-%m-%d}", "mg per m³ (chlorophyll-a)",
                    f"Single ~4.6 km pixel near {df['latitude'].iloc[0]:.2f}°N, {df['longitude'].iloc[0]:.2f}°E",
                    f"Newest composite is {(now - last.to_pydatetime()).days} day(s) old",
                    "Indicator of algal biomass, not a direct pollution measurement. Clouds leave gaps "
                    "(gaps are not zero) and shallow turbid water can read high.",
                    "https://oceancolor.gsfc.nasa.gov/")
                return {"df": df, "meta": meta}
    raise DataUnavailable("No chlorophyll value for this pixel (cloud cover, land or service gap).")


HABITAT = {  # key: (layer url, label, source, vintage)
    "coral": (OW + "98", "Coral reefs",
              "UNEP-WCMC, WorldFish Centre, WRI, TNC global warm-water coral reefs (hosted by Coastal Resilience)",
              "Composite compiled 2010 from older surveys"),
    "seagrass": (OW + "104", "Seagrass",
                 "UNEP-WCMC and F. Short global seagrass polygons (hosted by Coastal Resilience)",
                 "Hosted copy; version not stated by host"),
    "mangrove": (OW + "99", "Mangroves",
                 "World Mangrove Atlas, UNEP-WCMC with ISME (hosted by Coastal Resilience)",
                 "1997 atlas: may be out of date"),
    "protected": (WDPA, "Protected areas",
                  "World Database on Protected Areas, UNEP-WCMC and IUCN (ArcGIS layer WDPA_poly_May2019)",
                  "May 2019 layer"),
}


def fetch_habitat(kind: str, region) -> dict:
    if kind not in HABITAT:
        raise DataUnavailable("Unknown habitat layer.")
    base, label, source, vintage = HABITAT[kind]
    url = base if base.endswith("/query") else base + "/query"
    params = {"where": "1=1", "geometry": f"{region.west},{region.south},{region.east},{region.north}",
              "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
              "outFields": "*", "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.001,
              "resultRecordCount": 500, "f": "geojson"}
    body = _get(f"{url}?{urlencode(params)}")
    try:
        data = json.loads(body)
    except ValueError:
        raise DataUnavailable(f"{label}: unreadable reply.") from None
    feats = data.get("features") if isinstance(data, dict) else None
    if not isinstance(feats, list):
        raise DataUnavailable(f"{label}: the map service gave an unexpected reply (it may be down).")
    clean = []
    for f in feats:
        g = f.get("geometry") if isinstance(f, dict) else None
        if not isinstance(g, dict) or g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        props = f.get("properties") or {}
        name = next((str(props[k])[:80] for k in ("NAME", "COMNAME", "DESIG_ENG", "name") if props.get(k)), label)
        clean.append({"type": "Feature", "geometry": g, "properties": {"nid": len(clean), "name": name}})
    capped = bool(data.get("exceededTransferLimit")) or len(feats) >= 500
    meta = _meta(source, vintage, "Polygons (outline only)", "Bounding box of the selected region",
                 "Static reference layer",
                 "Baseline map, not current extent. No polygon does not prove absence. Outlines simplified."
                 + (" Result capped at 500 polygons." if capped else ""),
                 "https://data.unep-wcmc.org")
    return {"geojson": {"type": "FeatureCollection", "features": clean}, "n": len(clean),
            "names": [c["properties"]["name"] for c in clean], "meta": meta}


# ---- Synthetic demo data: only used when the user switches Demo mode on ----
def demo_series() -> dict:
    rng = np.random.default_rng(7)
    days = pd.date_range(end=pd.Timestamp.now(tz="UTC").normalize(), periods=90)
    t = np.arange(90)
    sst = 29 + 0.8 * np.sin(t / 14) + rng.normal(0, 0.1, 90)
    anom = 0.4 + 0.5 * np.sin(t / 20) + rng.normal(0, 0.08, 90)
    dhw = np.clip(np.cumsum(np.clip(anom - 0.3, 0, None)) / 7, 0, None)
    df = pd.DataFrame({"time": days, "CRW_SST": sst, "CRW_SSTANOMALY": anom, "CRW_DHW": dhw})
    meta = _meta("SYNTHETIC DEMO DATA (not real)", "Last 90 days (generated)", "°C; °C-weeks",
                 "None", "None", "Invented for layout testing. Never quote these numbers.",
                 "", synthetic=True)
    return {"df": df, "meta": meta}


def demo_obis(region) -> dict:
    rng = np.random.default_rng(11)
    n = 150
    df = pd.DataFrame({
        "scientificName": [f"Demo species {i}" for i in rng.integers(1, 8, n)],
        "decimalLatitude": rng.uniform(region.south, region.north, n),
        "decimalLongitude": rng.uniform(region.west, region.east, n),
        "date_year": rng.integers(2005, 2025, n)})
    meta = _meta("SYNTHETIC DEMO DATA (not real)", "Generated", "Occurrence records (count)",
                 "None", "None", "Invented for layout testing. Not real species records.",
                 "", synthetic=True)
    return {"df": df, "meta": meta}


def demo_chlorophyll() -> dict:
    rng = np.random.default_rng(5)
    days = pd.date_range(end=pd.Timestamp.now(tz="UTC").normalize(), periods=24, freq="8D")
    df = pd.DataFrame({"time": days, "chlorophyll": np.abs(0.35 + 0.15 * np.sin(np.arange(24) / 3) + rng.normal(0, 0.03, 24))})
    meta = _meta("SYNTHETIC DEMO DATA (not real)", "Generated", "mg per m³", "None", "None",
                 "Invented for layout testing. Never quote these numbers.", "", synthetic=True)
    return {"df": df, "meta": meta}
