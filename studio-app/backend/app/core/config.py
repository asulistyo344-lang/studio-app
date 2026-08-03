from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    byteplus_api_key: str
    byteplus_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    byteplus_image_model: str = "seedream-4-5-251128"
    byteplus_3d_model: str = "hyper3d-rodin-20250412"

    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_ai3d_region: str = "ap-guangzhou"

    database_url: str = "postgresql+asyncpg://studio:studio@127.0.0.1:5432/studio_db"

    # Nebula=DB0, Aura=DB1, Boost=DB2 on the shared VPS Redis — Studio=DB3
    redis_url: str = "redis://127.0.0.1:6379/3"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Local-disk storage for generated results (StorageService) — swappable
    # for S3/R2 later behind the same interface. public_base_url is used to
    # build full servable URLs for stored files (and must match whatever the
    # frontend/browser can actually reach — the real domain in production).
    storage_path: str = "./storage"
    public_base_url: str = "http://localhost:8006"

    # Transactional email via Resend's REST API (no mail server). Empty by
    # default — EmailService no-ops (logs + skips) rather than raising, so
    # missing credentials never break registration/generation/credit flows.
    resend_api_key: str = ""
    email_from_address: str = "Anom AI SaaS <onboarding@resend.dev>"
    frontend_base_url: str = "http://localhost:5173"

    app_name: str = "Anom-AI-SaaS"
    port: int = 8006
    environment: str = "development"

    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
