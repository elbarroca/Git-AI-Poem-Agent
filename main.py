from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH

def main():
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    automation.run_daily_automation()

if __name__ == "__main__":
    main() 