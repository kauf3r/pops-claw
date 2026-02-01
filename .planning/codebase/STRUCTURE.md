# Codebase Structure

**Analysis Date:** 2026-01-18

## Directory Layout

```
claude-life-os/
├── src/                        # Application source code
│   ├── index.js               # Main entry point
│   ├── core/                  # Core AI services
│   ├── land/                  # Land investing domain
│   ├── uas/                   # UAS/drone domain
│   ├── pipeline/              # Self-contained pipeline (standalone)
│   ├── browser/               # Playwright browser automation
│   ├── integrations/          # External system wrappers
│   ├── context/               # LLM context management
│   ├── services/              # Cross-cutting services
│   ├── cli/                   # CLI entry points
│   └── utils/                 # Shared utilities
├── config/                    # Configuration management
├── LLM-context/               # AI context files (Obsidian-compatible)
├── .beads/                    # Beads issue tracking data
├── .planning/                 # GSD planning documents
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── tests/                     # Test directory
├── plans/                     # Planning documents
├── openspec/                  # OpenSpec change proposals
├── KNOWLEDGE_BASE/            # Knowledge and research
├── CONTENT_LIBRARY/           # Marketing content
├── LAND_INVESTING/            # Land investing resources
├── UAS_OPERATIONS/            # UAS operations resources
└── PROJECT_NOTES/             # Project notes and PRDs
```

## Directory Purposes

**src/core/**
- Purpose: Centralized Claude AI service
- Contains: `claude.js` - all AI interactions
- Key files: `src/core/claude.js`

**src/land/**
- Purpose: Land investing analysis and workflows
- Contains: Analyzers, scoring algorithms, workflow automation
- Key files:
  - `src/land/analyzer.js` - property analysis with scoring
  - `src/land/workflows.js` - acquisition and lead workflows

**src/uas/**
- Purpose: UAS (drone) data processing
- Contains: Survey processors, payload-specific analysis
- Key files:
  - `src/uas/processor.js` - LiDAR, RGB, Multispectral processing
  - `src/uas/integration.js` - UAS + land analysis integration

**src/pipeline/**
- Purpose: Self-contained land investing pipeline dashboard
- Contains: Complete standalone application with own dependencies
- Key files:
  - `src/pipeline/pipeline-index.js` - main entry point
  - `src/pipeline/core/market-selector.js` - market scoring (Andy's methodology)
  - `src/pipeline/services/claude-vision.js` - screenshot processing
  - `src/pipeline/data/pipeline-database.js` - SQLite persistence
  - `src/pipeline/dashboard/cli/market-cli.js` - interactive CLI
  - `src/pipeline/package.json` - independent dependencies

**src/browser/**
- Purpose: Playwright browser automation
- Contains: Web scraping, form submission, screenshot capture
- Key files:
  - `src/browser/automation.js` - BrowserAutomation class
  - `src/browser/land-integration.js` - land investing integrations
  - `src/browser/examples.js` - usage examples

**src/integrations/**
- Purpose: External system wrappers
- Contains: CLI wrappers, API clients
- Key files:
  - `src/integrations/beads.js` - Beads issue tracker wrapper
  - `src/integrations/rangeos-vps.js` - RangeOS VPS connection

**src/context/**
- Purpose: LLM context file management
- Contains: Loaders, session tracking, process notes
- Key files:
  - `src/context/loader.js` - ContextLoader class
  - `src/context/session-history.js` - SessionHistoryTracker
  - `src/context/process-notes.js` - ProcessNotesGenerator
  - `src/context/compaction.js` - Context compaction utilities
  - `src/context/index.js` - module exports

**src/services/**
- Purpose: Cross-cutting aggregation services
- Contains: TodayService for daily context
- Key files: `src/services/today.js`

**src/cli/**
- Purpose: CLI entry points
- Contains: RangeOS CLI wrapper
- Key files: `src/cli/rangeos-cli.js`

**src/utils/**
- Purpose: Shared utilities
- Contains: Logging
- Key files: `src/utils/logger.js`

**config/**
- Purpose: Configuration management
- Contains: Environment loading, validation
- Key files: `config/index.js`

**LLM-context/**
- Purpose: AI context files (Obsidian-compatible markdown)
- Contains: Domain knowledge, session files
- Key files:
  - `LLM-context/_index.md` - master MOC
  - `LLM-context/session/today.md` - daily context
  - `LLM-context/landos/` - land investing context
  - `LLM-context/rangeos/` - UAS operations context

## Key File Locations

**Entry Points:**
- `src/index.js`: Main application entry
- `src/pipeline/pipeline-index.js`: Pipeline standalone entry
- `src/cli/rangeos-cli.js`: RangeOS CLI entry

**Configuration:**
- `config/index.js`: Central configuration
- `src/pipeline/config/pipeline-config.js`: Pipeline config
- `.env`: Environment variables (not committed)
- `.env.example`: Environment template

**Core Logic:**
- `src/core/claude.js`: All Claude AI interactions
- `src/land/analyzer.js`: Property analysis and scoring
- `src/pipeline/core/market-selector.js`: Market analysis with Andy's methodology

**Testing:**
- `test-config.js`: Configuration tests
- `test-core.js`: Claude service tests
- `test-playwright.js`: Browser automation tests
- `test-integration.js`: End-to-end tests
- `test-startup.js`: Application startup tests

**Documentation:**
- `CLAUDE.md`: Project documentation for AI assistants
- `README.md`: User documentation
- `ARCHITECTURE.md`: Architecture overview (root)

## Naming Conventions

**Files:**
- Lowercase with hyphens: `market-selector.js`, `claude-vision.js`
- Index files: `index.js` for module exports
- Test files: `test-*.js` in root, or colocated with `*.test.js`
- Config files: `*-config.js`

**Directories:**
- Lowercase with hyphens: `src/browser/`, `LLM-context/`
- Domain directories: singular (`src/land/`, not `src/lands/`)
- Pipeline subdirectories: `core/`, `services/`, `dashboard/`, `data/`

**Classes:**
- PascalCase: `ClaudeService`, `MarketSelector`, `BrowserAutomation`
- Suffix patterns: `*Service`, `*Analyzer`, `*Processor`, `*Tracker`

**Functions:**
- camelCase: `analyzeProperty`, `processUASData`, `generateMarketing`
- Verb prefixes: `get*`, `set*`, `calculate*`, `generate*`, `parse*`

**Variables:**
- camelCase: `propertyData`, `analysisResults`
- Constants: SCREAMING_SNAKE_CASE in modules, but mostly camelCase

## Where to Add New Code

**New Feature:**
- Primary code: Create new module in `src/<domain>/`
- Tests: Create `test-<feature>.js` in root or colocate
- If pipeline feature: Add to `src/pipeline/core/` or `src/pipeline/services/`

**New Component/Module:**
- Domain-specific: `src/<domain>/<component>.js`
- Shared service: `src/services/<service>.js`
- Integration: `src/integrations/<integration>.js`
- Export from domain index if applicable

**New CLI Command:**
- Add handler in `src/index.js` `handleCommand()` method
- Or create new CLI in `src/cli/<command>-cli.js`
- Register in `package.json` bin if standalone

**Utilities:**
- Shared helpers: `src/utils/<utility>.js`
- Pipeline utilities: `src/pipeline/utils/<utility>.js`

**Context Files:**
- Domain context: `LLM-context/<domain>/<topic>.md`
- Session files: `LLM-context/session/<file>.md`
- Include YAML frontmatter with domain, type, tags

**Configuration:**
- Add to `config/index.js` config object
- Add validation in `validateConfig()` if required
- Document in `.env.example`

## Special Directories

**.beads/**
- Purpose: Beads issue tracking data
- Generated: Yes (by bd CLI)
- Committed: Yes (via git hooks)

**.planning/**
- Purpose: GSD planning and codebase documents
- Generated: Partially (by GSD commands)
- Committed: Yes

**LLM-context/**
- Purpose: AI context files for Claude sessions
- Generated: Partially (`today.md` generated)
- Committed: Yes (except `today.md` may vary)

**src/pipeline/data/**
- Purpose: Pipeline database and exports
- Generated: Yes (SQLite database, exports)
- Committed: Partially (templates yes, database no)

**src/pipeline/node_modules/**
- Purpose: Pipeline-specific dependencies
- Generated: Yes (npm install)
- Committed: No

**node_modules/**
- Purpose: Project dependencies
- Generated: Yes (npm install)
- Committed: No

**output/**
- Purpose: Generated output files
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-01-18*
