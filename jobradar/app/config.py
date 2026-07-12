from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Scheduler
    SCRAPE_INTERVAL_HOURS: int = 6

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_NAME: str = "JobRadar"
    SMTP_FROM_EMAIL: str

    # Outreach
    EMAIL_SEND_DELAY_SECONDS: int = 5
    EMAIL_COOLDOWN_DAYS: int = 30

    # Applicant profile (injected into every cover letter)
    APPLICANT_SKILLS: str = "Python, FastAPI, Django, React, PostgreSQL, REST APIs"
    APPLICANT_GITHUB: str = "github.com/Olalekan2040-slack"
    APPLICANT_WEBSITE: str = "Quaddev.com"
    CV_PATH: str = "SHARAFDEEN QUADRI.pdf"

    # Sentry (optional)
    SENTRY_DSN: str = ""


settings = Settings()
