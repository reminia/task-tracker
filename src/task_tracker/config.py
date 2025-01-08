from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LINEAR_API_KEY: str
    TIMETRACKING_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings() 