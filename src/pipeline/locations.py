import csv
from pathlib import Path
from pipeline.openmeteo import LocationSpec

LOCATIONS_CSV = Path(__file__).parent / "locations.csv"

def load_locations() -> list[LocationSpec]:
    locations = []
    with open(LOCATIONS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append(
                LocationSpec(
                    slug=row["slug"],
                    name=row["name"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    elevation_m=float(row["elevation_m"]) if row["elevation_m"] else None,
                    timezone=row["timezone"],
                )
            )
    return locations

def get_location(slug: str) -> LocationSpec:
    locations = load_locations()
    for loc in locations:
        if loc.slug == slug:
            return loc
    raise ValueError(f"Unknown location slug: {slug}")
