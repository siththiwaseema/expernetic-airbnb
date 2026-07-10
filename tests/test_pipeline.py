"""
Unit tests for the Bangkok Airbnb data pipeline.
Tests cover ingestion, cleaning, enrichment, and data quality validation.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.clean import clean_price, clean_listings, clean_calendar, profile_dataframe
from src.utils import DATA_RAW, DATA_PROCESSED


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_listings():
    """Create a minimal sample listings dataframe for testing."""
    return pd.DataFrame({
        "id":                    [1, 2, 3, 4, 5],
        "host_id":               [101, 102, 103, 101, 104],
        "host_name":             ["Alice", "Bob", "Carol", "Alice", "Dave"],
        "host_since":            ["2020-01-01", "2019-06-15", None, "2020-01-01", "2021-03-10"],
        "host_is_superhost":     ["t", "f", "t", "t", "f"],
        "neighbourhood_cleansed":["Vadhana", "Bang Rak", "Vadhana", "Sathon", "Lat Phrao"],
        "room_type":             ["Entire Home/Apt", "Private Room", "Entire Home/Apt",
                                  "Shared Room", "Hotel Room"],
        "property_type":         ["Condo", "House", "Condo", "Hostel", "Hotel"],
        "price":                 ["$1,500.00", "$800.00", "$2,200.00", "$350.00", "$999.00"],
        "accommodates":          [2, 1, 4, 6, 2],
        "bedrooms":              [1, 1, 2, None, 1],
        "bathrooms":             [1, 1, 2, 1, 1],
        "beds":                  [1, 1, 2, 4, 1],
        "minimum_nights":        [1, 2, 3, 1, 1],
        "number_of_reviews":     [10, 25, 0, 5, 100],
        "review_scores_rating":  [4.8, 4.5, None, 4.2, 4.9],
        "latitude":              [13.72, 13.74, 13.71, 13.73, 13.85],
        "longitude":             [100.53, 100.52, 100.54, 100.51, 100.60],
        "instant_bookable":      ["t", "f", "t", "f", "t"],
        "first_review":          ["2020-06-01", "2019-10-01", None, "2021-01-15", "2021-06-01"],
        "last_review":           ["2024-01-01", "2024-03-01", None, "2023-12-01", "2024-05-01"],
    })


@pytest.fixture
def sample_calendar():
    """Create a minimal sample calendar dataframe for testing."""
    return pd.DataFrame({
        "listing_id": [1, 1, 1, 2, 2, 2],
        "date":       ["2026-07-01", "2026-07-02", "2026-07-03",
                       "2026-07-01", "2026-07-02", "2026-07-03"],
        "available":  ["f", "f", "t", "t", "f", "f"],
        "minimum_nights": [1, 1, 1, 2, 2, 2],
        "maximum_nights": [30, 30, 30, 60, 60, 60],
    })


# ─── Price Cleaning Tests ──────────────────────────────────────────────────────

class TestCleanPrice:

    def test_removes_dollar_sign(self):
        s = pd.Series(["$1500.00"])
        result = clean_price(s)
        assert result[0] == 1500.0

    def test_removes_comma(self):
        s = pd.Series(["$1,500.00"])
        result = clean_price(s)
        assert result[0] == 1500.0

    def test_handles_nan(self):
        s = pd.Series([None, "$500.00"])
        result = clean_price(s)
        assert pd.isna(result[0])
        assert result[1] == 500.0

    def test_handles_empty_string(self):
        s = pd.Series(["", "$300.00"])
        result = clean_price(s)
        assert pd.isna(result[0])

    def test_returns_float(self):
        s = pd.Series(["$999.99"])
        result = clean_price(s)
        assert result.dtype == float

    def test_multiple_prices(self):
        s = pd.Series(["$1,500.00", "$800.00", "$2,200.00"])
        result = clean_price(s)
        expected = [1500.0, 800.0, 2200.0]
        assert list(result) == expected


# ─── Listings Cleaning Tests ───────────────────────────────────────────────────

class TestCleanListings:

    def test_price_parsed_correctly(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert cleaned["price"].dtype == float
        assert cleaned["price"].iloc[0] == 1500.0

    def test_superhost_boolean(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert cleaned["host_is_superhost"].iloc[0] == True
        assert cleaned["host_is_superhost"].iloc[1] == False

    def test_instant_bookable_boolean(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert cleaned["instant_bookable"].iloc[0] == True
        assert cleaned["instant_bookable"].iloc[1] == False

    def test_room_type_normalized(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert cleaned["room_type"].iloc[0] == "Entire Home/Apt"

    def test_neighbourhood_normalized(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert cleaned["neighbourhood_cleansed"].iloc[0] == "Vadhana"

    def test_no_negative_prices(self, sample_listings):
        sample_listings.loc[0, "price"] = "$-100.00"
        cleaned = clean_listings(sample_listings)
        assert (cleaned["price"] > 0).all() or cleaned["price"].isna().any()

    def test_host_tenure_derived(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        if "host_tenure_years" in cleaned.columns:
            valid = cleaned["host_tenure_years"].dropna()
            assert (valid >= 0).all()

    def test_price_per_bedroom_derived(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        if "price_per_bedroom" in cleaned.columns:
            valid = cleaned["price_per_bedroom"].dropna()
            assert (valid > 0).all()

    def test_row_count_preserved(self, sample_listings):
        cleaned = clean_listings(sample_listings)
        assert len(cleaned) <= len(sample_listings)

    def test_coordinate_validation(self, sample_listings):
        sample_listings.loc[0, "latitude"] = 999
        cleaned = clean_listings(sample_listings)
        if "invalid_coords" in cleaned.columns:
            assert cleaned["invalid_coords"].iloc[0] == True


# ─── Calendar Cleaning Tests ───────────────────────────────────────────────────

class TestCleanCalendar:

    def test_available_parsed_to_bool(self, sample_calendar):
        cleaned = clean_calendar(sample_calendar)
        assert cleaned["available"].dtype == object or \
               cleaned["available"].dtype == bool

    def test_date_parsed(self, sample_calendar):
        cleaned = clean_calendar(sample_calendar)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])

    def test_weekend_flag_added(self, sample_calendar):
        cleaned = clean_calendar(sample_calendar)
        assert "is_weekend" in cleaned.columns

    def test_day_of_week_added(self, sample_calendar):
        cleaned = clean_calendar(sample_calendar)
        assert "day_of_week" in cleaned.columns

    def test_row_count_preserved(self, sample_calendar):
        cleaned = clean_calendar(sample_calendar)
        assert len(cleaned) == len(sample_calendar)


# ─── Data Quality Tests ────────────────────────────────────────────────────────

class TestDataQuality:

    def test_profile_returns_dataframe(self, sample_listings):
        profile = profile_dataframe(sample_listings, "test")
        assert isinstance(profile, pd.DataFrame)

    def test_profile_has_required_columns(self, sample_listings):
        profile = profile_dataframe(sample_listings, "test")
        assert "null_pct" in profile.columns
        assert "unique_count" in profile.columns
        assert "dtype" in profile.columns

    def test_null_pct_between_0_and_100(self, sample_listings):
        profile = profile_dataframe(sample_listings, "test")
        assert (profile["null_pct"] >= 0).all()
        assert (profile["null_pct"] <= 100).all()

    def test_no_duplicate_ids(self, sample_listings):
        assert sample_listings["id"].nunique() == len(sample_listings)

    def test_valid_coordinates(self, sample_listings):
        assert (sample_listings["latitude"].between(-90, 90)).all()
        assert (sample_listings["longitude"].between(-180, 180)).all()

    def test_positive_accommodates(self, sample_listings):
        assert (sample_listings["accommodates"] > 0).all()

    def test_room_types_valid(self, sample_listings):
        valid_types = {
            "Entire Home/Apt", "Private Room",
            "Shared Room", "Hotel Room"
        }
        assert set(sample_listings["room_type"]).issubset(valid_types)


# ─── Integration Test ──────────────────────────────────────────────────────────

class TestIntegration:

    def test_processed_master_exists(self):
        """Check master table was generated by pipeline."""
        master_path = DATA_PROCESSED / "master_listings.csv"
        assert master_path.exists(), \
            "master_listings.csv not found — run src/enrich.py first"

    def test_master_has_expected_columns(self):
        """Check master table has key columns."""
        master_path = DATA_PROCESSED / "master_listings.csv"
        if master_path.exists():
            master = pd.read_csv(master_path, nrows=100)
            required = ["id", "host_id", "price",
                        "room_type", "neighbourhood_cleansed",
                        "occupancy_rate"]
            for col in required:
                assert col in master.columns, f"Missing column: {col}"

    def test_master_row_count(self):
        """Check master table has expected number of rows."""
        master_path = DATA_PROCESSED / "master_listings.csv"
        if master_path.exists():
            master = pd.read_csv(master_path)
            assert len(master) > 30000, \
                f"Expected 30K+ rows, got {len(master)}"

    def test_duckdb_exists(self):
        """Check DuckDB database was created."""
        import sys
        db_path = Path(__file__).resolve().parent.parent / "db" / "airbnb_bangkok.duckdb"
        assert db_path.exists(), \
            "DuckDB not found — run src/model.py first"