#!/usr/bin/env python3
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
import time

def test_poem_generation():
    """Test poem generation with new vertical formatting"""
    # Create automation instance
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    
    print("Starting poem generation test...")
    
    try:
        # Get or create today's folder
        folder_path = automation.get_or_create_daily_folder()
        print(f"\nUsing folder: {folder_path}")
        
        # Generate 2 test poems
        for i in range(2):
            poem_number = i + 1
            print(f"\n{'='*50}")
            print(f"Generating test poem {poem_number}/2...")
            print(f"{'='*50}")
            
            # Create and push the poem
            file_path = automation.create_poem_file(folder_path, poem_number)
            
            if file_path and file_path.exists():
                print(f"\n📝 Generated poem {poem_number} at: {file_path}")
                
                # Display poem content
                print("\n📖 Poem content:")
                print("-" * 50)
                with open(file_path, 'r', encoding='utf-8') as f:
                    print(f.read())
                print("-" * 50)
                
                # Commit and push to git
                print("\n🚀 Pushing to git...")
                automation.git_commit_and_push(file_path)
                print(f"✅ Successfully pushed poem {poem_number}")
                
                # Wait between poems
                if i < 1:  # Don't wait after the last poem
                    print("\n⏳ Waiting 8 minutes before next poem...")
                    time.sleep(8 * 60)  # 8 minutes
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    test_poem_generation() 