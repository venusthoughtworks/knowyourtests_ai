import os
from git import Repo
from config import GITHUB_CLONE_PATH

def clone_repo(github_url: str, project_name: str) -> str:
    project_path = os.path.join(GITHUB_CLONE_PATH, project_name)

    if os.path.exists(project_path):
        print(f"Repo already exists at {project_path}.")
        return project_path

    print(f"Cloning {github_url} into {project_path}")
    Repo.clone_from(github_url, project_path)
    return project_path
