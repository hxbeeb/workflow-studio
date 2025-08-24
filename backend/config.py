import os
from dotenv import load_dotenv, dotenv_values

# Load environment variables from .env file
# Handle potential encoding issues gracefully
try:
    load_dotenv()
    print("DEBUG: .env file loaded successfully",dotenv_values())
    print(f"DEBUG: DATABASE_URL from os.environ: {os.environ.get('DATABASE_URL')}")
    print(f"DEBUG: All env vars: {dict(os.environ)}")
    print(f"DEBUG: DATABASE_URL from dotenv_values: {dotenv_values().get('DATABASE_URL')}")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default environment variables")

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./workflow.db"

    # Clerk Authentication
    CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

    # ChromaDB Configuration
    CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
    CHROMA_HOST = os.getenv("CHROMA_HOST")
    CHROMA_TENANT = "37ab43a1-deb4-419d-a4c8-43ed906dff15"
    CHROMA_DATABASE = "bot"
    # Force local usage
    CHROMA_USE_CLOUD = False

    # LLM API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # ChromaDB Settings
    CHROMA_LOCAL_PATH = "./chroma_db_new"
