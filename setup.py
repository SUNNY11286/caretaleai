"""Setup configuration for CARETALE AI Python package."""
from setuptools import setup, find_packages

setup(
    name="caretale-ai",
    version="0.1.0",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    python_requires=">=3.10",
)
