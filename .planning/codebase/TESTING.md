# Testing Patterns

**Analysis Date:** 2026-01-18

## Test Framework

**Runner:**
- No formal test framework configured (Jest/Vitest not installed)
- Manual test scripts using Node.js native execution
- Test files: `test-*.js` in project root

**Assertion Library:**
- No assertion library - tests use console output and manual verification
- Success/failure indicated by `console.log('...')` and `process.exit(1)`

**Run Commands:**
```bash
node test-config.js           # Test configuration validation
node test-core.js             # Test Claude service methods
node test-integration.js      # Test all CLI commands and integrations
node test-playwright.js       # Test browser automation
node test-startup.js          # Test application initialization
```

## Test File Organization

**Location:**
- Root-level test files for main system: `/test-*.js`
- Module-specific tests co-located: `src/context/test-loader.js`, `src/pipeline/test-screenshot-analysis.js`

**Naming:**
- `test-{feature}.js` pattern
- Examples: `test-config.js`, `test-core.js`, `test-integration.js`

**Structure:**
```
/
├── test-config.js              # Configuration validation
├── test-core.js                # Core Claude service
├── test-integration.js         # Full integration tests
├── test-playwright.js          # Browser automation
├── test-startup.js             # Module loading
└── src/
    ├── context/
    │   ├── test-loader.js      # Context loader
    │   ├── test-compaction.js  # Context compaction
    │   └── test-process-notes.js
    └── pipeline/
        ├── test-screenshot-analysis.js
        ├── test-data-pulls.js
        ├── test-campaign-exporter.js
        └── test-property-scrubber.js
```

## Test Structure

**Suite Organization:**
```javascript
#!/usr/bin/env node

/**
 * Test Description
 * Brief explanation of what is being tested
 */

import { ServiceToTest } from './path/to/service.js';

async function runTests() {
  console.log('...' Testing Component...\n');
  console.log('='.repeat(60));

  let passedTests = 0;
  let failedTests = 0;

  try {
    // Test 1: Description
    console.log('\n... Test 1: Test Name');
    console.log('-'.repeat(60));
    // Test code
    console.log('... Test passed');
    passedTests++;

    // Test 2: Description
    console.log('\n... Test 2: Test Name');
    // More tests...

    // Final Results
    console.log('\n' + '='.repeat(60));
    console.log('... TEST RESULTS');
    console.log(`... Passed: ${passedTests}/${passedTests + failedTests}`);

  } catch (error) {
    console.error('\n... TEST FAILED:', error.message);
    process.exit(1);
  }
}

runTests();
```

**Setup/Teardown:**
- Setup inline at test start (no beforeEach/afterEach hooks)
- Teardown in finally blocks:
```javascript
try {
  await browser.init({ headless: true });
  // tests...
} finally {
  await browser.close();
  console.log('\n... Browser closed.');
}
```

**Test Patterns:**
- Sequential test execution (no parallelization)
- Numbered tests for easy identification: `Test 1:`, `Test 2:`
- Visual separators: `console.log('='.repeat(60));`

## Mocking

**Framework:** None - no mocking framework installed

**Patterns:**
- Mock data defined inline:
```javascript
const samplePropertyData = {
  property: {
    id: 'TEST-001',
    acres: 40,
    price: 80000,
    location: 'Barry County, MI'
  },
  market: {
    avgPricePerAcre: 2500,
    recentSales: 15
  }
};
```

- Mock API responses simulated:
```javascript
const mockScreenshotAnalysis = {
  marketInfo: {
    location: "Barry County, MI",
    acreageRange: "2-40 acres"
  },
  keyMetrics: {
    str: 0.72,
    volume: 98
  }
};
```

**What to Mock:**
- Claude API responses (to avoid API costs during testing)
- External service responses (Land Insights, county websites)
- File system operations for deterministic tests

**What NOT to Mock:**
- Configuration loading (test real config validation)
- Service initialization (test actual instantiation)
- Module imports (test real module loading)

## Fixtures and Factories

**Test Data:**
```javascript
// Inline fixture definition
const sampleUASData = {
  id: 'SURVEY-001',
  aircraft: 'Quantum Systems Trinity Pro',
  payload: 'LiDAR',
  area: '40 acres',
  location: 'Barry County, MI',
  date: '2025-11-15',
  flightDetails: {
    altitude: '120m AGL',
    overlap: '80%/70%',
    gsd: '5cm',
    conditions: 'Clear, 10mph wind'
  }
};
```

**Location:**
- Test data defined inline in test files
- No dedicated fixtures directory (planned in `tests/fixtures/` per README)
- Real screenshots in `test-screenshot.png` for Playwright tests

**Factory Pattern:** Not implemented - direct object literals used

## Coverage

**Requirements:** None enforced - no coverage tooling configured

**View Coverage:** Not available

**Planned Structure (from `tests/README.md`):**
```
tests/
├── unit/
│   ├── core/
│   │   └── claude.test.js
│   ├── land/
│   │   └── analyzer.test.js
│   └── utils/
│       └── logger.test.js
├── integration/
│   ├── land-analysis.test.js
│   └── uas-processing.test.js
├── fixtures/
│   ├── sample-land-data.json
│   └── sample-uas-data.json
└── mocks/
    └── claude-api-responses.js
```

## Test Types

**Unit Tests:**
- Not formally implemented
- Simulated via `test-core.js` testing individual service methods
- Each method tested independently with sample data

**Integration Tests:**
- `test-integration.js` tests complete workflows
- Tests CLI commands end-to-end
- Tests service integrations (LandAnalyzer, UASProcessor)

**E2E Tests:**
- `test-playwright.js` for browser automation
- Tests against real websites (example.com)
- Screenshot capture verification

## Common Patterns

**Async Testing:**
```javascript
async function runTests() {
  try {
    // Test async operations with await
    const response = await service.asyncMethod();
    console.log(`... Result: ${response}`);

  } catch (error) {
    console.error('... TEST FAILED:', error.message);
    process.exit(1);
  }
}

runTests();
```

**Error Testing:**
```javascript
// Test error handling by checking success response
try {
  const result = await service.methodThatMightFail();
  if (result.success === false) {
    console.log('... Expected failure handled correctly');
  }
} catch (error) {
  // Catch and report unexpected errors
  console.error('Unexpected error:', error.message);
  failedTests++;
}
```

**Health Check Pattern:**
```javascript
console.log('\n... Test: Health Check');
const healthy = await service.checkHealth();
console.log(`... Health check: ${healthy ? 'PASSED' : 'FAILED'}`);
```

**Statistics Verification:**
```javascript
const stats = service.getStats();
console.log('... Service Stats:');
console.log(`   Total Requests: ${stats.totalRequests}`);
console.log(`   Successful: ${stats.successfulRequests}`);
console.log(`   Failed: ${stats.failedRequests}`);
```

## Testing Gaps and Recommendations

**Current State:**
- Manual test scripts only
- No automated test runner
- No CI/CD integration
- No code coverage measurement
- No mock framework for API isolation

**Priority Test Areas (from `tests/README.md`):**
1. **API Integration**: Claude AI service connection and error handling
2. **Scoring Algorithms**: Land investment scoring accuracy and edge cases
3. **Data Validation**: Input validation and malformed data handling
4. **Error Recovery**: Network failures and API limit scenarios

**Recommended Improvements:**
- Install Jest or Vitest as test runner
- Add `npm test` script to package.json
- Create mock API responses for offline testing
- Implement test coverage with threshold enforcement
- Add GitHub Actions workflow for CI/CD

## Running Tests

**Manual Execution:**
```bash
# Test configuration (no API calls)
node test-config.js

# Test Claude service (requires API key, makes real API calls)
node test-core.js

# Test full integration (requires API key, makes real API calls)
node test-integration.js

# Test Playwright (launches headless browser)
node test-playwright.js

# Quick startup test (no API calls)
node test-startup.js

# Module-specific tests
node src/context/test-loader.js
node src/pipeline/test-screenshot-analysis.js
```

**Test Output:**
```
... Testing Configuration System...
============================================================

... Step 1: Validating configuration...

============================================================
... Configuration validation PASSED

... Loaded Configuration:
App Settings:
  - Name: Claude Life OS
  - Version: 1.0.0
  - Environment: development

... Phase 1 - Configuration Foundation: SUCCESS
```

---

*Testing analysis: 2026-01-18*
