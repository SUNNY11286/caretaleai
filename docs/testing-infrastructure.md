# Testing Infrastructure Setup

This document describes the testing infrastructure configuration for the CARETALE AI system.

## Overview

The testing infrastructure supports both unit testing and property-based testing (PBT) across Python and TypeScript codebases, as specified in the design document.

## Configuration Summary

### Python (Hypothesis)
- **Framework**: pytest + Hypothesis
- **Configuration File**: `python/tests/conftest.py`
- **Settings File**: `pyproject.toml`
- **Minimum Iterations**: 100 (standard profile)
- **Timeout**: 30 seconds per property test

### TypeScript (fast-check)
- **Framework**: Jest + fast-check
- **Configuration File**: `src/shared/test-config.ts`
- **Settings File**: `jest.config.js`
- **Minimum Iterations**: 100 (standard configuration)
- **Timeout**: 30 seconds per property test

## Key Features

### 1. Standardized Configuration
All property-based tests run with a minimum of 100 iterations to ensure statistical confidence, as required by the design document.

### 2. Multiple Testing Profiles

**Python Profiles** (via `--hypothesis-profile` flag):
- `standard` (default): 100 iterations, 30s timeout
- `intensive`: 500 iterations, 60s timeout
- `quick`: 20 iterations, 10s timeout (development only)
- `ci`: 100 iterations, deterministic for CI/CD

**TypeScript Configurations**:
- `propertyTestConfig`: 100 iterations, verbose output
- `intensivePropertyTestConfig`: 500 iterations, verbose output
- `quickPropertyTestConfig`: 20 iterations, quiet output (development only)

### 3. Helper Functions

**Python**: Use standard Hypothesis decorators
```python
from hypothesis import given, strategies as st

@given(text=st.text())
def test_property(text):
    # Test implementation
    pass
```

**TypeScript**: Use provided helper function
```typescript
import { runPropertyTest } from './shared/test-config';

runPropertyTest('Property name', fc.property(/* ... */));
```

### 4. Example Tests

Example property-based tests are provided to demonstrate best practices:
- Python: `python/tests/test_pbt_example.py`
- TypeScript: `src/shared/__tests__/pbt-example.test.ts`

## Running Tests

### Quick Start

```bash
# Install dependencies
make install

# Run all tests
make test

# Run only property-based tests (standard profile)
make test-pbt

# Run property-based tests with intensive profile
make test-pbt-intensive
```

### Python-Specific Commands

```bash
# Run all Python tests
make test-py

# Run with specific profile
pytest --hypothesis-profile=intensive

# Run with coverage
pytest --cov=python/src --cov-report=html
```

### TypeScript-Specific Commands

```bash
# Run all TypeScript tests
make test-ts

# Run specific test file
npm test -- src/shared/__tests__/pbt-example.test.ts

# Run in watch mode
npm run test:watch
```

## File Structure

```
caretale-ai/
├── python/
│   ├── src/                          # Python source code
│   └── tests/
│       ├── conftest.py               # Hypothesis configuration
│       └── test_pbt_example.py       # Example property tests
├── src/
│   └── shared/
│       ├── test-config.ts            # fast-check configuration
│       └── __tests__/
│           └── pbt-example.test.ts   # Example property tests
├── jest.config.js                    # Jest configuration
├── pyproject.toml                    # Python project configuration
├── Makefile                          # Build and test commands
└── TESTING.md                        # Comprehensive testing guide
```

## Design Document Compliance

This testing infrastructure implements the requirements specified in the Design Document Testing Strategy section:

✅ **Dual Testing Approach**: Both unit testing and property-based testing configured
✅ **Hypothesis (Python)**: Configured for AI pipeline testing
✅ **fast-check (TypeScript)**: Configured for interface component testing
✅ **Minimum 100 Iterations**: Enforced via configuration profiles
✅ **Test Tagging**: Examples demonstrate property-to-requirement mapping

## Next Steps

1. **Write Property Tests**: Use the examples as templates for implementing the 12 correctness properties defined in the design document
2. **Integrate with CI/CD**: Add test execution to continuous integration pipeline
3. **Monitor Coverage**: Track test coverage and identify gaps
4. **Refine Strategies**: Develop custom Hypothesis strategies and fast-check arbitraries for domain-specific data types

## References

- [Design Document](../design.md) - Testing Strategy section
- [Testing Guide](../TESTING.md) - Comprehensive testing documentation
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [fast-check Documentation](https://fast-check.dev/)

## Validation

To verify the testing infrastructure is correctly configured:

```bash
# 1. Check Python configuration
pytest --hypothesis-show-statistics

# 2. Run example property tests
pytest python/tests/test_pbt_example.py -v

# 3. Run TypeScript example tests
npm test -- src/shared/__tests__/pbt-example.test.ts

# 4. Verify iteration counts in output
# Python: Look for "Trying example X/100"
# TypeScript: Look for verbose output showing 100 runs
```

All tests should pass and demonstrate the configured iteration counts.
