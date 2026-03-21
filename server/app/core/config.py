from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    token_expiry: int = 60
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    session_cookie_name: str = "session_token"
    csrf_cookie_name: str = "csrf_token"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    
settings = Settings()