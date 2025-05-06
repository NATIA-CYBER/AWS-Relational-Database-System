import os
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import unquote

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = '5432'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'aircraft_db'
    
    def clean_env_value(value):
        # Clean environment variable value by removing quotes and encoding special characters
        if not value:
            return value
        
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        # URL encode special characters
        return unquote(value)

    # AWS settings
    AWS_ACCESS_KEY_ID: str = clean_env_value(os.environ.get('AWS_ACCESS_KEY_ID', ''))
    AWS_SECRET_ACCESS_KEY: str = clean_env_value(os.environ.get('AWS_SECRET_ACCESS_KEY', ''))
    AWS_REGION: str = clean_env_value(os.environ.get('AWS_REGION', 'us-east-1'))
    S3_BUCKET: str = clean_env_value(os.environ.get('S3_BUCKET', ''))


    class Config:
        env_file = '.env'

settings = Settings()

engine = create_engine(
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
