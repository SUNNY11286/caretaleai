# Testing Quick Reference

Quick reference for writing tests in the CARETALE AI system.

## Running Tests

```bash
make test              # Run all tests
make test-py           # Python tests only
make test-ts           # TypeScript tests only
make test-pbt          # Property-based tests (100 iterations)
make test-pbt-intensive # Property-based tests (500 iterations)
```

## Python Property Test Template

```python
from hypothesis import given, strategies as st, example

@given(input_data=st.text(min_size=1, max_size=1000))
@example(input_data="edge case")
def test_property_name(input_data: str):
    """
    Property: [Description of the property]
    
    **Validates: Design Document Property X**
    
    For any [input description], the system should [expected behavior].
    """
    result = system_under_test(input_data)
    
    # Property assertions
    assert result is not None, "Result should not be None"
    assert isinstance(result, ExpectedType), "Result should be correct type"
    # Add more assertions as needed
```

## TypeScript Property Test Template

```typescript
import * as fc from 'fast-check';
import { propertyTestConfig } from '../shared/test-config';

test('Property: [Description]', () => {
  fc.assert(
    fc.property(
      fc.string({ minLength: 1, maxLength: 1000 }),
      (inputData) => {
        const result = systemUnderTest(inputData);
        
        expect(result).toBeDefined();
        expect(typeof result).toBe('string');
        // Add more assertions as needed
      }
    ),
    propertyTestConfig
  );
});
```

## Common Strategies/Arbitraries

### Python (Hypothesis)

```python
from hypothesis import strategies as st

st.text()                              # Any string
st.text(min_size=1, max_size=100)     # Bounded string
st.integers()                          # Any integer
st.integers(min_value=0, max_value=100) # Bounded integer
st.floats()                            # Any float
st.booleans()                          # True/False
st.lists(st.integers())                # List of integers
st.dictionaries(st.text(), st.integers()) # Dict
st.one_of(st.text(), st.integers())    # Union type
st.none()                              # None value
```

### TypeScript (fast-check)

```typescript
import * as fc from 'fast-check';

fc.string()                            // Any string
fc.string({ minLength: 1, maxLength: 100 }) // Bounded string
fc.integer()                           // Any integer
fc.integer({ min: 0, max: 100 })      // Bounded integer
fc.float()                             // Any float
fc.boolean()                           // true/false
fc.array(fc.integer())                 // Array of integers
fc.dictionary(fc.string(), fc.integer()) // Object
fc.oneof(fc.string(), fc.integer())    // Union type
fc.constant(null)                      // null value
```

## Property Test Checklist

- [ ] Test references design document property number
- [ ] Uses appropriate strategies/arbitraries for input generation
- [ ] Tests universal properties (not specific examples)
- [ ] Includes clear, descriptive assertions
- [ ] Runs minimum 100 iterations (automatic via config)
- [ ] Includes docstring/comment explaining the property
- [ ] Uses `@example` decorator for important edge cases (Python)

## Unit Test Template

### Python

```python
import pytest

class TestComponentName:
    def test_specific_behavior(self):
        """Test that component handles specific case correctly"""
        result = component.method(input_value)
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case handling"""
        with pytest.raises(ExpectedException):
            component.method(invalid_input)
```

### TypeScript

```typescript
describe('ComponentName', () => {
  test('should handle specific case correctly', () => {
    const result = component.method(inputValue);
    expect(result).toBe(expectedValue);
  });
  
  test('should handle edge case', () => {
    expect(() => component.method(invalidInput))
      .toThrow(ExpectedException);
  });
});
```

## Debugging Failed Property Tests

### Python

```bash
# Run with verbose output
pytest -v --hypothesis-verbosity=verbose

# Run with specific seed to reproduce
pytest --hypothesis-seed=12345

# Show statistics
pytest --hypothesis-show-statistics
```

### TypeScript

```typescript
// Add seed to configuration for reproducibility
fc.assert(
  fc.property(/* ... */),
  { ...propertyTestConfig, seed: 12345 }
);
```

## Coverage

```bash
# Python coverage
pytest --cov=python/src --cov-report=html
# View: open htmlcov/index.html

# TypeScript coverage
npm test -- --coverage
# View: open coverage/lcov-report/index.html
```

## Common Issues

**Tests too slow?**
- Use `quick` profile during development
- Optimize strategies/arbitraries
- Reduce max_examples temporarily

**Flaky tests?**
- Set specific seed for reproducibility
- Check for non-deterministic behavior
- Use `derandomize=True` in CI

**Memory issues?**
- Constrain strategy/arbitrary sizes
- Reduce max_examples
- Check for memory leaks in code

## Resources

- [TESTING.md](../TESTING.md) - Full testing guide
- [Design Document](../design.md) - Testing strategy
- [Hypothesis Docs](https://hypothesis.readthedocs.io/)
- [fast-check Docs](https://fast-check.dev/)
