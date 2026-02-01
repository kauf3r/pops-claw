# Technology Stack

**Analysis Date:** 2026-01-18

## Languages

**Primary:**
- JavaScript (ES Modules) - All application code

**Secondary:**
- SQL (SQLite) - Pipeline database queries
- Markdown - Documentation and LLM context files

## Runtime

**Environment:**
- Node.js 18.x+ (required by pipeline module)
- Runtime: V8 via Node.js

**Package Manager:**
- npm 10.x+
- Lockfile: `package-lock.json` present

**Module System:**
- ES Modules (`"type": "module"` in `package.json`)
- All imports use `import`/`export` syntax
- File extensions required in imports (`.js`)

## Frameworks

**Core:**
- None (vanilla Node.js application)
- Custom service-oriented architecture

**AI Services:**
- `@anthropic-ai/sdk` ^0.57.0 - Claude API client for all AI interactions

**Testing:**
- No formal test framework installed
- Manual test files: `test-config.js`, `test-core.js`, `test-startup.js`, `test-integration.js`

**Build/Dev:**
- `node --watch` for development mode (native Node.js watch)
- No build step required (native ESM)

## Key Dependencies

### Main Application (`package.json`)

**Critical:**
- `@anthropic-ai/sdk` ^0.57.0 - Claude AI API client (required for all AI functionality)
- `dotenv` ^17.2.1 - Environment variable management

**Utility:**
- `csv-parse` ^6.1.0 - CSV parsing for data imports

### Pipeline Module (`src/pipeline/package.json`)

**Critical:**
- `@anthropic-ai/sdk` ^0.57.0 - Claude Vision API for screenshot analysis
- `sqlite3` ^5.1.6 - Local database for pipeline data
- `dotenv` ^16.4.5 - Environment configuration

**Web Server:**
- `express` ^4.18.2 - HTTP server for web dashboard
- `cors` ^2.8.5 - Cross-origin resource sharing
- `multer` ^1.4.5-lts.1 - File upload handling

**Utility:**
- `axios` ^1.6.0 - HTTP client for API calls
- `winston` ^3.11.0 - Advanced logging
- `csv-parse` ^5.5.0 - CSV parsing
- `glob` ^11.0.3 - File pattern matching
- `node-cron` ^3.0.3 - Scheduled task execution

**Development:**
- `nodemon` ^3.0.1 - Auto-restart during development

### Optional (Browser Automation)
- `playwright` - Browser automation (not in package.json, requires separate install)

## Configuration

**Environment Variables (Required):**
- `ANTHROPIC_API_KEY` - Claude API authentication (required)

**Environment Variables (Optional):**
```bash
# Claude Configuration
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_VISION_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7

# Application Settings
NODE_ENV=development
LOG_LEVEL=info

# Optional API Integrations
LAND_INSIGHTS_API_KEY=
PEBBLE_CRM_API_KEY=
ROCKETMAIL_API_KEY=
PIX4D_API_KEY=
ARCGIS_API_KEY=

# RangeOS VPS Integration
RANGEOS_VPS_HOST=165.22.139.214
RANGEOS_VPS_USER=officernd
RANGEOS_SSH_KEY=
RANGEOS_WEBHOOK_URL=

# Pipeline-Specific
PIPELINE_DB_TYPE=sqlite
PIPELINE_DB_PATH=src/pipeline/data/pipeline.db
PIPELINE_PORT=3001
```

**Configuration Files:**
- `config/index.js` - Central configuration with validation
- `src/pipeline/config/pipeline-config.js` - Pipeline-specific configuration
- `.env` - Environment variables (not committed)
- `.env.example` - Environment template

**Validation:**
- `validateConfig()` in `config/index.js` runs at startup
- Validates API key format (`sk-ant-` prefix check)
- Logs enabled/disabled optional APIs

## File Locations

**Source Code:**
- `src/index.js` - Main application entry point
- `src/core/claude.js` - Core Claude AI service
- `src/land/` - Land investing analysis module
- `src/uas/` - UAS data processing module
- `src/browser/` - Playwright browser automation
- `src/integrations/` - External service wrappers
- `src/services/` - Application services
- `src/context/` - LLM context management
- `src/pipeline/` - Self-contained pipeline dashboard

**Configuration:**
- `config/index.js` - Main app config
- `src/pipeline/config/pipeline-config.js` - Pipeline config

**Data Storage:**
- `src/pipeline/data/pipeline.db` - SQLite database
- `src/pipeline/data/screenshots/` - Uploaded screenshots
- `src/pipeline/data/exports/` - Generated exports

## CLI Entry Points

**Main Application:**
```bash
npm start                    # Start interactive CLI
npm run dev                  # Development with auto-reload
npm run today                # Display daily task summary
npm run briefing             # RangeOS daily briefing
```

**Pipeline Module:**
```bash
cd src/pipeline && npm start              # Standalone pipeline
node src/pipeline/pipeline-index.js --interactive
node src/pipeline/pipeline-index.js --status
node src/pipeline/pipeline-index.js --health
```

**CLI Binaries (defined in package.json):**
- `rangeos` / `rangeos-cli` -> `src/cli/rangeos-cli.js`

## Platform Requirements

**Development:**
- macOS, Linux, or Windows with WSL
- Node.js 18.x or higher
- npm 10.x or higher
- Git for version control
- Beads CLI for issue tracking (`bd`)
- Optional: Playwright browsers for automation

**Production (VPS):**
- Ubuntu/Debian Linux
- Node.js 20.x+
- SSH access for RangeOS integration
- SQLite (no external database required)

## Default Claude Models

**Text Analysis:**
- Model: `claude-sonnet-4-5-20250929`
- Max tokens: 4000
- Temperature: 0.7 (general), 0.3 (analysis)

**Vision Processing:**
- Model: `claude-sonnet-4-5-20250929`
- Used for Land Insights screenshot analysis
- Max tokens: 4000

---

*Stack analysis: 2026-01-18*
