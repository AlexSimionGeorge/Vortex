import os
import unittest
import tempfile
import subprocess
from typing import List, Tuple, Optional
from pathlib import Path

from src.inspector_git.ig_log_reader import  IGLogReader
from data_structures.inspector_git.models import GitLogDTO, CommitDTO, ChangeDTO
from data_structures.inspector_git.enums import ChangeType


class TestIGLogReader(unittest.TestCase):
    """Test class for IGLogReader."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Define paths for test repositories
        cls.test_dir = Path(tempfile.gettempdir()) / "iglog_test"
        cls.test_repo_path = cls.test_dir / "test_repo"
        cls.test_iglog_path = Path("test/inspector_git/resources/test_repo.iglog")
        
        # Create test directory if it doesn't exist
        os.makedirs(cls.test_dir, exist_ok=True)
        
        # Clean up any existing test repository
        if cls.test_repo_path.exists():
            cls._run_git_command(f"rm -rf {cls.test_repo_path}")
        
        # Create a test repository with some commits
        cls._create_test_repository()
        
        # Generate an IGLog file from the test repository
        # Note: In a real test, you would use the actual inspector_git tool to generate this
        # For this test, we'll create a simplified IGLog file manually
        cls._create_test_iglog_file()

    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Remove the test repository
        if cls.test_repo_path.exists():
            cls._run_git_command(f"rm -rf {cls.test_repo_path}")

    @classmethod
    def _run_git_command(cls, command: str, cwd: Optional[Path] = None) -> Tuple[str, str]:
        """
        Run a git command and return the output.
        
        Args:
            command: The git command to run.
            cwd: The working directory for the command.
            
        Returns:
            A tuple containing the standard output and standard error.
        """
        if cwd is None:
            cwd = cls.test_dir
            
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd)
        )
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8'), stderr.decode('utf-8')

    @classmethod
    def _create_test_repository(cls):
        """Create a test git repository with some commits."""
        # Create the repository
        os.makedirs(cls.test_repo_path, exist_ok=True)
        
        # Initialize git repository
        cls._run_git_command("git init", cls.test_repo_path)
        
        # Configure git user
        cls._run_git_command("git config user.name 'Test User'", cls.test_repo_path)
        cls._run_git_command("git config user.email 'test@example.com'", cls.test_repo_path)
        
        # Create and commit a file
        with open(cls.test_repo_path / "file1.txt", "w") as f:
            f.write("Initial content")
        
        cls._run_git_command("git add file1.txt", cls.test_repo_path)
        cls._run_git_command("git commit -m 'Initial commit'", cls.test_repo_path)
        
        # Modify the file and commit
        with open(cls.test_repo_path / "file1.txt", "w") as f:
            f.write("Modified content")
        
        cls._run_git_command("git add file1.txt", cls.test_repo_path)
        cls._run_git_command("git commit -m 'Modified file1.txt'", cls.test_repo_path)
        
        # Add a new file and commit
        with open(cls.test_repo_path / "file2.txt", "w") as f:
            f.write("New file content")
        
        cls._run_git_command("git add file2.txt", cls.test_repo_path)
        cls._run_git_command("git commit -m 'Added file2.txt'", cls.test_repo_path)

    @classmethod
    def _create_test_iglog_file(cls):
        """
        Create a test IGLog file.
        
        In a real test, you would use the actual inspector_git tool to generate this.
        For this test, we'll create a simplified IGLog file manually.
        """
        # Create the resources directory if it doesn't exist
        os.makedirs(os.path.dirname(cls.test_iglog_path), exist_ok=True)
        
        # Get commit information from the test repository
        commits_info = cls._get_commits_info()
        
        # Create a simplified IGLog file
        with open(cls.test_iglog_path, "w") as f:
            # Write IGLog version
            f.write("1.0\n")
            
            # Write commits
            for commit in commits_info:
                commit_id, parent_ids, author_date, author_name, author_email, message, changes = commit
                
                # Write commit header
                f.write(f"ig#{commit_id}\n")
                f.write(f"{' '.join(parent_ids)}\n")
                f.write(f"{author_date}\n")
                f.write(f"{author_email}\n")
                f.write(f"{author_name}\n")
                
                # Write commit message
                for line in message.split("\n"):
                    f.write(f"${line}\n")
                
                # Write changes
                for change in changes:
                    change_type, old_file, new_file = change
                    
                    # Write change header
                    f.write(f"#{change_type}\n")
                    f.write(f"{parent_ids[0] if parent_ids else ''}\n")
                    
                    # Write file names
                    if change_type == "A":  # Add
                        f.write("/dev/null\n")
                        f.write(f"{new_file}\n")
                    elif change_type == "D":  # Delete
                        f.write(f"{old_file}\n")
                        f.write("/dev/null\n")
                    elif change_type == "M":  # Modify
                        f.write(f"{old_file}\n")
                        f.write(f"{new_file}\n")
                    
                    # Write a simple hunk (in a real IGLog file, this would be more complex)
                    f.write("@=1:5|0\n")

    @classmethod
    def _get_commits_info(cls) -> List[Tuple]:
        """
        Get information about the commits in the test repository.
        
        Returns:
            A list of tuples containing commit information.
        """
        # Get commit IDs
        output, _ = cls._run_git_command("git log --format=%H", cls.test_repo_path)
        commit_ids = output.strip().split("\n")
        
        commits_info = []
        for commit_id in commit_ids:
            # Get commit details
            output, _ = cls._run_git_command(f"git show --format='%P%n%ai%n%an%n%ae%n%B' --name-status {commit_id}", cls.test_repo_path)
            lines = output.strip().split("\n")
            
            # Parse commit details
            parent_ids = lines[0].split() if lines[0] else []
            author_date = lines[1]
            author_name = lines[2]
            author_email = lines[3]
            
            # Find the end of the commit message
            message_end = 4
            while message_end < len(lines) and not lines[message_end].startswith("A\t") and not lines[message_end].startswith("M\t") and not lines[message_end].startswith("D\t"):
                message_end += 1
            
            message = "\n".join(lines[4:message_end]).strip()
            
            # Parse changes
            changes = []
            for i in range(message_end, len(lines)):
                if not lines[i]:
                    continue
                    
                parts = lines[i].split("\t")
                if len(parts) >= 2:
                    change_type = parts[0]
                    if change_type == "A":  # Add
                        changes.append((change_type, "", parts[1]))
                    elif change_type == "D":  # Delete
                        changes.append((change_type, parts[1], ""))
                    elif change_type == "M":  # Modify
                        changes.append((change_type, parts[1], parts[1]))
            
            commits_info.append((commit_id, parent_ids, author_date, author_name, author_email, message, changes))
        
        return commits_info

    def test_read_iglog_file(self):
        """Test reading an IGLog file."""
        # Create an IGLogReader
        reader = IGLogReader()
        
        # Read the test IGLog file
        git_log = reader.read(str(self.test_iglog_path))
        
        # Verify the GitLogDTO object
        self.assertIsInstance(git_log, GitLogDTO)
        self.assertEqual(git_log.name, "test_repo")
        self.assertEqual(git_log.ig_log_version, "1.0")
        
        # Verify commits
        self.assertGreater(len(git_log.commits), 0)
        
        # Verify the first commit
        first_commit = git_log.commits[0]
        self.assertIsInstance(first_commit, CommitDTO)
        self.assertTrue(first_commit.id)
        self.assertEqual(len(first_commit.parent_ids), 0)  # First commit has no parents
        
        # Verify the second commit
        if len(git_log.commits) > 1:
            second_commit = git_log.commits[1]
            self.assertIsInstance(second_commit, CommitDTO)
            self.assertTrue(second_commit.id)
            self.assertEqual(len(second_commit.parent_ids), 1)  # Second commit has one parent
            self.assertEqual(second_commit.parent_ids[0], first_commit.id)
        
        # Verify changes in commits
        for commit in git_log.commits:
            for change in commit.changes:
                self.assertIsInstance(change, ChangeDTO)
                self.assertIn(change.type, [ChangeType.Add, ChangeType.Delete, ChangeType.Modify, ChangeType.Rename])
                
                # Verify file names based on change type
                if change.type == ChangeType.Add:
                    self.assertEqual(change.old_file_name, "/dev/null")
                    self.assertNotEqual(change.new_file_name, "/dev/null")
                elif change.type == ChangeType.Delete:
                    self.assertNotEqual(change.old_file_name, "/dev/null")
                    self.assertEqual(change.new_file_name, "/dev/null")
                elif change.type == ChangeType.Modify:
                    self.assertEqual(change.old_file_name, change.new_file_name)
                    self.assertNotEqual(change.old_file_name, "/dev/null")


if __name__ == "__main__":
    unittest.main()