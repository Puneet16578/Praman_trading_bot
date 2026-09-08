"""Environment-backed settings. Same pattern as InsightForge: frozen dataclass, no secrets in code."""
from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("PRAMAN_DATABASE_PATH", str(ROOT / "data" / "processed" / "praman.db"))
    fixture_dir: Path = ROOT / "data" / "fixtures"
    raw_data_dir: Path = ROOT / "data" / "raw"
    nse_request_delay_seconds: float = float(os.getenv("PRAMAN_NSE_REQUEST_DELAY_SECONDS", "1.0"))
    sebi_orders_base_url: str = os.getenv("PRAMAN_SEBI_ORDERS_BASE_URL", "https://www.sebi.gov.in/enforcement/orders.html")
    sebi_request_delay_seconds: float = float(os.getenv("PRAMAN_SEBI_REQUEST_DELAY_SECONDS", "2.0"))
    request_timeout_seconds: float = float(os.getenv("PRAMAN_REQUEST_TIMEOUT_SECONDS", "30.0"))

def get_settings() -> Settings:
    return Settings()
