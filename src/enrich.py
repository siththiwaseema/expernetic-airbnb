import pandas as pd
import numpy as np
from src.utils import get_logger, DATA_PROCESSED

logger = get_logger(__name__)


# ─── Join Listings with Detailed Listings ──────────────────────────────────────

def merge_detailed_listings(
    listings: pd.DataFrame,
    listings_detailed: pd.DataFrame
) -> pd.DataFrame:
    """Merge core listings with detailed listings to fill missing host fields."""
    logger.info("Merging core listings with detailed listings ...")

    # Only keep columns from detailed that are missing in core
    missing_cols = [
        col for col in listings_detailed.columns
        if col not in listings.columns or listings[col].isna().all()
    ]
    # Always keep id for joining
    cols_to_merge = ["id"] + [c for c in missing_cols if c != "id"]
    detailed_subset = listings_detailed[cols_to_merge].copy()

    merged = listings.merge(detailed_subset, on="id", how="left", suffixes=("", "_detail"))
    logger.info(f"After merge: {merged.shape[0]:,} rows x {merged.shape[1]} columns")
    return merged


# ─── Compute Occupancy from Calendar ──────────────────────────────────────────

def compute_occupancy(calendar: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-listing occupancy rate from calendar data.
    Note: Bangkok calendar has no price column, so revenue estimates
    are derived from listings price instead.
    """
    logger.info("Computing occupancy rates from calendar ...")

    occ = (
        calendar.groupby("listing_id")
        .agg(
            total_days=("available", "count"),
            booked_days=("available", lambda x: (x == False).sum()),
            weekend_booked=("is_weekend", lambda x: (
                (calendar.loc[x.index, "available"] == False) &
                (calendar.loc[x.index, "is_weekend"] == True)
            ).sum()),
            weekday_booked=("is_weekend", lambda x: (
                (calendar.loc[x.index, "available"] == False) &
                (calendar.loc[x.index, "is_weekend"] == False)
            ).sum()),
        )
        .reset_index()
    )

    occ["occupancy_rate"] = (occ["booked_days"] / occ["total_days"] * 100).round(2)
    occ["weekend_occupancy_rate"] = (occ["weekend_booked"] / occ["total_days"] * 100).round(2)
    occ["weekday_occupancy_rate"] = (occ["weekday_booked"] / occ["total_days"] * 100).round(2)

    logger.info(f"Occupancy computed for {len(occ):,} listings")
    logger.info(f"Avg occupancy rate: {occ['occupancy_rate'].mean():.1f}%")
    return occ


# ─── Neighbourhood Aggregates ─────────────────────────────────────────────────

def compute_neighbourhood_aggregates(listings: pd.DataFrame) -> pd.DataFrame:
    """Compute neighbourhood-level summary statistics."""
    logger.info("Computing neighbourhood aggregates ...")

    agg = (
        listings.groupby("neighbourhood_cleansed")
        .agg(
            listing_count=("id", "count"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            avg_rating=("review_scores_rating", "mean"),
            avg_reviews=("number_of_reviews", "mean"),
            superhost_pct=("host_is_superhost", lambda x: x.sum() / len(x) * 100),
            entire_home_pct=("room_type", lambda x: (x == "Entire Home/Apt").sum() / len(x) * 100),
        )
        .reset_index()
        .round(2)
    )

    agg.columns = [
        "neighbourhood", "listing_count", "median_price", "avg_price",
        "avg_rating", "avg_reviews", "superhost_pct", "entire_home_pct"
    ]

    logger.info(f"Neighbourhood aggregates computed for {len(agg)} neighbourhoods")
    return agg


# ─── Host Segmentation ────────────────────────────────────────────────────────

def segment_hosts(listings: pd.DataFrame) -> pd.DataFrame:
    """Segment hosts by portfolio size."""
    logger.info("Segmenting hosts ...")

    host_counts = (
        listings.groupby("host_id")
        .agg(
            total_listings=("id", "count"),
            avg_price=("price", "mean"),
            avg_rating=("review_scores_rating", "mean"),
            is_superhost=("host_is_superhost", "first"),
        )
        .reset_index()
    )

    host_counts["host_segment"] = pd.cut(
        host_counts["total_listings"],
        bins=[0, 1, 5, 20, float("inf")],
        labels=["Single", "Small (2-5)", "Medium (6-20)", "Large (21+)"]
    )

    logger.info(f"Host segments:\n{host_counts['host_segment'].value_counts().to_string()}")
    return host_counts


# ─── Build Master Table ───────────────────────────────────────────────────────

def build_master_table(
    listings: pd.DataFrame,
    listings_detailed: pd.DataFrame,
    calendar: pd.DataFrame,
    reviews_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build the enriched master listings table."""
    logger.info("=== Building master table ===")

    # Step 1: Merge detailed listings
    master = merge_detailed_listings(listings, listings_detailed)

   # Step 2: Merge reviews summary — aggregate first to avoid row explosion
    logger.info("Merging reviews summary ...")
    if "listing_id" in reviews_summary.columns:
        reviews_summary = reviews_summary.rename(columns={"listing_id": "id"})
    # Aggregate: count reviews per listing
    reviews_agg = (
        reviews_summary.groupby("id")
        .agg(total_reviews_in_file=("id", "count"))
        .reset_index()
    )
    master = master.merge(reviews_agg, on="id", how="left")

    # Step 3: Merge occupancy
    occupancy = compute_occupancy(calendar)
    occupancy = occupancy.rename(columns={"listing_id": "id"})
    master = master.merge(occupancy, on="id", how="left")

    # Estimate annual revenue using listings price x booked days
    if "price" in master.columns and "booked_days" in master.columns:
        master["est_annual_revenue"] = (master["price"] * master["booked_days"]).round(2)
        logger.info(f"Avg estimated annual revenue: ${master['est_annual_revenue'].mean():,.0f}")

    # Step 4: Merge neighbourhood aggregates
    neighbourhood_agg = compute_neighbourhood_aggregates(master)
    master = master.merge(
        neighbourhood_agg,
        left_on="neighbourhood_cleansed",
        right_on="neighbourhood",
        how="left",
        suffixes=("", "_neighbourhood")
    )

    # Step 5: Host segments
    host_segments = segment_hosts(master)
    master = master.merge(
        host_segments[["host_id", "host_segment", "total_listings"]],
        on="host_id",
        how="left"
    )

    logger.info(f"Master table built: {master.shape[0]:,} rows x {master.shape[1]} columns")

    # Save to processed
    out_path = DATA_PROCESSED / "master_listings.csv"
    master.to_csv(out_path, index=False)
    logger.info(f"Master table saved to {out_path}")

    return master


if __name__ == "__main__":
    from src.ingest import (
        load_listings, load_listings_detailed,
        load_calendar, load_reviews_summary
    )
    from src.clean import clean_listings, clean_calendar

    listings  = clean_listings(load_listings())
    detailed  = load_listings_detailed()
    calendar  = clean_calendar(load_calendar())
    reviews_s = load_reviews_summary()

    master = build_master_table(listings, detailed, calendar, reviews_s)

    print("\n--- Master Table Summary ---")
    print(f"Shape: {master.shape}")
    print(f"\nSample columns:")
    print(master[["id", "name", "price", "room_type", "neighbourhood_cleansed",
                  "occupancy_rate", "est_annual_revenue", "host_segment"]].head(5).to_string())