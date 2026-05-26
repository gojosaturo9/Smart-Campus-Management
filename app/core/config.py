from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    @property
    def app_dir(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def platform_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def env_file(self) -> Path:
        return self.platform_dir / ".env"

    @property
    def app_name(self) -> str:
        return "Smart Campus Management Platform"

    @property
    def session_secret(self) -> str:
        return os.getenv("PLATFORM_SESSION_SECRET", "change-this-dev-secret-before-production")

    @property
    def workspace_dir(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def templates_dir(self) -> Path:
        return self.app_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.app_dir / "static"

    @property
    def data_dir(self) -> Path:
        return self.platform_dir / "data"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "smartcampus.db"

    def env(self, key: str, default: str = "") -> str:
        return os.getenv(key, default).strip()


settings = Settings()
load_dotenv(settings.env_file)
