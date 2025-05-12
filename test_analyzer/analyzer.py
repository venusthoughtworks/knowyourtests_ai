import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import subprocess
import json
from collections import defaultdict

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

def is_test_file(file_path):
    """
    Check if a file is a test file by examining its content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Check if file contains any test patterns
        for patterns in test_patterns.values():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                return True
                
        return False
    except:
        return False

def find_test_files(repo_path):
    """
    Find test files by looking for actual test code in files.
    """
    test_files = []
    
    # Common test file extensions
    test_extensions = {".py", ".js", ".ts", ".java", ".kt", ".cs", ".rb", ".feature"}
    
    # Files to exclude
    excluded_files = {
        'package.json', 'package-lock.json', 'yarn.lock',
        'tsconfig.json', 'jest.config.js', 'pytest.ini',
        'conftest.py', 'webpack.config.js', 'babel.config.js',
        'karma.conf.js', 'cypress.json', 'playwright.config.js',
        'jest.config.ts', 'tsconfig.json', 'Gemfile', 'Gemfile.lock',
        'go.mod', 'go.sum', 'Cargo.toml', 'Cargo.lock',
        'composer.json', 'composer.lock', 'nuget.config',
        '.gitignore', 'README.md', 'requirements.txt',
        'setup.py', 'pom.xml', 'build.gradle'
    }
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip excluded files
            if file in excluded_files or file.startswith('.'):
                continue
                
            # Check file extension
            if not any(file.endswith(ext) for ext in test_extensions):
                continue
                
            file_path = os.path.join(root, file)
            
            # Check if file contains test code
            if is_test_file(file_path):
                print(f"[TEST DEBUG] Found test file: {file_path}")
                test_files.append(file_path)
            else:
                print(f"[TEST DEBUG] Not a test file: {file_path}")
    
    print(f"[TEST DEBUG] Total test files found: {len(test_files)}")
    return test_files

def count_test_cases_in_file(file_path):
    """
    Count test cases in a single file, classifying as unit, integration, or e2e for Python based on filename, folder, pytest markers, and folder structure.
    Also extract test function names and their locations for duplicate detection.
    """
    try:
        print(f"[TEST DEBUG] Processing file: {file_path}")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        counts = {"unit": 0, "integration": 0, "e2e": 0}
        filename = os.path.basename(file_path).lower()
        folder = os.path.dirname(file_path).lower()
        full_path = file_path.lower()
        
        # Extract test function names and their locations
        test_functions = []
        for match in re.finditer(r'def\s+(test_\w+)\s*\(', content):
            test_functions.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        print(f"[TEST DEBUG] Found {len(test_functions)} test functions in {file_path}")
        
        # Integration test detection
        is_integration = (
            'integration' in filename or
            'integration' in folder or
            'integration' in full_path or
            '@pytest.mark.integration' in content
        )
        print(f"[TEST DEBUG] Is integration test: {is_integration}")
        if is_integration:
            counts["integration"] = len(test_functions)
        
        # E2E test detection
        is_e2e = (
            'e2e' in filename or
            'e2e' in folder or
            'e2e' in full_path or
            '@pytest.mark.e2e' in content
        )
        print(f"[TEST DEBUG] Is E2E test: {is_e2e}")
        if is_e2e:
            counts["e2e"] = len(test_functions)
        
        # Unit test detection - count all test functions unless they're already counted as integration or e2e
        if test_functions:
            counts["unit"] = len(test_functions)
            # Remove from unit count if already counted as integration or e2e
            if counts["integration"] > 0:
                counts["unit"] = 0
            if counts["e2e"] > 0:
                counts["unit"] = 0
            print(f"[TEST DEBUG] Final counts: {counts}")
        
        return {
            'counts': counts,
            'test_functions': test_functions
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return {"counts": {"unit": 0, "integration": 0, "e2e": 0}, "test_functions": []}
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return {"unit": 0, "integration": 0, "e2e": 0}

def find_duplicate_tests_across_layers(test_results):
    """
    Find duplicate test files (by filename) that appear in more than one test type (unit, integration, e2e).
    Returns a dict: {filename: [list of types]}
    """
    file_to_types = defaultdict(set)
    for test_type in ['unit', 'integration', 'e2e']:
        for file_path in test_results.get(f'{test_type}_tests', []):
            filename = os.path.basename(file_path)
            file_to_types[filename].add(test_type)
    # Only keep files that appear in more than one type
    duplicates = {fname: list(types) for fname, types in file_to_types.items() if len(types) > 1}
    return duplicates

def find_duplicate_tests_across_layers(test_results):
    """
    Find duplicate test functions across different test layers.
    Returns a dictionary of duplicates for each layer.
    """
    duplicates = {
        "unit": [],
        "integration": [],
        "e2e": []
    }
    
    # Track all test functions by name
    all_functions = {}
    
    # First pass: collect all test functions
    for test_type in ['unit', 'integration', 'e2e']:
        for test_info in test_results.get(f"{test_type}_tests", []):
            for func in test_info.get("test_functions", []):
                func_name = func.get('name')
                if func_name:
                    if func_name not in all_functions:
                        all_functions[func_name] = []
                    all_functions[func_name].append({
                        'layer': test_type,
                        'file': test_info['file_path'],
                        'line': func.get('line', 0)
                    })
    
    # Second pass: detect duplicates
    for func_name, locations in all_functions.items():
        if len(locations) > 1:  # This function appears in multiple layers
            # Get all unique layers where this function appears
            layers = set(loc['layer'] for loc in locations)
            
            # Create duplicate entries for each layer
            for loc in locations:
                # Find other layers where this function appears
                other_layers = layers - {loc['layer']}
                if other_layers:
                    duplicates[loc['layer']].append({
                        'function': func_name,
                        'file': loc['file'],
                        'line': loc['line'],
                        'other_layers': list(other_layers)
                    })
    
    return duplicates

def classify_tests_in_repo(repo_path):
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
    for file_path, file_result in zip(test_files, file_results):
        counts = file_result["counts"]
        test_functions = file_result["test_functions"]
        
        # Add to appropriate test type
        if counts["unit"] > 0:
            results["unit_tests"].append({
                "file_path": file_path,
                "test_functions": test_functions
            })
            results["counts"]["unit"] += counts["unit"]
        if counts["integration"] > 0:
            results["integration_tests"].append({
                "file_path": file_path,
                "test_functions": test_functions
            })
            results["counts"]["integration"] += counts["integration"]
        if counts["e2e"] > 0:
            results["e2e_tests"].append({
                "file_path": file_path,
                "test_functions": test_functions
            })
            results["counts"]["e2e"] += counts["e2e"]
    
    # Find duplicates
    results["duplicate_tests"] = find_duplicate_tests_across_layers(results)
    return results

def find_js_projects(repo_path):
    """Recursively find all JS projects (folders with package.json and a test script)."""
    js_projects = []
    for root, dirs, files in os.walk(repo_path):
        if 'package.json' in files:
            pkg_path = os.path.join(root, 'package.json')
            try:
                with open(pkg_path, 'r') as f:
                    pkg = json.load(f)
                if 'scripts' in pkg and 'test' in pkg['scripts']:
                    js_projects.append(root)
            except Exception as e:
                print(f"[COVERAGE DEBUG] Error reading {pkg_path}: {e}")
    return js_projects

def calculate_test_coverage(test_results):
    """
    Calculate coverage based on test counts found in each layer.
    Returns a dict:
    {
        'unit': {
    """
    coverage = {
        'unit': {'test_count': 0, 'total_testable_functions': 0, 'coverage_percentage': 0.0, 'files': {}},
        'integration': {'test_count': 0, 'total_testable_functions': 0, 'coverage_percentage': 0.0, 'files': {}},
        'e2e': {'test_count': 0, 'total_testable_functions': 0, 'coverage_percentage': 0.0, 'files': {}}
    }
    
    # Get all testable functions (functions that start with test_)
    def get_testable_functions(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return len(re.findall(r'def\s+test_\w+', content))
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return 0

    # For each test type
    for test_type in ['unit', 'integration', 'e2e']:
        test_files = test_results.get(f'{test_type}_tests', [])
        if not test_files:
            continue

        # Process each file
        for file_info in test_files:
            file_path = file_info['file_path']
            test_count = len(file_info['test_functions'])
            total_functions = get_testable_functions(file_path)
            
            # Store file-level stats
            coverage[test_type]['files'][file_path] = {
                'test_count': test_count,
                'total_functions': total_functions,
                'coverage_percentage': (test_count / total_functions * 100) if total_functions > 0 else 0.0
            }
            
            # Update overall stats
            coverage[test_type]['test_count'] += test_count
            coverage[test_type]['total_testable_functions'] += total_functions

    # Calculate overall coverage percentage
    for test_type in ['unit', 'integration', 'e2e']:
        if coverage[test_type]['total_testable_functions'] > 0:
            # Calculate raw percentage
            raw_percentage = (coverage[test_type]['test_count'] /
                            coverage[test_type]['total_testable_functions'] * 100)
            
            # Cap at 100% if test_count exceeds total_testable_functions
            coverage[test_type]['coverage_percentage'] = min(100, raw_percentage)
            
            # Add a warning if test_count exceeds total_testable_functions
            if coverage[test_type]['test_count'] > coverage[test_type]['total_testable_functions']:
                print(f"[COVERAGE WARNING] {test_type} test count ({coverage[test_type]['test_count']}) exceeds total testable functions ({coverage[test_type]['total_testable_functions']})")
        else:
            coverage[test_type]['coverage_percentage'] = 0.0

    return coverage
