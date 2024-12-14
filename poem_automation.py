import os
import datetime
import random
from cohere import Client
import git
from pathlib import Path
import time

class PoemAutomation:
    def __init__(self, cohere_api_key, repo_path):
        self.cohere = Client(cohere_api_key)
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.daily_folder = None
        
    def load_existing_poems(self):
        """Load all existing poems from today's folder"""
        if not self.daily_folder or not self.daily_folder.exists():
            return []
        
        poems = []
        # Sort files numerically by poem number
        poem_files = sorted(
            self.daily_folder.glob("poem_*.txt"),
            key=lambda x: int(x.stem.split('_')[1])
        )
        
        for poem_file in poem_files:
            with open(poem_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract just the poem part (skip timestamp and poem number)
                poem_parts = content.split('\n\n', 2)
                if len(poem_parts) >= 3:
                    poems.append(poem_parts[2])
        
        return poems
    
    def get_poem_context(self):
        """Create context from all previously generated poems today"""
        existing_poems = self.load_existing_poems()
        
        if not existing_poems:
            return "This is the first poem of the day."
            
        context = "Previously generated poems today:\n\n"
        for i, poem in enumerate(existing_poems, 1):
            context += f"Poem {i}:\n{poem}\n\n"
        return context
    
    def generate_poem(self, poem_number):
        """Generate a poem using Cohere API with context awareness"""
        context = self.get_poem_context()
        
        # Define themes and select one based on poem number
        themes = [
            "nature and wilderness",
            "human emotions and relationships",
            "life's journey and personal growth",
            "seasons and time",
            "love and connection",
            "hope and inspiration",
            "dreams and aspirations",
            "technology and future",
            "urban life and society",
            "philosophical questions"
        ]
        suggested_theme = themes[poem_number % len(themes)]
        
        prompt = f"""
        Context: {context}

        Task: Write poem #{poem_number} out of 28 for today, following these guidelines:
        - Length: 4-8 lines
        - Must use the theme: {suggested_theme}
        - Must be completely different in style from any previous poems
        - Use vivid imagery and metaphors
        - Can be in any poetry style (free verse, haiku, etc.)
        - Must be original and not repeat concepts from previous poems
        - Format the output exactly like this:
          Title: [Your Title Here]
          
          [Poem lines here]
          [More poem lines]
          [...]

        Create a thoughtful and emotionally resonant poem that offers a fresh perspective.
        Remember: This is poem #{poem_number} out of 28, so make it unique.
        Important: Only output the title and poem, no additional text or formatting.
        """

        response = self.cohere.chat(
            message=prompt,
            model="command-r-plus-08-2024",
            temperature=0.8,
            max_tokens=300
        )
        
        # Handle the response correctly
        if hasattr(response, 'text'):
            return response.text.strip()
        elif hasattr(response, 'message'):
            return response.message.strip()
        else:
            return str(response).strip()
    
    def get_or_create_daily_folder(self):
        """Get existing daily folder or create if it doesn't exist"""
        today = datetime.datetime.now()
        folder_name = today.strftime("%Y-%m-%d_%A")
        folder_path = self.repo_path / folder_name
        
        if not folder_path.exists():
            folder_path.mkdir(exist_ok=True)
            print(f"Created new daily folder: {folder_path}")
        else:
            print(f"Using existing daily folder: {folder_path}")
            
        self.daily_folder = folder_path
        return folder_path
    
    def create_poem_file(self, folder_path, index):
        """Create a file with a poem"""
        file_name = f"poem_{index:02d}.md"
        file_path = folder_path / file_name
        
        # Skip if file already exists
        if file_path.exists():
            print(f"Poem {index} already exists, skipping...")
            return file_path
        
        poem = self.generate_poem(index)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Format the content in Markdown
        content = f"""# {poem.split('Title: ')[1].split('\n')[0]}

{poem.split('Title: ')[1].split('\n', 1)[1].strip()}

---
**Creator**: Ricardo Barroca Poem Agent | {timestamp}
"""
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return file_path
    
    def git_commit_and_push(self, file_path):
        """Commit and push changes to git"""
        self.repo.index.add([str(file_path)])
        commit_message = f"Added poem: {file_path.name}"
        self.repo.index.commit(commit_message)
        
        # Push changes
        origin = self.repo.remote(name='origin')
        origin.push()
    
    def run_daily_automation(self):
        """Run the daily automation process"""
        folder_path = self.get_or_create_daily_folder()
        
        for i in range(28):
            try:
                # Create poem file
                file_path = self.create_poem_file(folder_path, i + 1)
                if file_path and not file_path.exists():
                    print(f"Created poem {i + 1} at {file_path}")
                    
                    # Commit and push
                    self.git_commit_and_push(file_path)
                    print(f"Pushed poem {i + 1} to git")
                    
                    # Random delay between poems (1-3 minutes)
                    delay = random.randint(60, 180)
                    time.sleep(delay)
                
            except Exception as e:
                print(f"Error creating poem {i + 1}: {str(e)}")
                continue 