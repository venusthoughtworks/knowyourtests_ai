# GitHub Test Analyzer

A web-based tool that analyzes test coverage and organization in your codebase. It helps identify duplicate tests and provides detailed coverage statistics for unit, integration, and E2E tests.

## Features

- 📊 Test Coverage Analysis
  - Unit test coverage
  - Integration test coverage
  - E2E test coverage
  - Visual progress bars for each test type

- 🔄 Duplicate Test Detection
  - Identifies test functions that appear in multiple test layers
  - Shows test function names and their locations
  - Displays warning messages for potential test duplication issues

- 📊 Detailed Statistics
  - Number of test cases per layer
  - Total testable functions
  - File-level coverage breakdown
  - Warning messages for coverage issues

## Installation

1. Clone the repository:
```bash
git clone https://github.com/venusthoughtworks/knowyourtests_ai.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

The application will start on port 5005 by default.

## Usage

1. Open your web browser and navigate to `http://localhost:5005`

2. Enter the path to your project directory

3. Click "Analyze Tests" to get:
   - Test coverage statistics
   - Duplicate test detection results
   - Detailed file-level analysis

## Technology Stack

- Python Flask for the backend
- HTML/CSS for the frontend
- Chart.js for visualizations
- ThreadPoolExecutor for parallel processing






