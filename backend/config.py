"""App configuration from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str = ""   # required for write ops; get from Supabase → Settings → API
    SUPABASE_ANON_KEY: str = ""

    # Stripe (optional in dev — billing endpoints will fail gracefully)
    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    STRIPE_PRICE_ID: str = "price_placeholder"
    STRIPE_TRIAL_DAYS: int = 5

    # Hugging Face (optional in dev — AI endpoints will return fallback text)
    HUGGINGFACE_API_TOKEN: str = "hf_placeholder"
    HF_DEFAULT_MODEL: str = "tiiuae/falcon-7b-instruct"
    HF_FALLBACK_MODEL: str = "allenai/OLMo-7B-Instruct-hf"

    # Resend (optional in dev — emails will be skipped silently)
    RESEND_API_KEY: str = "re_placeholder"
    RESEND_FROM_EMAIL: str = "belon@belon.ai"
    RESEND_FROM_NAME: str = "Belon AI"

    # HubSpot
    HUBSPOT_APP_ID: str = ""
    HUBSPOT_CLIENT_ID: str = ""
    HUBSPOT_CLIENT_SECRET: str = ""
    HUBSPOT_REDIRECT_URI: str = "http://localhost:8000/integrations/hubspot/callback"

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Signal Engine
    SIGNAL_ENGINE_INTERVAL_MINUTES: int = 15
    SIGNAL_ENGINE_BATCH_SIZE: int = 50

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
