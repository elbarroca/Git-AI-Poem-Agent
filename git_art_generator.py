import os
import datetime
import json
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

class GitArtGenerator:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self._setup_logging()
        
        # Define the pixel art for "GIGACHAD :D"
        self.art_pattern = {
            "G": [
                "11111",
                "1....",
                "1.111",
                "1..1.",
                "11111"
            ],
            "I": [
                "11111",
                "..1..",
                "..1..",
                "..1..",
                "11111"
            ],
            "G": [
                "11111",
                "1....",
                "1.111",
                "1..1.",
                "11111"
            ],
            "A": [
                "11111",
                "1...1",
                "11111",
                "1...1",
                "1...1"
            ],
            "C": [
                "11111",
                "1....",
                "1....",
                "1....",
                "11111"
            ],
            "H": [
                "1...1",
                "1...1",
                "11111",
                "1...1",
                "1...1"
            ],
            "A": [
                "11111",
                "1...1",
                "11111",
                "1...1",
                "1...1"
            ],
            "D": [
                "1111.",
                "1...1",
                "1...1",
                "1...1",
                "1111."
            ],
            ":": [
                ".....",
                "..1..",
                ".....",
                "..1..",
                "....."
            ],
            "D": [
                "1111.",
                "1...1",
                "1...1",
                "1...1",
                "1111."
            ]
        }
        
        # Commit counts for pattern
        self.commit_counts = {
            "normal_day": 8,  # Regular days get 8 commits
            "pattern_day": 17  # Days that form letters get 17 commits
        }
    
    def _setup_logging(self):
        """Configure logging"""
        logs_dir = self.repo_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"git_art_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        
        self.logger = logging.getLogger('GitArtGenerator')
        self.logger.setLevel(logging.INFO)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def calculate_start_date(self):
        """Calculate the start date to begin the art pattern"""
        current_year = datetime.datetime.now().year
        start_date = datetime.datetime(current_year, 1, 1)
        while start_date.weekday() != 6:  # 6 represents Sunday
            start_date += datetime.timedelta(days=1)
        return start_date
    
    def generate_commit_map(self):
        """Generate a map of dates to commit counts for the entire year"""
        start_date = self.calculate_start_date()
        commit_map = {}
        
        # Initialize all days with normal commit count
        current_date = start_date
        end_date = datetime.datetime(start_date.year + 1, 1, 1)
        
        while current_date < end_date:
            commit_map[current_date.strftime('%Y-%m-%d')] = self.commit_counts["normal_day"]
            current_date += datetime.timedelta(days=1)
        
        # Define letter positions (weeks)
        letter_positions = {
            "G": (1, 7),      # January
            "I": (8, 14),     # February-March
            "G": (15, 21),    # March-April
            "A": (22, 28),    # May-June
            "C": (29, 35),    # June-July
            "H": (36, 42),    # August-September
            "A": (43, 46),    # September-October
            "D": (47, 49),    # November
            ":": (50, 50),    # December
            "D": (51, 52)     # December
        }
        
        # Process each letter
        for char, (start_week, end_week) in letter_positions.items():
            pattern = self.art_pattern.get(char)
            if not pattern:
                continue
            
            # For each week this letter spans
            for week in range(start_week, end_week + 1):
                # Apply the pattern vertically
                for day, row in enumerate(pattern):
                    if row[0] == "1":  # Only check first column for horizontal pattern
                        commit_date = start_date + datetime.timedelta(weeks=week-1, days=day)
                        commit_map[commit_date.strftime('%Y-%m-%d')] = self.commit_counts["pattern_day"]
        
        return commit_map
    
    def save_commit_map(self):
        """Save the commit map to a JSON file"""
        commit_map = self.generate_commit_map()
        
        # Save to a JSON file
        output_file = self.repo_path / "commit_pattern.json"
        with open(output_file, 'w') as f:
            json.dump(commit_map, f, indent=2)
        
        self.logger.info(f"Commit pattern saved to {output_file}")
        self.logger.info(f"Total days with pattern commits: {sum(1 for v in commit_map.values() if v == self.commit_counts['pattern_day'])}")
        
        # Print pattern preview
        self.print_pattern_preview(commit_map)
        
        return output_file
    
    def print_pattern_preview(self, commit_map):
        """Print an ASCII preview of the pattern that matches GitHub's contribution graph"""
        self.logger.info("\nGitHub Contribution Calendar Preview")
        self.logger.info("=" * 120)
        self.logger.info("Legend:")
        self.logger.info(f"█ = Pattern day ({self.commit_counts['pattern_day']} commits)")
        self.logger.info(f"░ = Normal day ({self.commit_counts['normal_day']} commits)")
        self.logger.info("· = Empty day (0 commits)")
        
        start_date = self.calculate_start_date()
        
        # Print month indicators
        current_date = start_date
        month_labels = []
        current_month = ""
        
        for week in range(53):  # 53 weeks to ensure full year coverage
            month = current_date.strftime("%b")
            if month != current_month:
                month_labels.append(f"{month:^12}")
                current_month = month
            else:
                month_labels.append(" " * 12)
            current_date += datetime.timedelta(weeks=1)
        
        # Print months row
        self.logger.info("\nMonths:")
        month_row = "    " + "".join(month_labels)
        self.logger.info(month_row)
        
        # Print day names and grid
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day_idx, day_name in enumerate(days):
            row = f"{day_name:<4}"
            
            # For each week
            for week in range(53):
                current_date = start_date + datetime.timedelta(weeks=week, days=day_idx)
                date_str = current_date.strftime('%Y-%m-%d')
                
                if current_date > datetime.datetime.now():
                    row += "·  "  # Future date
                elif commit_map.get(date_str, 0) == self.commit_counts["pattern_day"]:
                    row += "█  "  # Pattern day
                else:
                    row += "░  "  # Normal day
            
            self.logger.info(row)
        
        # Print statistics
        total_pattern_days = sum(1 for v in commit_map.values() if v == self.commit_counts["pattern_day"])
        total_normal_days = 365 - total_pattern_days
        total_pattern_commits = total_pattern_days * self.commit_counts["pattern_day"]
        total_normal_commits = total_normal_days * self.commit_counts["normal_day"]
        
        self.logger.info("\nPattern Statistics:")
        self.logger.info("-" * 50)
        self.logger.info(f"Pattern days: {total_pattern_days:>3} days × {self.commit_counts['pattern_day']:>2} commits = {total_pattern_commits:>4} commits")
        self.logger.info(f"Normal days:  {total_normal_days:>3} days × {self.commit_counts['normal_day']:>2} commits = {total_normal_commits:>4} commits")
        self.logger.info("-" * 50)
        self.logger.info(f"Total commits for the year: {total_pattern_commits + total_normal_commits}")
        
        self.logger.info("\nNote: Pattern starts from the first Sunday of the year ({})".format(
            start_date.strftime("%Y-%m-%d")
        )) 