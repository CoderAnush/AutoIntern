from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    migrate_on_start: bool = False  # set to true in local dev to create tables on startup

    class Config:
        env_file = ".env"

settings = Settings()
