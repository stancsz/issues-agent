# Issue Coding Agent GitHub Action

This repository contains a reusable GitHub Action that acts as a smart coding agent. When a new issue is created, the action will:

1. **Create a new branch** for the issue.
2. **Read the issue body and comments** for instructions.
3. **Scan the codebase** to find relevant files.
4. **Read and edit files** as needed, based on the instructions in the issue/comments.
5. **Commit and push changes** to the new branch.

## How it works

- The workflow is defined in `.github/workflows/issue-coding-agent.yml`.
- The main agent logic is in `coding-agent/agent.py` (Python, using [PyGithub](https://github.com/PyGithub/PyGithub)).
- The action runs automatically on new issues.

## Usage

1. Copy the workflow YAML and the `coding-agent` directory into your repository.
2. Ensure your repository has the `GITHUB_TOKEN` secret (provided by default in GitHub Actions).
3. When you open a new issue, the action will:
   - Create a branch named `issue-<number>`.
   - Parse the issue and comments for instructions.
   - Attempt to scan, read, and edit files as needed.
   - Commit and push changes to the new branch.

## Extending the Agent

- The core logic for scanning, reading, and editing files is in `coding-agent/agent.py`.
- You can extend the agent to use AI or more advanced logic for interpreting instructions and making code changes.

## Requirements

- Python 3.11+
- [PyGithub](https://github.com/PyGithub/PyGithub) (see `coding-agent/requirements.txt`)

## License

MIT
