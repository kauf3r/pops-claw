# External Integrations

**Analysis Date:** 2026-01-18

## APIs & External Services

### AI Services

**Anthropic Claude API (Required):**
- Purpose: Core AI processing for all analysis and content generation
- SDK: `@anthropic-ai/sdk` ^0.57.0
- Client: `src/core/claude.js` (ClaudeService class)
- Auth: `ANTHROPIC_API_KEY` environment variable
- Capabilities:
  - Text analysis and chat (`messages.create`)
  - Vision processing for screenshots
  - JSON-structured responses

**Usage Patterns:**
```javascript
// src/core/claude.js
const response = await this.client.messages.create({
  model: this.config.model,
  max_tokens: this.config.maxTokens,
  temperature: options.temperature,
  messages: [{ role: 'user', content: message }]
});
```

### Land Investing Services (Optional)

**Land Insights:**
- Purpose: Market data and property research
- Config: `config/index.js` -> `apis.landInsights`
- Auth: `LAND_INSIGHTS_API_KEY`
- Status: Optional, graceful degradation if unavailable
- Integration: Screenshot analysis via Claude Vision

**Pebble CRM:**
- Purpose: Customer relationship management for leads
- Config: `config/index.js` -> `apis.pebbleCRM`
- Auth: `PEBBLE_CRM_API_KEY`
- Status: Optional

**RocketMail / RocketPrint:**
- Purpose: Direct mail campaign management
- Config: `config/index.js` -> `apis.rocketMail`
- Auth: `ROCKETMAIL_API_KEY`
- Status: Optional

**AnswerForce:**
- Purpose: Call answering service integration
- Config: `src/pipeline/config/pipeline-config.js` -> `answerForce`
- Auth: `ANSWERFORCE_API_KEY`
- Status: Optional, pipeline-specific

### UAS/GIS Services (Optional)

**Pix4D:**
- Purpose: Photogrammetry and UAS data processing
- Config: `config/index.js` -> `apis.pix4d`
- Auth: `PIX4D_API_KEY`
- Status: Optional

**ArcGIS:**
- Purpose: Geographic information system integration
- Config: `config/index.js` -> `apis.arcgis`
- Auth: `ARCGIS_API_KEY`
- Status: Optional

## Data Storage

### Databases

**SQLite (Pipeline):**
- Type: Embedded relational database
- File: `src/pipeline/data/pipeline.db`
- Client: `sqlite3` ^5.1.6
- ORM: None (direct SQL queries)
- Implementation: `src/pipeline/data/pipeline-database.js`

**Schema Tables:**
- `markets` - Analyzed investment markets
- `properties` - Property data for campaigns
- `campaigns` - Mail campaign tracking
- `campaign_properties` - Many-to-many relationship
- `leads` - Campaign response tracking
- `deals` - Transaction management
- `kpi_snapshots` - Performance metrics
- `data_pulls` - Land Insights export tracking
- `system_log` - Audit trail

**PostgreSQL (Future):**
- Planned for Phase 4 production scaling
- Connection config ready in `pipeline-config.js`
- Not currently implemented

### File Storage

**Local Filesystem:**
- Screenshots: `src/pipeline/data/screenshots/`
- Exports: `src/pipeline/data/exports/`
- Templates: `src/pipeline/data/templates/`
- Backups: `src/pipeline/data/backups/`

**No Cloud Storage:**
- All files stored locally
- No S3, GCS, or other cloud storage integration

### Caching

**None implemented:**
- No Redis or Memcached
- No response caching for Claude API
- Database queries not cached

## Authentication & Identity

**No Auth Provider:**
- Single-user local application
- No user authentication system
- API keys stored in environment variables

**API Key Management:**
- All keys in `.env` file (not committed)
- Validated at startup via `validateConfig()`
- Format validation for Anthropic key (`sk-ant-` prefix)

## External System Integrations

### RangeOS VPS

**Purpose:** UAS test range operations data (weather, TFRs, NOTAMs, bookings)

**Implementation:** `src/integrations/rangeos-vps.js`

**Connection Methods:**
1. SSH (primary) - Direct command execution on VPS
2. Webhook (fallback) - REST API endpoints
3. Mock (development) - Fallback mock data

**Configuration:**
```bash
RANGEOS_VPS_HOST=165.22.139.214
RANGEOS_VPS_USER=officernd
RANGEOS_SSH_KEY=/path/to/key
RANGEOS_WEBHOOK_URL=https://...
```

**Commands:**
- `wx` - Weather conditions
- `tfr` - Temporary Flight Restrictions
- `notam` - NOTAMs
- `bookings` - Facility bookings

**Usage:**
```javascript
// src/integrations/rangeos-vps.js
const vps = new RangeOSVPSService();
const briefing = await vps.getDailyBriefing();
```

### Beads Issue Tracking

**Purpose:** AI-native issue tracking (Git-synced)

**Implementation:** `src/integrations/beads.js`

**Connection Method:** CLI wrapper around `bd` command

**Features:**
- `ready()` - Get unblocked issues
- `list()` - List all issues with filters
- `show(id)` - Get issue details
- `create()` - Create new issue
- `update()` - Update issue status
- `close()` - Close issue
- `addDependency()` - Manage dependencies

**Usage:**
```javascript
// src/integrations/beads.js
const beads = new BeadsService();
const readyIssues = await beads.ready();
const stats = await beads.getStats();
```

### Browser Automation (Playwright)

**Purpose:** Web scraping and automated data collection

**Implementation:** `src/browser/automation.js`

**Capabilities:**
- County assessor website scraping
- Property listing screenshot capture
- Public records request form submission
- Auction site monitoring

**Configuration:**
- Headless mode: true (default)
- User agent: Chrome 120 on macOS
- Viewport: 1920x1080

**Usage:**
```javascript
// src/browser/automation.js
const browser = new BrowserAutomation();
await browser.init({ headless: true });
await browser.navigateTo('https://county-assessor.example.com');
const data = await browser.scrapeCountyData(parcelId, countyUrl);
await browser.close();
```

## Monitoring & Observability

### Error Tracking

**None configured:**
- No Sentry, Bugsnag, or similar
- Errors logged to console/stdout

### Logging

**Main Application:**
- Custom logger: `src/utils/logger.js`
- Levels: error, warn, info, debug
- Output: Console with timestamps
- Format: `[timestamp] LEVEL: message {meta}`

**Pipeline Module:**
- Logger: Winston ^3.11.0
- Configurable log level via `PIPELINE_LOG_LEVEL`

### Health Checks

**Claude Service:**
```javascript
// src/core/claude.js
await claudeService.checkHealth(); // Returns boolean
```

**Pipeline Database:**
```javascript
// src/pipeline/data/pipeline-database.js
await database.checkConnection(); // Returns boolean
```

**RangeOS VPS:**
```javascript
// src/integrations/rangeos-vps.js
await vps.isConnected(); // Returns boolean
```

## CI/CD & Deployment

### Hosting

**Development:** Local machine or VPS
**Production:** VPS (Digital Ocean droplet)
- Host: 165.22.139.214 (RangeOS VPS)

### CI Pipeline

**None configured:**
- No GitHub Actions, CircleCI, or similar
- Manual deployment via Git

### Git Hooks

**Beads Integration:**
- Configured via `scripts/vps-setup.sh`
- Syncs issue tracking on commits

## Environment Configuration

### Required Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API authentication | Yes |

### Optional Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_MODEL` | Model for text analysis | claude-sonnet-4-5-20250929 |
| `CLAUDE_VISION_MODEL` | Model for vision tasks | claude-sonnet-4-5-20250929 |
| `CLAUDE_MAX_TOKENS` | Max response tokens | 4000 |
| `CLAUDE_TEMPERATURE` | Response creativity | 0.7 |
| `NODE_ENV` | Environment mode | development |
| `LOG_LEVEL` | Logging verbosity | info |
| `PIPELINE_PORT` | Web dashboard port | 3001 |

### Secrets Management

**Storage:** Local `.env` file
**Security:** File not committed (in `.gitignore`)
**Rotation:** Manual, no automated rotation

## Webhooks & Callbacks

### Incoming Webhooks

**None configured:**
- No external services push data to application

### Outgoing Webhooks

**None configured:**
- Application does not push to external webhook endpoints

## Integration Status Summary

| Integration | Status | Required |
|-------------|--------|----------|
| Anthropic Claude API | Active | Yes |
| Land Insights | Optional | No |
| Pebble CRM | Optional | No |
| RocketMail | Optional | No |
| Pix4D | Optional | No |
| ArcGIS | Optional | No |
| RangeOS VPS | Active (SSH/Mock) | No |
| Beads CLI | Active | No |
| Playwright | Optional | No |
| SQLite | Active | Pipeline only |

---

*Integration audit: 2026-01-18*
