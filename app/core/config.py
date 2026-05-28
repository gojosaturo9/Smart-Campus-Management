from dataclasses import dataclass
import os
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback is intentionally narrow.
    tomllib = None

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    @property
    def _secrets(self) -> dict:
        if tomllib is None:
            return {}
        merged: dict = {}
        for path in self.secrets_files:
            if not path.exists():
                continue
            with path.open("rb") as handle:
                _deep_merge(merged, tomllib.load(handle))
        return merged

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
    def secrets_file(self) -> Path:
        return self.platform_dir / "secrets.toml"

    @property
    def secrets_files(self) -> tuple[Path, ...]:
        return (
            self.platform_dir / ".streamlit.toml",
            self.platform_dir / ".streamlit" / "secrets.toml",
            self.secrets_file,
        )

    @property
    def app_name(self) -> str:
        return "Smart Campus Management Platform"

    @property
    def environment(self) -> str:
        return os.getenv("APP_ENV", "development").strip().lower()

    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}

    @property
    def session_secret(self) -> str:
        return (
            os.getenv("PLATFORM_SESSION_SECRET")
            or self._secrets.get("app", {}).get("session_secret")
            or "change-this-dev-secret-before-production"
        )

    @property
    def session_https_only(self) -> bool:
        value = os.getenv("SESSION_HTTPS_ONLY", "")
        if value:
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return self.environment == "production"

    @property
    def supabase_url(self) -> str:
        return os.getenv("SUPABASE_URL") or self._secrets.get("supabase", {}).get("url", "")

    @property
    def supabase_anon_key(self) -> str:
        return os.getenv("SUPABASE_ANON_KEY") or self._secrets.get("supabase", {}).get("anon_key", "")

    @property
    def supabase_service_role_key(self) -> str:
        return (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or self._secrets.get("supabase", {}).get("service_role_key", "")
        )

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

    @property
    def audit_log_path(self) -> Path:
        return self.data_dir / "audit.log"

    def env(self, key: str, default: str = "") -> str:
        value = os.getenv(key)
        if value is not None:
            return value.strip()
        module_values = self._secrets.get("modules", {})
        secret_value = module_values.get(key.lower())
        if secret_value is not None:
            return str(secret_value).strip()
        return default.strip()

    def validate_startup(self) -> None:
        if self.environment != "production":
            return

        missing = []
        if self.session_secret == "change-this-dev-secret-before-production":
            missing.append("PLATFORM_SESSION_SECRET")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_anon_key:
            missing.append("SUPABASE_ANON_KEY")
        if not self.supabase_service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required production configuration: {joined}")


settings = Settings()
load_dotenv(settings.env_file)


def _deep_merge(target: dict, source: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target
