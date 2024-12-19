#!/usr/bin/env python3
import datetime
import time
import traceback
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
from pathlib import Path

# Global retry configuration
MAX_RETRIES = 8
RETRY_DELAY = 8 # seconds
POEM_INTERVAL = 17  # minutes between poems

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
    
    for attempt in range(MAX_RETRIES):
        try:
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
            
        except Exception as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} to check poem status failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise

def calculate_poem_schedule():
    """Calculate the schedule for all 28 poems starting at 8 AM with 17-minute intervals"""
    base_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    # If it's past 8 AM, use tomorrow
    if datetime.datetime.now() >= base_time:
        base_time = base_time + datetime.timedelta(days=1)
    
    # Generate schedule for all 28 poems (17 minutes apart)
    schedule = []
    for i in range(28):
        poem_time = base_time + datetime.timedelta(minutes=i*POEM_INTERVAL)
        schedule.append(poem_time)
    
    return schedule

def wait_until_next_poem(target_time):
    """Wait precisely until the next scheduled poem time"""
    now = datetime.datetime.now()
    wait_time = (target_time - now).total_seconds()
    
    if wait_time > 0:
        print(f"\nWaiting until {target_time.strftime('%H:%M:%S')} for next poem...")
        print(f"Wait time: {wait_time/60:.1f} minutes")
        time.sleep(wait_time)

def run_daily_automation():
    """Run the daily automation process with robust error handling"""
    if not should_generate_poems():
        print("No poems to generate at this time.")
        return
    
    for attempt in range(MAX_RETRIES):
        try:
            automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
            folder_path = automation.get_or_create_daily_folder()
            
            print(f"Starting automation at {datetime.datetime.now()}")
            print(f"Using folder: {folder_path}")
            
            # Calculate schedule for all poems
            schedule = calculate_poem_schedule()
            
            # Count existing poems to determine where to start
            existing_poems = count_existing_poems(folder_path)
            start_number = existing_poems + 1
            
            print(f"Found {existing_poems} existing poems. Starting from poem {start_number}")
            print("\nPoem Schedule:")
            for i, time in enumerate(schedule[start_number-1:], start_number):
                print(f"Poem {i}: {time.strftime('%H:%M:%S')}")
            
            # Generate remaining poems according to schedule
            for poem_number, target_time in enumerate(schedule[start_number-1:], start_number):
                for poem_attempt in range(MAX_RETRIES):
                    try:
                        # Wait until the exact scheduled time
                        wait_until_next_poem(target_time)
                        
                        start_time = datetime.datetime.now()
                        print(f"\nGenerating poem {poem_number}/28 at {start_time}")
                        
                        # Create the poem with retry logic
                        file_path = None
                        for create_attempt in range(MAX_RETRIES):
                            try:
                                file_path = automation.create_poem_file(folder_path, poem_number)
                                if file_path and file_path.exists():
                                    break
                            except Exception as e:
                                print(f"Poem creation attempt {create_attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                                if create_attempt < MAX_RETRIES - 1:
                                    time.sleep(RETRY_DELAY)
                                else:
                                    raise
                        
                        if file_path and file_path.exists():
                            print(f"Created poem at: {file_path}")
                            
                            # Display poem content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                print("\nPoem content:")
                                print("-" * 50)
                                print(f.read())
                                print("-" * 50)
                            
                            # Add a small delay before git operations
                            time.sleep(3)
                            
                            # Git operations with retry logic
                            for git_attempt in range(MAX_RETRIES):
                                try:
                                    automation.git_commit_and_push(file_path)
                                    print(f"Successfully committed and pushed poem {poem_number}")
                                    break
                                except Exception as e:
                                    print(f"Git operation attempt {git_attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                                    if git_attempt < MAX_RETRIES - 1:
                                        time.sleep(RETRY_DELAY)
                                    else:
                                        raise
                            
                            # Calculate completion percentage
                            progress = (poem_number / 28) * 100
                            remaining = 28 - poem_number
                            print(f"\nProgress: {progress:.1f}% complete")
                            print(f"Remaining poems: {remaining}")
                            
                            # Calculate time spent on this poem
                            time_spent = (datetime.datetime.now() - start_time).total_seconds()
                            
                            if poem_number < 28:
                                next_time = schedule[poem_number]
                                time_until = next_time - datetime.datetime.now()
                                print(f"Next poem scheduled for: {next_time.strftime('%H:%M:%S')}")
                                print(f"Time until next poem: {time_until}")
                                
                                # If we finished early, wait the remaining time
                                if time_until.total_seconds() > 0:
                                    print(f"Waiting {time_until.total_seconds():.0f} seconds until next scheduled poem...")
                                    time.sleep(time_until.total_seconds())
                            
                            # Successfully completed this poem, break the retry loop
                            break
                            
                    except Exception as e:
                        print(f"Poem attempt {poem_attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                        print("Full error details:")
                        print(traceback.format_exc())
                        
                        if poem_attempt < MAX_RETRIES - 1:
                            print(f"Retrying poem {poem_number} in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                        else:
                            print(f"Failed to generate poem {poem_number} after {MAX_RETRIES} attempts")
                            # Continue to next poem after max retries
                            continue
            
            print(f"\nCompleted daily automation at {datetime.datetime.now()}")
            print(f"Total poems generated today: {count_existing_poems(folder_path)}")
            break
            
        except Exception as e:
            print(f"Daily automation attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
            print("Full error details:")
            print(traceback.format_exc())
            
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying entire automation in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Failed to complete daily automation after maximum retries")
                raise

if __name__ == "__main__":
    try:
        run_daily_automation()
    except Exception as e:
        print(f"Fatal error in daily automation: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)
    sys.exit(0) 