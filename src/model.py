import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import get_logger, DB_DIR, DATA_PROCESSED

logger = get_logger(__name__)

DB_PATH = DB_DIR / "airbnb_bangkok.duckdb"


# ─── Connect ───────────────────────────────────────────────────────────────────

def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the project database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    logger.info(f"Connected to DuckDB at {DB_PATH}")
    return conn


# ─── Dimension Tables ──────────────────────────────────────────────────────────

def create_dim_host(master: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Create and populate dim_host dimension table."""
    logger.info("Creating dim_host ...")

    host_cols = [
        "host_id", "host_name", "host_since", "host_is_superhost",
        "host_response_rate", "host_acceptance_rate", "host_identity_verified",
        "host_tenure_years", "host_segment", "total_listings"
    ]
    available_cols = [c for c in host_cols if c in master.columns]

    dim_host = (
        master[available_cols]
        .drop_duplicates(subset=["host_id"])
        .reset_index(drop=True)
    )
    dim_host = dim_host.replace([np.inf, -np.inf], np.nan)

    conn.execute("DROP TABLE IF EXISTS dim_host")
    conn.register("dim_host_df", dim_host)
    conn.execute("CREATE TABLE dim_host AS SELECT * FROM dim_host_df")
    conn.unregister("dim_host_df")

    logger.info(f"dim_host created: {len(dim_host):,} hosts")


def create_dim_neighbourhood(master: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Create and populate dim_neighbourhood dimension table."""
    logger.info("Creating dim_neighbourhood ...")

    neigh_cols = [
        "neighbourhood_cleansed", "listing_count", "median_price",
        "avg_price", "avg_rating", "avg_reviews",
        "superhost_pct", "entire_home_pct"
    ]
    available_cols = [c for c in neigh_cols if c in master.columns]

    dim_neighbourhood = (
        master[available_cols]
        .drop_duplicates(subset=["neighbourhood_cleansed"])
        .reset_index(drop=True)
        .rename(columns={"neighbourhood_cleansed": "neighbourhood"})
    )
    dim_neighbourhood = dim_neighbourhood.replace([np.inf, -np.inf], np.nan)

    conn.execute("DROP TABLE IF EXISTS dim_neighbourhood")
    conn.register("dim_neighbourhood_df", dim_neighbourhood)
    conn.execute("CREATE TABLE dim_neighbourhood AS SELECT * FROM dim_neighbourhood_df")
    conn.unregister("dim_neighbourhood_df")

    logger.info(f"dim_neighbourhood created: {len(dim_neighbourhood)} neighbourhoods")


def create_dim_room_type(master: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Create and populate dim_room_type dimension table."""
    logger.info("Creating dim_room_type ...")

    dim_room_type = (
        master[["room_type"]]
        .drop_duplicates()
        .dropna()
        .reset_index(drop=True)
        .assign(room_type_id=lambda df: df.index + 1)
    )

    conn.execute("DROP TABLE IF EXISTS dim_room_type")
    conn.register("dim_room_type_df", dim_room_type)
    conn.execute("CREATE TABLE dim_room_type AS SELECT room_type_id, room_type FROM dim_room_type_df")
    conn.unregister("dim_room_type_df")

    logger.info(f"dim_room_type created: {len(dim_room_type)} room types")


def create_dim_property_type(master: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Create and populate dim_property_type dimension table."""
    logger.info("Creating dim_property_type ...")

    dim_property_type = (
        master[["property_type"]]
        .drop_duplicates()
        .dropna()
        .reset_index(drop=True)
        .assign(property_type_id=lambda df: df.index + 1)
    )

    conn.execute("DROP TABLE IF EXISTS dim_property_type")
    conn.register("dim_property_type_df", dim_property_type)
    conn.execute("CREATE TABLE dim_property_type AS SELECT property_type_id, property_type FROM dim_property_type_df")
    conn.unregister("dim_property_type_df")

    logger.info(f"dim_property_type created: {len(dim_property_type)} property types")


# ─── Fact Table ────────────────────────────────────────────────────────────────

def create_fact_listings(master: pd.DataFrame, conn: duckdb.DuckDBPyConnection):
    """Create and populate fact_listings fact table."""
    logger.info("Creating fact_listings ...")

    fact_cols = [
        "id", "host_id", "neighbourhood_cleansed", "room_type", "property_type",
        "price", "accommodates", "bedrooms", "bathrooms", "beds",
        "minimum_nights", "maximum_nights",
        "number_of_reviews", "review_scores_rating",
        "review_scores_cleanliness", "review_scores_location",
        "review_scores_communication", "review_scores_value",
        "occupancy_rate", "booked_days", "total_days",
        "weekend_occupancy_rate", "weekday_occupancy_rate",
        "est_annual_revenue", "price_per_bedroom", "review_frequency",
        "host_tenure_years", "instant_bookable", "last_review", "first_review"
    ]
    available_cols = [c for c in fact_cols if c in master.columns]

    fact_listings = (
        master[available_cols]
        .copy()
        .rename(columns={
            "id": "listing_id",
            "neighbourhood_cleansed": "neighbourhood"
        })
    )
    fact_listings = fact_listings.replace([np.inf, -np.inf], np.nan)

    conn.execute("DROP TABLE IF EXISTS fact_listings")
    conn.register("fact_listings_df", fact_listings)
    conn.execute("CREATE TABLE fact_listings AS SELECT * FROM fact_listings_df")
    conn.unregister("fact_listings_df")

    logger.info(f"fact_listings created: {len(fact_listings):,} rows")


# ─── Build Full Schema ─────────────────────────────────────────────────────────

def build_star_schema(master: pd.DataFrame):
    """Build the full star schema in DuckDB."""
    logger.info("=== Building star schema in DuckDB ===")
    conn = get_connection()

    create_dim_host(master, conn)
    create_dim_neighbourhood(master, conn)
    create_dim_room_type(master, conn)
    create_dim_property_type(master, conn)
    create_fact_listings(master, conn)

    # Verify all tables
    tables = conn.execute("SHOW TABLES").fetchdf()
    logger.info(f"Tables in database:\n{tables.to_string(index=False)}")

    conn.close()
    logger.info("=== Star schema build complete ===")


# ─── Analytical SQL Queries ───────────────────────────────────────────────────

def run_analytical_queries():
    """Run key analytical queries against the star schema."""
    conn = get_connection()

    queries = {
        "Top 10 Neighbourhoods by Median Price": """
            SELECT
                f.neighbourhood,
                COUNT(*) AS listing_count,
                ROUND(MEDIAN(f.price), 2) AS median_price,
                ROUND(AVG(f.occupancy_rate), 1) AS avg_occupancy_pct,
                ROUND(AVG(f.review_scores_rating), 2) AS avg_rating
            FROM fact_listings f
            WHERE f.price IS NOT NULL
            GROUP BY f.neighbourhood
            ORDER BY median_price DESC
            LIMIT 10
        """,

        "Price by Room Type": """
            SELECT
                f.room_type,
                COUNT(*) AS listing_count,
                ROUND(AVG(f.price), 2) AS avg_price,
                ROUND(MEDIAN(f.price), 2) AS median_price,
                ROUND(AVG(f.occupancy_rate), 1) AS avg_occupancy_pct
            FROM fact_listings f
            WHERE f.price IS NOT NULL
            GROUP BY f.room_type
            ORDER BY avg_price DESC
        """,

        "Superhost vs Non-Superhost Performance": """
            SELECT
                h.host_is_superhost,
                COUNT(DISTINCT h.host_id) AS host_count,
                COUNT(f.listing_id) AS listing_count,
                ROUND(AVG(f.price), 2) AS avg_price,
                ROUND(AVG(f.review_scores_rating), 2) AS avg_rating,
                ROUND(AVG(f.occupancy_rate), 1) AS avg_occupancy_pct
            FROM fact_listings f
            JOIN dim_host h ON f.host_id = h.host_id
            GROUP BY h.host_is_superhost
        """,

        "Top 5 Neighbourhoods by Estimated Annual Revenue": """
            SELECT
                neighbourhood,
                COUNT(*) AS listing_count,
                ROUND(AVG(est_annual_revenue), 0) AS avg_annual_revenue,
                ROUND(AVG(occupancy_rate), 1) AS avg_occupancy_pct,
                ROUND(MEDIAN(price), 2) AS median_price
            FROM fact_listings
            WHERE est_annual_revenue IS NOT NULL
            GROUP BY neighbourhood
            ORDER BY avg_annual_revenue DESC
            LIMIT 5
        """,

        "Host Segment Analysis": """
            SELECT
                h.host_segment,
                COUNT(DISTINCT h.host_id) AS host_count,
                COUNT(f.listing_id) AS total_listings,
                ROUND(AVG(f.price), 2) AS avg_price,
                ROUND(AVG(f.review_scores_rating), 2) AS avg_rating,
                ROUND(AVG(f.occupancy_rate), 1) AS avg_occupancy_pct
            FROM fact_listings f
            JOIN dim_host h ON f.host_id = h.host_id
            WHERE h.host_segment IS NOT NULL
            GROUP BY h.host_segment
            ORDER BY host_count DESC
        """,

        "Weekend vs Weekday Occupancy by Room Type": """
            SELECT
                room_type,
                ROUND(AVG(weekend_occupancy_rate), 2) AS avg_weekend_occupancy,
                ROUND(AVG(weekday_occupancy_rate), 2) AS avg_weekday_occupancy,
                ROUND(AVG(weekend_occupancy_rate) - AVG(weekday_occupancy_rate), 2) AS occupancy_diff
            FROM fact_listings
            WHERE weekend_occupancy_rate IS NOT NULL
            GROUP BY room_type
            ORDER BY occupancy_diff DESC
        """,
    }

    results = {}
    for name, query in queries.items():
        logger.info(f"Running: {name}")
        result = conn.execute(query).fetchdf()
        print(f"\n--- {name} ---")
        print(result.to_string(index=False))
        results[name] = result

    conn.close()
    return results


if __name__ == "__main__":
    from src.ingest import (
        load_listings, load_listings_detailed,
        load_calendar, load_reviews_summary
    )
    from src.clean import clean_listings, clean_calendar
    from src.enrich import build_master_table

    listings  = clean_listings(load_listings())
    detailed  = load_listings_detailed()
    calendar  = clean_calendar(load_calendar())
    reviews_s = load_reviews_summary()
    master    = build_master_table(listings, detailed, calendar, reviews_s)

    build_star_schema(master)
    run_analytical_queries()