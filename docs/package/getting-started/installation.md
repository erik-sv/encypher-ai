# Installation

EncypherAI is available on PyPI and can be installed using uv.

## Requirements

- Python 3.8 or later
- uv (Python package installer)

## Basic Installation

```bash
uv pip install encypher-ai
```

This installs the core EncypherAI package with all required dependencies.

## Development Installation

For development purposes, you can install EncypherAI with additional development dependencies:

```bash
# Clone the repository
git clone https://github.com/erik-sv/encypher_ai.git
cd encypher_ai

# Install with development dependencies
uv pip install -e ".[dev]"
```

## Dependencies

EncypherAI has the following core dependencies:

- `rich`: For formatted terminal output in demo scripts
- `requests`: For HTTP client functionality in API examples
- `python-dotenv`: For environment variable management

For development, additional dependencies include:

- `pytest`: For running tests
- `black`: For code formatting
- `isort`: For import sorting
- `flake8`: For linting
- `mypy`: For static type checking

## Verifying Installation

You can verify that EncypherAI is installed correctly by running:

```python
import encypher
print(encypher.__version__)
```

If the installation was successful, this will print the version number of the installed package.

## Next Steps

Once you have EncypherAI installed, continue to the [Quick Start Guide](quickstart.md) to learn how to use the package.
