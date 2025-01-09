from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LINEAR_API_KEY: str
    LINEAR_TEAM: str | None = None

    TRACKINGTIME_USERNAME: str | None = None
    TRACKINGTIME_PASSWORD: str | None = None
    TRACKINGTIME_API_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings() 