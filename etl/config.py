import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'saas_analytics')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    RAW_DATA_PATH = 'simulation_output'

    @classmethod
    def validate(cls):
        if not cls.DB_USER:
            raise ValueError("DB_USER environment variable not set")
        if not cls.DB_PASSWORD:
            raise ValueError("DB_PASSWORD environment variable not set")
        return True