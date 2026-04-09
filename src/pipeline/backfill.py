from datetime import date, timedelta
from pipeline.openmeteo import LocationSpec, ingest_historical_daily_weather
from pipeline.locations import load_locations
import db

def backfill_location(
    location: LocationSpec, 
    start_date: date, 
    end_date: date | None = None,
    ingest_fn=ingest_historical_daily_weather,
    db_mod=db
) -> list:
    if end_date is None:
        end_date = date.today()
        
    location_id = db_mod.upsert_location(location)
    latest_date = db_mod.get_latest_observed_date(location_id)
    
    fetch_start = start_date
    if latest_date:
        # If we have data, we start from the day after the latest record
        # but only if latest_date is >= start_date
        if latest_date >= start_date:
            fetch_start = latest_date + timedelta(days=1)
        
    if fetch_start > end_date:
        return []
        
    return ingest_fn(location, fetch_start, end_date)

def backfill_all(start_date: date = date(2024, 1, 1)):
    locations = load_locations()
    for loc in locations:
        print(f"Backfilling {loc.slug}...")
        backfill_location(loc, start_date)
