import logging
import os
from pathlib import Path

# Project root paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
DB_DIR = ROOT_DIR / "db"

def get_logger(name: str) -> logging.Logger:
    """Return a consistently formatted logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)

def ensure_dirs():
 
    for d in [DATA_RAW, DATA_PROCESSED, DB_DIR]:
        d.mkdir(parents=True, exist_ok=True)