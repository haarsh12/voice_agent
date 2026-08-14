# Quick Start - Testing Guide

## 30-Second Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Install test dependencies
pip install pytest httpx

# 4. Run setup check
python check_setup.py
```

## Run Tests

```bash
# All tests
pytest

# Or use test runner
python run_tests.py
```

## Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then visit: http://127.0.0.1:8000/docs

## What Was Created

✅ **8 Test Files** with 60+ tests covering:
- Health endpoint (`/api/health`)
- Token endpoint (`/api/token`)
- CORS configuration
- Settings & configuration
- Provider factories
- Integration workflows
- Import validation

✅ **Helper Scripts**:
- `check_setup.py` - Verify everything is ready
- `run_tests.py` - Run all tests with nice output

✅ **Documentation**:
- `TESTING.md` - Complete testing guide
- `TEST_COMMANDS.md` - Command reference
- `TEST_SUMMARY.md` - Detailed overview
- `QUICKSTART_TESTING.md` - This file

## Common Commands

```bash
# Check setup
python check_setup.py

# Run all tests
pytest

# Verbose output
pytest -v

# Specific test file
pytest tests/test_health_endpoint.py

# With coverage
pytest --cov=app

# Start server
uvicorn app.main:app --reload
```

## Test Files Overview

| File | Tests | What It Checks |
|------|-------|----------------|
| `test_imports.py` | 10 | All modules import correctly |
| `test_main_app.py` | 12 | FastAPI app setup |
| `test_health_endpoint.py` | 7 | Health endpoint works |
| `test_token_endpoint.py` | 10 | Token generation works |
| `test_cors.py` | 4 | CORS headers correct |
| `test_configuration.py` | 13 | Settings load properly |
| `test_providers.py` | 8 | Provider factories work |
| `test_integration.py` | 8 | Complete workflows |

## Expected Results

✅ All tests should **PASS** regardless of configuration

- Without LiveKit keys: Token endpoint returns 503 ✅ Expected
- With LiveKit keys: Token endpoint returns 200 ✅ Expected

## Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'app'`
```bash
cd backend
pip install -e .
```

**Problem**: `ModuleNotFoundError: No module named 'pytest'`
```bash
pip install pytest httpx
```

**Problem**: Tests fail with import errors
```bash
python check_setup.py
```

## Next Steps

1. ✅ Tests created - you're here
2. Run `python check_setup.py` to verify
3. Run `pytest` to test everything
4. Run `uvicorn app.main:app --reload` to start server
5. Check code is working at http://127.0.0.1:8000/docs

## Full Documentation

- **Complete guide**: See `TESTING.md`
- **All commands**: See `TEST_COMMANDS.md`
- **Detailed summary**: See `TEST_SUMMARY.md`
