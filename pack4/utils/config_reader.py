from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    width: int
    height: int
    food_static: int
    state_delay_ms: int
    game_name: str
    user_name: str
    cell_size: int

    class Config:
        env_file = "./game.env"
        env_file_encoding = "utf-8"


class GameConfig:

    def __init__(self, width, height, food_static, state_delay_ms, game_name, user_name, cell_size):
        self.width = width
        self.height = height
        self.food_static = food_static
        self.state_delay_ms = state_delay_ms
        self.game_name = game_name
        self.user_name = user_name
        self.cell_size = cell_size


# config = Settings()
