# YOLO Build Protocol

You are executing an autonomous overnight build. Follow these steps exactly in order. Do not skip steps. Do not deviate from the constraints.

## Step 0: Pre-Flight Checks

Before starting, run these checks. If any check fails, STOP and log the reason.

**Check disk space:**
```bash
df -h /workspace/yolo-dev/
```
If less than 500MB free, STOP the build. Log a warning: "Skipped build: insufficient disk space."

**Check tech stack variety:**
```python
import sqlite3

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT tech_stack FROM builds WHERE status IN ('success','partial') ORDER BY id DESC LIMIT 2"
).fetchall()
conn.close()

recent_stacks = [r['tech_stack'] for r in rows]
print("Recent tech stacks:", recent_stacks)
```
If both recent builds used the same primary language (e.g., both start with "python"), you MUST pick a DIFFERENT primary approach for this build. For example, if the last two were Python CLI tools, build an HTML dashboard instead.

## Step 1: Generate Ideas

Read the interests file for inspiration:
```bash
cat /workspace/yolo-dev/YOLO_INTERESTS.md
```

Generate exactly 3-5 candidate project ideas. For EACH candidate, write:
- **Name:** A short, memorable project name
- **Description:** One sentence explaining what it does
- **Tech stack:** What languages/tools it uses (e.g., "python", "html,css,javascript", "python,html")
- **Estimated LOC:** How many lines of code (must be 100-500)

Consider the tech stack variety check from Step 0. Avoid repeating recent stacks.

Evaluate ALL candidates. Pick the BEST one with 2-3 sentences of reasoning explaining why it's the most interesting and feasible. Do NOT just pick the first idea.

## Step 2: Initialize Build

**Get the next build number:**
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.row_factory = sqlite3.Row
next_id = conn.execute(
    "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM builds"
).fetchone()['next_id']
conn.close()

print("Next build number:", next_id)
```

**Create the build slug** from the project name: lowercase, replace spaces with hyphens, remove special characters. Format: `{NNN}-{slug}` where NNN is the zero-padded build number (e.g., 002, 003, 010).

**Create the build directory:**
```bash
mkdir -p /workspace/yolo-dev/{NNN}-{slug}/
```

**Write ideas.md** in the build directory. Include ALL candidate ideas and your selection reasoning:
```markdown
# Build {NNN}: Ideas

## Candidates

### 1. {Name}
{Description}
- Tech stack: {stack}
- Estimated LOC: {loc}

### 2. {Name}
...

## Selected: {Name}

{2-3 sentences of reasoning for why this idea was chosen.}
```

**Insert the build into yolo.db with status 'idea':**
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.execute("""
    INSERT INTO builds (date, slug, name, description, status, tech_stack, started_at)
    VALUES (?, ?, ?, ?, 'idea', ?, ?)
""", (
    datetime.now().strftime('%Y-%m-%d'),
    slug,
    name,
    description,
    tech_stack,
    datetime.now().isoformat()
))
conn.commit()
conn.close()
```

**Update status to 'building':**
```python
import sqlite3

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.execute("UPDATE builds SET status='building' WHERE id=?", (build_id,))
conn.commit()
conn.close()
```

## Step 3: Build Prototype

Write the code files in your build directory: `/workspace/yolo-dev/{NNN}-{slug}/`

**Rules:**
- Default stack: Python stdlib + vanilla HTML/CSS/JS
- No pip install. No npm install. No external package installs of any kind.
- Total lines of code: 100-500 (across all source files, excluding README.md and ideas.md)
- Total files: 2-6 (including README.md)
- If creating HTML, make it self-contained with inline CSS and JS
- All file operations MUST stay within `/workspace/yolo-dev/{NNN}-{slug}/`

**Write a README.md** as you build:
```markdown
# {Project Name}

{One paragraph description of what it does and why it's interesting.}

## How to Run

{Exact command to run it, e.g.:}
```
python3 main.py
```

## What It Does

{Brief explanation of features and output.}

## Files

- `main.py` - {description}
- `index.html` - {description, if applicable}
```

## Step 4: Test

**Update status to 'testing':**
```python
import sqlite3

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.execute("UPDATE builds SET status='testing' WHERE id=?", (build_id,))
conn.commit()
conn.close()
```

**Run the main script:**
```bash
cd /workspace/yolo-dev/{NNN}-{slug}/
python3 main.py
```

Capture both stdout and stderr. Check:
1. Does it exit with code 0?
2. Does the output look correct?
3. If it generates an HTML file, does the file exist and contain valid HTML?

If the test fails, try ONE fix attempt. Fix the bug, re-run. If it still fails after one fix attempt, proceed to Step 5 with the failure noted.

## Step 5: Evaluate

Score the build on a 1-5 scale:

| Score | Label | Criteria |
|-------|-------|----------|
| 1 | Broken | Does not run at all |
| 2 | Runs with errors | Starts but crashes or produces wrong output |
| 3 | Works but rough | Runs correctly, code is messy or missing features |
| 4 | Solid prototype | Clean code, works as intended, good README |
| 5 | Impressive | Polished, creative, would show someone |

Write 2-3 sentences of evaluation reasoning explaining your score.

Determine the final status based on your score:
- Score 4-5: status = **success**
- Score 3: status = **partial**
- Score 1-2: status = **failed**

## Step 6: Log Results to yolo.db

**Count lines of code** (exclude README.md, ideas.md, POSTMORTEM.md):
```bash
wc -l /workspace/yolo-dev/{NNN}-{slug}/*.py /workspace/yolo-dev/{NNN}-{slug}/*.html /workspace/yolo-dev/{NNN}-{slug}/*.js /workspace/yolo-dev/{NNN}-{slug}/*.css 2>/dev/null | tail -1
```

**Count files** in the build directory:
```bash
ls -1 /workspace/yolo-dev/{NNN}-{slug}/ | wc -l
```

**Final UPDATE to yolo.db:**
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.execute("""
    UPDATE builds SET
        status=?,
        tech_stack=?,
        lines_of_code=?,
        files_created=?,
        self_score=?,
        self_evaluation=?,
        build_log=?,
        error_log=?,
        completed_at=?,
        duration_seconds=?
    WHERE id=?
""", (
    final_status,
    tech_stack,
    total_loc,
    file_count,
    score,
    evaluation_text,
    stdout_log,
    stderr_log,
    datetime.now().isoformat(),
    duration_secs,
    build_id
))
conn.commit()
conn.close()
```

## Step 7: Handle Failure (if applicable)

If the final status is 'failed' or 'partial', write a POSTMORTEM.md in the build directory:

```markdown
# POSTMORTEM: {project name}

## What Was Attempted
{Brief description of the project goal}

## Where It Broke
{Specific error or failure point}

## Root Cause
{Why it failed -- missing capability, logic error, time constraint, etc.}

## What Would Fix It
{Concrete steps to make it work if revisited}
```

If the final status is 'success', skip this step.

---

## Constraints (HARD RULES)

These rules are NON-NEGOTIABLE. Violating any of them makes the build invalid.

1. **Python stdlib + vanilla HTML/CSS/JS ONLY.** No pip install. No npm install. No external packages.
2. **100-500 lines of code total.** Measured across all source files (not README.md, ideas.md, POSTMORTEM.md).
3. **2-6 files maximum** in the build directory (including README.md and ideas.md).
4. **No file operations outside** `/workspace/yolo-dev/{NNN}-{slug}/` except reading YOLO_INTERESTS.md and accessing yolo.db.
5. **No external HTTP calls.** No requests, no urllib to external URLs, no fetching remote data.
6. **Build directory:** `/workspace/yolo-dev/{NNN}-{slug}/`
7. **DB path:** `/workspace/yolo-dev/yolo.db`
8. **All Python sqlite3 operations** MUST use explicit `conn.close()` after every operation. Do not leave connections open.
