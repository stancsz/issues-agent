import os
import sys
import re
import subprocess
import openai
from github import Github

def get_env(var, required=True):
    value = os.environ.get(var)
    if required and not value:
        print(f"Missing required environment variable: {var}", file=sys.stderr)
        sys.exit(1)
    return value

def run(cmd, check=True, capture_output=False):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True)
    if capture_output:
        return result.stdout.strip()
    return None

def parse_file_paths(text):
    # Look for code blocks or inline code with file paths, e.g. `src/utils.js`
    code_blocks = re.findall(r"`([^`]+)`", text)
    # Also look for patterns like src/utils.js or utils.py
    file_like = re.findall(r"([\\w./-]+\\.[a-zA-Z0-9]+)", text)
    return list(set(code_blocks + file_like))

def find_file_in_repo(filename):
    # Use git ls-files to find the file anywhere in the repo
    try:
        files = run(f"git ls-files '*{filename}'", capture_output=True)
        files = [f for f in files.splitlines() if os.path.isfile(f)]
        if files:
            return files[0]  # Return the first match
    except Exception as e:
        print(f"Error searching for {filename}: {e}")
    return None

def openai_suggest_files(issue_body, repo_file_list):
    openai.api_key = get_env("OPENAI_API_KEY")
    prompt = (
        "Given the following user request, suggest the most relevant file(s) from this list:\n"
        f"User request:\n{issue_body}\n\n"
        f"Files in repo:\n" + "\n".join(repo_file_list) + "\n"
        "Respond with a comma-separated list of file paths."
    )
    response = openai.resources.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=128,
        temperature=0
    )
    files = response.choices[0].message.content.strip()
    return [f.strip() for f in files.split(",") if f.strip() in repo_file_list]

def openai_modify_file(issue_body, file_path, file_content):
    openai.api_key = get_env("OPENAI_API_KEY")
    prompt = (
        "You are an expert software engineer. Your task is to modify the following file based on the user's request.\n"
        "Only output the complete, modified file content. Do not include any other text or explanations.\n\n"
        f"User's request:\n{issue_body}\n\n"
        f"File: {file_path}\n"
        f"Current content:\n{file_content}\n"
    )
    response = openai.resources.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def get_all_repo_files():
    files = run("git ls-files", capture_output=True)
    return [f for f in files.splitlines() if os.path.isfile(f)]

def main():
    # Observe
    token = get_env("GITHUB_TOKEN")
    repo_name = get_env("REPO_NAME")
    issue_number = int(get_env("ISSUE_NUMBER"))
    issue_title = get_env("ISSUE_TITLE")
    issue_body = get_env("ISSUE_BODY")

    g = Github(token)
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(number=issue_number)
    comments = [c.body for c in issue.get_comments()]
    full_issue_text = issue_title + "\n" + issue_body + "\n" + "\n".join(comments)


    # Orient: Find target file(s)
    file_paths = parse_file_paths(full_issue_text)
    repo_files = get_all_repo_files()
    target_files = []

    for path in file_paths:
        if os.path.isfile(path):
            target_files.append(path)
        else:
            # Try to find by filename
            fname = os.path.basename(path)
            found = find_file_in_repo(fname)
            if found:
                target_files.append(found)

    if not target_files:
        # Use OpenAI to suggest files
        print("No explicit file paths found, asking OpenAI to suggest files...")
        target_files = openai_suggest_files(full_issue_text, repo_files)
        if not target_files:
            print("No relevant files found. Exiting.")
            sys.exit(0)

    print(f"Target files: {target_files}")

    # Decide & Act: For each file, get new content from OpenAI and overwrite
    import difflib

    for file_path in target_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        new_content = openai_modify_file(full_issue_text, file_path, file_content)
        # Basic sanity check: don't overwrite with empty or non-code
        if not new_content.strip():
            print(f"OpenAI returned empty content for {file_path}, skipping.")
            continue

        # Compute diff and apply only changed blocks
        if file_content != new_content:
            old_lines = file_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
            if diff:
                # Apply the diff as a patch
                # For simplicity, just replace the changed blocks in the file
                # (A more robust approach would use a patch library)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {file_path} with changes from OpenAI (diff applied)")
            else:
                print(f"No changes detected for {file_path}")
        else:
            print(f"No changes detected for {file_path}")

    # Git operations
    branch_name = f"feature/issue-{issue_number}"
    run(f"git checkout -b {branch_name}")
    run("git add .")
    run(f'git commit -m "feat: Implement changes for issue #{issue_number}"')
    run(f"git push origin {branch_name}")

    # Create PR using GitHub CLI
    pr_title = f"PR for Issue #{issue_number}: {issue_title}"
    pr_body = f"This PR was automatically generated by the coding agent to address issue #{issue_number}."
    run(f'gh pr create --title "{pr_title}" --body "{pr_body}" --base {repo.default_branch}')

if __name__ == "__main__":
    main()
