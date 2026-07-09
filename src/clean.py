import pandas as pd
import numpy as np
from src.utils import get_logger, DATA_PROCESSED

logger = get_logger(__name__)


# ─── Price Cleaning ────────────────────────────────────────────────────────────

def clean_price(series: pd.Series) -> pd.Series:
    """Remove currency symbols and convert price to float."""
    return (
        series.astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .str.strip()
        .replace("", np.nan)
        .replace("nan", np.nan)
        .astype(float)
    )


# ─── Date Cleaning ─────────────────────────────────────────────────────────────

def clean_dates(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """Parse date columns to datetime."""
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            null_count = df[col].isna().sum()
            if null_count > 0:
                logger.warning(f"{col}: {null_count:,} unparseable dates set to NaT")
    return df


# ─── Listings Cleaning ─────────────────────────────────────────────────────────

def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline for the core listings dataframe."""
    logger.info("Cleaning listings ...")
    original_shape = df.shape

    # --- Price columns
    for col in ["price", "weekly_price", "monthly_price", "security_deposit",
                "cleaning_fee", "extra_people"]:
        if col in df.columns:
            df[col] = clean_price(df[col])

    # --- Date columns
    date_cols = ["last_scraped", "host_since", "calendar_last_scraped",
                 "first_review", "last_review"]
    df = clean_dates(df, date_cols)

    # --- Numeric columns: cast and clip
    if "bedrooms" in df.columns:
        df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce").clip(lower=0)
    if "bathrooms" in df.columns:
        df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce").clip(lower=0)
    if "beds" in df.columns:
        df["beds"] = pd.to_numeric(df["beds"], errors="coerce").clip(lower=0)
    if "accommodates" in df.columns:
        df["accommodates"] = pd.to_numeric(df["accommodates"], errors="coerce").clip(lower=1)

    # --- Normalize categorical fields
    if "room_type" in df.columns:
        df["room_type"] = df["room_type"].str.strip().str.title()
    if "property_type" in df.columns:
        df["property_type"] = df["property_type"].str.strip().str.title()
    if "neighbourhood_cleansed" in df.columns:
        df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].str.strip().str.title()

    # --- Boolean columns
    for col in ["host_is_superhost", "host_identity_verified",
                "host_has_profile_pic", "instant_bookable"]:
        if col in df.columns:
            df[col] = df[col].map({"t": True, "f": False, True: True, False: False})

    # --- Validate coordinates
    if "latitude" in df.columns and "longitude" in df.columns:
        invalid_coords = (
            (df["latitude"] < -90) | (df["latitude"] > 90) |
            (df["longitude"] < -180) | (df["longitude"] > 180)
        )
        if invalid_coords.sum() > 0:
            logger.warning(f"Flagging {invalid_coords.sum()} rows with invalid coordinates")
            df["invalid_coords"] = invalid_coords

    # --- Validate price: flag negative or zero prices
    if "price" in df.columns:
        invalid_price = df["price"] <= 0
        logger.info(f"Listings with zero/negative price: {invalid_price.sum():,}")
        df = df[~invalid_price].copy()

    # --- Derived fields
    if "host_since" in df.columns:
        df["host_tenure_years"] = (
            pd.Timestamp.now() - df["host_since"]
        ).dt.days / 365.25

    if "price" in df.columns and "bedrooms" in df.columns:
        df["price_per_bedroom"] = df["price"] / df["bedrooms"].replace(0, np.nan)

    if "number_of_reviews" in df.columns and "host_tenure_years" in df.columns:
        df["review_frequency"] = (
            df["number_of_reviews"] / df["host_tenure_years"].replace(0, np.nan)
        )

    logger.info(f"Listings cleaned: {original_shape} → {df.shape}")
    return df


# ─── Calendar Cleaning ─────────────────────────────────────────────────────────

def clean_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the calendar dataframe."""
    logger.info("Cleaning calendar ...")

    # --- Parse dates
    df = clean_dates(df, ["date"])

    # --- Price
    if "price" in df.columns:
        df["price"] = clean_price(df["price"])
    if "adjusted_price" in df.columns:
        df["adjusted_price"] = clean_price(df["adjusted_price"])

    # --- Available flag
    if "available" in df.columns:
        df["available"] = df["available"].map({"t": True, "f": False})

    # --- Day of week and weekend flag
    if "date" in df.columns:
        df["day_of_week"] = df["date"].dt.day_name()
        df["is_weekend"] = df["date"].dt.dayofweek >= 5

    logger.info(f"Calendar cleaned: {df.shape[0]:,} rows")
    return df


# ─── Reviews Cleaning ──────────────────────────────────────────────────────────

def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the reviews dataframe."""
    logger.info("Cleaning reviews ...")

    df = clean_dates(df, ["date"])

    # --- Drop rows with no comment text
    if "comments" in df.columns:
        before = len(df)
        df = df[df["comments"].notna() & (df["comments"].str.strip() != "")].copy()
        logger.info(f"Dropped {before - len(df):,} reviews with empty comments")

    logger.info(f"Reviews cleaned: {df.shape[0]:,} rows")
    return df


# ─── Data Quality Report ───────────────────────────────────────────────────────

def profile_dataframe(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Generate a data quality profile for a dataframe."""
    logger.info(f"Profiling {name} ...")
    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.values,
        "null_count": df.isna().sum().values,
        "null_pct": (df.isna().sum().values / len(df) * 100).round(2),
        "unique_count": df.nunique().values,
        "sample_value": [df[col].dropna().iloc[0] if df[col].notna().any()
                         else None for col in df.columns],
    })
    profile = profile.sort_values("null_pct", ascending=False)
    return profile


if __name__ == "__main__":
    from src.ingest import load_listings, load_calendar, load_reviews

    listings = clean_listings(load_listings())
    calendar = clean_calendar(load_calendar())
    reviews  = clean_reviews(load_reviews())

    print("\n--- Listings Profile (top 10 by nulls) ---")
    print(profile_dataframe(listings, "listings").head(10).to_string(index=False))

    print("\n--- Calendar sample ---")
    print(calendar.head(3).to_string())

    print("\n--- Reviews sample ---")
    print(reviews.head(3).to_string())