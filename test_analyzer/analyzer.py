import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# Define patterns for unit, integration, and e2e tests across multiple languages
test_patterns = {
    "unit": [
        # C# xUnit specific patterns
        r"\[Fact\]",  # xUnit Fact attribute
        r"\[Theory\]",  # xUnit Theory attribute
        r"public\s+void\s+\w+_Should",  # Common C# test naming pattern
        r"public\s+async\s+Task\s+\w+_Should",  # Async test pattern
        r"public\s+void\s+Test",  # Generic test pattern
        r"public\s+async\s+Task\s+Test",  # Async generic test pattern
        # General test patterns
        r"@Test",  # Java/JUnit
        r"^using\s+xunit",  # C# xUnit
        r"^using\s+nunit",  # C# NUnit
        r"^import\s+junit",  # Java JUnit
        r"test_\w+\s*\(",  # Python test methods
        r"def\s+test_\w+",  # Python test methods
        r"\[Test\]",  # .NET test methods
        r"@TestMethod",  # .NET test methods
    ],
    "integration": [
        r"@SpringBootTest",  # Spring Integration test
        r"testcontainers",  # Docker-based integration
        r"with_database\(.*\)",  # Custom integration
        r"\bservice\b",  # Service-level testing
        r"\bapi\b",  # API-related tests
        r"IntegrationTest",  # Integration test naming
    ],
    "e2e": [
        r"@E2ETest",  # Custom e2e annotation
        r"\b(user|login|end-to-end|browser|e2e)\b",  # E2E test patterns
        r"e2e",  # General keyword for E2E tests
        r"\.spec\.js$",  # E2E test files
        r"\.feature$",  # Cucumber feature files
        r"E2ETest",  # E2E test naming
    ]
}

def count_test_cases_in_file(file_path):
    """
    Count test cases in a single file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        counts = {
            "unit": 0,
            "integration": 0,
            "e2e": 0
        }
        
        # Count test cases for each type
        for test_type, patterns in test_patterns.items():
            # First check if this is a test file
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                # For C# xUnit tests
                if test_type == "unit" and ("using Xunit" in content or "using xunit" in content):
                    # Count [Fact] and [Theory] attributes
                    fact_count = len(re.findall(r'\[Fact\]', content))
                    theory_count = len(re.findall(r'\[Theory\]', content))
                    counts[test_type] = fact_count + theory_count
                else:
                    # Count test methods
                    test_methods = len(re.findall(
                        r'\[Fact\]|\[Theory\]|@Test\s+|test_\w+\s*\(|def\s+test_\w+|\b(it|test)\s*\(',
                        content
                    ))
                    counts[test_type] = test_methods if test_methods > 0 else 1
                
        return counts
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return {"unit": 0, "integration": 0, "e2e": 0}

def find_test_files(repo_path):
    """
    Find test files with optimized file extension checking.
    """
    test_extensions = {".py", ".js", ".kt", ".java", ".cs", ".rb", ".feature"}
    test_files = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in test_extensions):
                test_files.append(os.path.join(root, file))
    
    return test_files

def classify_tests_in_repo(repo_path, test_patterns=None):
    """
    Classifies tests into unit, integration, and e2e based on file names and patterns in the code.
    Uses parallel processing for better performance.
    """
    test_files = find_test_files(repo_path)
    results = {
        "unit_tests": [],
        "integration_tests": [],
        "e2e_tests": [],
        "counts": {
            "unit": 0,
            "integration": 0,
            "e2e": 0
        }
    }
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        file_results = list(executor.map(count_test_cases_in_file, test_files))
    
    # Aggregate results
    for file_path, counts in zip(test_files, file_results):
        if counts["unit"] > 0:
            results["unit_tests"].append(file_path)
            results["counts"]["unit"] += counts["unit"]
        if counts["integration"] > 0:
            results["integration_tests"].append(file_path)
            results["counts"]["integration"] += counts["integration"]
        if counts["e2e"] > 0:
            results["e2e_tests"].append(file_path)
            results["counts"]["e2e"] += counts["e2e"]
    
    return results

