from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
import time

def test_poem_generation():
    # Create automation instance
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    
    print("Starting poem generation test...")
    
    try:
        # Get or create today's folder
        folder_path = automation.get_or_create_daily_folder()
        print(f"\nUsing folder: {folder_path}")
        
        # Generate 3 test poems
        for i in range(3):
            print(f"\nGenerating poem {i + 1}...")
            file_path = automation.create_poem_file(folder_path, i + 1)
            
            # Read and display the generated poem
            if file_path and file_path.exists():
                print(f"\nGenerated poem {i + 1} at: {file_path}")
                print("\nPoem content:")
                print("-" * 50)
                print(file_path.read_text())
                print("-" * 50)
                
                # Optional: test git operations
                automation.git_commit_and_push(file_path)
                print(f"Pushed poem {i + 1} to git")
            
            # Small delay between poems
            if i < 2:  # Don't delay after the last poem
                print("\nWaiting 10 seconds before next poem...")
                time.sleep(10)
            
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    test_poem_generation() 