# Setup and Reference Guide

## Quick Navigation

- **First time?** → Go to [Quick Start](#quick-start)
- **Need setup help?** → See [Installation & Setup](#installation--setup)
- **Daily development?** → See [Daily Development Workflow](#daily-development-workflow)
- **Using the CLI?** → See [CLI Reference](#cli-reference)
- **Coding with the library?** → See [Programmatic Usage](#programmatic-usage)
- **Something broken?** → See [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1-Minute Setup
```bash
uv pip install -e ".[dev]"
cp .env.example .env
uv run pytest tests/ -v
```

### First Commands
```bash
# Verify CLI works
uv run agentic-news-reaper --help

# Initialize database
uv run agentic-news-reaper init

# Run tests
uv run pytest tests/ -v
```

### Expected Output
```
CLI help message displays
Database initialized successfully
88 tests pass (2 optional smoke tests OK to skip)
```

---

## Installation & Setup

### Prerequisites
- Python 3.12 or higher
- pip or uv package manager
- Git

### Install Development Environment

```bash
# Clone and navigate
git clone <repository-url>
cd agentic-news-reaper

# Install with all dependencies
uv pip install -e ".[dev]"
```

### Configure Environment

```bash
# Copy configuration template
cp .env.example .env

# Edit if needed (defaults work for development)
# nano .env  (optional)
```

### Verify Installation

```bash
# Check CLI
uv run agentic-news-reaper --help

# Run tests
uv run pytest tests/ -v

# Expected: 88 tests pass
```

---

## Daily Development Workflow

### Format Code
```bash
uv run black agentic_news_reaper tests
```

### Lint Code
```bash
uv run ruff check --fix agentic_news_reaper tests
```

### Type Check
```bash
uv run mypy agentic_news_reaper
```

### Run Tests
```bash
uv run pytest tests/ -v
```

### Pre-Commit Checklist (Run Before Committing)
```bash
uv run black agentic_news_reaper tests && \
uv run ruff check --fix agentic_news_reaper tests && \
uv run mypy agentic_news_reaper && \
uv run pytest tests/ -v
```

### Run Specific Tests
```bash
# Database tests only
uv run pytest tests/test_database.py -v

# EPM agent tests only
uv run pytest tests/test_epm.py -v

# HN client tests only
uv run pytest tests/test_hn_client.py -v

# Single test function
uv run pytest tests/test_epm.py::TestConfidenceCalculation::test_calculate_confidence_title_only -v
```

### Coverage Report
```bash
uv run pytest tests/ --cov=agentic_news_reaper --cov-report=html
# Opens htmlcov/index.html in browser
```

---

## CLI Reference

### Initialize Database
```bash
# Default: creates hn_state.db
uv run agentic-news-reaper init

# Custom path
uv run agentic-news-reaper init --db-path /path/to/custom.db
```

### Run Pipeline
```bash
# Full pipeline with 100 stories
uv run agentic-news-reaper run --stories-count 100

# Dry-run mode (no database persistence)
uv run agentic-news-reaper run --dry-run

# Debug mode with verbose logging
uv run agentic-news-reaper --debug run
```

### Generate Weekly Brief
```bash
# Generate brief for current week
uv run agentic-news-reaper brief

# Generate brief for specific week
uv run agentic-news-reaper brief --week 2026-W08

# Save to file
uv run agentic-news-reaper brief --output ./reports/brief.md
```

### Display Database Schema
```bash
uv run agentic-news-reaper schema
```

### Get Help
```bash
uv run agentic-news-reaper --help
uv run agentic-news-reaper run --help
```

---

## Programmatic Usage

### Configuration

```python
from agentic_news_reaper.config import get_config

config = get_config()
print(config.database.db_path)
print(config.agents.ndd_ambiguity_threshold)
print(config.logging.log_level)
```

### Database Operations

```python
from agentic_news_reaper.db.connection import DatabaseConnection
from agentic_news_reaper.db.schema import init_schema
from pathlib import Path

# Initialize database
db_path = Path("hn_state.db")
init_schema(db_path)

# Connect and query
with DatabaseConnection(db_path) as conn:
    # Insert story
    cursor = conn.execute(
        "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        ("12345", "Test Story", "https://example.com")
    )
    conn.commit()
    
    # Query stories
    cursor = conn.execute("SELECT * FROM hn_raw WHERE score > ?", (100,))
    for row in cursor.fetchall():
        print(row)
```

### Non-Determinism Detector (NDD)

```python
from agentic_news_reaper.agents.ndd import NonDeterminismDetector

ndd = NonDeterminismDetector(ambiguity_threshold=0.78)

flag = ndd.analyze(
    story_id="12345",
    title="You won't believe what happened next!",
    comments_count=50
)

if flag:
    print(f"Ambiguity detected: {flag.reason}")
```

### Execution Pattern Miner (EPM)

```python
from agentic_news_reaper.agents.epm import ExecutionPatternMiner

epm = ExecutionPatternMiner(min_confidence=0.5)

patterns = epm.mine(
    story_id="12345",
    title="Shocking Python vulnerability discovered!",
    url="https://security.example.com",
    metadata={
        "score": 150,
        "descendants": 25,
        "sentiment_variance": 0.5
    }
)

for pattern in patterns:
    print(f"Pattern: {pattern.pattern_id}, Confidence: {pattern.confidence}")
```

### Failure Mode Analyzer (FMA)

```python
from agentic_news_reaper.agents.fma import FailureModeAnalyzer

fma = FailureModeAnalyzer()

failure_mode = fma.analyze_pattern(
    pattern_instance_id=1,
    comment_count=50,
    spam_score=0.1,
    sentiment_variance=0.2
)

print(f"Risk Score: {failure_mode.risk_score}")
print(f"Mitigation: {failure_mode.mitigation}")
```

### Human Override Detector (HOD)

```python
from agentic_news_reaper.agents.hod import HumanOverrideDetector

hod = HumanOverrideDetector(override_threshold=0.9)

decision = hod.evaluate(
    story_id="12345",
    risk_score=0.95,
    pattern_type="financial"
)

if decision.requires_override:
    print(f"Override required: {decision.reason}")
```

### Hacker News Client

```python
import asyncio
from agentic_news_reaper.hn_client import HackerNewsClient

async def fetch_data():
    client = HackerNewsClient()
    
    # Get top stories (async, cached, rate-limited)
    story_ids = await client.get_top_stories(count=100)
    print(f"Fetched {len(story_ids)} story IDs")
    
    # Get single story details
    story = await client.get_story(story_ids[0])
    print(f"Title: {story['title']}")
    print(f"Score: {story['score']}")
    
    # Get batch of stories concurrently
    stories = await client.get_stories_batch(story_ids[:10])
    print(f"Fetched {len([s for s in stories if s])} stories")
    
    # Get user info
    user = await client.get_user(story['by'])
    print(f"User: {user['id']}, Karma: {user['karma']}")
    
    # Get comments recursively
    comments = await client.get_comments(story_ids[0], max_depth=2)
    print(f"Fetched {len(comments)} top-level comments")

asyncio.run(fetch_data())
```

### Logging

```python
from agentic_news_reaper.logging import configure_logging, get_logger

# Configure logging (debug=True for verbose output)
configure_logging(debug=True)

# Get logger for your module
logger = get_logger(__name__)

# Use structured logging
logger.info("Application started", version="0.1.0")
logger.warning("This is a warning", error_code=42)
logger.error("An error occurred", error="Something went wrong")
```

---

### Project Structure

```
agentic-news-reaper/
├── agentic_news_reaper/
│   ├── agents/                  # Multi-agent system
│   │   ├── ndd.py              # Non-Determinism Detector
│   │   ├── epm.py              # Execution Pattern Miner
│   │   ├── fma.py              # Failure Mode Analyzer
│   │   └── hod.py              # Human Override Detector
│   ├── db/                      # Database layer
│   │   ├── schema.py           # Schema definitions
│   │   └── connection.py       # DB connection
│   ├── templates/
│   │   └── patterns.yaml       # 10 pattern library
│   ├── cli.py                  # CLI commands
│   ├── config.py               # Configuration
│   ├── hn_client.py            # HN API client (259 lines)
│   └── logging.py              # Structured logging
├── tests/                       # 88 tests across 4 files
│   ├── test_database.py        # 25 tests
│   ├── test_epm.py             # 31 tests
│   ├── test_hn_client.py       # 27 tests
│   └── test_smoke.py           # 2 optional tests (WIP)
├── .env.example                # Configuration template
├── pyproject.toml              # Project config
└── README.md                   # Project overview
```

### Dependencies

**Runtime** (7 packages):
- click>=8.1.0 - CLI framework
- pydantic>=2.0.0 - Data validation
- pydantic-settings>=2.0.0 - Settings management
- structlog>=23.2.0 - Structured logging
- httpx>=0.24.0 - Async HTTP client
- python-dotenv>=1.0.0 - .env file loading
- pyyaml>=6.0.0 - YAML pattern loading

**Development** (7 packages):
- pytest>=7.4.0 - Testing framework
- pytest-asyncio>=0.21.0 - Async test support
- mypy>=1.5.0 - Type checking
- ruff>=0.1.0 - Linting
- black>=23.0.0 - Code formatting
- types-click - Click type stubs
- types-PyYAML - PyYAML type stubs

### Environment Variables

```bash
# Database Configuration
ANR_DB_PATH=hn_state.db              # SQLite database file

# Hacker News API
ANR_HN_STORIES_COUNT=100             # Stories to fetch per run
ANR_HN_TIMEOUT=30                    # Request timeout (seconds)

# Agent Thresholds (optional, use defaults if unsure)
ANR_NDD_AMBIGUITY_THRESHOLD=0.78     # Duplicate detection sensitivity
ANR_EPM_MIN_CONFIDENCE=0.5           # Pattern matching confidence
ANR_FMA_MOMENTUM_DECAY=0.95          # Frequency decay factor
ANR_HOD_OVERRIDE_THRESHOLD=0.3       # Human override detection

# Logging Configuration
ANR_LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
ANR_LOG_FORMAT=json                  # json or text

# Application Settings
ANR_WORKERS=4                        # Concurrent worker threads
```

---

## Optional Tasks

These are non-blocking enhancements for future sprints:

### High Priority (30-45 min each)

- [ ] **Fix 2 smoke tests**
  - Location: `tests/test_smoke.py`
  - Issue: Mock setup needs adjustment
  - Impact: Improve test pass rate from 97.8% to 100%
  - Effort: 30 minutes

- [ ] **Add pre-commit hooks**
  - Create `.pre-commit-config.yaml`
  - Automate: black, ruff, mypy on commit
  - Impact: Prevent code quality regressions
  - Effort: 20 minutes

### Medium Priority (15-30 min each)

- [ ] **Migrate Pydantic config**
  - Replace deprecated `class Config` with `ConfigDict`
  - File: `agentic_news_reaper/config.py`
  - Impact: Remove deprecation warnings
  - Effort: 20 minutes

- [ ] **Update datetime usage**
  - Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`
  - Files: `hn_client.py`, test files
  - Impact: Use Python 3.11+ recommended approach
  - Effort: 15 minutes

- [ ] **Migrate ruff config**
  - Move `select`/`ignore` to `[tool.ruff.lint]`
  - File: `pyproject.toml`
  - Impact: Comply with ruff 0.1+ format
  - Effort: 5 minutes

### Lower Priority (45 min - 2 hours each)

- [ ] **Add GitHub Actions CI/CD**
  - Create `.github/workflows/ci.yml`
  - Automate testing on push/PR
  - Impact: Continuous integration
  - Effort: 45 minutes

- [ ] **Expand documentation**
  - Add API examples and usage docs
  - Create architecture diagrams
  - Add agent interaction guide
  - Impact: Better developer onboarding
  - Effort: 1-2 hours

- [ ] **Performance optimization**
  - Profile HN client response times
  - Optimize pattern matching algorithm
  - Add database query optimization
  - Impact: Faster pipeline execution
  - Effort: 2-3 hours

---

## Troubleshooting

### "Command not found" or "No module named X"

**Solution**: Always use `uv run` prefix
```bash
uv run pytest tests/    # ✅ Correct
pytest tests/           # ❌ Wrong (uses system pytest)
```

### ImportError: missing package dependencies

**Solution**: Reinstall dependencies
```bash
uv pip install -e ".[dev]" --force-reinstall
```

### Virtual environment issues or strange errors

**Solution**: Recreate environment from scratch
```bash
rm -rf .venv
uv sync --dev
uv run pytest tests/ -v
```

### Access venv directly without `uv run`

**Solution**: Activate the virtual environment
```bash
source .venv/bin/activate
mypy agentic_news_reaper
pytest tests/ -v
deactivate
```

### Type checking fails after code changes

**Solution**: Reinstall with type stubs
```bash
uv pip install -e ".[dev]" --force-reinstall
uv run mypy agentic_news_reaper
```

### Database locked error

**Solution**: Remove old database and reinitialize
```bash
rm hn_state.db
uv run agentic-news-reaper init
```

### Tests fail with async errors

**Solution**: Ensure pytest-asyncio is installed
```bash
uv pip install pytest-asyncio
uv run pytest tests/ -v
```

---

## Code Quality Tips

### Use Type Hints Everywhere
```python
def process_story(story_id: int) -> StoryResult | None:
    """Process a single story and return result or None."""
    pass
```

### Keep Code DRY
Extract common patterns into utility functions or helper modules.

### Use Structured Logging
```python
import structlog
log = structlog.get_logger()
log.info("processing", story_id=123, count=5)
```

### Write Async Code Correctly
```python
async def fetch_stories(count: int) -> list[Story]:
    client = HackerNewsClient()
    return await client.get_top_stories(count)
```

### Document Complex Logic
```python
def calculate_confidence(signals: dict[str, float]) -> float:
    """Calculate pattern confidence using weighted average.
    
    Args:
        signals: Dict of signal_name -> score (0-1)
    
    Returns:
        Weighted confidence score (0-1)
    """
    pass
```

---

## Development Workflow

### Making Changes

1. Create feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes and run tests
   ```bash
   uv run pytest tests/ -v
   ```

3. Format and lint
   ```bash
   uv run black agentic_news_reaper tests
   uv run ruff check --fix agentic_news_reaper tests
   ```

4. Type check
   ```bash
   uv run mypy agentic_news_reaper
   ```

5. Commit
   ```bash
   git add .
   git commit -m "feat: Add my feature"
   ```

6. Push and create PR
   ```bash
   git push origin feature/my-feature
   ```

---

## Resources

- **[uv Documentation](https://docs.astral.sh/uv/)** - Package manager & venv
- **[Click Documentation](https://click.palletsprojects.com/)** - CLI framework
- **[Pydantic Documentation](https://docs.pydantic.dev/)** - Data validation
- **[pytest Documentation](https://docs.pytest.org/)** - Testing framework
- **[mypy Documentation](https://www.mypy-lang.org/)** - Type checking
- **[Hacker News API](https://github.com/HackerNews/API)** - HN API reference

---

## Getting Help

1. Check existing tests in `tests/` for usage examples
2. Review docstrings in source code modules
3. Enable debug logging: `ANR_LOG_LEVEL=DEBUG`
4. Check `README.md` for project overview
5. Review `CONTRIBUTING.md` before contributing
6. See `REVIEW_AND_IMPROVEMENTS.md` for technical deep-dive

---

## Next Steps

1. **Verify Setup**: Run `uv run pytest tests/ -v`
2. **Explore Code**: Review `agentic_news_reaper/` directory
3. **Try CLI**: Run commands in [CLI Reference](#cli-reference)
4. **Read Documentation**: See `README.md` and `CONTRIBUTING.md`
5. **Check Tasks**: Review [Optional Tasks](#optional-tasks) for next work items

---

For contribution guidelines, see: `CONTRIBUTING.md`  
For project overview, see: `README.md`  
For technical deep-dive, see: `REVIEW_AND_IMPROVEMENTS.md`
