# HYROX Course Correct - Test Suite

This directory contains the test framework for the HYROX Course Correct application.

## Test Structure

### Unit Tests (`test_unit.py`)
Tests individual functions in isolation:
- Time parsing (HH:MM:SS and MM:SS formats)
- Time formatting (seconds to HH:MM:SS)
- Handicap calculations
- Edge cases and boundary conditions

### Component Tests (`test_components.py`)
Tests integration of related components:
- Data processing pipeline
- Handicap calculation logic
- Venue configuration loading
- Data file validation
- Data quality checks

### Integration Tests (`test_integration.py`)
Tests the Flask web application:
- API endpoints (`/`, `/venues`, `/convert`, `/analysis`)
- Time conversion functionality
- Venue handicap loading
- Error handling

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run with coverage:
```bash
pytest tests/ --cov=web --cov=execution --cov-report=html
```

### Run specific test categories:
```bash
pytest tests/test_unit.py          # Unit tests only
pytest tests/test_components.py    # Component tests only
pytest tests/test_integration.py   # Integration tests only
```

### Run with verbose output:
```bash
pytest tests/ -v
```

## Test Coverage

The test suite covers:
- ✅ Time parsing and formatting functions
- ✅ Handicap calculation logic
- ✅ Data processing and validation
- ✅ Flask API endpoints
- ✅ Data quality and integrity
- ✅ Configuration file validation

## Adding New Tests

When adding new features, create tests in the appropriate file:
- **Unit tests**: For pure functions with no dependencies
- **Component tests**: For modules that integrate multiple functions
- **Integration tests**: For API endpoints and user-facing features

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `client`: Flask test client for integration tests
- `sample_scraped_data`: Mock scraped data for component tests
- `sample_results_df`: Mock results DataFrame for testing

## Continuous Integration

This test framework is designed to be run in CI/CD pipelines. All tests should:
- Run quickly (< 10 seconds total)
- Be deterministic (no flaky tests)
- Clean up after themselves (no side effects)
