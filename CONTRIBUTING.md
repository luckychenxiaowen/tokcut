# Contributing to tokcut

Thank you for your interest in contributing to tokcut! 🎉

tokcut is a transparent multi-model token saving proxy. We welcome contributions of all kinds — bug reports, feature requests, documentation improvements, code changes, and benchmark reports.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- A virtual environment (recommended)

### Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/tokcut.git
cd tokcut

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install in development mode with dev dependencies
pip install -e ".[dev]"

# 4. Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

1. **Find or create an issue** — Check [GitHub Issues](https://github.com/luckychenxiaowen/tokcut/issues) for existing tasks or open a new one.
2. **Create a feature branch**:

   ```bash
   git checkout -b feat/your-feature-name
   # or: fix/bug-description, docs/what-you-updated, perf/optimization-name
   ```

3. **Make your changes** — Write code, add tests, update docs.
4. **Run the full test suite**:

   ```bash
   pytest tests/ -v --cov=src/tokcut --cov-report=term-missing
   ```

5. **Commit with conventional commit messages**:

   ```bash
   git commit -m "feat: add streaming response support"
   git commit -m "fix: handle empty cache in sqlite backend"
   git commit -m "docs: update USAGE.md with streaming examples"
   ```

6. **Push and open a PR**:

   ```bash
   git push origin feat/your-feature-name
   ```

## Pull Request Guidelines

- **Keep PRs focused** — One feature or fix per PR.
- **Link issues** — Reference related issues with `Closes #123` or `Related to #456`.
- **Add tests** — New features must include tests. Bug fixes should include regression tests.
- **Update documentation** — If your change affects user-facing behavior, update relevant docs.
- **Pass CI** — All checks must pass before review.
- **Wait for review** — A maintainer will review your PR. Be responsive to feedback.

### PR Title Convention

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: description       # New feature
fix: description        # Bug fix
docs: description       # Documentation only
refactor: description   # Code restructuring
perf: description       # Performance improvement
test: description       # Adding tests
chore: description      # Maintenance tasks
```

## Code Style

We use **Ruff** for linting and formatting. Configuration is in `pyproject.toml`.

```bash
# Check code style
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

### Style Guidelines

- **Type hints** — Use type annotations for all public functions.
- **Docstrings** — Use Google-style docstrings for public modules and functions.
- **Line length** — Max 100 characters.
- **Imports** — Sort imports with `ruff` (standard library → third-party → local).

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/tokcut --cov-report=html

# Run specific test file
pytest tests/test_compressor.py -v

# Run with verbose output
pytest tests/ -v -s
```

### Writing Tests

- Place tests in `tests/` with `test_` prefix matching the module name.
- Use `pytest` fixtures for reusable test data.
- Mock external API calls in unit tests.
- Include integration tests for pipeline flows.

## Documentation

- **README.md** — Project overview, quick start, features.
- **USAGE.md** — Detailed usage instructions, API reference.
- **INSTALL.md** — Installation guide for all platforms.
- **docs/BENCHMARK_REPORT.md** — Benchmark methodology and results.
- **CONTRIBUTING.md** — This file.
- **CHANGELOG.md** — Release history.

When adding new features, update the relevant documentation files.

## Project Structure

```
tokcut/
├── src/tokcut/          # Core library
│   ├── server.py        # FastAPI proxy server
│   ├── compressor.py    # Output style compressor
│   ├── prompt_compressor.py  # Input semantic compressor
│   ├── cache.py         # Semantic cache (memory + SQLite)
│   ├── protector.py     # Content protector for tech strings
│   ├── token_counter.py # Token counting utilities
│   └── config.py        # Configuration management
├── tests/               # Test suite
│   └── benchmarks/      # Benchmark scripts
├── config/              # Default configuration
├── docs/                # Documentation
└── examples/            # Usage examples
```

## Release Process

Releases are managed by maintainers:

1. Update version in `src/tokcut/__version__.py` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.1.0`
4. Push the tag: `git push --tags`
5. The CI pipeline will build and publish to PyPI

## Questions?

- Open a [GitHub Discussion](https://github.com/luckychenxiaowen/tokcut/discussions)
- Join our [Discord](https://discord.gg/example)
- Email maintainers at [your-email@example.com]

Thank you for contributing! 🚀
