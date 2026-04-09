from datetime import date
from unittest.mock import MagicMock
from pipeline.backfill import backfill_location
from pipeline.openmeteo import LocationSpec

def test_backfill_location_skips_if_up_to_date():
    loc = LocationSpec(slug="stowe-vt", name="Stowe", latitude=44.4, longitude=-72.6, elevation_m=486, timezone="UTC")
    mock_ingest = MagicMock()
    
    # Mock DB to return latest date as today
    mock_db = MagicMock()
    mock_db.get_latest_observed_date.return_value = date.today()
    mock_db.upsert_location.return_value = 1
    
    # This should result in 0 rows ingested
    rows = backfill_location(loc, start_date=date(2024, 1, 1), ingest_fn=mock_ingest, db_mod=mock_db)
    assert len(rows) == 0
    mock_ingest.assert_not_called()

def test_backfill_location_fetches_gap():
    loc = LocationSpec(slug="stowe-vt", name="Stowe", latitude=44.4, longitude=-72.6, elevation_m=486, timezone="UTC")
    mock_ingest = MagicMock(return_value=[1, 2, 3])
    
    # Mock DB to return latest date as 2024-01-01
    mock_db = MagicMock()
    mock_db.get_latest_observed_date.return_value = date(2024, 1, 1)
    mock_db.upsert_location.return_value = 1
    
    # Requested start date is same as latest_date, so we should fetch from latest_date + 1
    rows = backfill_location(loc, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5), ingest_fn=mock_ingest, db_mod=mock_db)
    assert len(rows) == 3
    mock_ingest.assert_called_once_with(loc, date(2024, 1, 2), date(2024, 1, 5))
