# Test Commands - Quick Reference

## Prerequisites

Make sure you're in the `backend` directory and your virtual environment is activated:

```bash
cd backend
# On Windows
.venv\Scripts\activate
# On Linux/Mac
source .venv/bin/activate
```

## Install Test Dependencies

```bash
pip install pytest pytest-cov httpx
```

## Verification Commands

### 1. Check Setup
Verify everything is installed correctly:

```bash
python check_setup.py
```

This will check:
- Python version
- Required packages
- App structure
- Test structure
- Configuration
- Import capability

### 2. Check Server Can Start
Verify the server module is correct:

```bash
# This should show the error if module path is wrong
uvicorn app.main:app --help
```

## Running Tests

### Basic Test Run

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with more details
pytest -vv
```

### Run Specific Test Files

```bash
# Test imports only
pytest tests/test_imports.py -v

# Test health endpoint
pytest tests/test_health_endpoint.py -v

# Test token endpoint
pytest tests/test_token_endpoint.py -v

# Test configuration
pytest tests/test_configuration.py -v

# Test integration
pytest tests/test_integration.py -v
```

### Run Specific Tests

```bash
# Run a single test function
pytest tests/test_health_endpoint.py::test_health_endpoint_exists -v

# Run tests matching a pattern
pytest -k "health" -v
pytest -k "token" -v
pytest -k "cors" -v
```

### Test with Coverage

```bash
# Basic coverage report
pytest --cov=app

# Detailed coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
# Then open: htmlcov/index.html

# Coverage with specific threshold
pytest --cov=app --cov-fail-under=70
```

### Using Test Runner Script

```bash
python run_tests.py
```

## Running the Server

### Development Server

```bash
# Standard run
uvicorn app.main:app --reload

# With custom host and port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With log level
uvicorn app.main:app --reload --log-level debug
```

### Test Server Manually

Once server is running, test in another terminal:

```bash
# Test health endpoint
curl http://127.0.0.1:8000/api/health

# Test token endpoint (no body)
curl -X POST http://127.0.0.1:8000/api/token

# Test token endpoint (with body)
curl -X POST http://127.0.0.1:8000/api/token \
  -H "Content-Type: application/json" \
  -d '{"room_name":"test-room","participant_name":"TestUser"}'
```

Or use PowerShell (Windows):

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get

# Test token endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/token" -Method Post -ContentType "application/json" -Body '{"room_name":"test-room"}'
```

## API Documentation

When server is running, access interactive API docs:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## Troubleshooting Tests

### Test Fails: Module Not Found

```bash
# Make sure you're in the backend directory
pwd

# Reinstall package in development mode
pip install -e .
```

### Test Fails: Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install from pyproject.toml
pip install -e .
```

### Test Hangs

Some tests might hang if they're waiting for a response. Press Ctrl+C and check:
- Is another server running on port 8000?
- Are there network issues?

### All Tests Skip

If tests are skipped:
```bash
# Check pytest is installed
pytest --version

# Run with more verbose output
pytest -v --tb=short
```

## Continuous Testing

### Watch Mode (requires pytest-watch)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw
```

### Quick Test Loop

```bash
# Run tests repeatedly
while true; do pytest; sleep 2; done
```

## Expected Results

### When NOT Configured (No LiveKit Keys)

```
tests/test_health_endpoint.py::test_health_endpoint_exists ✓
tests/test_health_endpoint.py::test_health_endpoint_configured_is_boolean ✓
tests/test_token_endpoint.py::test_token_endpoint_exists ✓ (returns 503)
```

### When Fully Configured

```
All tests should PASS ✓
Coverage should be > 70%
```

## Summary of All Commands

```bash
# Setup verification
python check_setup.py

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health_endpoint.py -v

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test manually
curl http://127.0.0.1:8000/api/health
```
