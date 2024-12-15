#!/usr/bin/env python3
import time
import datetime
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH

def run_daily_automation():
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    folder_path = automation.get_or_create_daily_folder()
    
    print(f"Starting daily automation at {datetime.datetime.now()}")
    print(f"Using folder: {folder_path}")
    
    # Generate exactly 28 poems with 28-minute intervals
    for poem_number in range(1, 29):  # 1 to 28
        try:
            print(f"\nGenerating poem {poem_number}/28 at {datetime.datetime.now()}")
            
            # Create and commit the poem
            file_path = automation.create_poem_file(folder_path, poem_number)
            if file_path and file_path.exists():
                print(f"Created poem at: {file_path}")
                
                # Display poem content
                with open(file_path, 'r', encoding='utf-8') as f:
                    print("\nPoem content:")
                    print("-" * 50)
                    print(f.read())
                    print("-" * 50)
                
                # Commit and push
                automation.git_commit_and_push(file_path)
                print(f"Pushed poem {poem_number} to git")
            
            # Wait 28 minutes before next poem (unless it's the last poem)
            if poem_number < 28:
                print(f"\nWaiting 28 minutes until next poem...")
                time.sleep(28 * 60)  # 28 minutes in seconds
                
        except Exception as e:
            print(f"Error creating poem {poem_number}: {str(e)}")
            # Wait before retrying
            time.sleep(60)
            continue
    
    print(f"\nCompleted daily automation at {datetime.datetime.now()}")

if __name__ == "__main__":
    # Run forever, once per day
    while True:
        # Get current time
        now = datetime.datetime.now()
        
        # Set target time to 00:00:00 (midnight) of the next day
        target_time = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # If it's not yet time to run
        if now < target_time:
            # Calculate sleep duration
            sleep_seconds = (target_time - now).total_seconds()
            print(f"Waiting until midnight ({target_time})...")
            time.sleep(sleep_seconds)
        
        # Run the automation
        run_daily_automation() 