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

if not GOOGLE_API_KEYS:
    raise ValueError("No GOOGLE_API_KEYS found in .env file. Please add at least one key.")
