import os
import unittest
import subprocess
import tempfile
import shutil

class TestAgentScript(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as a dummy repo
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.test_dir)
        # Initialize a git repo
        subprocess.run("git init", shell=True, check=True)
        # Create a dummy file
        self.dummy_file = "dummy.txt"
        with open(self.dummy_file, "w") as f:
            f.write("Original content")
        subprocess.run(f"git add {self.dummy_file}", shell=True, check=True)
        subprocess.run('git commit -m "Initial commit"', shell=True, check=True)
        # Set required environment variables
        os.environ["GITHUB_TOKEN"] = "dummy"
        os.environ["REPO_NAME"] = "dummy/dummy"
        os.environ["ISSUE_NUMBER"] = "1"
        os.environ["ISSUE_TITLE"] = "Test Issue"
        os.environ["ISSUE_BODY"] = f"Please update `{self.dummy_file}` to say 'Updated by agent.'"
        os.environ["OPENAI_API_KEY"] = "dummy"

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.test_dir)

    def test_agent_creates_or_modifies_file(self):
        # Path to agent.py relative to this test file
        agent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "agent.py"))
        # Run the agent script (expect it to fail on real API calls, but we check file logic)
        try:
            subprocess.run(f"python {agent_path}", shell=True, check=True)
        except subprocess.CalledProcessError:
            # Expected to fail due to dummy tokens, but file may be updated before failure
            pass
        # Check if the file was updated
        with open(self.dummy_file, "r") as f:
            content = f.read()
        self.assertIn("Updated by agent", content)

if __name__ == "__main__":
    unittest.main()
