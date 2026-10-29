import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.getenv("ATLAS_DATA_DIR", str(ROOT / "data")))
DATABASE_URL = os.getenv(
    "ATLAS_DATABASE_URL", "postgresql://atlasiq:atlasiq_local@127.0.0.1:5544/atlasiq"
)
DEFAULT_MONTH = "2025-01"
DEFAULT_LIMIT = 100_000
