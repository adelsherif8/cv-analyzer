import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    # Data Configuration
    DATA_DIR: str = os.getenv("DATA_DIR", "./app/data")
    
    # Computed paths
    @property
    def UPLOADS_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "uploads")
    
    @property
    def RESULTS_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "results")
    
    @property
    def ROLES_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "roles")
    
    @property
    def SAMPLES_DIR(self) -> str:
        return os.path.join(self.DATA_DIR, "samples")

settings = Settings()

# Create data directories on startup
def create_data_directories():
    """Create required data directories if they don't exist"""
    directories = [
        settings.DATA_DIR,
        settings.UPLOADS_DIR,
        settings.RESULTS_DIR,
        settings.ROLES_DIR,
        settings.SAMPLES_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
