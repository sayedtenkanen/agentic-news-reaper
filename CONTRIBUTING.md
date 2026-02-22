# Contributing to Agentic News Reaper

Thank you for your interest in contributing to the **Agentic News Reaper** project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and professional environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (or `pip`)
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/agentic-news-reaper.git
   cd agentic-news-reaper
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   # or with pip:
   # pip install -e ".[dev]"
   ```

3. **Initialize the database:**
   ```bash
   agentic-news-reaper init
   ```

4. **Run tests:**
   ```bash
   pytest
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, concise code with type hints
- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Write tests for new functionality

### 3. Code Quality Checks

Before submitting, ensure your code passes:

```bash
# Format code
black agentic_news_reaper tests

# Lint code
ruff check agentic_news_reaper tests

# Type checking
mypy agentic_news_reaper

# Run tests
pytest --cov=agentic_news_reaper
```

Or run all checks at once:
```bash
make lint
make test
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new agent feature"
```

Follow conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for test additions
- `refactor:` for code refactoring
- `perf:` for performance improvements

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots or logs if applicable

## Project Structure

```
agentic-news-reaper/
├── agentic_news_reaper/        # Main package
│   ├── agents/                 # Multi-agent modules
│   │   ├── ndd.py             # Non-Determinism Detector
│   │   ├── epm.py             # Execution Pattern Miner
│   │   ├── fma.py             # Failure Mode Analyzer
│   │   └── hod.py             # Human Override Detector
│   ├── db/                     # Database layer
│   │   ├── connection.py       # SQLite connection management
│   │   └── schema.py           # Schema initialization
│   ├── config.py               # Configuration management
│   ├── logging.py              # Logging setup
│   ├── cli.py                  # Command-line interface
│   └── __init__.py
├── tests/                      # Test suite
├── .github/workflows/          # CI/CD workflows
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # Project documentation
└── CONTRIBUTING.md             # This file
```

## Testing Guidelines

### Writing Tests

- Use `pytest` as the test framework
- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test names: `test_<function>_<scenario>`

Example:
```python
def test_ndd_detects_ambiguous_title():
    """Test that NDD correctly identifies clickbait titles."""
    detector = NonDeterminismDetector(ambiguity_threshold=0.78)
    flag = detector.analyze("12345", "You Won't Believe This!!")
    assert flag is not None
    assert flag.ambiguity_score > 0.78
```

### Test Coverage

Aim for at least 80% code coverage. Check with:
```bash
pytest --cov=agentic_news_reaper --cov-report=html
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def analyze(self, story_id: str, title: str) -> Optional[Flag]:
    """Analyze a story for ambiguity.

    Args:
        story_id: Unique HN story identifier.
        title: Story title text.

    Returns:
        AmbiguityFlag if detected, else None.

    Raises:
        ValueError: If story_id is empty.
    """
```

### Updating README

- Keep the README in sync with code changes
- Document new features or configuration options
- Add examples for new CLI commands

## Agent Development Guidelines

When implementing new agents or extending existing ones:

1. **Follow the agent interface:**
   - Inherit from a base class (if established)
   - Implement standard methods like `analyze()`, `mine()`, etc.
   - Log important events using the structured logger

2. **Use type hints:**
   ```python
   def analyze(self, data: dict) -> dict:
       """Analyze data and return results."""
   ```

3. **Add configuration support:**
   - Accept thresholds and weights as parameters
   - Make values configurable via `AppConfig`

4. **Log appropriately:**
   ```python
   from agentic_news_reaper.logging import get_logger
   
   logger = get_logger(__name__)
   logger.info("Analysis complete", story_id=story_id, score=score)
   ```

## Database Schema Changes

If you modify the database schema:

1. Update `schema.sql` in `agentic_news_reaper/db/schema.py`
2. Add a migration if needed (or follow the versioning approach)
3. Test schema initialization with a fresh database
4. Update this guide if new tables are added

## Performance Considerations

- Minimize database queries; use batching when possible
- Cache pattern templates if loaded frequently
- Profile code before optimizing prematurely
- Document performance-sensitive areas

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Steps to reproduce
- Expected vs. actual behavior
- Relevant logs or error messages

### Feature Requests

Include:
- Clear use case
- Proposed implementation approach (if known)
- Example usage or API design

## Questions?

- Open an issue on GitHub
- Check existing documentation
- Review recent PRs for similar features

---

Thank you for contributing to making Agentic News Reaper better! 🚀