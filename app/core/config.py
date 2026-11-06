from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    BOOTSTRAP_TOKEN: str

    DATABASE_URL: str
    REDIS_URL: str

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, url: str) -> str:
        """
        Accept a connection string pasted straight from a hosted Postgres
        provider (Neon, Supabase, Render, Heroku) without hand editing.

        Handles three incompatibilities with the asyncpg driver:
        - forces the asyncpg driver when a plain `postgresql://` URL is given
        - renames libpq's `sslmode` parameter to asyncpg's `ssl`
        - drops `channel_binding`, which asyncpg does not accept

        Other parameters are preserved, so deliberately tuned URLs (for
        example the local Docker database with no TLS settings) pass through
        unchanged.
        """
        if not url:
            return url

        scheme, separator, rest = url.partition("://")
        if not separator:
            return url

        if "+" not in scheme and scheme in ("postgres", "postgresql"):
            scheme = "postgresql+asyncpg"

        parts = urlsplit(f"{scheme}://{rest}")
        query = [
            ("ssl" if key == "sslmode" else key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key != "channel_binding"
        ]

        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
