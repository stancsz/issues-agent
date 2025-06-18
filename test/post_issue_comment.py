"""
Script to post a comment ("add a hello world") to a specified GitHub issue using GitHub CLI (gh).

Usage:
    python post_issue_comment.py <issue_url>

Requirements:
    - Python 3.x
    - GitHub CLI (gh) installed and authenticated

If no issue URL is provided, defaults to:
    https://github.com/stancsz/issues-agent/issues/1

Example:
    python post_issue_comment.py https://github.com/owner/repo/issues/1
    python post_issue_comment.py
"""

import sys
import subprocess

def main():
    default_issue_url = "https://github.com/stancsz/issues-agent/issues/1"
    if len(sys.argv) == 2:
        issue_url = sys.argv[1]
    else:
        print(f"No issue URL provided, using default: {default_issue_url}")
        issue_url = default_issue_url

    comment = "add a hello world"
    try:
        result = subprocess.run(
            ["gh", "issue", "comment", issue_url, "--body", comment],
            check=True,
            capture_output=True,
            text=True
        )
        print("Comment posted successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to post comment via GitHub CLI.")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
