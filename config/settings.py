import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class ScannerSettings(BaseModel):
    """Configuration settings for OpenMarketScanner."""

    # Data Provider
    default_provider: str = Field(default_factory=lambda: os.getenv("DEFAULT_DATA_PROVIDER", "simulator"))
    polygon_api_key: str = Field(default_factory=lambda: os.getenv("POLYGON_API_KEY", ""))
    fmp_api_key: str = Field(default_factory=lambda: os.getenv("FMP_API_KEY", ""))

    # Engine Throughput
    concurrent_workers: int = Field(default_factory=lambda: int(os.getenv("CONCURRENT_WORKERS", "50")))
    scan_interval_seconds: int = Field(default_factory=lambda: int(os.getenv("SCAN_INTERVAL_SECONDS", "15")))
    universe_size: int = Field(default_factory=lambda: int(os.getenv("UNIVERSE_SIZE", "5000")))

    # Quantitative Filters
    min_price: float = Field(default_factory=lambda: float(os.getenv("MIN_STOCK_PRICE", "2.00")))
    max_price: float = Field(default_factory=lambda: float(os.getenv("MAX_STOCK_PRICE", "500.00")))
    min_avg_volume: int = Field(default_factory=lambda: int(os.getenv("MIN_AVG_VOLUME_30D", "500000")))
    min_rvol: float = Field(default_factory=lambda: float(os.getenv("MIN_RVOL_THRESHOLD", "2.0")))
    min_gap_pct: float = Field(default_factory=lambda: float(os.getenv("MIN_GAP_PERCENT", "3.0")))
    consolidation_bars: int = Field(default_factory=lambda: int(os.getenv("MIN_BREAKOUT_CONSOLIDATION_BARS", "20")))

    # Real-Time Alerts
    enable_telegram: bool = Field(default_factory=lambda: os.getenv("ENABLE_TELEGRAM_ALERTS", "false").lower() in ("true", "1", "yes"))
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    enable_discord: bool = Field(default_factory=lambda: os.getenv("ENABLE_DISCORD_ALERTS", "false").lower() in ("true", "1", "yes"))
    discord_webhook_url: str = Field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))

    # Server API
    api_host: str = Field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))


settings = ScannerSettings()

