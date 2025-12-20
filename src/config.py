import os
from dotenv import load_dotenv

load_dotenv()

# Data & DB Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(BASE_DIR, "db")

# Chunking Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Rate Limiting (Default settings for Gemini Free)
# Adjust based on your specific tier limits
RPM_LIMIT = 5          # Requests Per Minute
TPM_LIMIT = 10000     # Tokens Per Minute
SLEEP_INTERVAL = 1.0    # Seconds to check/sleep

# API Keys
# Expects a comma-separated list of keys
GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")
GOOGLE_API_KEYS = [k.strip() for k in GOOGLE_API_KEYS if k.strip()]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Local Model (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

if not GOOGLE_API_KEYS:
    print("Warning: No GOOGLE_API_KEYS found in .env file. Retrieval might fail.")
