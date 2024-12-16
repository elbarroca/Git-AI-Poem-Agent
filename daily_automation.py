#!/usr/bin/env python3
import datetime
import time
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
from pathlib import Path

def get_next_run_time():
    """Calculate the next 8 AM run time"""
    now = datetime.datetime.now()
    next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # If it's already past 8 AM today, set for tomorrow
    if now >= next_run:
        next_run = next_run + datetime.timedelta(days=1)
    
    return next_run

def count_existing_poems(folder_path):
    """Count how many poems exist in the current day's folder"""
    if not folder_path.exists():
        return 0
    return len(list(folder_path.glob("[0-9][0-9]_RB_*.md")))

def should_generate_poems():
    """Determine if we should generate poems now"""
    now = datetime.datetime.now()
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    folder_path = automation.get_or_create_daily_folder()
    
    existing_poems = count_existing_poems(folder_path)
    
    # If we have all 28 poems, don't generate more
    if existing_poems >= 28:
        print("Already have 28 poems for today. No more poems needed.")
        return False
        
    # If we have no poems and it's before 8 AM, don't start yet
    if existing_poems == 0 and now.hour < 8:
        print("No poems yet and it's before 8 AM. Waiting for scheduled time.")
        return False
    
    # If we have unfinished poems (less than 28), continue
    return True

def run_daily_automation():
    if not should_generate_poems():
        print("No poems to generate at this time.")
        return
        
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    folder_path = automation.get_or_create_daily_folder()
    
    print(f"Starting automation at {datetime.datetime.now()}")
    print(f"Using folder: {folder_path}")
    
    # Count existing poems to determine where to start
    existing_poems = count_existing_poems(folder_path)
    start_number = existing_poems + 1
    
    print(f"Found {existing_poems} existing poems. Starting from poem {start_number}")
    
    # Generate remaining poems sequentially with delays
    for poem_number in range(start_number, 29):  # Continue until we have all 28
        try:
            start_time = datetime.datetime.now()
            print(f"\nGenerating poem {poem_number}/28 at {start_time}")
            
            # Create the poem
            file_path = automation.create_poem_file(folder_path, poem_number)
            
            if file_path and file_path.exists():
                print(f"Created poem at: {file_path}")
                
                # Display poem content
                with open(file_path, 'r', encoding='utf-8') as f:
                    print("\nPoem content:")
                    print("-" * 50)
                    print(f.read())
                    print("-" * 50)
                
                # Commit and push this poem
                automation.git_commit_and_push(file_path)
                print(f"Successfully committed and pushed poem {poem_number}")
                
                # Add a small delay between poems to avoid rate limiting
                if poem_number < 28:
                    delay_time = 30  # 30 seconds delay between poems
                    print(f"Waiting {delay_time} seconds before next poem...")
                    time.sleep(delay_time)
            
        except Exception as e:
            print(f"Error creating poem {poem_number}: {str(e)}")
            # Wait a bit before failing
            time.sleep(10)
            raise  # Re-raise the exception to fail the GitHub Action
    
    print(f"\nCompleted daily automation at {datetime.datetime.now()}")

if __name__ == "__main__":
    run_daily_automation() 