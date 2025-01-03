#!/usr/bin/env python3
import os
from pathlib import Path
from git_art_generator import GitArtGenerator

def main():
    # Get the repository path (current directory)
    repo_path = Path(os.getcwd())
    
    print("Starting Git Contribution Art Generator")
    print(f"Repository path: {repo_path}")
    
    # Create and run the art generator
    generator = GitArtGenerator(repo_path)
    
    try:
        # Generate the art commits
        generator.create_art_commits()
        
        # Push changes to remote
        generator.push_changes()
        
        print("\nArt generation completed successfully!")
        print("Check your GitHub profile to see the contribution art.")
        print("Note: It may take a few minutes for GitHub to update the contribution graph.")
        
    except Exception as e:
        print(f"\nError during art generation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 