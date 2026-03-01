from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM
    llm_primary_model: str = "claude-sonnet-4-6"
    llm_fallback_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_monthly_budget_usd: float = 10.0

    # 네이버 쇼핑 API
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # 이메일
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    report_email_to: str = ""

    # 애플리케이션
    database_url: str = "sqlite+aiosqlite:///./data/shopigent.db"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True

    # 스크래핑
    scrape_delay_min: float = 2.0
    scrape_delay_max: float = 8.0
    max_concurrent_scrapers: int = 3


settings = Settings()
