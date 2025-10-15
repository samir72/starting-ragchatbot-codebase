# RAG System Test Suite

## Quick Start

### Run All Tests
```bash
uv run pytest backend/tests/
```

### Run Specific Test Files
```bash
# API endpoint tests
uv run pytest backend/tests/test_api.py -v

# AI generator tests
uv run pytest backend/tests/test_ai_generator.py -v

# RAG system tests
uv run pytest backend/tests/test_rag_system.py -v

# Error handling tests
uv run pytest backend/tests/test_error_handling.py -v

# Search tools tests
uv run pytest backend/tests/test_search_tools.py -v

# Vector store tests
uv run pytest backend/tests/test_vector_store.py -v
```

### Run Tests by Marker
```bash
# API tests only
uv run pytest -m api -v

# Unit tests only
uv run pytest -m unit -v

# Integration tests (requires API key)
uv run pytest -m integration -v
```

### Run Specific Test Classes or Functions
```bash
# Run specific class
uv run pytest backend/tests/test_api.py::TestQueryEndpoint -v

# Run specific test
uv run pytest backend/tests/test_api.py::TestQueryEndpoint::test_query_endpoint_success -v
```

## Test Organization

```
backend/tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api.py              # FastAPI endpoint tests (34 tests) ⭐ NEW
├── test_ai_generator.py     # AI generator component tests
├── test_rag_system.py       # RAG system integration tests
├── test_search_tools.py     # Search tool functionality tests
├── test_vector_store.py     # Vector store tests
├── test_error_handling.py   # Error handling and edge cases
├── API_TEST_SUMMARY.md      # Detailed documentation ⭐ NEW
└── README.md                # This file ⭐ NEW
```

## Test Statistics

- **Total Tests**: 152
- **API Endpoint Tests**: 34 (new)
- **Unit Tests**: 118 (existing)
- **Test Execution Time**: ~2-3 seconds for API tests

## Markers

Tests are categorized with markers for selective execution:

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require API keys)

## Available Fixtures

### FastAPI Testing
- `test_app` - FastAPI application instance for testing
- `test_client` - TestClient for making HTTP requests
- `mock_rag_system` - Pre-configured mock RAG system

### Test Data
- `sample_course_chunks` - Example course chunk data
- `sample_query_request` - Example query request
- `sample_query_response` - Example query response
- `sample_course_stats` - Example course statistics

### Component Mocks
- `mock_vector_store` - Mocked vector store
- `mock_ai_generator` - Mocked AI generator
- `mock_tool_manager` - Mocked tool manager

### Real Components
- `test_config` - Application configuration
- `vector_store_instance` - Real vector store instance
- `search_tool` - Real course search tool
- `tool_manager` - Real tool manager
- `ai_generator` - Real AI generator
- `rag_system_instance` - Real RAG system

## Common Test Patterns

### Testing API Endpoints
```python
def test_endpoint(test_client):
    response = test_client.post("/api/query", json={"query": "test"})
    assert response.status_code == 200
    assert "answer" in response.json()
```

### Overriding Mock Behavior
```python
def test_error_handling(test_client, test_app):
    # Override mock to simulate error
    mock = MagicMock()
    mock.query.side_effect = Exception("Error")
    test_app.state.mock_rag = mock

    response = test_client.post("/api/query", json={"query": "test"})
    assert response.status_code == 500
```

### Using Parametrize
```python
@pytest.mark.parametrize("query", ["test1", "test2", "test3"])
def test_multiple_queries(test_client, query):
    response = test_client.post("/api/query", json={"query": query})
    assert response.status_code == 200
```

## Pytest Configuration

Configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
addopts = ["-v", "--strict-markers", "--tb=short", "-ra"]
markers = ["unit", "integration", "api"]
asyncio_mode = "auto"
```

## Debugging Tests

### Verbose Output
```bash
uv run pytest -v
```

### Show Print Statements
```bash
uv run pytest -s
```

### Stop on First Failure
```bash
uv run pytest -x
```

### Run Last Failed Tests
```bash
uv run pytest --lf
```

### Show Full Traceback
```bash
uv run pytest --tb=long
```

### Generate Coverage Report
```bash
uv run pytest --cov=backend --cov-report=html
```

## Environment Setup

Tests automatically handle:
- Missing API keys (integration tests are skipped)
- Vector database initialization
- Session management
- Mock configuration

No manual setup required for running tests!

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    uv sync
    uv run pytest backend/tests/ --tb=short -ra
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/project
uv run pytest backend/tests/
```

### Slow Tests
```bash
# Run only fast unit tests
uv run pytest -m "not integration" -v
```

### ChromaDB Warnings
Warnings about resource trackers are suppressed in `backend/app.py` and can be ignored.

## Getting Help

- Check `API_TEST_SUMMARY.md` for detailed documentation
- Review `conftest.py` for available fixtures
- Run `uv run pytest --fixtures` to see all available fixtures
- Run `uv run pytest --markers` to see all available markers

## Contributing

When adding new tests:
1. Use appropriate markers (`@pytest.mark.api`, etc.)
2. Follow existing naming conventions (`test_<feature>_<scenario>`)
3. Add docstrings to describe test purpose
4. Use fixtures for common setup
5. Keep tests isolated and independent
