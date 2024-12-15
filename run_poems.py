#!/usr/bin/env python3
import argparse
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
import time

def run_poem_generation(num_poems=2, delay_minutes=1):
    """
    Run poem generation with configurable parameters
    
    Args:
        num_poems (int): Number of poems to generate (default: 2)
        delay_minutes (int): Delay between poems in minutes (default: 1)
    """
    # Create automation instance
    automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
    
    print(f"Starting poem generation for {num_poems} poems...")
    
    try:
        # Get or create today's folder
        folder_path = automation.get_or_create_daily_folder()
        print(f"\nUsing folder: {folder_path}")
        
        # Generate specified number of poems
        for i in range(num_poems):
            print(f"\nGenerating poem {i + 1}/{num_poems}...")
            file_path = automation.create_poem_file(folder_path, i + 1)
            
            # Read and display the generated poem
            if file_path and file_path.exists():
                print(f"\nGenerated poem {i + 1} at: {file_path}")
                print("\nPoem content:")
                print("-" * 50)
                with open(file_path, 'r', encoding='utf-8') as f:
                    print(f.read())
                print("-" * 50)
                
                # Commit and push to git
                automation.git_commit_and_push(file_path)
                print(f"Pushed poem {i + 1} to git")
            
            # Delay between poems (unless it's the last poem)
            if i < num_poems - 1:
                print(f"\nWaiting {delay_minutes} minutes before next poem...")
                time.sleep(delay_minutes * 60)
            
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Generate and commit poems')
    parser.add_argument('--poems', type=int, default=2,
                      help='Number of poems to generate (default: 2)')
    parser.add_argument('--delay', type=int, default=1,
                      help='Delay between poems in minutes (default: 1)')
    
    args = parser.parse_args()
    run_poem_generation(args.poems, args.delay)

if __name__ == "__main__":
    main() 