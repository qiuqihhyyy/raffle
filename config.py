import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )

    # получение токена
    def get_token(self) -> str:
        """Возвращает URL вебхука с кодированием специальных символов."""
        return self.BOT_TOKEN

    # получение админ id
    def get_admin_id(self) -> int:
        return self.ADMIN_ID

# admin_ids=list(map(int, env.list('ADMIN_IDS'))),
# channel_id=int(env('CHANNEL_ID'))

settings = Settings()