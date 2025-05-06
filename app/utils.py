import os
import subprocess

def extract_repo_name(git_url):
    return git_url.rstrip('/').split('/')[-1].replace(".git", "")

def clone_or_update_repo(git_url, base_dir="cloned_repos"):
    repo_name = extract_repo_name(git_url)
    repo_path = os.path.join(base_dir, repo_name)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    if os.path.exists(repo_path):
        return repo_path, "Repository already cloned."
    else:
        try:
            subprocess.check_call(["git", "clone", git_url, repo_path])
            return repo_path, "Repository cloned successfully."
        except subprocess.CalledProcessError:
            return None, "Error cloning repository."
