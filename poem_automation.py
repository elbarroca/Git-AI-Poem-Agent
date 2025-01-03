import os
import datetime
import random
from cohere import Client
import git
from pathlib import Path
import time
import logging
from logging.handlers import RotatingFileHandler
import json
import traceback

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
            
            # Debug output
            print("\nReceived poem text:")
            print(poem_text)
            print("\nSplit lines:")
            print(lines)
            
            # Extract title and content
            title_line = None
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if 'Title:' in line or line.startswith('#'):  # More flexible title detection
                    title_line = line
                elif line and not line.startswith('>') and not line.startswith('---'):  # Skip formatting lines
                    # Skip empty lines, markdown formatting, and emoji-only lines
                    if (line and not line.isspace() and 
                        not line.startswith('*') and 
                        not line.startswith('#') and
                        not all(c in '✨🌌🌙🌊🎯🌠🌍💫🌟🐲🔢🎭💰🐒🤖🎮🌸🐧🚀🍵 ' for c in line)):
                        content_lines.append(line)
            
            # Verify we have a title
            if not title_line:
                print("❌ Invalid poem structure: No title found")
                return False
            
            # Clean up content lines
            content_lines = [line for line in content_lines if line.strip()]
            
            # Verify we have exactly 8 lines of content
            if len(content_lines) != 8:
                print(f"❌ Invalid poem structure: Found {len(content_lines)} lines, expected 8")
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

    def generate_one_liner(self, themes_used, content_lines):
        """Generate a dynamic Gen Z one-liner based on themes and content"""
        theme_list = [t['theme'] for t in themes_used]
        themes_text = ', '.join(theme_list)
        content_preview = ' '.join(content_lines[:2])  # Use first two lines for context
        
        prompt = f"""
        You are a Gen Z social media expert. Create a single fun, witty one-liner comment about a poem.
        
        The poem is about these themes: {themes_text}
        Here's a preview: {content_preview}
        
        Rules for the one-liner:
        - Must be exactly one line
        - Use Gen Z slang and style
        - Include 1-2 relevant emojis
        - Keep it under 60 characters
        - Make it fun and engaging
        - Reference modern trends/culture
        - Don't use hashtags
        
        Examples of good one-liners:
        - vibing with the cosmic tea, no cap 🌌✨
        - main character energy loading... 🚀
        - living rent free in my head rn 🌟
        - it's giving enlightenment fr fr ✨
        """
        
        try:
            response = self.cohere.chat(
                message=prompt,
                model="command-r-plus-08-2024",
                temperature=0.93,
                max_tokens=60
            )
            
            one_liner = response.text.strip()
            # Clean up the response
            one_liner = one_liner.replace('"', '').replace('*', '').strip()
            return one_liner
            
        except Exception as e:
            self.logger.warning(f"Failed to generate custom one-liner: {str(e)}")
            return "vibes so immaculate they transcend the timeline ✨"

    def format_poem_content(self, poem_text, themes_used):
        """Format the poem with enhanced Markdown in vertical format"""
        # Split into lines
        lines = poem_text.strip().split('\n')
        
        # Extract title and content
        title = "Untitled"  # Default title
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
            elif line.startswith('# '):
                title = line.replace('# ', '').strip()
            elif title and line:  # Only include non-empty lines after title
                content_lines.append(line)
        
        # Ensure we have a valid title
        if not title or title == "Untitled":
            self.logger.warning("No valid title found in poem, using generated title")
            # Generate a title based on the first line if available
            if content_lines:
                title = f"Poem about {content_lines[0][:30]}..."
            else:
                title = f"Quantum Poem {datetime.datetime.now().strftime('%H:%M:%S')}"
        
        # Ensure we don't exceed 8 lines
        content_lines = content_lines[:8]
        
        # Generate a dynamic one-liner
        one_liner = self.generate_one_liner(themes_used, content_lines)
        
        # Format themes used
        theme_list = [t['theme'] for t in themes_used]
        themes_section = "**Themes**: " + " • ".join(theme_list)
        
        # Format the final content with enhanced Markdown and vertical spacing
        formatted_content = f"""# {title}

> *{one_liner}*

{chr(10).join([f"**{i+1}.** {line}{chr(10)}{chr(10)}" for i, line in enumerate(content_lines)])}

---

*Generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}*  
**Creator**: Ricardo Barroca's AI Poetry Agent  
{themes_section}  
**Collection**: A journey through consciousness and reality"""
        
        return formatted_content, title

    def generate_poem(self, poem_number):
        """Generate a poem using Cohere API with context awareness"""
        context = self.get_poem_context()
        # Define available themes
        themes = [
            {
                "theme": "Chinese Astrology",
                "description": "Zodiac wisdom, cosmic cycles, and destiny's dance 🐲"
            },
            {
                "theme": "Numerology", 
                "description": "Sacred numbers and life patterns 🔢"
            },
            {
                "theme": "Satirical Commentary",
                "description": "Witty takes on modern life's chaos 🎭"
            },
            {
                "theme": "Wealth and Freedom",
                "description": "Money moves and soul searching 💰"
            },
            {
                "theme": "Monkeys",
                "description": "Chaos masters and jungle vibes 🐒"
            },
            {
                "theme": "Technology and AI",
                "description": "Digital dreams and robot schemes 🤖"
            },
            {
                "theme": "Traveling",
                "description": "Wanderlust and world wonders 🌍"
            },
            {
                "theme": "Gaming",
                "description": "Level ups and epic quests 🎮"
            },
            {
                "theme": "Money Laundering",
                "description": "Money laundering and tax evasion 💰"
            },
            {
                "theme": "Penguins",
                "description": "Ice cool squad goals 🐧"
            },
            {
                "theme": "Crypto",
                "description": "To the moon and back 🚀"
            },
            {
                "theme": "Japanese Philosophy",
                "description": "Zen vibes and mindful moments 🍵"
            },
            {
                "theme": "Billionaire",
                "description": "Living the luxury life and building empires 💎"
            },
            {
                "theme": "Entrepreneur",
                "description": "Hustling and grinding to success 💼"
            },
            {
                "theme": "888K Month Soon",
                "description": "Manifesting abundance and wealth goals 🎯"
            },
            {
                "theme": "888 Wealth",
                "description": "Manifesting 888 and abundance vibes 💰"
            },
            {
                "theme": "2025 Vision",
                "description": "The gigachad year of pure success 🔥"
            },
            {
                "theme": "Gigachad Life",
                "description": "Breaking rules, making moves, staying alpha 💪"
            },
            {
                "theme": "Blonde Beauty",
                "description": "Golden hair and gorgeous vibes ✨"
            },
            {
                "theme": "Italian Wife",
                "description": "La dolce vita with amore 💝"
            },
            {
                "theme": "Roman Empire",
                "description": "Living that Italian luxury lifestyle 🏛️"
            },
            {
                "theme": "Gen Z Memes Lingo",
                "description": "No cap fr fr, bussin vibes only 💅"
            },
            {
                "theme": "League of Legends",
                "description": "Mid diff and pentakills all day ⚔️"
            },
            {
                "theme": "Humility",
                "description": "Staying grounded while reaching heights 🙏"
            },
            {
                "theme": "China Vibes",
                "description": "Ancient wisdom meets modern power 🏮"
            }
        ]
        
        # Select 2-4 themes randomly but weighted by poem number
        num_themes = random.randint(2, 4)
        selected_themes = random.sample(themes, num_themes)
        
        # Create theme prompts with emojis
        theme_prompts = [f"{t['theme']} - {t['description']}" for t in selected_themes]
        
        prompt = f"""
        You are a Gen Z poet creating a fun and meaningful poem. Your task is to write an 8-line poem mixing these themes:
        {chr(10).join('• ' + t for t in theme_prompts)}

        IMPORTANT FORMAT RULES:
        1. Start with exactly: "Title: [Your Creative Title]"
        2. Skip one line
        3. Write exactly 8 lines of poem
        4. Each line must be a complete thought
        5. Do not add any extra text, numbers, or formatting

        Style Guide:
        • Keep it Gen Z fresh but authentic
        • Include 2-3 emojis max in the whole poem
        • Mix fun and deep vibes (60% fun, 40% deep)
        • Make each line hit different
        • Keep it relatable to 2024
        Example Format:

        # Crypto Monkey Business

        *Living that NFT life, swinging through the trees* 🐒

        *Diamond hands hold tight, HODL with the breeze*

        *In the digital jungle, where bananas grow*

        *Smart contracts whisper, "To the moon we go"* 🚀

        *Ancient wisdom says to trust the flow*

        *But Web3's calling, time to steal the show*

        *Monkey mindset in a blockchain game*

        *Evolving daily, never quite the same* 🎮

        Remember: EXACTLY 8 lines, no more, no less. Start with "Title: " and make it meaningful.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.cohere.chat(
                    message=prompt,
                    model="command-r-plus-08-2024",
                    temperature=0.92,
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
                
                # Debug output
                print("\nGenerated poem text:")
                print(poem_text)
                
                # Validate basic structure
                if self.validate_poem_structure(poem_text):
                    # Ensure we return both the poem and themes
                    return poem_text, selected_themes
                
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
        themes = None
        
        for attempt in range(max_attempts):
            try:
                generated_poem, selected_themes = self.generate_poem(index)
                if self.validate_poem_structure(generated_poem):
                    poem = generated_poem
                    themes = selected_themes
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
        formatted_content, title = self.format_poem_content(poem, themes)
        
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
        print(f"Themes: {' • '.join(t['theme'] for t in themes)}")
        
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
• Number: Poem {poem_number} of 8
• Path: {file_path.relative_to(self.repo_path)}
• Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # Commit changes
            print("Committing changes...")
            self.repo.index.commit(commit_message)
            
            # Push changes with retry logic
            max_retries = 8
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
                    print("Retrying in 8 seconds...")
                    time.sleep(8)
            
        except Exception as e:
            error_msg = f"Error in git operations: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def test_daily_pattern(self):
        """Test if the daily pattern detection is working correctly"""
        self.logger.info("\n=== Testing Daily Pattern System ===")
        
        # Read the commit pattern file
        pattern_file = self.repo_path / "commit_pattern.json"
        if not pattern_file.exists():
            self.logger.error("❌ commit_pattern.json not found!")
            return False
            
        try:
            # Load the pattern
            with open(pattern_file, 'r') as f:
                commit_pattern = json.load(f)
            
            # Test current date
            today = datetime.datetime.now()
            today_str = today.strftime('%Y-%m-%d')
            num_commits = commit_pattern.get(today_str, 8)
            
            self.logger.info(f"\nToday ({today_str}):")
            self.logger.info(f"Required commits: {num_commits}")
            self.logger.info(f"Pattern type: {'Heavy (Pattern Day)' if num_commits == 17 else 'Normal Day'}")
            
            # Test next 7 days
            self.logger.info("\nNext 7 days preview:")
            self.logger.info("-" * 50)
            
            for i in range(7):
                test_date = today + datetime.timedelta(days=i)
                date_str = test_date.strftime('%Y-%m-%d')
                commits = commit_pattern.get(date_str, 8)
                
                self.logger.info(f"Date: {date_str} ({test_date.strftime('%A')})")
                self.logger.info(f"Commits: {commits} ({'Heavy' if commits == 17 else 'Normal'})")
                self.logger.info("-" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error testing pattern: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def run_daily_automation(self):
        """Run the daily automation process"""
        # First, test the pattern system
        self.logger.info("\nTesting commit pattern system...")
        if not self.test_daily_pattern():
            self.logger.error("Pattern system test failed! Please check commit_pattern.json")
            return
            
        folder_path = self.get_or_create_daily_folder()
        
        self.logger.info(f"\nStarting automation at {datetime.datetime.now()}")
        self.logger.info(f"Using folder: {folder_path}")
        
        # Read the commit pattern from commit_pattern.json
        pattern_file = self.repo_path / "commit_pattern.json"
        if not pattern_file.exists():
            self.logger.warning("No commit_pattern.json found. Using default 8 commits.")
            num_commits = 8
        else:
            try:
                with open(pattern_file, 'r') as f:
                    commit_pattern = json.load(f)
                
                # Get today's date in YYYY-MM-DD format
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                
                # Get number of commits for today from pattern
                num_commits = commit_pattern.get(today, 8)  # Default to 8 if date not found
                
                self.logger.info(f"\nDate: {today}")
                self.logger.info(f"Commits required today: {num_commits}")
                
            except Exception as e:
                self.logger.error(f"Error reading commit pattern: {str(e)}", exc_info=True)
                self.logger.warning("Falling back to default 8 commits")
                num_commits = 8
        
        # Count existing poems to determine where to start
        existing_poems = len(list(folder_path.glob("[0-9][0-9]_RB_*.md")))
        start_number = existing_poems + 1
        
        self.logger.info(f"Found {existing_poems} existing poems. Starting from poem {start_number}")
        self.logger.info(f"Target number of poems for today: {num_commits}")
        
        # Generate remaining poems sequentially with dynamic timing
        for poem_number in range(start_number, num_commits + 1):
            try:
                start_time = datetime.datetime.now()
                self.logger.info(f"\nGenerating poem {poem_number}/{num_commits} at {start_time}")
                
                # Create the poem
                file_path = self.create_poem_file(folder_path, poem_number)
                
                if file_path and file_path.exists():
                    self.logger.info(f"Created poem at: {file_path}")
                    
                    # Display poem content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.logger.info("\nPoem content:")
                        self.logger.info("-" * 50)
                        self.logger.info(content)
                        self.logger.info("-" * 50)
                    
                    # Commit and push this poem before waiting
                    self.git_commit_and_push(file_path)
                    self.logger.info(f"Successfully committed and pushed poem {poem_number}")
                    
                    # Calculate time spent and determine wait time
                    time_spent = (datetime.datetime.now() - start_time).total_seconds()
                    operation_window = 480 // num_commits  # Distribute 8 hours (480 minutes) across all poems
                    
                    # Wait remaining time to complete operation window if needed
                    if time_spent < operation_window * 60:
                        remaining_time = (operation_window * 60) - time_spent
                        self.logger.info(f"\nWaiting {remaining_time:.0f} seconds to complete {operation_window}-minute operation window...")
                        time.sleep(remaining_time)
                    
                    # If there's another poem to generate, add a small buffer
                    if poem_number < num_commits:
                        buffer_time = 30  # 30 seconds buffer
                        self.logger.info(f"Adding {buffer_time} second buffer before next poem...")
                        time.sleep(buffer_time)
                
            except Exception as e:
                self.logger.error(f"Error creating poem {poem_number}: {str(e)}", exc_info=True)
                # Wait before retrying
                time.sleep(30)
                continue
        
        self.logger.info(f"\nCompleted daily automation at {datetime.datetime.now()}") 