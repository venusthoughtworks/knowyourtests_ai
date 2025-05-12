import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import subprocess
import json

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

def run_coverage_by_type(repo_path, test_results):
    """
    Run coverage for the repo and return coverage for unit, integration, and e2e tests.
    Returns a dict:
    {
        'unit': {'covered_lines': int, 'total_lines': int, 'coverage_percentage': float},
        'integration': {...},
        'e2e': {...}
    }
    """
    import subprocess
    import os
    from test_analyzer.tech_stack_validator import detect_tech_stack

    def parse_coverage_py(coverage_file):
        try:
            with open(coverage_file, 'r') as f:
                lines = f.readlines()
            total, covered = 0, 0
            for line in lines:
                if line.strip().startswith('TOTAL'):
                    parts = line.split()
                    if len(parts) >= 4:
                        total = int(parts[1])
                        covered = int(parts[2])
            return covered, total
        except Exception as e:
            print(f"[COVERAGE DEBUG] Error reading coverage file: {e}")
            return 0, 0

    def parse_nyc_output(output):
        for line in output.splitlines():
            if line.strip().startswith('All files'):
                parts = line.split('|')
                if len(parts) >= 2:
                    try:
                        percent = float(parts[1].strip())
                        return percent
                    except Exception:
                        pass
        return 0.0

    coverage = {
        'unit': {'covered_lines': 0, 'total_lines': 0, 'coverage_percentage': 0.0},
        'integration': {'covered_lines': 0, 'total_lines': 0, 'coverage_percentage': 0.0},
        'e2e': {'covered_lines': 0, 'total_lines': 0, 'coverage_percentage': 0.0},
    }

    techs = detect_tech_stack(repo_path)
    print(f"[COVERAGE DEBUG] Detected tech stack: {techs}")
    if 'Python' in techs:
        # Run coverage for each test type separately
        for test_type in ['unit', 'integration', 'e2e']:
            test_files = test_results.get(f'{test_type}_tests', [])
            if not test_files:
                continue
            # Create a .coveragerc to only include these files
            coveragerc_path = os.path.join(repo_path, '.coveragerc')
            with open(coveragerc_path, 'w') as f:
                f.write('[run]\n')
                f.write('branch = True\n')
                f.write('source = .\n')
                f.write('[report]\n')
                f.write('omit =\n')
                # Omit all test files except the current type
                for other_type in ['unit', 'integration', 'e2e']:
                    if other_type != test_type:
                        for file in test_results.get(f'{other_type}_tests', []):
                            rel_path = os.path.relpath(file, repo_path)
                            f.write(f'    {rel_path}\n')
            try:
                subprocess.run(['coverage', 'erase'], cwd=repo_path, timeout=30)
                proc_run = subprocess.run(['coverage', 'run', '-m', 'pytest'], cwd=repo_path, capture_output=True, text=True, timeout=120)
                print(f"[COVERAGE DEBUG] {test_type} coverage run stdout:\n{proc_run.stdout}")
                print(f"[COVERAGE DEBUG] {test_type} coverage run stderr:\n{proc_run.stderr}")
                proc_report = subprocess.run(['coverage', 'report', '-m'], cwd=repo_path, capture_output=True, text=True, timeout=30)
                print(f"[COVERAGE DEBUG] {test_type} coverage report stdout:\n{proc_report.stdout}")
                print(f"[COVERAGE DEBUG] {test_type} coverage report stderr:\n{proc_report.stderr}")
                cov_file = os.path.join(repo_path, f'coverage_{test_type}.txt')
                with open(cov_file, 'w') as f:
                    f.write(proc_report.stdout)
                covered, total = parse_coverage_py(cov_file)
                percent = (covered / total * 100) if total else 0.0
                coverage[test_type] = {'covered_lines': covered, 'total_lines': total, 'coverage_percentage': percent}
            except Exception as e:
                print(f"[COVERAGE DEBUG] Exception during {test_type} coverage: {e}")
            finally:
                # Clean up .coveragerc
                if os.path.exists(coveragerc_path):
                    os.remove(coveragerc_path)
    elif 'JavaScript' in techs:
        # Find all JS projects (monorepo support)
        js_projects = find_js_projects(repo_path)
        print(f"[COVERAGE DEBUG] Found JS projects: {js_projects}")
        total_percent = {'unit': 0.0, 'integration': 0.0, 'e2e': 0.0}
        total_counts = {'unit': 0, 'integration': 0, 'e2e': 0}
        for project in js_projects:
            try:
                # 1. Run npm install if node_modules is missing
                if not os.path.exists(os.path.join(project, 'node_modules')):
                    print(f"[COVERAGE DEBUG] Running npm install in {project}")
                    subprocess.run(['npm', 'install'], cwd=project, timeout=180)
                # 2. Run tests with coverage
                proc = subprocess.run(['npx', 'nyc', '--reporter=text-summary', 'npm', 'test'], cwd=project, capture_output=True, text=True, timeout=180)
                print(f"[COVERAGE DEBUG] JS project {project} nyc stdout:\n{proc.stdout}")
                print(f"[COVERAGE DEBUG] JS project {project} nyc stderr:\n{proc.stderr}")
                percent = parse_nyc_output(proc.stdout)
                # 3. Count test files for each type in this project
                for test_type in ['unit', 'integration', 'e2e']:
                    files = [f for f in test_results.get(f'{test_type}_tests', []) if f.startswith(project)]
                    count = len(files)
                    total_counts[test_type] += count
                    # Distribute coverage by file count proportion
                    total_files = sum([len([f for f in test_results.get(f'{t}_tests', []) if f.startswith(project)]) for t in ['unit', 'integration', 'e2e']])
                    prop = (count / total_files) if total_files else 0
                    total_percent[test_type] += percent * prop
            except Exception as e:
                print(f"[COVERAGE DEBUG] Exception during JS coverage in {project}: {e}")
        for test_type in ['unit', 'integration', 'e2e']:
            coverage[test_type]['coverage_percentage'] = total_percent[test_type]
            coverage[test_type]['covered_lines'] = 0  # Not available from nyc summary
            coverage[test_type]['total_lines'] = 0
    print(f"[COVERAGE DEBUG] Final coverage dict: {coverage}")
    return coverage

