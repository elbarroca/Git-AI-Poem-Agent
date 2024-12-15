import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

# Validate required environment variables
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY environment variable is not set")