# SmartCanopy AI - Testing Guide

Complete testing strategy with 80+ tests covering all system components.

---

## Quick Start

### Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests

```bash
# All tests
python scripts/run_tests.py

# Specific categories
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --e2e
python scripts/run_tests.py --performance

# With coverage
python scripts/run_tests.py --coverage
```

---

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── test_agent.py              # Agent core (10+ tests)
├── test_api_integration.py    # API endpoints (20+ tests)
├── test_e2e_user_journey.py  # User scenarios (2+ tests)
├── test_performance.py        # Performance (15+ tests)
└── tools/                     # Tool tests (30+ tests)
    ├── test_species_recommender.py
    ├── test_environmental_calculator.py
    ├── test_pricing_calculator.py
    ├── test_hazard_checker.py
    └── test_remaining_tools.py
```

**Total: ~80 tests**

---

## Test Categories

### 1. Unit Tests (~50 tests)
Test individual components in isolation.

**Examples:**
- Agent initialization
- Tool execution
- Database queries
- Caching logic

```bash
python scripts/run_tests.py --unit
```

### 2. Integration Tests (~20 tests)
Test how components work together.

**Examples:**
- API endpoint responses
- Database + Cache interaction
- Agent + Tools integration

```bash
python scripts/run_tests.py --integration
```

### 3. End-to-End Tests (~2 tests)
Test complete user journeys.

**Examples:**
- Science fair demo scenario
- Multi-species comparison

```bash
python scripts/run_tests.py --e2e
```

### 4. Performance Tests (~15 tests)
Validate performance targets.

**Targets:**
- Database queries: < 100ms
- Tool execution: < 2 seconds
- Full conversation: < 8 seconds
- Cache hit rate: > 60%

```bash
python scripts/run_tests.py --performance
```

---

## Running Tests

### Test Runner Script

```bash
# Run all tests
python scripts/run_tests.py

# Run specific file
python scripts/run_tests.py --file test_agent.py

# Run specific test
python scripts/run_tests.py --test test_species_recommender

# Skip slow tests
python scripts/run_tests.py --fast

# Run in parallel
python scripts/run_tests.py --parallel 4

# Stop on first failure
python scripts/run_tests.py --exitfirst

# Verbose output
python scripts/run_tests.py --verbose
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_agent.py

# Run specific test
pytest tests/test_agent.py::TestSmartCanopyAgent::test_agent_initialization

# Run with pattern
pytest -k "species"

# With coverage
pytest --cov=agent --cov=api --cov-report=html

# In parallel
pytest -n 4
```

---

## Writing Tests

### Available Fixtures

Common fixtures from `conftest.py`:

- `db_manager` - In-memory test database
- `cache_service` - Redis cache (DB 15)
- `sample_species` - American Sycamore data
- `sample_planting_site` - Sample site data
- `mock_anthropic_response` - Mock Claude API
- `mock_hardiness_zone_api` - Mock USDA API

### Example Test

```python
import pytest
from agent.tools.my_tool import MyTool

@pytest.mark.asyncio
class TestMyTool:
    async def test_basic_execution(self, db_manager):
        tool = MyTool(db_manager)
        
        result = await tool.execute(param="value")
        
        assert "result" in result
        assert result["result"] is not None
```

### Best Practices

1. **Descriptive names**: `test_species_recommender_filters_by_zone`
2. **One thing per test**: Separate tests for separate behaviors
3. **Use fixtures**: Avoid duplicated setup code
4. **Mock external APIs**: Don't make real API calls
5. **Assert specifics**: Check exact values, not just truthiness

---

## Coverage Reports

### Generate Coverage

```bash
# HTML report
python scripts/run_tests.py --coverage

# Terminal report
pytest --cov=agent --cov=api --cov-report=term-missing
```

### View Report

```bash
# Open HTML report
open htmlcov/index.html
```

### Coverage Targets

| Component | Target |
|-----------|--------|
| Agent Core | 90%+ |
| Tools | 85%+ |
| API Routes | 80%+ |
| Overall | 80%+ |

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
cd /path/to/urban-tree-ai
source venv/bin/activate
pytest
```

### "Redis connection refused"
```bash
# Start Redis
redis-server

# Or skip Redis tests
pytest -m "not requires_redis"
```

### "Database connection failed"
```bash
# Install aiosqlite for in-memory tests
pip install aiosqlite>=0.19.0
```

### Tests are slow
```bash
# Run in parallel
python scripts/run_tests.py --parallel 4

# Skip slow tests
python scripts/run_tests.py --fast
```

---

## Performance Benchmarks

### Expected Test Duration

| Category | Tests | Duration |
|----------|-------|----------|
| Unit | ~50 | < 30s |
| Integration | ~20 | < 60s |
| E2E | ~2 | < 30s |
| Performance | ~15 | < 60s |
| **Total** | **~80** | **< 3min** |

### Monitor Performance

```bash
# Show slowest tests
pytest --durations=10
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - run: pip install -r requirements.txt
    - run: python scripts/run_tests.py --unit --coverage
    - run: python scripts/run_tests.py --integration
```

---

## Next Steps

1. Run full test suite: `python scripts/run_tests.py`
2. Set up pre-commit hooks
3. Configure CI/CD
4. Monitor coverage regularly
5. Add tests for new features

---

**Happy Testing! 🧪**

For more details, see test files in the `tests/` directory.
