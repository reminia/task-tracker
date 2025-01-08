from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LINEAR_API_KEY: str
    TIMETRACKING_API_KEY: str
    LINEAR_TEAM: str | None = None

    class Config:
        env_file = ".env"

settings = Settings() 