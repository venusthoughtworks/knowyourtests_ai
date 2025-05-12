import os
import re

# Define best practices for various technologies, including Java and C#
BEST_PRACTICES = {
    "Python": [
        {"pattern": r"if\s+__name__\s*==\s*['\"]__main__['\"]",
         "message": "Ensure proper script entry points using __name__ == '__main__'."},
        {"pattern": r"def\s+[a-z_]+\(", "message": "Follow naming conventions for functions (snake_case)."},
        {"pattern": r"class\s+[A-Z][a-zA-Z0-9]+", "message": "Follow naming conventions for classes (PascalCase)."},
        {"pattern": r"(import\s+pdb|pdb\.set_trace\(\))",
         "message": "Remove all debugging statements (e.g., pdb.set_trace)."}
    ],
    "Flask": [
        {"pattern": r"app\.run\(", "message": "Avoid using debug mode in production when running Flask applications."},
        {"pattern": r"from\s+flask_sqlalchemy\s+import",
         "message": "Check for proper database configurations using Flask SQLAlchemy."},
    ],
    "Django": [
        {"pattern": r"from\s+django\.conf", "message": "Ensure settings are configured securely in Django projects."},
        {"pattern": r"DEBUG\s*=\s*True", "message": "DEBUG should be set to False in production."},
    ],
    "JavaScript": [
        {"pattern": r"console\.log\(", "message": "Remove debugging logs (e.g., console.log)."},
        {"pattern": r"var\s+", "message": "Use 'let' or 'const' instead of 'var' for variable declarations."}
    ],
    "Java": [
        {"pattern": r"System\.out\.println\(", "message": "Remove System.out.println debugging statements."},
        {"pattern": r"public\s+class\s+[A-Z][a-zA-Z0-9]+",
         "message": "Follow naming conventions for classes (PascalCase)."},
        {"pattern": r"@Override",
         "message": "Ensure methods that override parent methods use the @Override annotation."},
        {"pattern": r"throws\s+Exception",
         "message": "Avoid using generic Exception in method signatures. Use specific exceptions."},
    ],
    "C#": [
        {"pattern": r"Console\.WriteLine\(", "message": "Remove Console.WriteLine debugging statements."},
        {"pattern": r"class\s+[A-Z][a-zA-Z0-9]+", "message": "Follow naming conventions for classes (PascalCase)."},
        {"pattern": r"private\s+[A-Z][a-zA-Z0-9]+",
         "message": "Private fields should begin with a lowercase letter (camelCase)."},
        {"pattern": r"{\s*get;\s*set;\s*}",
         "message": "Encapsulate fields with properties instead of using public fields."},
        {"pattern": r"async\s+void",
         "message": "Avoid 'async void' methods; use 'async Task' instead, except for event handlers."},
    ],
    # Add additional tech-specific best practices here...
}


def detect_tech_stack(repo_path):
    """
    Detects the primary technologies used in the repository based on file extensions and content patterns.
    """
    tech_stack = set()
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Detect based on file extensions
            if file.endswith(".py"):
                tech_stack.add("Python")
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if re.search(r"from\s+flask", content):
                        tech_stack.add("Flask")
                    elif re.search(r"from\s+django", content):
                        tech_stack.add("Django")
            elif file.endswith(".js"):
                tech_stack.add("JavaScript")
            elif file.endswith(".java"):
                tech_stack.add("Java")
            elif file.endswith(".cs"):
                tech_stack.add("C#")
            # Add more detections based on file type

    return list(tech_stack)


def combine_files_by_pattern(repo_path, tech):
    """
    Combines all files that match patterns for a specific technology.

    Args:
        repo_path (str): Path to the repository.
        tech (str): The technology to filter files for.

    Returns:
        str: Combined content of all matched files.
    """
    combined_content = ""
    patterns = BEST_PRACTICES.get(tech, [])

    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # If any pattern matches, add the file content to combined_content
                    if any(re.search(rule["pattern"], content, re.IGNORECASE) for rule in patterns):
                        combined_content += f"\n\n# {file_path}\n{content}"

            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    return combined_content


def validate_best_practices(repo_path):
    """
    Validates repository code against best practices and groups files for each rule.

    Args:
        repo_path (str): Path to the repository.

    Returns:
        dict: Results of the validation including passing and failing files for rules.
    """
    results = {}
    tech_stack = detect_tech_stack(repo_path)

    for tech in tech_stack:
        results[tech] = []
        
        if tech in BEST_PRACTICES:
            for rule in BEST_PRACTICES[tech]:
                rule_result = {"message": rule["message"], "passing_files": [], "failing_files": []}

                for root, _, files in os.walk(repo_path):
                    for file in files:
                        file_path = os.path.join(root, file)

                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()

                                if re.search(rule["pattern"], content, re.IGNORECASE):
                                    # File fails the rule because the pattern matches
                                    rule_result["failing_files"].append(file_path)
                                else:
                                    # File passes this rule
                                    rule_result["passing_files"].append(file_path)

                        except Exception as e:
                            print(f"Error reading file {file_path}: {e}")

                results[tech].append(rule_result)

    return results


# Example usage
if __name__ == "__main__":
    repo_path = "/Users/venusjain/AIFSD_hackathon/knowyourtests_ai/cloned_repos/BookStoreAPI_xUnitTesting"  # Replace with the actual repo path
    validation_results = validate_best_practices(repo_path)

    for tech, issues in validation_results.items():
        print(f"\nTechnology: {tech}")
        for rule in issues:
            print(f"\nRule: {rule['message']}")
            print(f"Passing Files ({len(rule['passing_files'])}):")
            for passing_file in rule["passing_files"]:
                print(f"  - {passing_file}")
            print(f"Failing Files ({len(rule['failing_files'])}):")
            for failing_file in rule["failing_files"]:
                print(f"  - {failing_file}")