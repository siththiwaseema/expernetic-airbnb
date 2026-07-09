import gzip
import shutil
import pandas as pd
from pathlib import Path
from src.utils import get_logger, DATA_RAW, DATA_PROCESSED, ensure_dirs

logger = get_logger(__name__)


def extract_gz(gz_path: Path) -> Path:
    out_path = DATA_PROCESSED / gz_path.stem  # removes .gz, keeps .csv
    if out_path.exists():
        logger.info(f"Already extracted: {out_path.name} — skipping")
        return out_path
    logger.info(f"Extracting {gz_path.name} ...")
    with gzip.open(gz_path, "rb") as f_in:
        with open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    logger.info(f"Extracted to {out_path}")
    return out_path


def load_listings() -> pd.DataFrame:
    """Load and return the core listings CSV."""
    path = extract_gz(DATA_RAW / "listings.csv.gz")
    logger.info("Loading listings ...")
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Listings loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_listings_detailed() -> pd.DataFrame:
    """Load and return the detailed listings CSV (no gz)."""
    path = DATA_RAW / "listings.csv"
    logger.info("Loading detailed listings ...")
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Detailed listings loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_calendar() -> pd.DataFrame:
    """Load and return the calendar CSV."""
    path = extract_gz(DATA_RAW / "calendar.csv.gz")
    logger.info("Loading calendar ...")
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Calendar loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_reviews() -> pd.DataFrame:
    """Load and return the full reviews CSV."""
    path = extract_gz(DATA_RAW / "reviews.csv.gz")
    logger.info("Loading reviews ...")
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Reviews loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_reviews_summary() -> pd.DataFrame:
    """Load and return the reviews summary CSV (no gz)."""
    path = DATA_RAW / "reviews.csv"
    logger.info("Loading reviews summary ...")
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Reviews summary loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_neighbourhoods() -> pd.DataFrame:
    """Load and return the neighbourhoods CSV."""
    path = DATA_RAW / "neighbourhoods.csv"
    logger.info("Loading neighbourhoods ...")
    df = pd.read_csv(path)
    logger.info(f"Neighbourhoods loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_geojson() -> dict:
    """Load and return the neighbourhoods GeoJSON as a dict."""
    import json
    path = DATA_RAW / "neighbourhoods.geojson"
    logger.info("Loading GeoJSON ...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"GeoJSON loaded: {len(data['features'])} features")
    return data


def ingest_all() -> dict:
    """Run full ingestion pipeline and return all dataframes."""
    ensure_dirs()
    logger.info("=== Starting full ingestion pipeline ===")
    datasets = {
        "listings":          load_listings(),
        "listings_detailed": load_listings_detailed(),
        "calendar":          load_calendar(),
        "reviews":           load_reviews(),
        "reviews_summary":   load_reviews_summary(),
        "neighbourhoods":    load_neighbourhoods(),
        "geojson":           load_geojson(),
    }
    logger.info("=== Ingestion complete ===")
    return datasets


if __name__ == "__main__":
    ingest_all()