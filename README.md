# Deterministic Execution Engine – Multi‑Agent System for News Catchup  

---

## 1. Purpose & Scope  

The **Deterministic Execution Engine (DEE)** is a purpose‑built, fully‑automated workflow that extracts, analyses, and synthesizes daily Hacker News (HN) data into a repeatable, auditable execution plan.  

- **Determinism** – Every run produces the *same* set of actions, timestamps, and metadata when fed the same input data.  
- **Multi‑Agent Architecture** – Four specialized agents collaborate, each owning a distinct decision‑making domain.  
- **Persistence Layer** – All intermediate artefacts are stored in a lightweight **SQLite** database, providing instant queryability and version‑controlled state.  
- **Human‑In‑the‑Loop** – A single “Human Override” checkpoint guarantees that critical out‑of‑band decisions can be approved before execution.  

The DEE is intended for internal use by the **Founder‑Briefing** team, delivering a weekly executive‑level synthesis of HN signals that can be directly materialised into operational tasks (e.g., product feature gates, investor outreach, research topics).

---

## 2. System Overview  

```
+-------------------+       +-------------------+
|   Daily HN Crawler| ----> |   SQLite Memory   |
+-------------------+       +-------------------+
        |                               |
        v                               v
+-------------------+       +----------------------+
| Non‑Determinism   | ----> |  Agent Orchestration |
| Detector (NDD)    |       |   (Scheduler)        |
+-------------------+       +----------------------+
        |                               |
        v                               v
+-------------------+       +-------------------+
| Execution Pattern | ----> | Execution Pattern |
| Miner (EPM)       |       | Miner (EPM)       |
+-------------------+       +-------------------+
        |                               |
        v                               v
+-------------------+       +-------------------+
| Failure Mode      | ----> | Failure Mode      |
| Analyzer (FMA)    |       | Analyzer (FMA)    |
+-------------------+       +-------------------+
        |                               |
        v                               v
+-------------------+       +-------------------+
| Human Override    | <---- | Human Override    |
| Detector (HOD)    |       | Detector (HOD)    |
+-------------------+       +-------------------+
        |                               |
        v                               v
+-------------------+       +-----------------+
| Weekly Founder    | <---- |  SQLite Memory  |
| Brief Synthesizer |       +-----------------+
+-------------------+                
```

*The diagram illustrates the flow of data from raw HN posts to the final weekly synthesis, highlighting the central SQLite “memory” that persists every artefact.*

---

## 3. Agent Roles & Responsibilities  

| Agent | Core Function | Primary Input | Primary Output |
|-------|---------------|---------------|----------------|
| **Non‑Determinism Detector (NDD)** | Flags posts that have *multiple possible interpretations* (e.g., ambiguous titles, mixed sentiment). | Raw HN feed (JSON) | List of “Ambiguity Flags” with severity scores. |
| **Execution Pattern Miner (EPM)** | Extracts repeatable execution patterns (e.g., “post → comment → up‑vote cascade”) from HN threads. | HN posts + NDD flags | Pattern templates (JSON‑Schema) stored in memory. |
| **Failure Mode Analyzer (FMA)** | Predicts failure modes for each pattern (e.g., “low‑engagement”, “spam‑injection”). | Pattern templates + HN metadata | Failure‑risk scores & mitigation tactics. |
| **Human Override Detector (HOD)** | Identifies moments where human approval is mandatory (e.g., high‑risk financial decisions). | Pattern + Failure‑risk + business rules | Boolean “Require‑Human‑Approval” flag + justification notes. |
| **Weekly Founder Brief Synthesizer** | Collates all weekly signals into a concise executive brief. | All persisted artefacts | Structured brief (PDF/Markdown) delivered to founders. |

---

## 4. Daily Processing Flow  

1. **Fetch** – `daily_hacker_news_fetch()` pulls the top 100 HN stories, comments, and metadata via the official API.  
2. **Parse & Index** – Parsed items are stored in the SQLite **`hn_raw`** table.  
3. **Detect Non‑Determinism** – `NDD.run()` evaluates each story using a set of heuristics (title ambiguity, mixed sentiment, author reputation).  
4. **Mine Patterns** – `EPM.run()` matches each story against known pattern templates, producing **Pattern Instances** (`hn_patterns`).  
5. **Assess Failure Modes** – `FMA.run()` applies statistical and textual filters to each pattern, outputting risk scores.  
6. **Human‑Override Check** – `HOD.run()` reviews patterns whose risk exceeds a configurable threshold; if triggered, the system pauses and prompts the operator via a lightweight UI.  
7. **Persist** – All artefacts (raw posts, flags, patterns, risk scores) are written to the SQLite DB (`hn_state.db`).  

> **Note:** The daily cycle repeats every 24 h (UTC). The SQLite DB is the single source of truth; no external state is retained.

---

## 5. Agent Interaction Details  

### 5.1 Non‑Determinism Detector (NDD)  

- **Algorithm**:  
  1. Compute token entropy of the title.  
  2. Run sentiment analysis on first‑level comments.  
  3. Compare against a calibrated threshold (`θ = 0.78`).  
- **Output Format**:  
  ```json
  {
    "story_id": "32987456",
    "ambiguity_score": 0.84,
    "reason": "Mixed sentiment across comment body"
  }
  ```

### 5.2 Execution Pattern Miner (EPM)  

- **Pattern Templates**: Defined in `patterns.yaml` (e.g., `title_clickbait → upvote_burst`).  
- **Matching Logic**: A lightweight regex/phrase‑match engine operates on post titles, comment bodies, and vote deltas.  
- **Result Storage**: `patterns.db` table `patterns_instances` (columns: `pattern_id`, `story_id`, `timestamp`, `confidence`).  

### 5.3 Failure Mode Analyzer (FMA)  

- **Risk Model**:  
  - **Engagement Risk** = (low comment count) * weight₁  
  - **Spam Risk** = (high URL blacklist score) * weight₂  
  - **Sentiment Drift** = (sentiment polarity variance) * weight₃  
- **Mitigation Strategies**: Pre‑defined actions (e.g., “add to watch‑list”, “auto‑defer”).  

### 5.4 Human Override Detector (HOD)  

- **Decision Threshold**: Configurable per domain (e.g., 0.9 for financial‑related patterns).  
- **Trigger Output**:  
  ```json
  {
    "story_id": "32987456",
    "requires_override": true,
    "reason": "Potential market‑impact investment"
  }
  ```  
- **Operator Flow**: UI pops up; operator can “Accept”, “Reject”, or “Escalate”. Decision is logged back to SQLite (`override_log`).  

---

## 6. SQLite Memory Architecture  

| Table | Description | Key Columns |
|-------|------------|-------------|
| `hn_raw` | Raw scraped items | `story_id`, `title`, `url`, `timestamp` |
| `patterns_instances` | Executed patterns | `pattern_id`, `story_id`, `confidence` |
| `failure_modes` | Analyzed risks | `pattern_id`, `risk_score`, `mitigation` |
| `override_log` | Human‑override records | `story_id`, `override_decision`, `operator_id`, `timestamp` |
| `weekly_summary` | Aggregated weekly data | `week_start`, `summary_json` |

*All tables are indexed on `story_id` and `timestamp` for O(1) lookup.*

---

## 7. Weekly Founder Brief  

### 7.1 Output Format  

- **File**: `founder_brief_YYYY_W##.md`  
- **Sections**:  
  1. **Executive Summary** – High‑level sentiment trend.  
  2. **Key Signals** – Top‑5 patterns with highest confidence.  
  3. **Risk Dashboard** – Heat‑map of failure modes.  
  4. **Action Items** – Human‑approved overrides ready for execution.  

### 7.2 Automation Script  

```bash
python generate_brief.py \
  --db hn_state.db \
  --output ./reports/founder_brief_$(date +%Y_W%U).md \
  --template ./templates/brief_template.md
```

The script aggregates weekly rows, applies a simple templating engine (Jinja2), and posts the markdown to the internal knowledge base.

---

## 8. Implementation Checklist  

| Step | Action | Owner | Due |
|------|--------|-------|-----|
| 1 | Set up SQLite DB schema (migrations) | DevOps | Week 1 |
| 2 | Implement NDD heuristics (title, comment sentiment) | Data Science | Week 1 |
| 3 | Develop pattern template library | Engineering | Week 2 |
| 4 | Build EPM matcher & store results | Engineering | Week 2 |
| 5 | Deploy FMA risk scoring pipeline | Data Science | Week 3 |
| 6 | Create HOD UI (React modal) | Front‑end | Week 3 |
| 7 | Wire orchestrator (cron) to run daily pipeline | DevOps | Week 4 |
| 8 | Generate first weekly founder brief | PM | End of Week 4 |
| 9 | Conduct QA & sign‑off with Founder team | PM / Founder | Week 5 |

---

## 9. Benefits & KPIs  

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Pattern Accuracy** | ≥ 85 % of patterns correctly flagged | Post‑execution audit vs. manual review |
| **Override Frequency** | ≤ 5 % of daily patterns | Count of `override_log` entries / total patterns |
| **Brief Delivery Latency** | ≤ 2 h after week‑end | Timestamp diff (end of week → brief publish) |
| **System Uptime** | 99.5 % | Monitoring of cron jobs & DB health |
| **Founder Satisfaction** | ≥ 4.5/5 (post‑brief survey) | Quarterly survey |

---

## 10. Future Enhancements  

| Feature | Description | ETA |
|---------|-------------|-----|
| **Multi‑Modal Sentiment** | Incorporate image/video sentiment analysis for richer context. | Q2 2026 |
| **Dynamic Pattern Generation** | Auto‑generate new patterns from emergent HN vocabularies. | Q4 2026 |
| **Predictive Execution Scheduler** | Use reinforcement learning to pre‑schedule patterns based on historical ROI. | Q1 2027 |
| **Cross‑Domain Correlation** | Link HN signals to other data sources (e.g., Crunchbase, LinkedIn). | Q2 2027 |
| **Explainable AI Layer** | Provide natural‑language explanations for each pattern’s risk. | Q3 2027 |

---

## 11. Appendices  

### A. SQLite Schema (SQL)  

```sql
CREATE TABLE hn_raw (
    id INTEGER PRIMARY KEY,
    story_id TEXT UNIQUE,
    title TEXT,
    url TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patterns_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT,
    story_id TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE failure_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT,
    risk_score REAL,
    mitigation TEXT,
    FOREIGN KEY(pattern_id) REFERENCES patterns_instances(pattern_id)
);

CREATE TABLE override_log (
    story_id TEXT,
    decision TEXT,          -- 'accept' / 'reject' / 'escalate'
    operator_id TEXT,
    decision_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### B. Example Pattern Template (`patterns.yaml`)  

```yaml
- id: "clickbait_upvote"
  description: "Click‑bait title leading to up‑vote cascade"
  trigger_conditions:
    - title_contains: ["shocking", "you won't believe"]
    - comment_upvote_ratio > 0.6
  execution_template: "schedule_feature_launch('{{story_id}}')"
```

---

## 12. Quick Start Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Initialize database
agentic-news-reaper init

# View help
agentic-news-reaper --help

# Format code
black agentic_news_reaper tests

# Lint code
ruff check agentic_news_reaper tests

# Type check
mypy agentic_news_reaper

# Check coverage
pytest tests/ --cov=agentic_news_reaper
```

---

## 12. Closing Remarks  

The deterministic execution engine transforms the chaotic flow of Hacker News into a disciplined, repeatable workflow. By leveraging a multi‑agent approach, persistent SQLite storage, and explicit human‑override checkpoints, the system delivers:

- **Consistent, auditable execution plans**  
- **Rapid insight generation** for founders  
- **Scalable automation** without sacrificing human judgment
