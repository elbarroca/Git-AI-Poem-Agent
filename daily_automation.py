#!/usr/bin/env python3
import time
import datetime
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

def should_start_now():
    """Determine if we should start now or wait for 8 AM"""
    now = datetime.datetime.now()
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    folder_path = automation.get_or_create_daily_folder()
    
    existing_poems = count_existing_poems(folder_path)
    
    # If we have no poems yet and it's before 8 AM, wait
    if existing_poems == 0 and now.hour < 8:
        return False
    
    # If we have unfinished poems (less than 28), continue regardless of time
    if existing_poems < 28:
        return True
    
    # If all poems are done, wait for next day
    return False

def run_daily_automation():
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    folder_path = automation.get_or_create_daily_folder()
    
    print(f"Starting automation at {datetime.datetime.now()}")
    print(f"Using folder: {folder_path}")
    
    # Count existing poems to determine where to start
    existing_poems = count_existing_poems(folder_path)
    start_number = existing_poems + 1
    
    print(f"Found {existing_poems} existing poems. Starting from poem {start_number}")
    
    # Generate remaining poems sequentially with 16-minute intervals
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
                
                # Commit and push this poem before waiting
                automation.git_commit_and_push(file_path)
                print(f"Successfully committed and pushed poem {poem_number}")
                
                # Calculate time spent on creation and push
                time_spent = (datetime.datetime.now() - start_time).total_seconds()
                
                # Wait remaining time to complete 8 minutes for operation if needed
                if time_spent < 8 * 60:
                    remaining_operation_time = (8 * 60) - time_spent
                    print(f"\nWaiting {remaining_operation_time:.0f} seconds to complete 8-minute operation window...")
                    time.sleep(remaining_operation_time)
                
                # If there's another poem to generate, wait 8 minutes
                if poem_number < 28:
                    print(f"Waiting 8 minutes before next poem...")
                    time.sleep(8 * 60)  # 8 minutes wait
            
        except Exception as e:
            print(f"Error creating poem {poem_number}: {str(e)}")
            # Wait a minute before retrying
            time.sleep(60)
            continue
    
    print(f"\nCompleted daily automation at {datetime.datetime.now()}")

if __name__ == "__main__":
    while True:
        if should_start_now():
            # Run the automation immediately if we have unfinished poems
            run_daily_automation()
        else:
            # Wait until next 8 AM if we're starting fresh
            next_run = get_next_run_time()
            now = datetime.datetime.now()
            wait_seconds = (next_run - now).total_seconds()
            
            print(f"Waiting until {next_run.strftime('%Y-%m-%d %H:%M:%S')} to start automation...")
            time.sleep(wait_seconds)
            
            # Run the automation
            run_daily_automation() 