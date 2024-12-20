#!/usr/bin/env python3
import datetime
import time
import traceback
import sys
import os
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
from pathlib import Path

# Global retry configuration
MAX_RETRIES = 8
RETRY_DELAY = 8 # seconds
POEM_INTERVAL = 17  # minutes between poems

def print_debug_info():
    """Print debug information about the environment"""
    print("\n=== Debug Information ===")
    print(f"Current time (UTC): {datetime.datetime.utcnow()}")
    print(f"Current time (Local): {datetime.datetime.now()}")
    print(f"REPO_PATH: {REPO_PATH}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"COHERE_API_KEY exists: {'Yes' if COHERE_API_KEY else 'No'}")
    print(f"Python version: {sys.version}")
    print("Environment variables:")
    for key, value in os.environ.items():
        if 'KEY' in key or 'TOKEN' in key:
            print(f"  {key}: {'[REDACTED]'}")
        else:
            print(f"  {key}: {value}")
    print("=== End Debug Info ===\n")

def should_generate_poems():
    """Determine if we should generate poems now"""
    now = datetime.datetime.now()
    print(f"\nChecking if poems should be generated at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
        folder_path = automation.get_or_create_daily_folder()
        existing_poems = count_existing_poems(folder_path)
        
        print(f"Found {existing_poems} existing poems for today")
        print(f"Current hour (local): {now.hour}")
        print(f"Current hour (UTC): {datetime.datetime.utcnow().hour}")
        
        # If we have all 28 poems, don't generate more
        if existing_poems >= 28:
            print("Already have 28 poems for today. No more poems needed.")
            return False
        
        # Always generate if we have started (have some poems)
        if existing_poems > 0:
            print("Continuing poem generation as we have existing poems.")
            return True
        
        # If no poems yet, start at 8 AM
        if now.hour >= 8:
            print("It's after 8 AM, starting new poem generation.")
            return True
        
        print("Waiting for 8 AM to start new poem generation.")
        return False
        
    except Exception as e:
        print(f"Error checking poem status: {str(e)}")
        print(traceback.format_exc())
        # If there's an error, return True to attempt generation
        return True

def count_existing_poems(folder_path):
    """Count how many poems exist in the current day's folder"""
    if not folder_path.exists():
        print(f"Folder does not exist: {folder_path}")
        return 0
    poems = list(folder_path.glob("[0-9][0-9]_RB_*.md"))
    print(f"Found poems: {[p.name for p in poems]}")
    return len(poems)

def calculate_next_poem_time(current_poems):
    """Calculate when the next poem should be generated"""
    base_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    if current_poems == 0 and datetime.datetime.now().hour < 8:
        # If no poems and before 8 AM, start at 8 AM today
        return base_time
    elif current_poems == 0:
        # If no poems and after 8 AM, start immediately
        return datetime.datetime.now()
    else:
        # Calculate next time based on current poem count
        return base_time + datetime.timedelta(minutes=current_poems * POEM_INTERVAL)

def run_daily_automation():
    """Run the daily automation process"""
    print(f"\nStarting daily automation at {datetime.datetime.now()}")
    print_debug_info()
    
    if not should_generate_poems():
        print("No poems to generate at this time.")
        return
    
    try:
        automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
        folder_path = automation.get_or_create_daily_folder()
        existing_poems = count_existing_poems(folder_path)
        
        print(f"\nCurrent status:")
        print(f"Folder: {folder_path}")
        print(f"Existing poems: {existing_poems}")
        
        next_poem_time = calculate_next_poem_time(existing_poems)
        print(f"Next poem scheduled for: {next_poem_time}")
        
        # Generate remaining poems
        for poem_number in range(existing_poems + 1, 29):
            try:
                # Wait until scheduled time
                wait_time = (next_poem_time - datetime.datetime.now()).total_seconds()
                if wait_time > 0:
                    print(f"\nWaiting {wait_time/60:.1f} minutes until {next_poem_time}")
                    time.sleep(wait_time)
                
                print(f"\nGenerating poem {poem_number}/28")
                file_path = automation.create_poem_file(folder_path, poem_number)
                
                if file_path and file_path.exists():
                    print(f"Created poem at: {file_path}")
                    automation.git_commit_and_push(file_path)
                    
                    # Calculate next poem time
                    next_poem_time = datetime.datetime.now() + datetime.timedelta(minutes=POEM_INTERVAL)
                    print(f"Next poem scheduled for: {next_poem_time}")
                else:
                    print("Failed to create poem file!")
                
            except Exception as e:
                print(f"Error generating poem {poem_number}: {str(e)}")
                print(traceback.format_exc())
                time.sleep(RETRY_DELAY)
                continue
        
        print(f"\nCompleted daily automation at {datetime.datetime.now()}")
        
    except Exception as e:
        print(f"Error in daily automation: {str(e)}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        print(f"\n{'='*50}")
        print(f"Daily Poem Automation")
        print(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        run_daily_automation()
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)
    sys.exit(0)