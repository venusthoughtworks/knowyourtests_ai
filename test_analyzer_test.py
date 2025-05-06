import os
from test_analyzer.analyzer import classify_tests_in_repo


def get_latest_cloned_repo_path(base_path="cloned_repos"):
    """
    Returns the path of the most recently modified repo inside cloned_repos.
    """
    entries = [os.path.join(base_path, d) for d in os.listdir(base_path)
               if os.path.isdir(os.path.join(base_path, d))]
    if not entries:
        raise FileNotFoundError("No cloned repositories found.")

    latest_repo = max(entries, key=os.path.getmtime)
    return latest_repo

if __name__ == "__main__":
    repo_path = get_latest_cloned_repo_path()

    print(f"Analyzing repository at: {repo_path}\n")

    results = classify_tests_in_repo(repo_path)

    print("\n--- Unit Tests ---")
    for file in results["unit_tests"]:
        print(file)

    print("\n--- Integration Tests ---")
    for file in results["integration_tests"]:
        print(file)

    print("\n--- E2E Tests ---")
    for file in results["e2e_tests"]:
        print(file)
