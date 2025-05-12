import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
import xml.etree.ElementTree as ET
import glob

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
                test_files.append(file_path)
    
    return test_files

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

def detect_stack(repo_path):
    if os.path.exists(os.path.join(repo_path, 'requirements.txt')) or os.path.exists(os.path.join(repo_path, 'pytest.ini')):
        return 'python'
    if os.path.exists(os.path.join(repo_path, 'package.json')):
        return 'javascript'
    if os.path.exists(os.path.join(repo_path, 'pom.xml')) or os.path.exists(os.path.join(repo_path, 'build.gradle')):
        return 'java'
    if any(f.endswith('.csproj') for f in os.listdir(repo_path)):
        return 'dotnet'
    return None

def run_coverage(repo_path, stack):
    coverage_data = {}
    if stack == 'python':
        subprocess.run(['coverage', 'erase'], cwd=repo_path)
        subprocess.run(['coverage', 'run', '-m', 'pytest'], cwd=repo_path)
        result = subprocess.run(['coverage', 'report', '-m'], cwd=repo_path, capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            parts = line.split()
            if len(parts) >= 4 and parts[0].endswith('.py'):
                filename = os.path.abspath(os.path.join(repo_path, parts[0]))
                total = int(parts[1])
                missing = int(parts[2])
                covered = total - missing
                percentage = float(parts[3].strip('%'))
                coverage_data[filename] = {
                    "covered_lines": covered,
                    "total_lines": total,
                    "coverage_percentage": percentage
                }
    elif stack == 'javascript':
        js_projects = []
        for root, dirs, files in os.walk(repo_path):
            if 'package.json' in files:
                pkg_path = os.path.join(root, 'package.json')
                try:
                    with open(pkg_path) as pkg_file:
                        pkg = json.load(pkg_file)
                        if 'scripts' in pkg and 'test' in pkg['scripts']:
                            js_projects.append(root)
                except Exception as e:
                    print(f"Error reading {pkg_path}: {e}")
                    continue
        for project_dir in js_projects:
            try:
                subprocess.run(['npm', 'install'], cwd=project_dir, timeout=120, check=True)
                subprocess.run(['npm', 'test', '--', '--coverage'], cwd=project_dir, timeout=180, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running npm in {project_dir}: {e}")
                continue
            except subprocess.TimeoutExpired as e:
                print(f"Timeout running npm in {project_dir}: {e}")
                continue
            cov_json = os.path.join(project_dir, 'coverage', 'coverage-summary.json')
            if os.path.exists(cov_json):
                with open(cov_json) as f:
                    data = json.load(f)
                    files = data.get('files') or data.get('total') or {}
                    for file, info in files.items():
                        abs_file = os.path.abspath(os.path.join(project_dir, file)) if not os.path.isabs(file) else file
                        lines_info = info.get('lines') or info.get('statements')
                        if lines_info:
                            covered = lines_info.get('covered', 0)
                            total = lines_info.get('total', 0)
                            pct = lines_info.get('pct', 0)
                            if abs_file not in coverage_data:
                                coverage_data[abs_file] = {"covered_lines": 0, "total_lines": 0, "coverage_percentage": 0}
                            coverage_data[abs_file]["covered_lines"] += covered
                            coverage_data[abs_file]["total_lines"] += total
                            if coverage_data[abs_file]["total_lines"] > 0:
                                coverage_data[abs_file]["coverage_percentage"] = (
                                    coverage_data[abs_file]["covered_lines"] / coverage_data[abs_file]["total_lines"] * 100
                                )
    elif stack == 'java':
        subprocess.run(['./gradlew', 'test', 'jacocoTestReport'], cwd=repo_path)
        jacoco_xml = os.path.join(repo_path, 'build', 'reports', 'jacoco', 'test', 'jacocoTestReport.xml')
        if os.path.exists(jacoco_xml):
            tree = ET.parse(jacoco_xml)
            for package in tree.findall('.//package'):
                for sourcefile in package.findall('sourcefile'):
                    filename = sourcefile.attrib['name']
                    for root, _, files in os.walk(repo_path):
                        if filename in files:
                            abs_file = os.path.abspath(os.path.join(root, filename))
                            break
                    else:
                        abs_file = filename
                    covered = 0
                    missed = 0
                    for line in sourcefile.findall('line'):
                        if line.attrib.get('ci', '0') != '0':
                            covered += 1
                        else:
                            missed += 1
                    total = covered + missed
                    pct = (covered / total * 100) if total else 0
                    coverage_data[abs_file] = {
                        "covered_lines": covered,
                        "total_lines": total,
                        "coverage_percentage": pct
                    }
    elif stack == 'dotnet':
        subprocess.run(['dotnet', 'test', '--collect:"XPlat Code Coverage"'], cwd=repo_path)
        cobertura_xml = None
        for root, dirs, files in os.walk(os.path.join(repo_path, 'TestResults')):
            for file in files:
                if file.endswith('.xml'):
                    cobertura_xml = os.path.join(root, file)
                    break
        if cobertura_xml and os.path.exists(cobertura_xml):
            tree = ET.parse(cobertura_xml)
            for class_elem in tree.findall('.//class'):
                filename = class_elem.get('filename')
                if filename:
                    abs_path = os.path.abspath(os.path.join(repo_path, filename))
                    line_rate = float(class_elem.get('line-rate', 0))
                    lines = int(class_elem.get('lines', 0))
                    covered = int(lines * line_rate)
                    coverage_data[abs_path] = {
                        "covered_lines": covered,
                        "total_lines": lines,
                        "coverage_percentage": line_rate * 100
                    }
    return coverage_data

def classify_tests_in_repo(repo_path):
    stack = detect_stack(repo_path)
    coverage_map = run_coverage(repo_path, stack) if stack else {}

    test_files = find_test_files(repo_path)
    print("Test files:", test_files)
    results = {
        "unit_tests": [],
        "integration_tests": [],
        "e2e_tests": [],
        "counts": {"unit": 0, "integration": 0, "e2e": 0},
        "coverage": {
            "unit": {"covered_lines": 0, "total_lines": 0, "coverage_percentage": 0},
            "integration": {"covered_lines": 0, "total_lines": 0, "coverage_percentage": 0},
            "e2e": {"covered_lines": 0, "total_lines": 0, "coverage_percentage": 0}
        }
    }

    for file_path in test_files:
        counts = count_test_cases_in_file(file_path)
        abs_path = os.path.abspath(file_path)
        cov = coverage_map.get(abs_path, {"covered_lines": 0, "total_lines": 0, "coverage_percentage": 0})

        # For each test type, if this file has tests of that type, aggregate coverage
        for test_type in ["unit", "integration", "e2e"]:
            if counts[test_type] > 0:
                results[f"{test_type}_tests"].append(file_path)
                results["counts"][test_type] += counts[test_type]
                results["coverage"][test_type]["covered_lines"] += cov["covered_lines"]
                results["coverage"][test_type]["total_lines"] += cov["total_lines"]

    # Calculate coverage percentages for each test type
    for test_type in ["unit", "integration", "e2e"]:
        cov = results["coverage"][test_type]
        if cov["total_lines"] > 0:
            cov["coverage_percentage"] = cov["covered_lines"] / cov["total_lines"] * 100

    return results

