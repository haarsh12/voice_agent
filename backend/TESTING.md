# Testing Guide for Vyamit Voice Backend

## Overview

This document describes how to run tests for the Vyamit Voice Backend application.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_imports.py          # Test all modules can be imported
├── test_main_app.py         # Test FastAPI application setup
├── test_health_endpoint.py  # Test /api/health endpoint
├── test_token_endpoint.py   # Test /api/token endpoint
├── test_cors.py             # Test CORS configuration
├── test_configuration.py    # Test settings and environment variables
├── test_providers.py        # Test STT, LLM, TTS provider factories
└── test_integration.py      # Integration tests for complete workflows
```

## Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-cov httpx
```

Or if using the project's dependency groups:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Quick Test Run

From the `backend` directory:

```bash
pytest
```

### Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_health_endpoint.py
```

### Run Specific Test

```bash
pytest tests/test_health_endpoint.py::test_health_endpoint_exists
```

### Using the Test Runner Script

```bash
python run_tests.py
```

### With Coverage Report

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Test Categories

### Import Tests (`test_imports.py`)
- Verifies all modules can be imported without errors
- Catches syntax errors and missing dependencies early

### Main App Tests (`test_main_app.py`)
- Tests FastAPI application initialization
- Verifies middleware configuration
- Checks API documentation endpoints

### Health Endpoint Tests (`test_health_endpoint.py`)
- Tests `/api/health` endpoint functionality
- Verifies response structure and data types
- Checks status, agent_name, and configured fields

### Token Endpoint Tests (`test_token_endpoint.py`)
- Tests `/api/token` endpoint with various payloads
- Validates room name constraints
- Tests participant name handling
- Checks error responses for invalid input

### CORS Tests (`test_cors.py`)
- Verifies CORS headers are present
- Tests preflight requests
- Validates origin handling

### Configuration Tests (`test_configuration.py`)
- Tests settings loading from environment
- Validates default values
- Checks configuration validation logic
- Tests property methods

### Provider Tests (`test_providers.py`)
- Tests STT, LLM, and TTS factory functions
- Verifies provider configuration
- Tests language parameter handling

### Integration Tests (`test_integration.py`)
- Tests complete workflows
- Verifies multiple endpoints work together
- Tests concurrent token requests
- Validates end-to-end functionality

## Expected Test Behavior

### When LiveKit is NOT Configured

- Health endpoint returns `configured: false`
- Token endpoint returns `503 Service Unavailable`
- Tests should PASS with this expected behavior

### When LiveKit IS Configured

- Health endpoint returns `configured: true`
- Token endpoint returns `200 OK` with valid tokens
- All integration tests should pass

## Environment Variables for Testing

Tests use the same environment configuration as the application:

```env
# Minimal config for basic tests
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Provider keys for full integration tests
DEEPGRAM_API_KEY=your-deepgram-key
MISTRAL_API_KEY=your-mistral-key
CARTESIA_API_KEY=your-cartesia-key
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Run tests with coverage
pytest --cov=app --cov-report=xml --cov-report=term

# Exit with error if coverage is below threshold
pytest --cov=app --cov-fail-under=70
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError: No module named 'app'`:
- Make sure you're running tests from the `backend` directory
- Install the package in editable mode: `pip install -e .`

### Missing Dependencies

If tests fail with missing packages:
```bash
pip install pytest httpx fastapi
```

### Environment Variable Issues

If tests fail due to configuration:
- Create a `.env` file in the backend directory
- Add required environment variables
- Tests will automatically use these values

## Writing New Tests

When adding new features:

1. Add unit tests in appropriate `test_*.py` file
2. Add integration tests in `test_integration.py`
3. Use fixtures from `conftest.py` for common setup
4. Follow naming convention: `test_<what_is_being_tested>`

Example:

```python
def test_new_feature():
    """Test description of what is being verified."""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/api/new-endpoint")
    
    # Assert
    assert response.status_code == 200
```

## Test Coverage Goals

- Aim for >80% code coverage
- All API endpoints should have tests
- All configuration options should be tested
- Critical paths must have integration tests
