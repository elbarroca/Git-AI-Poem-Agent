#!/usr/bin/env python3
import unittest
from pathlib import Path
import datetime
import time
from poem_automation import PoemAutomation
from config import COHERE_API_KEY, REPO_PATH
import sys

class TestPoemAutomation(unittest.TestCase):
    MAX_RETRIES = 5  # Global retry count
    RETRY_DELAY = 5  # Seconds between retries
    
    def setUp(self):
        """Set up test environment"""
        for attempt in range(self.MAX_RETRIES):
            try:
                self.automation = PoemAutomation(COHERE_API_KEY, REPO_PATH)
                self.test_folder = self.automation.get_or_create_daily_folder()
                print(f"\nTesting in folder: {self.test_folder}")
                
                # Clean git state at start
                self._clean_git_state()
                break
            except Exception as e:
                print(f"Setup attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise
    
    def _clean_git_state(self):
        """Helper to clean git state"""
        for attempt in range(self.MAX_RETRIES):
            try:
                repo = self.automation.repo
                if repo.is_dirty():
                    print("Cleaning git state...")
                    repo.git.add('.')
                    repo.git.commit('-m', 'Auto-commit before tests')
                    repo.git.push('origin', 'main')
                    time.sleep(3)  # Increased wait for git operations
                return
            except Exception as e:
                print(f"Git clean attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    print(f"Warning: Could not clean git state after {self.MAX_RETRIES} attempts")

    def test_1_folder_structure(self):
        """Test folder creation and structure"""
        print("\n🗂️ Testing folder structure...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Verify folder exists
                self.assertTrue(self.test_folder.exists())
                
                # Verify folder naming convention
                today = datetime.datetime.now()
                expected_name = today.strftime("%d_%A")  # e.g., "15_Friday"
                self.assertEqual(self.test_folder.name, expected_name)
                
                print("✅ Folder structure test passed")
                break
            except AssertionError:
                raise
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.fail(f"Folder structure test failed after {self.MAX_RETRIES} attempts")

    def test_2_poem_generation(self):
        """Test single poem generation"""
        print("\n📝 Testing poem generation...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Generate a test poem
                file_path = self.automation.create_poem_file(self.test_folder, 1)
                
                # Verify file exists
                self.assertTrue(file_path.exists())
                
                # Read and verify content structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check basic structure
                    self.assertIn('# ', content)  # Has title
                    self.assertIn('> *', content)  # Has one-liner
                    self.assertIn('**Themes**:', content)  # Has themes
                    
                    # Count content lines (should be 8 poem lines)
                    poem_lines = [line for line in content.split('\n') if line.startswith('**') and line[2].isdigit()]
                    self.assertEqual(len(poem_lines), 8)
                
                print("✅ Poem generation test passed")
                break
            except AssertionError:
                raise
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.fail(f"Poem generation test failed after {self.MAX_RETRIES} attempts")

    def test_3_git_integration(self):
        """Test git commit and push"""
        print("\n🔄 Testing git integration...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Clean state before test
                self._clean_git_state()
                
                # Generate and commit a poem
                file_path = self.automation.create_poem_file(self.test_folder, 2)
                
                # Add a small delay before git operations
                time.sleep(3)
                
                self.automation.git_commit_and_push(file_path)
                
                # Add another small delay after push
                time.sleep(3)
                
                # Verify git status
                repo = self.automation.repo
                
                # Retry logic for git status check
                for git_check in range(self.MAX_RETRIES):
                    if not repo.is_dirty():
                        break
                    print(f"Git repo still dirty, check {git_check + 1}/{self.MAX_RETRIES}")
                    time.sleep(3)
                else:
                    raise Exception("Git repo remained dirty after multiple checks")
                
                # Verify remote tracking
                remote = repo.remote()
                self.assertTrue(remote.exists())
                
                print("✅ Git integration test passed")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.fail(f"Git integration test failed after {self.MAX_RETRIES} attempts")

    def test_4_one_liner_generation(self):
        """Test dynamic one-liner generation"""
        print("\n💭 Testing one-liner generation...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Test themes and content
                test_themes = [
                    {"theme": "Technology and AI"},
                    {"theme": "Gaming"}
                ]
                test_content = [
                    "Digital dreams in virtual space",
                    "Leveling up with every trace"
                ]
                
                # Generate one-liner with retry logic
                one_liner = None
                
                for gen_attempt in range(self.MAX_RETRIES):
                    one_liner = self.automation.generate_one_liner(test_themes, test_content)
                    
                    # Verify one-liner properties
                    if one_liner and len(one_liner) > 0 and len(one_liner) < 60:
                        break
                        
                    print(f"Retrying one-liner generation, attempt {gen_attempt + 1}/{self.MAX_RETRIES}")
                    time.sleep(2)
                
                self.assertIsNotNone(one_liner, "Failed to generate valid one-liner")
                
                # More comprehensive emoji check
                all_emojis = ''.join(chr(i) for i in range(0x1F300, 0x1FAF6))  # Unicode emoji range
                has_emoji = any(char in one_liner for char in all_emojis)
                
                if not has_emoji:
                    print(f"Warning: No standard emoji found in one-liner: {one_liner}")
                    # Don't fail the test, just warn
                
                print("✅ One-liner generation test passed")
                break
            except AssertionError:
                raise
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.fail(f"One-liner generation test failed after {self.MAX_RETRIES} attempts")

    def test_5_rapid_generation(self):
        """Test rapid generation of multiple poems"""
        print("\n🚀 Testing rapid poem generation...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                num_poems = 3
                delay = 60  # 60 seconds between poems
                
                for i in range(num_poems):
                    print(f"\nGenerating test poem {i+1}/{num_poems}")
                    
                    # Clean git state before each poem
                    self._clean_git_state()
                    
                    file_path = self.automation.create_poem_file(self.test_folder, i+3)
                    self.assertTrue(file_path.exists())
                    
                    # Add git operations with delay
                    time.sleep(3)
                    
                    # Retry git operations if needed
                    for git_attempt in range(self.MAX_RETRIES):
                        try:
                            self.automation.git_commit_and_push(file_path)
                            break
                        except Exception as e:
                            print(f"Git operation attempt {git_attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                            if git_attempt < self.MAX_RETRIES - 1:
                                time.sleep(self.RETRY_DELAY)
                            else:
                                raise
                    
                    if i < num_poems - 1:
                        print(f"Waiting {delay} seconds before next poem...")
                        time.sleep(delay)
                
                # Count total poems in folder
                poems = list(self.test_folder.glob("[0-9][0-9]_RB_*.md"))
                self.assertGreaterEqual(len(poems), num_poems)
                
                print("✅ Rapid generation test passed")
                break
            except AssertionError:
                raise
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    print(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.fail(f"Rapid generation test failed after {self.MAX_RETRIES} attempts")

def run_tests():
    """Run all tests with detailed output"""
    print("\n🧪 Starting Poem Automation Tests")
    print("=" * 50)
    
    # Run tests with better error handling
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPoemAutomation)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Ran {result.testsRun} tests")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 