# Testing Guide for CARETALE AI

This document provides comprehensive guidance on testing practices for the CARETALE AI system, including both unit testing and property-based testing.

## Overview

The CARETALE AI testing strategy employs a dual approach:

1. **Unit Testing**: Validates specific examples and edge cases
2. **Property-Based Testing (PBT)**: Validates universal properties across all inputs

Both approaches are essential and complement each other to ensure system reliability and correctness.

## Testing Frameworks

### Python Testing Stack
- **pytest**: Unit testing framework
- **Hypothesis**: Property-based testing framework
- **pytest-cov**: Code coverage reporting

### TypeScript Testing Stack
- **Jest**: Unit testing framework
- **fast-check**: Property-based testing framework
- **ts-jest**: TypeScript integration for Jest

## Property-Based Testing Configuration

### Python (Hypothesis)

The Hypothesis configuration is defined in `python/tests/conftest.py` with the following profiles:

- **standard** (default): 100 iterations, 30s timeout
- **intensive**: 500 iterations, 60s timeout
- **quick**: 20 iterations, 10s timeout (development only)
- **ci**: 100 iterations, 30s timeout, deterministic

To use a specific profile:
```bash
# Run with intensive profile
pytest --hypothesis-profile=intensive

# Run with CI profile
pytest --hypothesis-profile=ci
```

### TypeScript (fast-check)

The fast-check configuration is defined in `src/shared/test-config.ts`:

```typescript
import { propertyTestConfig } from './shared/test-config';

fc.assert(
  fc.property(/* ... */),
  propertyTestConfig  // 100 iterations, verbose output
);
```

## Writing Property-Based Tests

### Python Example

```python
from hypothesis import given, strategies as st

@given(text_input=st.text(min_size=1, max_size=1000))
def test_property_example(text_input: str):
    """
    Property: Description of the property being tested
    
    **Validates: Design Document Property X**
    
    For any valid input, the system should exhibit this behavior.
    """
    result = system_under_test(text_input)
    
    # Property assertions
    assert result is not None
    assert isinstance(result, str)
```

### TypeScript Example

```typescript
import * as fc from 'fast-check';
import { propertyTestConfig } from '../shared/test-config';

test('Property: Description', () => {
  fc.assert(
    fc.property(
      fc.string({ minLength: 1, maxLength: 1000 }),
      (textInput) => {
        const result = systemUnderTest(textInput);
        
        expect(result).toBeDefined();
        expect(typeof result).toBe('string');
      }
    ),
    propertyTestConfig
  );
});
```

## Property Test Requirements

Each property-based test MUST:

1. **Reference the design document property** it validates
2. **Use appropriate strategies** for input generation
3. **Test universal properties** that hold across all valid inputs
4. **Include clear assertions** with descriptive error messages
5. **Run minimum 100 iterations** (configured automatically)

## Running Tests

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=python/src --cov-report=html

# Run specific test file
pytest python/tests/test_example.py

# Run with verbose output
pytest -v

# Run property tests with intensive profile
pytest --hypothesis-profile=intensive
```

### TypeScript Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/shared/__tests__/example.test.ts

# Run in watch mode (development)
npm run test:watch

# Run with verbose output
npm test -- --verbose
```

## Test Organization

### Python Test Structure
```
python/
├── src/
│   └── [source code]
└── tests/
    ├── conftest.py              # Hypothesis configuration
    ├── test_pbt_example.py      # Property-based test examples
    └── [component tests]/
```

### TypeScript Test Structure
```
src/
├── shared/
│   ├── test-config.ts           # fast-check configuration
│   └── __tests__/
│       └── pbt-example.test.ts  # Property-based test examples
└── [layer]/
    ├── [component].ts
    └── __tests__/
        ├── [component].test.ts  # Unit tests
        └── [component].pbt.test.ts  # Property tests
```

## Common Hypothesis Strategies

```python
from hypothesis import strategies as st

# Basic types
st.text()                    # Any string
st.integers()                # Any integer
st.floats()                  # Any float
st.booleans()                # True or False

# Constrained types
st.text(min_size=1, max_size=100)
st.integers(min_value=0, max_value=1000)
st.lists(st.integers(), min_size=1, max_size=50)

# Complex types
st.dictionaries(keys=st.text(), values=st.integers())
st.tuples(st.text(), st.integers())
st.one_of(st.text(), st.integers(), st.none())

# Custom strategies
@st.composite
def patient_profile(draw):
    return {
        'patient_id': draw(st.uuids()),
        'name': draw(st.text(min_size=1)),
        'age': draw(st.integers(min_value=0, max_value=120))
    }
```

## Common fast-check Arbitraries

```typescript
import * as fc from 'fast-check';

// Basic types
fc.string()                  // Any string
fc.integer()                 // Any integer
fc.float()                   // Any float
fc.boolean()                 // true or false

// Constrained types
fc.string({ minLength: 1, maxLength: 100 })
fc.integer({ min: 0, max: 1000 })
fc.array(fc.integer(), { minLength: 1, maxLength: 50 })

// Complex types
fc.dictionary(fc.string(), fc.integer())
fc.tuple(fc.string(), fc.integer())
fc.oneof(fc.string(), fc.integer(), fc.constant(null))

// Custom arbitraries
const patientProfileArbitrary = fc.record({
  patientId: fc.uuid(),
  name: fc.string({ minLength: 1 }),
  age: fc.integer({ min: 0, max: 120 })
});
```

## Best Practices

### 1. Property Selection
- Focus on invariants that should always hold
- Test relationships between inputs and outputs
- Verify idempotence, commutativity, associativity where applicable

### 2. Strategy Design
- Constrain inputs to valid ranges
- Use composite strategies for complex data structures
- Include edge cases explicitly with `@example` (Python) or `.examples()` (TypeScript)

### 3. Assertion Quality
- Use descriptive assertion messages
- Test multiple properties in a single test when related
- Avoid testing implementation details

### 4. Performance
- Keep property tests focused and fast
- Use appropriate iteration counts (100 for standard, 500 for intensive)
- Profile slow tests and optimize strategies

### 5. Debugging
- Use `print_blob=True` (Hypothesis) to see failing examples
- Use `verbose` mode to understand test execution
- Reproduce failures with specific seeds

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --hypothesis-profile=ci --cov=python/src

  test-typescript:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test -- --coverage
```

## Troubleshooting

### Hypothesis Issues

**Problem**: Tests are too slow
- **Solution**: Reduce `max_examples` or optimize strategies

**Problem**: Flaky tests
- **Solution**: Use `derandomize=True` or set a specific seed

**Problem**: Shrinking takes too long
- **Solution**: Simplify strategies or disable shrinking phases

### fast-check Issues

**Problem**: Tests timeout
- **Solution**: Increase Jest timeout or reduce `numRuns`

**Problem**: Non-deterministic failures
- **Solution**: Set a specific seed in configuration

**Problem**: Memory issues with large inputs
- **Solution**: Constrain arbitrary sizes

## Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [fast-check Documentation](https://fast-check.dev/)
- [Property-Based Testing Patterns](https://fsharpforfunandprofit.com/posts/property-based-testing/)
- [Design Document](./design.md) - See Testing Strategy section

## Support

For questions or issues with testing:
1. Check this guide and the design document
2. Review example tests in the codebase
3. Consult the team's testing channel
4. Open an issue with the testing label
