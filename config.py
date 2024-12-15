import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration settings
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
REPO_PATH = os.getenv('REPO_PATH')

if not COHERE_API_KEY or not REPO_PATH:
    raise ValueError("Missing required environment variables. Please check your .env file.")