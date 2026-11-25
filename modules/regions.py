"""Region configuration. Only allow-listed regions can ever reach an API call."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    key: str
    name: str
    lat: float      # pilot point used for the NOAA time series
    lon: float
    south: float    # bounding box used for OBIS
    north: float
    west: float
    east: float
    enabled: bool
    note: str

    @property
    def wkt(self) -> str:
        w, e, s, n = self.west, self.east, self.south, self.north
        return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


REGIONS = {
    "gulf_of_mannar": Region(
        "gulf_of_mannar", "Gulf of Mannar, Tamil Nadu", 8.9, 79.0,
        8.7, 9.35, 78.1, 79.35, True,
        "Pilot region. Bounding box is approximate: review it before publishing."),
    "palk_bay": Region(
        "palk_bay", "Palk Bay, Tamil Nadu", 9.6, 79.45,
        9.2, 10.3, 79.2, 79.9, False, "Planned next expansion. Not enabled."),
}
DEFAULT_REGION = "gulf_of_mannar"


def get_region(key: str) -> Region:
    region = REGIONS.get(key)
    if region is None or not region.enabled:
        return REGIONS[DEFAULT_REGION]
    return region
