# Coding Conventions

**Analysis Date:** 2026-01-18

## Naming Patterns

**Files:**
- kebab-case for filenames: `claude-vision.js`, `market-selector.js`, `pipeline-index.js`
- Suffix with module type: `-cli.js`, `-config.js`, `-database.js`
- Test files: `test-*.js` in root or `test-*.js` within module directories

**Functions:**
- camelCase for all functions: `analyzeProperty()`, `processUASData()`, `generateMarketing()`
- Async functions prefixed descriptively: `async loadFile()`, `async getStats()`
- Private methods prefixed with build/calculate/parse: `buildLandAnalysisPrompt()`, `calculateMetrics()`, `parseJSONResponse()`

**Variables:**
- camelCase for all variables: `screenshotPaths`, `marketData`, `analysisResults`
- Constants in UPPER_SNAKE_CASE: `DEFAULT_CONTEXT_DIR`, `PROJECT_ROOT`
- Boolean variables with is/has prefix: `isHealthy`, `hasExternalService`

**Classes:**
- PascalCase for class names: `ClaudeService`, `LandAnalyzer`, `BrowserAutomation`
- Service suffix for service classes: `ClaudeService`, `BeadsService`, `TodayService`
- Descriptive noun names: `ContextLoader`, `MarketSelector`, `CampaignEngine`

**Types/Constants:**
- Enum-like objects with PascalCase keys:
```javascript
export const Domain = {
  LANDOS: 'landos',
  RANGEOS: 'rangeos',
  UAS_SHARED: 'uas-shared'
};
```

## Code Style

**Formatting:**
- No explicit formatter configured (Prettier/ESLint not detected)
- 2-space indentation observed throughout codebase
- Single quotes for strings preferred
- Semicolons required at end of statements

**Linting:**
- No ESLint configuration detected
- No linting enforcement in CI/CD

**Line Length:**
- No explicit limit, but ~100-120 characters typical
- Long strings broken across lines with template literals

## Import Organization

**Order:**
1. Node.js built-ins: `import { exec } from 'child_process';`
2. External packages: `import { Anthropic } from '@anthropic-ai/sdk';`
3. Internal absolute imports: `import { config } from '../../config/index.js';`
4. Internal relative imports: `import { logger } from './utils/logger.js';`

**Path Aliases:**
- None configured - all imports use relative paths
- File extensions required (`.js`): `import { ClaudeService } from './core/claude.js';`

**Module System:**
- ES Modules exclusively (`"type": "module"` in package.json)
- Named exports preferred: `export { ClaudeLifeOS };`
- Default exports used for main class: `export default BrowserAutomation;`

## Error Handling

**Patterns:**
- Try-catch in all async functions that call external services
- Error re-throwing with context: `throw new Error(\`Claude API error: ${error.message}\`);`
- Graceful fallbacks for optional features:
```javascript
try {
  const pipelineModule = await import('./pipeline/pipeline-index.js');
  LandInvestingPipeline = pipelineModule.LandInvestingPipeline;
} catch (error) {
  logger.debug('Pipeline Dashboard not available', { error: error.message });
}
```

**Error Logging:**
- Always log errors before throwing: `logger.error('Land analysis failed', { error: error.message });`
- Include contextual metadata in error logs
- Use structured error objects with `{ error: error.message }`

**Validation:**
- Configuration validated at startup: `validateConfig()`
- Throw descriptive errors for missing required config:
```javascript
if (!config.claude.apiKey) {
  throw new Error(
    'ANTHROPIC_API_KEY is required. Please set it in your .env file.\n' +
    'Get your API key from: https://console.anthropic.com/'
  );
}
```

## Logging

**Framework:** Custom Logger class (`src/utils/logger.js`)

**Log Levels:**
- `error`: Critical failures requiring attention
- `warn`: Non-critical issues (JSON parsing fallback, optional module unavailable)
- `info`: Normal operations (initialization, analysis complete)
- `debug`: Detailed diagnostics (request details, token counts)

**Patterns:**
```javascript
// Initialization
logger.info('ClaudeService initialized', { model, visionModel, maxTokens });

// Operations
logger.info('Land analysis request initiated', { analysisType, propertyId });

// Success
logger.info('Land analysis completed', { propertyId, investmentScore, riskScore });

// Errors
logger.error('Land analysis failed', { error: error.message });

// Warnings
logger.warn('JSON parsing failed, returning text analysis', { error: parseError.message });
```

**Structured Logging:**
- Always include relevant IDs: `propertyId`, `surveyId`, `marketId`
- Include metric data in completion logs: `{ inputTokens, outputTokens }`

## Comments

**When to Comment:**
- JSDoc blocks on all public methods
- Inline comments for complex business logic
- TODO comments with category: `// TODO [Error Handling]: Add retry logic`

**JSDoc/TSDoc:**
```javascript
/**
 * Analyze land investment data using Andy's 20+ year methodology
 * @param {Object} data - Property and market data
 * @param {string} analysisType - Type of analysis (comprehensive, quick, comparative)
 * @returns {Promise<Object>} - Structured land analysis results
 */
async analyzeLandData(data, analysisType = 'comprehensive') {
```

**TODO Format:**
```javascript
// TODO [Category]: Description of work needed
// TODO [Error Handling]: Add specific error recovery strategies
// TODO [Validation]: Validate landData structure before processing
// TODO [Performance]: Cache analysis results
```

## Function Design

**Size:**
- Methods typically 20-50 lines
- Larger methods broken into private helpers

**Parameters:**
- Options object pattern for multiple optional params:
```javascript
async init(options = {}) {
  const { headless = true, slowMo = 0 } = options;
}
```

**Return Values:**
- Async methods return objects with structured data
- Include metadata in returns: `{ ...analysis, parsedSuccessfully: false }`
- Chainable methods return `this`: `return this;`

**Default Values:**
- Use parameter defaults: `analysisType = 'comprehensive'`
- Use destructuring defaults: `const { timeout = 30000 } = options;`

## Module Design

**Exports:**
- Named exports for classes and functions
- Default export for main module class
- Re-export aggregation in `index.js`:
```javascript
export { ContextLoader, Domain, ContextType } from './loader.js';
```

**Barrel Files:**
- `index.js` files for module aggregation in `src/context/`, `src/pipeline/models/`
- Clean public API exposure

**Class Structure:**
```javascript
export class ServiceName {
  constructor(options = {}) {
    // Initialize configuration
    // Initialize dependencies
    // Initialize state
  }

  // Public methods first
  async publicMethod() { }

  // Private/helper methods last (prefixed or marked @private)
  buildPrompt() { }
}
```

## Async/Await Patterns

**All IO operations are async:**
```javascript
// Database operations
await this.database.initialize();

// API calls
const response = await this.client.messages.create({...});

// File operations
const content = await readFile(fullPath, 'utf-8');
```

**Parallel execution with Promise.all:**
```javascript
const [beadsIssues, pipelineStatus, rangeOSBriefing] = await Promise.all([
  this.getBeadsReady(),
  this.getPipelineStatus(),
  this.getRangeOSBriefing()
]);
```

## Configuration Pattern

**Centralized config with validation:**
- All config in `config/index.js`
- Environment variables loaded via dotenv
- Type coercion for numbers/booleans:
```javascript
maxTokens: parseInt(process.env.CLAUDE_MAX_TOKENS || '4000', 10),
temperature: parseFloat(process.env.CLAUDE_TEMPERATURE || '0.7')
```

**Dependency injection for services:**
```javascript
constructor(options = {}) {
  this.config = options.config || config.claude;
  this.claudeService = options.claudeService; // Optional external service
}
```

---

*Convention analysis: 2026-01-18*
