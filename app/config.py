"""Environment-driven configuration. No secrets in code."""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DATA_DIR = Path(os.getenv("DEMO_DATA_DIR", ROOT_DIR / "demo-data"))
CONTEXT_DEV_API_KEY = os.getenv("CONTEXT_DEV_API_KEY", "")
SITE_LOCATION = os.getenv("SITE_LOCATION", "London")
CONTEXT_DEV_BASE_URL = os.getenv("CONTEXT_DEV_BASE_URL", "https://api.context.dev/v1")
