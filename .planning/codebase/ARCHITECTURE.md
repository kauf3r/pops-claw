# Architecture

**Analysis Date:** 2026-01-18

## Pattern Overview

**Overall:** Service-Oriented Modular Architecture

**Key Characteristics:**
- AI-first design with Claude API as the central intelligence layer
- Domain-driven modules (land investing, UAS operations, pipeline)
- Optional module loading with graceful degradation
- Layered services with clear separation of concerns
- ESM modules with async/await throughout

## Layers

**Application Layer:**
- Purpose: Main orchestration and entry point
- Location: `src/index.js`
- Contains: `ClaudeLifeOS` class, interactive CLI, command routing
- Depends on: Core services, optional pipeline module
- Used by: End users via CLI or programmatic import

**Core Services Layer:**
- Purpose: Centralized AI interactions and shared functionality
- Location: `src/core/`
- Contains: `ClaudeService` class with domain-specific prompts
- Depends on: External Anthropic SDK, configuration
- Used by: All domain modules (land, UAS, pipeline)

**Domain Modules Layer:**
- Purpose: Domain-specific business logic
- Location: `src/land/`, `src/uas/`, `src/pipeline/`
- Contains: Analyzers, workflows, processors, scoring algorithms
- Depends on: Core services, utilities
- Used by: Application layer, CLI commands

**Integration Layer:**
- Purpose: External system connections
- Location: `src/integrations/`, `src/browser/`
- Contains: BeadsService, RangeOSVPSService, BrowserAutomation
- Depends on: External CLIs (bd), SSH, HTTP
- Used by: Services layer, application layer

**Context Layer:**
- Purpose: LLM context management and session continuity
- Location: `src/context/`
- Contains: ContextLoader, SessionHistoryTracker, ProcessNotesGenerator
- Depends on: File system (LLM-context directory)
- Used by: TodayService, slash commands

**Services Layer:**
- Purpose: Cross-cutting aggregation services
- Location: `src/services/`
- Contains: TodayService (aggregates Beads, pipeline, RangeOS)
- Depends on: Integration layer, context layer
- Used by: Application layer, CLI commands

**Configuration Layer:**
- Purpose: Environment and settings management
- Location: `config/index.js`
- Contains: Config object, validateConfig function
- Depends on: dotenv, environment variables
- Used by: All layers

**Utilities Layer:**
- Purpose: Shared utilities
- Location: `src/utils/`
- Contains: Logger class
- Depends on: Configuration
- Used by: All layers

## Data Flow

**Land Investment Analysis:**

1. User invokes `processLandInvestment(landData)` via CLI or API
2. `ClaudeLifeOS` delegates to `ClaudeService.analyzeLandData()`
3. `ClaudeService` builds domain-specific prompt with Andy's methodology
4. Anthropic API returns structured JSON analysis
5. Response parsed, scores calculated, flags identified
6. Enhanced analysis returned to caller

**Pipeline Market Analysis:**

1. User drops screenshots via pipeline CLI
2. `MarketSelector.analyzeScreenshots()` validates files
3. `ClaudeVisionService` processes images with Claude Vision API
4. `MarketSelector` applies scoring algorithm (Andy's methodology)
5. Results stored in SQLite database via `PipelineDatabase`
6. Market queue updated with priorities

**Daily Context Aggregation:**

1. User runs `today` command
2. `TodayService` aggregates data in parallel:
   - `BeadsService.ready()` - fetch ready issues
   - `RangeOSVPSService.getDailyBriefing()` - weather, TFRs, bookings
   - `SessionHistoryTracker.getContinuitySummary()` - session continuity
3. Data formatted into markdown
4. Optionally writes to `LLM-context/session/today.md`

**State Management:**
- No global state - each service instance manages own state
- Pipeline uses SQLite for persistence
- Session context via markdown files in LLM-context/
- Beads issues tracked externally via `.beads/` directory

## Key Abstractions

**ClaudeService:**
- Purpose: All AI interactions go through this service
- Examples: `src/core/claude.js`
- Pattern: Prompt engineering with JSON response parsing
- Methods: `chat()`, `analyzeLandData()`, `processUASData()`, `generateMarketingContent()`

**Domain Analyzers:**
- Purpose: Domain-specific analysis with scoring algorithms
- Examples: `src/land/analyzer.js`, `src/uas/processor.js`
- Pattern: Combine calculated metrics with AI analysis

**Integration Services:**
- Purpose: Wrap external systems with consistent interface
- Examples: `src/integrations/beads.js`, `src/integrations/rangeos-vps.js`
- Pattern: Exec wrapper with JSON parsing, fallback to text

**ContextLoader:**
- Purpose: Load and filter LLM context files
- Examples: `src/context/loader.js`
- Pattern: Frontmatter parsing, domain/type filtering, caching

**Pipeline Components:**
- Purpose: Self-contained land investing pipeline
- Examples: `src/pipeline/core/market-selector.js`, `src/pipeline/services/claude-vision.js`
- Pattern: Dependency injection, SQLite persistence, scoring methodology

## Entry Points

**Main Application:**
- Location: `src/index.js`
- Triggers: `npm start`, `node src/index.js`
- Responsibilities: Initialize services, start interactive CLI, handle commands

**Pipeline Standalone:**
- Location: `src/pipeline/pipeline-index.js`
- Triggers: `cd src/pipeline && npm start`, `node src/pipeline/pipeline-index.js --interactive`
- Responsibilities: Independent pipeline operation, market analysis CLI

**RangeOS CLI:**
- Location: `src/cli/rangeos-cli.js`
- Triggers: `npm run rangeos`, `rangeos briefing`
- Responsibilities: RangeOS operations via VPS

**Configuration Entry:**
- Location: `config/index.js`
- Triggers: Imported at application startup
- Responsibilities: Load .env, validate API keys, export config object

## Error Handling

**Strategy:** Try-catch with structured logging and graceful degradation

**Patterns:**
- All async operations wrapped in try-catch
- Logger captures error message and metadata
- Optional modules (pipeline) loaded with try-catch fallback
- JSON parsing uses fallback to raw text analysis
- API failures return structured error objects

**Example:**
```javascript
try {
  const analysis = await this.claude.analyzeLandData(data);
  return analysis;
} catch (error) {
  logger.error('Analysis failed', { error: error.message });
  throw error;
}
```

## Cross-Cutting Concerns

**Logging:**
- Centralized Logger class in `src/utils/logger.js`
- Log levels: error, warn, info, debug
- Structured logging with timestamps and metadata
- Pipeline has separate PipelineLogger with component tagging

**Validation:**
- Config validation at startup via `validateConfig()`
- Survey data validation in UASProcessor
- Screenshot validation in MarketSelector
- Missing required fields throw descriptive errors

**Authentication:**
- API keys via environment variables
- `ANTHROPIC_API_KEY` required
- Optional API keys enable/disable features
- SSH key for RangeOS VPS connection

**Configuration:**
- Central `config` object exported from `config/index.js`
- Environment variables loaded via dotenv
- Pipeline has separate `pipeline-config.js`
- Model selection, max tokens, temperature configurable

---

*Architecture analysis: 2026-01-18*
