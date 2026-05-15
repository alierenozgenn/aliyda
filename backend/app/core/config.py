from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Aliyda"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()