"""
Property-Based Testing Configuration

This module provides centralized configuration for property-based testing
using Hypothesis. All property tests should use these settings to ensure
consistency with the design requirements (minimum 100 iterations).
"""

from hypothesis import settings, Verbosity, Phase

# Standard profile for property-based tests
# - max_examples: Minimum 100 iterations as per design document
# - deadline: 30 seconds for complex property tests
# - verbosity: Normal output for debugging
settings.register_profile(
    "standard",
    max_examples=100,
    deadline=30000,  # 30 seconds in milliseconds
    verbosity=Verbosity.normal,
    print_blob=True,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target, Phase.shrink],
)

# Intensive profile for thorough testing
settings.register_profile(
    "intensive",
    max_examples=500,
    deadline=60000,  # 60 seconds
    verbosity=Verbosity.verbose,
    print_blob=True,
)

# Quick profile for development (not recommended for CI/CD)
settings.register_profile(
    "quick",
    max_examples=20,
    deadline=10000,  # 10 seconds
    verbosity=Verbosity.quiet,
)

# CI profile for continuous integration
settings.register_profile(
    "ci",
    max_examples=100,
    deadline=30000,
    verbosity=Verbosity.normal,
    print_blob=True,
    derandomize=True,  # Reproducible tests in CI
)

# Load the standard profile by default
settings.load_profile("standard")
