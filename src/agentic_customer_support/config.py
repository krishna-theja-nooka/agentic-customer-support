from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SUPPORT_AGENT_", env_file=".env", extra="ignore")

    db_path: Path = Path("data/support.sqlite3")
    api_key: str = Field(default="", repr=False)
    requests_per_minute: int = Field(default=30, ge=1, le=300)
    max_refund_usd: int = Field(default=250, ge=1, le=1000)
