from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    bot_token: SecretStr
    weather_token: SecretStr
    trip_map_token: SecretStr

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
