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
    
    def validate_poem_structure(self, poem_text):
        """Validate basic poem structure"""
        try:
            # Split the poem into parts
            lines = poem_text.strip().split('\n')
            
            # Extract title and content
            title_line = None
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('Title:'):
                    title_line = line
                elif title_line and line:  # Only count non-empty lines after title
                    content_lines.append(line)
            
            # Verify we have content
            if len(content_lines) < 1:
                print(f"❌ Invalid poem structure: No content lines found")
                return False
            
            # Verify each line has meaningful content
            for i, line in enumerate(content_lines, 1):
                if not line or line.isspace() or '...' in line or '[' in line or ']' in line:
                    print(f"❌ Invalid content in line {i}: '{line}'")
                    return False
            
            print("✅ Poem structure validation passed:")
            print(f"- Title: {title_line}")
            print(f"- Content lines: {len(content_lines)}")
            return True
            
        except Exception as e:
            print(f"❌ Poem validation error: {str(e)}")
            return False

    def format_poem_content(self, poem_text):
        """Format the poem with enhanced Markdown in vertical format"""
        # Split into lines
        lines = poem_text.strip().split('\n')
        
        # Extract title and content
        title = None
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
            elif title and line:  # Only include non-empty lines after title
                content_lines.append(line)
        
        # Ensure we don't exceed 8 lines
        content_lines = content_lines[:8]
        
        # Format the final content with enhanced Markdown
        formatted_content = f"""# {title}

> *An abstract exploration of {title.lower()}*

{chr(10).join([f"**{i+1}.**\n{line}\n" for i, line in enumerate(content_lines)])}

---
*Written on {datetime.datetime.now().strftime("%Y-%m-%d")}*  
**Creator**: Ricardo Barroca Poem Agent  
**Theme**: Abstract Art Poetry
"""
        return formatted_content, title

    def generate_poem(self, poem_number):
        """Generate a poem using Cohere API with context awareness"""
        context = self.get_poem_context()
        
        # Define themes with guidelines
        themes = {
            "abstract concepts and consciousness": "Explore the nature of awareness, perception, and the self",
            "time and existence": "Examine the relationship between temporality and being",
            "dreams and surrealism": "Blend dream-like imagery with reality-bending concepts",
            "cosmic interconnectedness": "Explore the unity of all things in the universe",
            "metaphysical questions": "Investigate fundamental questions about reality and existence",
            "emotional landscapes": "Map feelings onto abstract and physical terrains",
            "quantum reality": "Explore quantum concepts like superposition and entanglement",
            "collective unconscious": "Delve into shared human experiences and archetypes",
            "metamorphosis and transformation": "Examine change and evolution of consciousness",
            "infinite possibilities": "Explore the boundless nature of potential and existence"
        }
        
        # Select three themes randomly but weighted by poem number
        base_theme = list(themes.keys())[poem_number % len(themes)]
        other_themes = list(set(themes.keys()) - {base_theme})
        import random
        selected_themes = [base_theme] + random.sample(other_themes, 2)
        
        # Get guidelines for selected themes
        theme_guidelines = "\n".join([f"- {theme}: {themes[theme]}" for theme in selected_themes])
        
        prompt = f"""
        Context: {context}

        Task: Create a concise abstract art poem (maximum 8 lines) that weaves together these three themes:
        {theme_guidelines}

        POETIC ELEMENTS TO INCLUDE:
        * Imagery:
          - Dense, powerful metaphors
          - Abstract concepts distilled to essence
          - Rich sensory details
          - Deep philosophical insights
        
        * Techniques:
          - Each line must be impactful and complete
          - Mix different senses (synesthesia)
          - Use internal rhymes and sound patterns
          - Create unexpected connections
        
        * Structure:
          - Maximum 8 lines total
          - Each line should be meaningful and standalone
          - Progress from concrete to abstract
          - End with transcendental insight
        
        FORMAT:
        1. Start with: "Title: [Your Abstract Title]"
        2. Skip ONE line
        3. Write your poem (maximum 8 lines)
        4. Each line should be complete and powerful
        5. Avoid clichés and common phrases

        Remember: Create a concentrated journey through abstract consciousness that combines all three themes.
        Important: Only output the title and poem (max 8 lines), no additional text or formatting.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.cohere.chat(
                    message=prompt,
                    model="command-r-plus-08-2024",
                    temperature=0.92,  # Slightly increased for creativity
                    max_tokens=1000
                )
                
                # Get poem text
                poem_text = ""
                if hasattr(response, 'text'):
                    poem_text = response.text.strip()
                elif hasattr(response, 'message'):
                    poem_text = response.message.strip()
                else:
                    poem_text = str(response).strip()
                
                # Validate basic structure
                if poem_text.startswith('Title:'):
                    # Ensure we don't exceed 8 lines
                    lines = poem_text.split('\n')
                    title_line = lines[0]
                    content_lines = [line for line in lines[1:] if line.strip()]
                    if len(content_lines) > 8:
                        content_lines = content_lines[:8]
                    return title_line + '\n\n' + '\n'.join(content_lines)
                else:
                    print(f"Attempt {attempt + 1}: Invalid poem structure, retrying...")
                    continue
                    
            except Exception as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                continue
        
        raise ValueError("Failed to generate a valid poem after multiple attempts")
    
    def get_or_create_daily_folder(self):
        """Get or create hierarchical folder structure: poems/YYYY/MM/Week_N/DD_Weekday"""
        today = datetime.datetime.now()
        
        # Create base poems directory
        poems_dir = self.repo_path / "poems"
        poems_dir.mkdir(exist_ok=True)
        
        # Create year folder (YYYY)
        year_folder = poems_dir / today.strftime("%Y")
        year_folder.mkdir(exist_ok=True)
        
        # Create month folder (MM)
        month_folder = year_folder / today.strftime("%m")
        month_folder.mkdir(exist_ok=True)
        
        # Calculate week number within the month
        week_number = (today.day - 1) // 7 + 1
        weekly_folder = month_folder / f"Week_{week_number}"
        weekly_folder.mkdir(exist_ok=True)
        
        # Create daily folder with weekday name
        daily_folder = weekly_folder / today.strftime("%d_%A")
        daily_folder.mkdir(exist_ok=True)
        
        # Print folder structure for visibility
        print(f"\n📁 Poem Directory Structure:")
        print(f"poems")
        print(f"└── {year_folder.name}")
        print(f"    └── {month_folder.name}")
        print(f"        └── {weekly_folder.name}")
        print(f"            └── {daily_folder.name}")
        
        self.daily_folder = daily_folder
        return daily_folder
    
    def create_poem_file(self, folder_path, index):
        """Create a file with a poem in the proper folder structure"""
        today = datetime.datetime.now()
        
        # Create folder structure
        poems_dir = self.repo_path / "poems"
        year_folder = poems_dir / today.strftime("%Y")
        month_folder = year_folder / today.strftime("%m")
        week_number = (today.day - 1) // 7 + 1
        weekly_folder = month_folder / f"Week_{week_number}"
        daily_folder = weekly_folder / today.strftime("%d_%A")
        
        # Ensure all folders exist
        for folder in [poems_dir, year_folder, month_folder, weekly_folder, daily_folder]:
            folder.mkdir(exist_ok=True)
        
        # Generate and validate the poem
        max_attempts = 3
        poem = None
        
        for attempt in range(max_attempts):
            try:
                generated_poem = self.generate_poem(index)
                if self.validate_poem_structure(generated_poem):
                    poem = generated_poem
                    break
                else:
                    print(f"Attempt {attempt + 1}: Invalid poem structure, retrying...")
            except Exception as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    raise
        
        if not poem:
            raise ValueError("Failed to generate a valid poem after multiple attempts")
        
        # Format the poem content
        formatted_content, title = self.format_poem_content(poem)
        
        # Create file name
        sanitized_title = "".join(c for c in title if c.isalnum() or c in [' ', '-']).strip()
        sanitized_title = sanitized_title.replace(' ', '-')
        file_name = f"RB_{sanitized_title}.md"
        file_path = daily_folder / file_name
        
        # Skip if file already exists
        if file_path.exists():
            print(f"Poem {index} already exists, skipping...")
            return file_path
        
        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        
        # Print structure and verification
        print(f"\n📁 Created poem in folder structure:")
        print(f"poems")
        print(f"└── {year_folder.name}")
        print(f"    └── {month_folder.name}")
        print(f"        └── {weekly_folder.name}")
        print(f"            └── {daily_folder.name}")
        print(f"                └── {file_name}")
        
        # Verify final content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract only the numbered lines from the content
            poem_lines = [line for line in content.split('\n') 
                         if line.strip() and line.strip().startswith('**') and '.**' in line]
            
            print(f"\n✅ Final poem verification:")
            print(f"Title: {title}")
            print(f"Content lines: {len(poem_lines)}")
            
        return file_path
    
    def git_commit_and_push(self, file_path):
        """Commit and push changes to git"""
        self.repo.index.add([str(file_path)])
        
        # Read the poem title from the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            poem_title = content.split('\n')[0].replace('# ', '')
        
        commit_message = f"✨ Created Poem: {poem_title} 📝"
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