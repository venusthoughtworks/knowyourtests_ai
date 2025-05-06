import os
import re

# Define patterns for unit, integration, and e2e tests across multiple languages
test_patterns = {
    "unit": [
        # Python, JavaScript, Java Unit Test Patterns
        r"import\s+unittest",  # Python unittest
        r"@Test",  # Java/JUnit
        r"describe\(.*\)",  # JS testing frameworks (Mocha, Jest, Jasmine)
        r"it\(.*\)",  # JS tests
        r"\btest\b",  # General test keyword
        r"\bassert\b",  # General assertion keyword
        r"^using\s+xunit",  # C# xUnit
        r"^using\s+nunit",  # C# NUnit
        r"^require\s+rspec",  # Ruby RSpec
        r"^import\s+junit"  # Java JUnit
    ],
    "integration": [
        r"@SpringBootTest",  # Spring Integration test for Java
        r"testcontainers",  # Docker-based integration test libs
        r"with_database\(.*\)",  # Custom integration hints
        r"\bservice\b",  # Service-level testing
        r"\bapi\b",  # API-related tests
        r"@BeforeEach",  # JUnit-based integration
        r"beforeEach",  # Mocha-based integration
        r"before(:each)"  # RSpec-based integration
    ],
    "e2e": [
        # More specific patterns for E2E testing
        r"from\s+cypress",  # Cypress for e2e
        r"selenium",  # Selenium-based test
        r"puppeteer",  # Puppeteer for e2e
        r"@E2ETest",  # Custom e2e annotation
        r"\b(user|login|end-to-end|browser|e2e)\b",  # E2E test patterns
        r"^describe\s+\".*e2e.*\"",  # Mocha-based E2E test
        r"^it\s+\".*e2e.*\"",  # Mocha-based E2E test
        r"e2e",  # General keyword for E2E tests
        r"test\('e2e'",  # Jasmine-based E2E
        r"^require\s+selenium-webdriver",  # Ruby Selenium-based E2E test
        r"playwright.config.js",  # Playwright config file (E2E)
        r"signupForm.spec.js",  # Playwright or other E2E test file
        r"\.spec\.js$"  # Matches spec files which are commonly used in E2E testing
    ]
}


def classify_tests_in_repo(repo_path, test_patterns=None):
    """
    Classifies tests into unit, integration, and e2e based on file names and patterns in the code.
    """
    # Set default test patterns if none are passed
    if test_patterns is None:
        test_patterns = {
            "unit": [
                # Python, JavaScript, Java Unit Test Patterns
                r"import\s+unittest",  # Python unittest
                r"@Test",  # Java/JUnit
                r"describe\(.*\)",  # JS testing frameworks (Mocha, Jest, Jasmine)
                r"it\(.*\)",  # JS tests
                r"\btest\b",  # General test keyword
                r"\bassert\b",  # General assertion keyword
                r"^using\s+xunit",  # C# xUnit
                r"^using\s+nunit",  # C# NUnit
                r"^require\s+rspec",  # Ruby RSpec
                r"^import\s+junit"  # Java JUnit
            ],
            "integration": [
                r"@SpringBootTest",  # Spring Integration test for Java
                r"testcontainers",  # Docker-based integration test libs
                r"with_database\(.*\)",  # Custom integration hints
                r"\bservice\b",  # Service-level testing
                r"\bapi\b",  # API-related tests
                r"@BeforeEach",  # JUnit-based integration
                r"beforeEach",  # Mocha-based integration
                r"before(:each)"  # RSpec-based integration
            ],
            "e2e": [
                # More specific patterns for E2E testing
                r"from\s+cypress",  # Cypress for e2e
                r"selenium",  # Selenium-based test
                r"puppeteer",  # Puppeteer for e2e
                r"@E2ETest",  # Custom e2e annotation
                r"\b(user|login|end-to-end|browser|e2e)\b",  # E2E test patterns
                r"^describe\s+\".*e2e.*\"",  # Mocha-based E2E test
                r"^it\s+\".*e2e.*\"",  # Mocha-based E2E test
                r"e2e",  # General keyword for E2E tests
                r"test\('e2e'",  # Jasmine-based E2E
                r"^require\s+selenium-webdriver",  # Ruby Selenium-based E2E test
                r"playwright.config.js",  # Playwright config file (E2E)
                r"signupForm.spec.js",  # Playwright or other E2E test file
                r"\.spec\.js$"  # Matches spec files which are commonly used in E2E testing
            ]
        }

    test_files = find_test_files(repo_path)
    results = {"unit_tests": [], "integration_tests": [], "e2e_tests": []}

    for test_file in test_files:
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            file_content = f.read()

        # Check the file name first
        for test_type, patterns in test_patterns.items():
            # Check if any pattern in the file name matches
            if any(re.search(pattern, test_file) for pattern in patterns[:3]):  # Match file name patterns
                results[f"{test_type}_tests"].append(test_file)
                break
            # Then check inside the file content for matching patterns
            if any(re.search(pattern, file_content, re.IGNORECASE) for pattern in patterns[3:]):  # Match file content patterns
                results[f"{test_type}_tests"].append(test_file)
                break

    return results


def find_test_files(repo_path):
    """
    Walk through the directory to find test files (e.g., .py, .js, .kt, .java, .cs, .rb).
    """
    test_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            # Ensure correct paths are being joined and no tuples
            if file.endswith((".py", ".js", ".kt", ".java", ".cs", ".rb")):  # Support for Python, JS, Kotlin, Java, C#, Ruby
                test_files.append(os.path.join(root, file))  # Join paths properly to avoid tuples
    return test_files

