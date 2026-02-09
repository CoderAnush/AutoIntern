from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
