# Task 2: Verify gbrain works end-to-end from inside the sandbox

## Method
Ran Docker container with same image and bind-mounts as openclaw sandbox to test gbrain end-to-end.

## Results

### Step 1 -- Version (INFRA-02)
```
gbrain 0.10.1
```
PASS

### Step 2 -- Doctor (HEALTH-02)
```
Health score: 85/100. All checks OK (some warnings).
  [WARN] resolver_health: Could not find skills directory
  [OK] connection: Connected, 1 pages
  [WARN] pgvector: Could not check pgvector extension
  [WARN] rls: Could not check RLS status
  [OK] schema_version: Version 4 (latest: 4)
  [OK] embeddings: 100% coverage, 0 missing
  [OK] link_integrity: No dead links
```
PASS (85 >= 60 threshold; warnings expected for PGLite mode)

### Step 3 -- Put test page
```json
{"slug": "sandbox-verify-test", "status": "created_or_updated", "chunks": 1}
```
PASS

### Step 4 -- Search
```
[0.9940] sandbox-verify-test -- This page was created from inside Bob Docker sandbox...
```
PASS (1 result, 0.9940 relevance)

### Step 5 -- Embed (INFRA-04)
```
sandbox-verify-test: all 1 chunks already embedded
```
PASS (auto-embedded during put -- confirms OPENAI_API_KEY working)

### Step 6 -- Query (hybrid RAG)
```
[0.8531] sandbox-verify-test -- This page was created from inside Bob Docker sandbox...
[0.4687] test-install-verify -- This is a test page created during gbrain installation...
```
PASS (returns both pages with proper relevance ranking)

### Step 7 -- Stats
```
Pages:     2
Chunks:    2
Embedded:  2
Links:     0
Tags:      3
Timeline:  0
```
PASS (>= 1 page, >= 1 embedding)

## All Acceptance Criteria Met
- [x] gbrain --version returns 0.10.1 from inside sandbox
- [x] gbrain doctor health score 85 >= 60
- [x] gbrain put sandbox-verify-test succeeds (exit 0)
- [x] gbrain search returns at least one result
- [x] gbrain embed confirms OPENAI_API_KEY works (auto-embedded)
- [x] gbrain stats shows 2 pages and 2 embeddings
