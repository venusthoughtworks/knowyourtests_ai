from flask import Blueprint, render_template, request, redirect, url_for, flash

from test_analyzer.tech_stack_validator import validate_best_practices
from .utils import clone_or_update_repo, extract_repo_name
from test_analyzer.analyzer import classify_tests_in_repo, test_patterns

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    validation_results = None
    test_results = None
    error_message = None

    if request.method == "POST":
        repo_url = request.form.get("github_url")
        if not repo_url:
            error_message = "Repository URL is required."
        else:
            try:
                repo_path, message = clone_or_update_repo(repo_url)  # repo_path is the actual path
                if not repo_path:
                    error_message = message  # Show error if repo_path is empty
                else:
                    # Only pass the repo_path to classify_tests_in_repo
                    test_results = classify_tests_in_repo(repo_path)
                    validation_results = validate_best_practices(repo_path)
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"

    return render_template("index.html", validation_results=validation_results,
test_results=test_results, error_message=error_message)
