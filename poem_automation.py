import os
import datetime
import random
from cohere import Client
import git
from pathlib import Path
import time
import logging
from logging.handlers import RotatingFileHandler

class PoemAutomation:
    def __init__(self, cohere_api_key, repo_path):
        self.cohere = Client(cohere_api_key)
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.daily_folder = None
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging to store logs in the logs folder"""
        # Create logs directory if it doesn't exist
        logs_dir = self.repo_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create log files with timestamps
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Main log file
        main_log = logs_dir / f"poem_automation_{timestamp}.log"
        
        # Error log file
        error_log = logs_dir / f"poem_automation_error_{timestamp}.log"
        
        # Configure main logger
        self.logger = logging.getLogger('PoemAutomation')
        self.logger.setLevel(logging.INFO)
        
        # Rotating file handler for main log (max 10MB per file, keep 5 backup files)
        main_handler = RotatingFileHandler(
            main_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.INFO)
        main_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        main_handler.setFormatter(main_formatter)
        
        # Rotating file handler for error log
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s')
        error_handler.setFormatter(error_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Clean up old log files
        self._cleanup_old_logs(logs_dir)
        
        self.logger.info("Logging initialized successfully")
    
    def _cleanup_old_logs(self, logs_dir):
        """Clean up log files older than 7 days"""
        try:
            current_time = datetime.datetime.now()
            for log_file in logs_dir.glob("*.log*"):
                file_time = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                if (current_time - file_time).days > 7:
                    self.logger.info(f"Removing old log file: {log_file}")
                    log_file.unlink()
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {str(e)}")
    
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
        
        # Format the final content with enhanced Markdown and vertical spacing
        formatted_content = f"""# {title}

> *An abstract exploration through consciousness and time*

{chr(10).join([f"**{i+1}.** {line}{chr(10)}{chr(10)}" for i, line in enumerate(content_lines)])}

---

*Generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}*  
**Creator**: Ricardo Barroca's AI Poetry Agent  
**Theme**: Quantum Abstract Poetry  
**Collection**: Daily Philosophical Reflections
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
        """Get or create hierarchical folder structure: poems/YYYY/MM_Month/DD_Weekday"""
        today = datetime.datetime.now()
        
        # Create base poems directory
        poems_dir = self.repo_path / "poems"
        poems_dir.mkdir(exist_ok=True)
        
        # Create year folder (YYYY)
        year_folder = poems_dir / str(today.year)
        year_folder.mkdir(exist_ok=True)
        
        # Create month folder (MM_MonthName)
        month_name = today.strftime("%B")  # Full month name
        month_folder = year_folder / f"{today.strftime('%m')}_{month_name}"
        month_folder.mkdir(exist_ok=True)
        
        # Create daily folder with weekday name
        daily_folder = month_folder / today.strftime("%d_%A")  # e.g., "15_Friday"
        daily_folder.mkdir(exist_ok=True)
        
        # Print folder structure for visibility
        print(f"\n📁 Current Poetry Structure:")
        print(f"poems/")
        print(f"└── {year_folder.name}/")
        print(f"    └── {month_folder.name}/")
        print(f"        └── {daily_folder.name}/")
        
        # Clean up old files and empty folders
        self._cleanup_old_folders(poems_dir, today)
        
        self.daily_folder = daily_folder
        return daily_folder
    
    def _cleanup_old_folders(self, poems_dir, current_date):
        """Clean up old folders and files, keeping only recent ones"""
        try:
            # Keep only current year and month
            for year_dir in poems_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                
                year = int(year_dir.name)
                if year < current_date.year:
                    self.logger.info(f"Removing old year folder: {year_dir}")
                    import shutil
                    shutil.rmtree(year_dir)
                    continue
                
                # Clean up months in current year
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    month = int(month_dir.name.split('_')[0])
                    if month < current_date.month:
                        self.logger.info(f"Removing old month folder: {month_dir}")
                        import shutil
                        shutil.rmtree(month_dir)
                        continue
                    
                    # Clean up days in current month
                    for day_dir in month_dir.iterdir():
                        if not day_dir.is_dir():
                            continue
                        
                        day = int(day_dir.name.split('_')[0])
                        if day < current_date.day:
                            self.logger.info(f"Removing old day folder: {day_dir}")
                            import shutil
                            shutil.rmtree(day_dir)
                            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

    def create_poem_file(self, folder_path, index):
        """Create a file with a poem in the proper folder structure"""
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
                if attempt == max_retries - 1:
                    raise
        
        if not poem:
            raise ValueError("Failed to generate a valid poem after multiple attempts")
        
        # Format the poem content
        formatted_content, title = self.format_poem_content(poem)
        
        # Create file name with index for proper ordering
        sanitized_title = "".join(c for c in title if c.isalnum() or c in [' ', '-']).strip()
        sanitized_title = sanitized_title.replace(' ', '-')
        file_name = f"{index:02d}_RB_{sanitized_title}.md"
        file_path = folder_path / file_name
        
        # Skip if file already exists
        if file_path.exists():
            print(f"Poem {index} already exists, skipping...")
            return file_path
        
        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        
        # Print structure and verification
        print(f"\n✅ Created poem {index}:")
        print(f"Path: {file_path}")
        print(f"Title: {title}")
        
        return file_path
    
    def git_commit_and_push(self, file_path):
        """Commit and push changes to git with enhanced error handling"""
        try:
            # Set git configuration
            print("Setting git configuration...")
            self.repo.git.config('--global', 'pull.rebase', 'false')
            self.repo.git.config('--global', 'pull.ff', 'false')
            self.repo.git.config('--global', 'merge.ff', 'false')

            # Ensure we're on the main branch
            current = self.repo.active_branch
            if current.name != 'main':
                print(f"Switching from {current.name} to main branch...")
                self.repo.heads.main.checkout()

            # Fetch all changes
            print("Fetching latest changes...")
            origin = self.repo.remote(name='origin')
            origin.fetch()

            # Merge strategy
            try:
                print("Pulling with merge strategy...")
                self.repo.git.pull('origin', 'main', '--no-rebase')
            except Exception as pull_error:
                print(f"Pull failed: {str(pull_error)}")
                # If pull fails, try to merge manually
                try:
                    print("Attempting manual merge...")
                    self.repo.git.merge('origin/main', '--no-ff')
                except Exception as merge_error:
                    print(f"Merge failed: {str(merge_error)}")
                    # If merge fails, abort and try to recover
                    print("Aborting merge and trying to recover...")
                    self.repo.git.merge('--abort')
                    raise

            # Add the file
            print(f"Adding file: {file_path}")
            self.repo.index.add([str(file_path)])
            
            # Read the poem title from the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                poem_title = content.split('\n')[0].replace('# ', '')
            
            # Create detailed commit message
            poem_number = file_path.name.split('_')[0]
            commit_message = f"""✨ Created Poem {poem_number}: {poem_title} 📝

• Type: Daily Quantum Poetry
• Number: Poem {poem_number} of 28
• Path: {file_path.relative_to(self.repo_path)}
• Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # Commit changes
            print("Committing changes...")
            self.repo.index.commit(commit_message)
            
            # Push changes with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Pushing changes to origin/main (attempt {attempt + 1}/{max_retries})...")
                    self.repo.git.push('origin', 'main', '--force-with-lease')
                    print("Successfully pushed changes to main! 🚀")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Push attempt {attempt + 1} failed: {str(e)}")
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
            
        except Exception as e:
            error_msg = f"Error in git operations: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
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