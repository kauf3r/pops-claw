# Phase 49: Install Top 5 ClawhHub Skills on EC2 - Research

**Researched:** 2026-03-04
**Domain:** OpenClaw skill management via ClawhHub CLI
**Confidence:** HIGH

## Summary

This phase installs five ClawhHub skills on the EC2 instance: youtube-full, summarize, nano-banana-pro, blogwatcher, and real-estate-lead-machine. The ClawhHub CLI (`npx clawhub@latest`) is already confirmed working on the EC2 host (v0.7.0 via npx). Skills install as directories under `~/.openclaw/skills/` containing a `SKILL.md` and optional supporting files.

**youtube-full is already installed** (since 2026-02-16) but is at an older version -- the registry shows v1.4.1 while the installed copy dates from Feb 16. The other four skills are not yet present. Three of the five skills require external CLI binaries (`summarize`, `blogwatcher`, `uv`) that are not currently installed on the EC2 host. The `real-estate-lead-machine` skill requires an Apify API key/account.

**Primary recommendation:** Install the four missing skills via `npx clawhub@latest install <slug> --workdir ~/.openclaw`, update youtube-full with `--force`, install required CLI dependencies (`uv`, `summarize`, `blogwatcher`), add any new env vars, then restart the gateway.

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| clawhub CLI | 0.7.0 (via npx) | Install/manage skills from ClawhHub registry | Official OpenClaw skill manager |
| OpenClaw | v2026.2.17 | Agent platform running on EC2 | Already deployed and running |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| uv | latest | Python package runner for nano-banana-pro | Required by nano-banana-pro's generate_image.py script |
| summarize | latest (npm) | CLI for URL/file/YouTube summarization | Required by summarize skill (requires.bins) |
| blogwatcher | latest (Go) | RSS/blog feed monitor | Required by blogwatcher skill (requires.bins) |
| npx | 10.9.4 (installed) | Run clawhub without global install | Already available on EC2 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| npx clawhub@latest | npm install -g clawhub | Global install persists but adds maintenance; npx always gets latest |
| uv run (for nano-banana-pro) | pip install + python3 | uv handles venv/deps automatically; pip requires manual venv management |
| npm -g install summarize | npx @steipete/summarize | npx on-demand avoids global install but requires Node on PATH in sandbox |

**Installation commands:**
```bash
# Install uv (Python package runner)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install summarize via npm (Node.js 22+ already on host)
npm install -g @steipete/summarize

# Install blogwatcher (requires Go — not installed)
# Option A: Download pre-built binary from GitHub releases
# Option B: Install Go, then: go install github.com/Hyaxia/blogwatcher/cmd/blogwatcher@latest
```

## Architecture Patterns

### Skill Installation Directory
```
~/.openclaw/
├── skills/                      # Skill root (15 existing skills)
│   ├── youtube-full/            # ALREADY INSTALLED (needs update)
│   │   ├── SKILL.md
│   │   └── scripts/tapi-auth.js
│   ├── nano-banana-pro/         # NEW - to install
│   │   ├── SKILL.md
│   │   └── scripts/generate_image.py
│   ├── summarize/               # NEW - to install
│   │   └── SKILL.md
│   ├── blogwatcher/             # NEW - to install
│   │   └── SKILL.md
│   └── real-estate-lead-machine/# NEW - to install
│       └── SKILL.md
├── openclaw.json                # Config (skills.entries for API keys)
└── .env                         # Environment vars (API keys)
```

### Pattern 1: ClawhHub Install with --workdir
**What:** Point clawhub at the OpenClaw config root so skills land in `~/.openclaw/skills/`
**When to use:** Always — the EC2 skills directory is `~/.openclaw/skills/`, not the default `./skills`
**Example:**
```bash
# Install a new skill
npx clawhub@latest install <slug> --workdir ~/.openclaw

# Update an existing skill
npx clawhub@latest install youtube-full --workdir ~/.openclaw --force

# List installed skills
npx clawhub@latest list --workdir ~/.openclaw
```

### Pattern 2: Skill Environment Variables
**What:** Skills declare required env vars in frontmatter `metadata.openclaw.requires.env`
**When to use:** Before enabling any skill that needs API keys
**Example:**
```bash
# Add to ~/.openclaw/.env
TRANSCRIPT_API_KEY=xxx      # youtube-full (already set if working)
GEMINI_API_KEY=xxx          # nano-banana-pro (already set for memory embeddings)
APIFY_API_TOKEN=xxx         # real-estate-lead-machine (NEW - needs Apify account)
```

### Pattern 3: Skill Configuration in openclaw.json
**What:** Some skills need entries in `skills.entries` in openclaw.json
**When to use:** When a skill needs config beyond env vars (e.g., nano-banana-pro has apiKey in skills.entries)
**Example:**
```json
{
  "skills": {
    "entries": {
      "nano-banana-pro": {
        "apiKey": "AIzaSy..."
      }
    }
  }
}
```
Note: nano-banana-pro already has an entry in openclaw.json with an API key.

### Anti-Patterns to Avoid
- **Installing skills without --workdir:** Default installs to `./skills` in CWD, not the OpenClaw skills directory
- **Forgetting gateway restart:** Skills are snapshotted at gateway startup; new installs won't appear until restart
- **Installing binaries only on host:** If a skill has `requires.bins`, the binary must be accessible inside the Docker sandbox too (bind-mount or install in container image)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Skill installation | Manual git clone + copy | `npx clawhub@latest install` | Handles versioning, lockfile, directory structure |
| Skill updates | Manual diff + replace | `npx clawhub@latest install --force` or `update` | Preserves lockfile, handles version tracking |
| Python env for nano-banana-pro | Manual venv + pip | `uv run` | Auto-manages deps from script inline metadata |
| Skill inspection | Reading raw registry | `npx clawhub@latest inspect <slug>` | Shows metadata, files, hashes before install |

**Key insight:** The clawhub CLI handles skill lifecycle management including versioning via `.clawhub/lock.json`. Manual copying bypasses this tracking and makes updates harder.

## Common Pitfalls

### Pitfall 1: Sandbox Binary Access
**What goes wrong:** Skill installs on host but agent in Docker sandbox can't find required binaries
**Why it happens:** Docker sandbox is isolated; binaries on host PATH aren't automatically available inside the container
**How to avoid:** For each skill with `requires.bins`, either bind-mount the binary into the sandbox or rebuild the sandbox image with it installed. Check existing binds in openclaw.json for the pattern.
**Warning signs:** `openclaw doctor` shows skill as "blocked" or "ineligible"; agent errors with "command not found"

### Pitfall 2: Go Not Installed for blogwatcher
**What goes wrong:** `go install github.com/Hyaxia/blogwatcher/cmd/blogwatcher@latest` fails
**Why it happens:** Go is not installed on the EC2 instance
**How to avoid:** Download pre-built binary from GitHub releases instead, or install Go first. Check https://github.com/Hyaxia/blogwatcher/releases for Linux amd64 binary.
**Warning signs:** `which go` returns empty

### Pitfall 3: nano-banana-pro Uses uv (Not pip)
**What goes wrong:** Trying to run `python3 scripts/generate_image.py` directly fails with missing dependencies
**Why it happens:** The skill's SKILL.md instructs using `uv run` which auto-manages a virtual environment and dependencies. Running with bare python3 skips dependency resolution.
**How to avoid:** Install `uv` first: `curl -LsSf https://astral.sh/uv/install.sh | sh`
**Warning signs:** ImportError for google-genai or Pillow

### Pitfall 4: youtube-full Already Installed (Version Mismatch)
**What goes wrong:** Skipping youtube-full because it exists, missing new features/fixes
**Why it happens:** Installed version is from Feb 16; registry shows v1.4.1 (updated Mar 4)
**How to avoid:** Use `npx clawhub@latest install youtube-full --workdir ~/.openclaw --force` to update
**Warning signs:** Comparing SKILL.md dates or running `clawhub list`

### Pitfall 5: real-estate-lead-machine Needs Apify Account
**What goes wrong:** Skill installs but can't scrape anything
**Why it happens:** The skill uses Apify actors (Zillow Scraper, Rightmove Scraper, etc.) which require an Apify API token
**How to avoid:** Sign up at apify.com (free tier: $5/month credits, no card required), get API token, add to .env as APIFY_API_TOKEN
**Warning signs:** Skill runs but returns zero results or auth errors from Apify

### Pitfall 6: ClawHavoc / Malicious Skills
**What goes wrong:** Installing unvetted skills that steal credentials or install malware
**Why it happens:** 1,184+ malicious skills found on ClawHub (Feb 2026). The ClawHavoc campaign targeted credential theft via AMOS stealer.
**How to avoid:** All five target skills are from known authors (steipete, therohitdas, g4dr). Run `npx clawhub@latest inspect <slug>` before install to review files and hashes. VirusTotal scanning is now integrated into ClawHub.
**Warning signs:** Skills with suspicious `requires.bins` pointing to external downloads, very new skills from unknown authors

## Code Examples

### Install All Five Skills
```bash
# SSH to EC2
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9

# Update youtube-full (already installed, needs update)
npx clawhub@latest install youtube-full --workdir ~/.openclaw --force

# Install four new skills
npx clawhub@latest install nano-banana-pro --workdir ~/.openclaw
npx clawhub@latest install summarize --workdir ~/.openclaw
npx clawhub@latest install blogwatcher --workdir ~/.openclaw
npx clawhub@latest install real-estate-lead-machine --workdir ~/.openclaw

# Verify all installed
npx clawhub@latest list --workdir ~/.openclaw
ls -la ~/.openclaw/skills/{youtube-full,nano-banana-pro,summarize,blogwatcher,real-estate-lead-machine}/SKILL.md
```

### Install Required CLI Dependencies
```bash
# uv (for nano-banana-pro Python script)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.profile to pick up PATH

# summarize (npm global install — Node 22 already on host)
npm install -g @steipete/summarize

# blogwatcher — check GitHub releases for pre-built Linux binary
# If no pre-built: install Go first, then go install
# Alternative: skip blogwatcher binary for now, skill still installs (just won't be "eligible")
```

### Add Environment Variables
```bash
# Check what's already set
grep -E 'TRANSCRIPT_API_KEY|GEMINI_API_KEY|APIFY_API_TOKEN' ~/.openclaw/.env

# Add missing vars (APIFY_API_TOKEN is new)
echo 'APIFY_API_TOKEN=your_token_here' >> ~/.openclaw/.env

# Also add to sandbox env if agent needs them inside Docker
# Edit openclaw.json → agents.defaults.sandbox.docker.env
```

### Restart Gateway and Verify
```bash
# Restart gateway to load new skills
systemctl --user restart openclaw-gateway

# Run doctor to verify skill eligibility
/home/ubuntu/.npm-global/bin/openclaw doctor

# Check skills are recognized
/home/ubuntu/.npm-global/bin/openclaw skills  # or similar list command
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual skill file copy | `npx clawhub@latest install` | ClawHub launched ~Jan 2026 | Versioning, lockfile, registry search |
| VirusTotal not integrated | VirusTotal skill scanning | Feb 2026 | Malicious skill detection before install |
| No skill inspect | `clawhub inspect` pre-install | CLI v0.7.0 | Review files/hashes before committing |

**Deprecated/outdated:**
- Manual skill copy from GitHub: Use `clawhub install` instead for version tracking
- `clawdhub` (npm package): The correct package is `clawhub` (no 'd')

## Open Questions

1. **blogwatcher binary availability for Linux**
   - What we know: Requires Go to build from source. Go is not installed on EC2.
   - What's unclear: Whether pre-built Linux binaries are available on GitHub releases
   - Recommendation: Check https://github.com/Hyaxia/blogwatcher/releases first; if no binary, either install Go or defer blogwatcher to a later phase

2. **Sandbox access for new binaries**
   - What we know: uv, summarize, and blogwatcher need to be on PATH. Agent Bob runs in Docker sandbox.
   - What's unclear: Whether these binaries need to be bind-mounted into the Docker container, or if the skill only runs host-side
   - Recommendation: Test after install. If agent can't use the skill, add bind-mounts to openclaw.json sandbox.docker.binds (following the existing gog/gh pattern)

3. **APIFY_API_TOKEN for real-estate-lead-machine**
   - What we know: Skill needs Apify actors to scrape property data. Free tier available ($5/month credits).
   - What's unclear: Whether Andy has or wants an Apify account
   - Recommendation: Install the skill now (no harm), defer Apify signup/token to user decision

4. **nano-banana-pro API key scope**
   - What we know: openclaw.json already has a `skills.entries.nano-banana-pro.apiKey` (Gemini key) AND .env has `GEMINI_API_KEY`. The skill's SKILL.md references `--api-key` flag or env var.
   - What's unclear: Whether the existing config key is sufficient or if additional setup is needed
   - Recommendation: Install and test; the existing Gemini API key should work

5. **TRANSCRIPT_API_KEY for youtube-full**
   - What we know: youtube-full requires `TRANSCRIPT_API_KEY` env var (for TranscriptAPI.com)
   - What's unclear: Whether this key is already configured (not visible in .env grep)
   - Recommendation: Check if key exists; if not, sign up at transcriptapi.com (free tier: 100 credits/month)

## Skill-by-Skill Requirements Summary

| Skill | Status | Env Vars Needed | Binaries Needed | External Account |
|-------|--------|-----------------|-----------------|------------------|
| youtube-full | UPDATE (v1.4.1) | TRANSCRIPT_API_KEY | None | TranscriptAPI.com (free 100/mo) |
| nano-banana-pro | NEW install | GEMINI_API_KEY (already set) | uv (NOT installed) | None (uses existing Gemini key) |
| summarize | NEW install | GEMINI_API_KEY or similar (already set) | summarize CLI (NOT installed) | None |
| blogwatcher | NEW install | None | blogwatcher CLI (NOT installed, needs Go) | None |
| real-estate-lead-machine | NEW install | APIFY_API_TOKEN (NOT set) | None (uses Apify cloud) | Apify.com (free $5/mo) |

## EC2 Resource Check

| Resource | Current | After Install | Risk |
|----------|---------|---------------|------|
| Disk | 24GB used / 38GB total (63%) | +~1MB skills + ~100MB binaries | LOW |
| RAM | 977MB used / 1910MB total | No change (skills are markdown) | NONE |
| Swap | 725MB used / 2047MB | No change | NONE |

## Sources

### Primary (HIGH confidence)
- ClawhHub CLI help output (`npx clawhub@latest --help`, `install --help`) - verified on EC2
- EC2 filesystem inspection - live state of `~/.openclaw/skills/`, `openclaw.json`, `.env`
- `clawhub inspect` output for all 5 skills - verified metadata, files, versions

### Secondary (MEDIUM confidence)
- [ClawHub - OpenClaw Docs](https://docs.openclaw.ai/tools/clawhub) - official installation docs
- [OpenClaw Skills Docs](https://docs.openclaw.ai/tools/skills) - skill format and requirements
- [steipete/summarize GitHub](https://github.com/steipete/summarize) - summarize CLI install methods
- [uv Installation](https://docs.astral.sh/uv/getting-started/installation/) - uv install on Linux
- [Apify Pricing](https://apify.com/pricing) - free tier details

### Tertiary (LOW confidence)
- [VirusTotal Blog - ClawHavoc](https://blog.virustotal.com/2026/02/from-automation-to-infection-how.html) - security context
- [Hyaxia/blogwatcher GitHub](https://github.com/Hyaxia/blogwatcher) - blogwatcher install (Go required)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - clawhub CLI verified working on EC2, commands tested
- Architecture: HIGH - existing skill directory structure inspected, patterns match
- Pitfalls: HIGH - binary dependencies confirmed missing via SSH, sandbox constraints documented from prior phases

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (stable — skills and CLI don't change frequently)
