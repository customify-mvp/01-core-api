## Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests  
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/domain/test_user_entity.py -v

# View coverage report
open htmlcov/index.html
```

## Test Results

Current coverage: **77%**

| Layer | Coverage |
|-------|----------|
| Domain | 92% |
| Application | 81% |
| Infrastructure | 68% |
| Presentation | 85% |