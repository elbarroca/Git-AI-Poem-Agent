#!/usr/bin/env python3
import os
from pathlib import Path
from git_art_generator import GitArtGenerator

def main():
    # Get the repository path (current directory)
    repo_path = Path(os.getcwd())
    
    print("Starting Git Contribution Pattern Generator")
    print(f"Repository path: {repo_path}")
    
    # Create and run the pattern generator
    generator = GitArtGenerator(repo_path)
    
    try:
        # Generate and save the commit pattern
        output_file = generator.save_commit_map()
        
        print("\nPattern generation completed successfully!")
        print(f"Pattern saved to: {output_file}")
        print("\nNext steps:")
        print("1. Update your daily automation to read commit_pattern.json")
        print("2. Modify the number of commits based on the pattern")
        print("3. Normal days: 8 commits")
        print("4. Pattern days: 17 commits")
        
    except Exception as e:
        print(f"\nError during pattern generation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 