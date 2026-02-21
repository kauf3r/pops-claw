# Pitfalls Research

**Domain:** Next.js monitoring dashboard reading from actively-written SQLite databases on resource-constrained EC2 (pops-claw v2.5)
**Researched:** 2026-02-20
**Confidence:** HIGH (pitfalls derived from SQLite official docs, Next.js official docs, better-sqlite3 docs, and direct project history)

> This file supersedes the v2.3-era PITFALLS.md. The v2.3 pitfalls (config nuking by doctor --fix, SecureClaw
> blocking crons, observability hook latency, DMARC escalation, Gmail scope reduction, DM session loss) are
> still valid and remain in the project's institutional knowledge -- they are not repeated here. This file
> covers v2.5 Mission Control Dashboard pitfalls only.

---

## Critical Pitfalls

### Pitfall 1: SQLite SQLITE_BUSY Errors From Dashboard Reads Blocking Agent Writes (and Vice Versa)

**What goes wrong:**
Mission Control opens read connections to 5 SQLite databases (coordination.db, observability.db, content.db, email.db, health.db) that OpenClaw agents and cron jobs are actively writing to. Without WAL mode, a dashboard SELECT query holds a shared lock that blocks agent INSERT/UPDATE operations. The agent's write attempt gets `SQLITE_BUSY` and -- if no `busy_timeout` is set (the default is 0ms) -- fails immediately. A cron job that needed to write its heartbeat to coordination.db silently fails. Worse: if the dashboard holds a long-running read transaction (e.g., a Server Component that queries multiple tables in sequence without closing), it can block writes for the entire duration of the request.

**Why it happens:**
SQLite's default journal mode is `DELETE` (rollback journal), which uses exclusive locks for writes and shared locks for reads -- reads and writes block each other. The default `busy_timeout` is 0, meaning any lock contention results in immediate failure rather than retry. better-sqlite3 uses synchronous operations, so a slow query on the dashboard thread holds the lock for the entire duration. With 5 databases each potentially queried on every page load, the window for contention is significant.

**How to avoid:**
- Enable WAL mode on ALL 5 databases: `db.pragma('journal_mode = WAL')` -- do this once per database, it persists across connections
- Set `busy_timeout` on EVERY connection (dashboard AND agent-side): `db.pragma('busy_timeout = 5000')` -- this is per-connection and must be set every time a connection opens
- Open dashboard connections as read-only: `new Database(path, { readonly: true })` -- this prevents accidental writes from the dashboard and signals intent to SQLite
- Keep dashboard read transactions as short as possible -- do NOT wrap multiple queries in a transaction; let each query be its own implicit transaction
- Use `BEGIN IMMEDIATE` for any write operations on the agent side to avoid deferred-transaction upgrade deadlocks

**Warning signs:**
- Agent cron logs show "database is locked" or "SQLITE_BUSY" errors
- Dashboard pages intermittently return stale or empty data
- Heartbeat crons miss their window and show gaps in coordination.db
- Morning briefing takes noticeably longer after dashboard is running

**Phase to address:** Phase 1 (database connection layer) -- WAL mode and busy_timeout must be configured before ANY dashboard reads go live

---

### Pitfall 2: WAL Checkpoint Starvation From Always-Open Dashboard Connections

**What goes wrong:**
The dashboard keeps database connections open to serve requests. If there is always at least one active read transaction, SQLite cannot complete WAL checkpoints -- the WAL file grows without bound. On a t3.small with 40GB EBS (currently ~55% full, ~13GB free), an unbounded WAL file for 5 databases can consume gigabytes of disk in days. When disk fills, ALL writes fail -- not just dashboard reads, but agent operations, cron jobs, email processing, everything.

This is called "checkpoint starvation": checkpoints cannot shrink the WAL while there are active readers, so the WAL file grows indefinitely if a reader always has a transaction open. SQLite's official documentation explicitly warns about this.

**Why it happens:**
better-sqlite3 connections in a long-running Node.js process (like a Next.js server) can hold implicit read transactions open if:
- A prepared statement is stepped but not finalized
- A query result iterator is not fully consumed
- The connection object is held open in a module-level singleton
- Server-Side Rendering reads span multiple event loop ticks

Each of these prevents SQLite from checkpointing past that reader's snapshot.

**How to avoid:**
- Do NOT keep persistent database connections in module-level singletons -- open connections per-request and close them when done
- If using connection pooling, ensure connections are returned to the pool (and thus release their read snapshots) after each request
- Run periodic manual checkpoints: `db.pragma('wal_checkpoint(TRUNCATE)')` on a timer (every 5 minutes)
- Monitor WAL file sizes: `ls -la *.db-wal` -- if any exceed 10MB, checkpoint starvation is occurring
- Set `PRAGMA wal_autocheckpoint = 1000` (default) and verify it is not disabled
- Consider opening dashboard connections, running queries, then immediately closing -- the overhead is minimal for better-sqlite3 (synchronous, no connection handshake)

**Warning signs:**
- `*.db-wal` files growing continuously (check with `du -h ~/.openclaw/agents/main/*.db-wal`)
- Disk usage climbing even when no new data is being added
- "disk I/O error" or "database or disk is full" errors in any OpenClaw component
- Dashboard queries getting progressively slower as WAL file grows

**Phase to address:** Phase 1 (database connection layer) -- connection lifecycle management is foundational

---

### Pitfall 3: Next.js Process Exhausts 2GB RAM on t3.small, Triggers OOM Killer

**What goes wrong:**
The EC2 instance has 2GB RAM + 2GB swap. Currently running: OpenClaw gateway (~300-500MB), Docker sandbox (agent-browser + Chromium), systemd services, Tailscale. Adding a Next.js 14 production server with 5 SQLite connections, server-side rendering, and React component trees pushes total memory past 2GB. Linux OOM killer activates and kills whichever process has the highest OOM score -- which is likely the OpenClaw gateway or Docker container (not the dashboard), because the gateway doesn't have OOM protection unless explicitly configured. Bob goes down, 20 cron jobs stop, and the dashboard ironically shows nothing because the system it monitors is dead.

Note: tailscaled and sshd already have `OOMScoreAdjust=-900` (from v2.0 hardening). The OpenClaw gateway does NOT have this protection.

**Why it happens:**
Next.js 14 in production mode typically uses 200-400MB for a simple app. With server components doing SSR, multiple database connections (each with page caches), and React hydration on the client, memory can spike to 500MB+. Combined with the existing ~1.2GB baseline (gateway + Docker + system), this leaves almost no headroom. The 2GB swap file helps but swap thrashing on EBS (gp3) is extremely slow and degrades everything.

**How to avoid:**
- Set `NODE_OPTIONS='--max-old-space-size=384'` for the Next.js process -- cap it before it can OOM the host
- Use `output: 'standalone'` in next.config.js to minimize the deployed footprint
- Set `experimental.isrMemoryCacheSize: 0` (or `cacheMaxMemorySize: 0` in newer versions) to disable in-memory caching
- Add `OOMScoreAdjust=500` to the Mission Control systemd service -- this tells the OOM killer to prefer killing the dashboard over the gateway
- Add `OOMScoreAdjust=-500` to the OpenClaw gateway service -- protect it from OOM killer
- Do NOT use `next dev` in production -- dev mode uses 2-3x more memory than production
- Monitor with: `free -h` and `cat /proc/meminfo | grep -i swap` after deployment
- Consider whether the dashboard can use `next export` (static generation) instead of SSR for pages that don't need real-time data

**Warning signs:**
- `free -h` shows swap usage above 500MB
- System becomes sluggish (swap thrashing on EBS)
- `dmesg | grep -i oom` shows OOM killer invocations
- Gateway or Docker container spontaneously restarts

**Phase to address:** Phase 1 (infrastructure setup) -- memory budget must be established before writing any dashboard code

---

### Pitfall 4: Hydration Mismatches From Server/Client Timezone Divergence

**What goes wrong:**
Server Components render timestamps in UTC (EC2 server timezone). Client-side React hydrates with the user's local timezone (America/Los_Angeles for Andy). Every timestamp rendered by a Server Component will mismatch the client hydration, causing React hydration errors. This is NOT hypothetical -- it already happened in the existing Mission Control code and was fixed by deferring `new Date()` to a client-side `useEffect`. But the fix was applied narrowly, and every new component that renders a date will re-introduce this bug.

**Why it happens:**
Next.js Server Components run on the EC2 server in UTC. The same component code runs on the client in the user's timezone. `new Date()`, `Date.now()`, `toLocaleString()`, and `Intl.DateTimeFormat` all produce different output on server vs. client when timezones differ. React strict mode makes this a hard error, not a warning.

**How to avoid:**
- Establish a project-wide rule: ALL date/time rendering happens in Client Components only, using `useEffect` + `useState` to hydrate after mount
- Create a shared `<RelativeTime timestamp={iso} />` Client Component that all pages use -- enforce this in code review
- For Server Components that need to display dates: render the raw ISO timestamp as a `data-` attribute or `<time datetime="">` element, then hydrate it client-side
- Use `suppressHydrationWarning={true}` on the `<time>` element as a safety net (not as the primary solution)
- Set `TZ=America/Los_Angeles` in the Next.js process environment to match the user's timezone -- this reduces (but does not eliminate) mismatches because Intl formatting may still differ
- Do NOT use `Date.now()` or `new Date()` in any shared component that renders on both server and client

**Warning signs:**
- React console errors: "Text content does not match server-rendered HTML"
- Timestamps flicker or change on page load (client hydration replaces server-rendered value)
- Time-based sorting appears wrong on initial load, then corrects itself

**Phase to address:** Every phase that adds UI components -- but the shared `<RelativeTime>` component should be created in Phase 1

---

### Pitfall 5: Dashboard Reads Corrupt Data by Opening Databases Without Matching Schema Expectations

**What goes wrong:**
The 5 SQLite databases are created and managed by OpenClaw, its plugins, and agent skills -- NOT by the dashboard. Their schemas can change when OpenClaw is updated, plugins are reinstalled, or skills are modified. The dashboard hardcodes queries like `SELECT * FROM agent_activity ORDER BY timestamp DESC` -- but if an OpenClaw update renames `agent_activity` to `activity_log` or adds/removes columns, the dashboard queries fail with cryptic SQLite errors. Worse: if the dashboard opens a database before it has been created (e.g., during initial setup or after a fresh install), better-sqlite3 will CREATE an empty database file, which then confuses the OpenClaw component that expects to create it with its own schema.

**Why it happens:**
The dashboard is a separate application that reads databases it doesn't own. There is no shared schema definition, no migration system, and no version contract between OpenClaw's database schemas and the dashboard's queries. OpenClaw treats these databases as internal implementation details.

**How to avoid:**
- Before opening any database, verify the file exists AND has the expected tables: `SELECT name FROM sqlite_master WHERE type='table'` -- if expected tables are missing, show a "database not initialized" message, do NOT create the file
- Open all databases with `{ readonly: true }` to prevent accidental file creation
- Use `SELECT * FROM table LIMIT 0` to validate column names at startup -- fail fast if schema doesn't match
- Build a schema validation layer that checks on server startup: expected tables, expected columns, and logs warnings for missing/extra columns
- When OpenClaw is updated, re-run schema validation and update dashboard queries if needed
- Pin dashboard compatibility to a specific OpenClaw version and document it

**Warning signs:**
- Dashboard shows empty data for a section that should have data
- New `.db` files appear that are 0 bytes (dashboard created them by opening a non-existent path)
- SQLite errors like "no such table" or "no such column" in Next.js server logs

**Phase to address:** Phase 1 (database connection layer) -- schema validation must be built into the connection module

---

## Moderate Pitfalls

### Pitfall 6: Replacing Convex With Direct SQLite Reads Loses Real-Time Push Updates

**What goes wrong:**
The current Mission Control uses Convex for the activity feed, which provides real-time push updates -- when a new activity happens, the UI updates automatically without polling. Replacing Convex with direct SQLite reads means the dashboard becomes pull-based: it only shows new data when the user refreshes or a polling interval fires. If polling is set too infrequently, the dashboard feels stale. If set too aggressively, it creates unnecessary database load (and potential lock contention per Pitfall 1).

**Why it happens:**
SQLite has no built-in pub/sub or change notification mechanism for external processes. The dashboard cannot "subscribe" to changes in coordination.db. It must poll. The transition from Convex (push) to SQLite (pull) is a UX regression that's easy to overlook.

**How to avoid:**
- Accept the tradeoff: for a single-user dashboard behind Tailscale, 10-30 second polling is fine
- Use Next.js client-side polling with `setInterval` in a `useEffect` -- NOT server-side revalidation (which triggers full re-renders)
- For the activity feed specifically: fetch only records newer than the last-seen timestamp to minimize query scope
- Consider SSE (Server-Sent Events) via a Next.js Route Handler if near-real-time is desired -- the handler polls SQLite every 5 seconds and pushes to the client only when new data exists
- Do NOT use WebSockets -- they're overkill for a single-user dashboard and add memory overhead
- Profile the polling query cost: `EXPLAIN QUERY PLAN SELECT ... WHERE timestamp > ?` should use an index

**Warning signs:**
- Dashboard shows data that's minutes old and user keeps refreshing manually
- Multiple browser tabs each polling creates multiplicative database load
- SSE connections that never close cause checkpoint starvation (see Pitfall 2)

**Phase to address:** Phase 2 (activity feed migration) -- polling strategy and interval must be decided before removing Convex

---

### Pitfall 7: Binding Next.js to Tailscale IP Exposes It If Tailscale Goes Down

**What goes wrong:**
The plan is to bind Next.js to the Tailscale IP (100.72.143.9) so it's directly accessible from the tailnet without SSH tunneling. But if Next.js is bound to `0.0.0.0` (common default) instead of the specific Tailscale IP, it's also accessible on the EC2's public IP (if one exists) or any other network interface. Even binding to the Tailscale IP specifically: if Tailscale goes down and comes back up with a different interface configuration, or if the tailscale0 interface is temporarily down, Next.js may fail to start or silently rebind.

Additionally: the current setup binds the OpenClaw gateway to 100.72.143.9:18789. Adding Next.js on the same IP but a different port (3001) is fine, but UFW rules must be updated to allow port 3001 on the tailscale0 interface.

**Why it happens:**
The security model relies on Tailscale as the sole access control layer. If Tailscale's interface is not up when Next.js starts, the bind fails. If Next.js falls back to 0.0.0.0, it's exposed. EC2 security groups provide a second layer (only allowing 100.64.0.0/10), but defense-in-depth requires intentional configuration at each layer.

**How to avoid:**
- Bind Next.js explicitly to the Tailscale IP: `next start -H 100.72.143.9 -p 3001`
- In the systemd service file, add `After=tailscaled.service` and `Requires=tailscaled.service` so Next.js only starts after Tailscale is running
- Add a startup check in the service: verify `ip addr show tailscale0` shows the expected IP before starting Next.js
- Update UFW: `sudo ufw allow in on tailscale0 to any port 3001 proto tcp`
- Do NOT bind to `0.0.0.0` -- even with SG and UFW protection, it's an unnecessary exposure
- EC2 security group already restricts to 100.64.0.0/10, but add port 3001 to the allowed list

**Warning signs:**
- Next.js accessible from outside the tailnet (test with: `curl http://<public-ip>:3001`)
- Next.js fails to start after Tailscale restart
- UFW blocks legitimate dashboard access on the tailnet

**Phase to address:** Phase 1 (infrastructure setup) -- network binding configuration must be done before the dashboard is accessible

---

### Pitfall 8: observability.db Writes by Hooks Plugin Conflict With Dashboard Reads

**What goes wrong:**
The observability-hooks plugin writes to observability.db on EVERY agent turn (llm_output + agent_end events). The morning briefing alone generates dozens of turns. If the dashboard is reading from observability.db (for token usage, agent activity) at the same time a flurry of hook writes is happening (e.g., during morning briefing at 6 AM), write-read contention is at its highest. Even with WAL mode, the write lock is exclusive -- multiple rapid writes from the hooks plugin can cause brief but repeated lock contention with dashboard reads.

This is distinct from Pitfall 1 (general SQLITE_BUSY) because the write frequency of observability.db is much higher than the other databases. coordination.db gets written to every 15 minutes (heartbeats). observability.db gets written to on EVERY LLM turn -- potentially hundreds of times per hour during active agent sessions.

**Why it happens:**
The hooks plugin writes synchronously to observability.db in the hook handler. Each hook invocation opens a connection, writes, and closes. The dashboard has its own connection open for reads. With WAL mode, reads don't block writes, but the write lock is still exclusive -- if the hooks plugin is in the middle of a write and the dashboard tries to write (even just updating a read cursor), there's contention.

**How to avoid:**
- Dashboard connections to observability.db must be strictly read-only: `new Database(path, { readonly: true })`
- Set a generous `busy_timeout` on the dashboard's observability.db connection: `db.pragma('busy_timeout = 10000')` (10 seconds)
- Dashboard queries on observability.db should be simple and fast: avoid JOINs, use indexed columns, LIMIT results
- Add indexes on the observability.db columns the dashboard queries (timestamp, agent_id) -- coordinate with the hooks plugin schema
- Consider caching observability data: query once per minute and serve from in-memory cache, rather than querying on every page load
- If observability.db becomes a hot spot: consider a separate "dashboard summary" table that a background job aggregates into periodically

**Warning signs:**
- Dashboard token usage section loads slowly or times out during active agent sessions
- `SQLITE_BUSY` errors in Next.js logs specifically for observability.db
- Observability hook latency increases (because the dashboard's read transactions delay WAL checkpoints)

**Phase to address:** Phase 3 (agent monitoring / observability views) -- this pitfall is specific to the observability.db integration

---

### Pitfall 9: Production Next.js Process Not Managed by systemd (Dies Silently)

**What goes wrong:**
During development, Next.js runs with `npx next dev` in an SSH terminal. When the terminal is closed or the SSH session drops, the process dies. The dashboard is gone and nobody notices until the next time Andy tries to load it. Even in production mode (`next start`), if the process is started manually (not via systemd), it has no automatic restart, no log management, and no startup-on-boot behavior.

**Why it happens:**
Development workflows naturally evolve: "I'll just run it in a terminal for now and productionize later." But "later" often means "after it crashes for the first time and I lose an hour debugging why the dashboard is down." The existing project has this exact pattern with the OpenClaw gateway (solved by `openclaw-gateway.service`), but the dashboard doesn't have one yet.

**How to avoid:**
- Create a systemd user service from day one: `~/.config/systemd/user/mission-control.service`
- Set `Restart=always`, `RestartSec=5` (same pattern as openclaw-gateway.service)
- Set `OOMScoreAdjust=500` (dashboard is expendable; gateway is not)
- Use `StandardOutput=journal` and `StandardError=journal` for log management
- Set `Environment=NODE_OPTIONS=--max-old-space-size=384` to cap memory
- Set `After=openclaw-gateway.service` -- dashboard depends on the gateway being up
- Enable with: `systemctl --user enable mission-control.service`
- Use `next build && next start` (not `next dev`) in the ExecStart

**Warning signs:**
- Dashboard inaccessible after EC2 reboot
- No systemd service file exists for Mission Control
- `ps aux | grep next` shows nothing after SSH session ends
- Dashboard process running under `tmux` or `screen` (fragile workaround)

**Phase to address:** Phase 1 (infrastructure setup) -- systemd service must be created alongside the initial deployment

---

### Pitfall 10: Five Separate Database Connections Per Request Multiply Latency and Memory

**What goes wrong:**
Mission Control needs data from 5 databases. A naive implementation opens 5 separate better-sqlite3 connections per incoming request, queries each, aggregates the results, then renders the page. Each connection has overhead: file handle, page cache, WAL reader state. With 5 connections and server-side rendering, a single page load allocates ~50-100MB of SQLite page cache memory (default page cache is 2000 pages x 4KB = 8MB per connection x 5 = 40MB). On a 2GB RAM system, this is significant.

**Why it happens:**
Each database is a separate file with a separate schema. better-sqlite3 requires a separate `Database` instance per file. There's no way around this -- but the default page cache size is tuned for larger systems.

**How to avoid:**
- Reduce page cache per connection: `db.pragma('cache_size = 200')` (200 pages = ~800KB per connection, 5 connections = ~4MB total)
- Create a single database access module that lazily opens connections and reuses them across requests (but see Pitfall 2 about checkpoint starvation -- close idle connections after 60 seconds)
- NOT all 5 databases need to be queried on every page: the activity feed only needs coordination.db and observability.db; the email page only needs email.db. Route-based connection selection reduces per-request overhead
- Consider using SQLite's `ATTACH DATABASE` to query multiple databases through a single connection -- but be aware this makes write contention worse (one connection holds locks on all attached databases)
- Profile actual memory usage after connecting all 5: `process.memoryUsage().heapUsed` before and after opening connections

**Warning signs:**
- Next.js process memory climbing steadily (memory leak from unclosed connections)
- Page load times exceeding 2 seconds
- `too many open files` errors (each SQLite connection uses 2-3 file descriptors; ulimit may be low)

**Phase to address:** Phase 1 (database connection layer) -- connection management strategy must be designed before building individual pages

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip WAL mode setup ("it works in dev") | Faster initial setup | SQLITE_BUSY errors in production under any concurrent access | Never -- WAL mode is a one-time pragma with zero downside |
| Use `next dev` in production | Hot reload during iteration | 2-3x memory usage, no optimization, crashes on t3.small | Only during active development sessions, never overnight |
| Module-level singleton DB connections | Simpler code, no connection management | Checkpoint starvation, WAL file growth, eventual disk full | Acceptable with periodic manual checkpoint on a timer |
| Skip systemd service ("I'll just use tmux") | Works immediately | Dashboard dies on SSH disconnect, no auto-restart, no logs | First 24 hours of development only |
| Query all 5 databases on every page load | Complete data on every view | Unnecessary lock contention and memory usage | Never -- use route-based connection selection |
| Poll every 1 second for "real-time feel" | UI feels responsive | 60 queries/minute per database, lock contention during agent activity | Never -- 10-30 second intervals are sufficient for single user |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| better-sqlite3 + WAL | Enabling WAL on the dashboard side only | WAL must be enabled on the database file itself (it persists); verify the writing process (OpenClaw) also uses WAL or at least doesn't force rollback mode |
| better-sqlite3 readonly | Opening with `readonly: true` on a WAL database where the `-wal` file needs write access for reading | Ensure the `-shm` and `-wal` files are readable; readonly mode in WAL works but cannot create the shared-memory file if it doesn't exist |
| Next.js + better-sqlite3 | Using `better-sqlite3` in Client Components | better-sqlite3 is a Node.js native module -- it can ONLY be used in Server Components, Route Handlers, or API routes; never import it on the client side |
| Next.js standalone | Forgetting to copy `.db` files when using `output: 'standalone'` | Database files are outside the build output; use absolute paths to the original locations on disk |
| Convex removal | Removing Convex before the SQLite replacement is verified | Keep both running in parallel during transition; remove Convex only after SQLite data is verified to match |
| observability.db | Assuming the schema matches the hooks plugin documentation | Schema may differ from docs; inspect the actual database with `.schema` before writing queries |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unbounded `SELECT * FROM activity` queries | Page load takes 5+ seconds; memory spikes | Always use `LIMIT` and `WHERE timestamp > ?`; paginate | When activity table exceeds ~10,000 rows (weeks of agent activity) |
| Full table scans on timestamp columns | Queries slow down linearly as data grows | Add index: `CREATE INDEX IF NOT EXISTS idx_timestamp ON table(timestamp)` | When any table exceeds ~5,000 rows |
| Rendering all activity items in one React component | Browser freezes on initial load | Virtualized list (react-window or tanstack-virtual) or pagination | When rendering 100+ items |
| No data retention / pruning | Databases grow indefinitely; queries slow; disk fills | Add age-based pruning (keep 30 days); run via cron | When databases exceed 100MB combined (months of operation) |
| SSR for all pages | Every page load does server-side rendering with DB queries | Use static generation for layout/nav; SSR only for data sections | On t3.small: when 3+ pages are requested within 5 seconds |

---

## Security Mistakes

Domain-specific security issues for this milestone.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Binding Next.js to 0.0.0.0 instead of Tailscale IP | Dashboard accessible from public internet (if SG misconfigured) | Bind explicitly to 100.72.143.9; add UFW rule for tailscale0 interface only |
| No authentication on the dashboard | Anyone on the tailnet can access all data | Add basic auth or Tailscale auth headers (funnel/serve) -- acceptable to skip for single-user but document the decision |
| Database paths hardcoded in client-side code | Leaks filesystem structure to browser | Keep all DB paths in server-only code (Server Components / API routes); never expose paths in client bundles |
| Serving source maps in production | Leaks internal code structure | Set `productionBrowserSourceMaps: false` in next.config.js (this is the default) |
| Dashboard read-only connection writing accidentally | Could corrupt agent databases | Always use `{ readonly: true }` for all dashboard DB connections; test by attempting a write |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing raw UTC timestamps | Confusing -- Andy is in Pacific time | Client-side timezone conversion via shared `<RelativeTime>` component |
| Loading all data on the home page | Slow initial load; overwhelming information density | Progressive disclosure: summary cards first, drill-down on click |
| No loading states during data fetch | Page appears broken while waiting for DB queries | Skeleton loaders for each card/section; `<Suspense>` boundaries per section |
| Stale data without indication | User doesn't know if they're seeing current or old data | "Last updated: X seconds ago" indicator on each data section |
| No empty states | Blank sections when data is missing (new install, DB not created) | Explicit "No data yet -- waiting for first [heartbeat/cron/email]" messages |
| Auto-refresh interrupting user interaction | User reading data when page refreshes and loses scroll position | Pause auto-refresh when tab is focused; use incremental updates, not full page reload |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Database layer:** WAL mode enabled AND `busy_timeout` set on all connections AND `readonly: true` for all dashboard connections AND page cache size reduced (`cache_size = 200`)
- [ ] **Activity feed:** Convex fully removed AND SQLite queries verified to return matching data AND polling interval configured AND pagination implemented for large result sets
- [ ] **Timestamps:** ALL date displays use the shared `<RelativeTime>` client component AND no hydration errors in React console AND EC2 timezone handling verified
- [ ] **Memory budget:** `NODE_OPTIONS=--max-old-space-size=384` set AND `free -h` checked after deployment AND swap usage below 500MB under normal operation
- [ ] **Process management:** systemd service exists AND `Restart=always` AND `OOMScoreAdjust=500` AND starts on boot AND survives SSH disconnect
- [ ] **Network binding:** Next.js bound to 100.72.143.9 (not 0.0.0.0) AND UFW rule added for port 3001 on tailscale0 AND tested inaccessible from public IP
- [ ] **Schema validation:** Dashboard validates expected tables exist before querying AND handles missing databases gracefully AND does NOT create empty `.db` files
- [ ] **observability.db:** Separate connection management from other DBs AND higher busy_timeout AND queries use indexed columns AND cached where possible

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SQLITE_BUSY errors during agent writes | LOW | Enable WAL mode: `sqlite3 database.db "PRAGMA journal_mode=WAL;"` on all 5 databases; set busy_timeout; restart dashboard |
| WAL file grown to gigabytes | LOW | Close all dashboard connections; run `sqlite3 database.db "PRAGMA wal_checkpoint(TRUNCATE);"` on each DB; implement connection lifecycle management |
| OOM killer killed the gateway | MEDIUM | `systemctl --user restart openclaw-gateway.service`; DM Bob to re-establish session; add OOMScoreAdjust to both services; reduce Next.js memory cap |
| Hydration mismatch errors on every page | LOW | Extract all date rendering to `<RelativeTime>` client component; add `suppressHydrationWarning` as interim fix |
| Dashboard created empty .db files | LOW | `rm` the empty files; add `readonly: true` and file-existence check; restart dashboard |
| Disk full from WAL + logs | MEDIUM | Delete WAL files (they'll be recreated); truncate Next.js logs; implement log rotation; add WAL checkpoint timer |
| Next.js process died silently | LOW | Create systemd service; enable it; start it; verify with `systemctl --user status mission-control.service` |
| observability.db locking blocks hook writes | MEDIUM | Dashboard stops querying observability.db directly; implement a 1-minute cache; increase hook busy_timeout to 10 seconds |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| SQLITE_BUSY from concurrent access (Pitfall 1) | Phase 1 (DB layer) | `PRAGMA journal_mode` returns `wal` for all 5 databases; `PRAGMA busy_timeout` returns non-zero |
| WAL checkpoint starvation (Pitfall 2) | Phase 1 (DB layer) | WAL files stay under 10MB after 24 hours of operation |
| OOM on t3.small (Pitfall 3) | Phase 1 (infra) | `free -h` shows <500MB swap usage with dashboard + gateway + Docker running |
| Hydration mismatch on dates (Pitfall 4) | Phase 1 (UI foundation) | Zero React hydration errors in browser console; `<RelativeTime>` component exists |
| Schema mismatch / empty DB creation (Pitfall 5) | Phase 1 (DB layer) | Dashboard shows "not initialized" message for missing DBs; no 0-byte .db files created |
| Loss of real-time from Convex removal (Pitfall 6) | Phase 2 (activity feed) | Polling interval configured; data freshness indicator visible; Convex removed only after verification |
| Tailscale binding exposure (Pitfall 7) | Phase 1 (infra) | `curl http://<public-ip>:3001` returns connection refused; UFW rule verified |
| observability.db write contention (Pitfall 8) | Phase 3 (agent views) | No SQLITE_BUSY errors during morning briefing; observability queries cached |
| Process dies without systemd (Pitfall 9) | Phase 1 (infra) | `systemctl --user status mission-control` shows active; service survives SSH disconnect |
| Five DB connections multiply overhead (Pitfall 10) | Phase 1 (DB layer) | `process.memoryUsage()` under 200MB with all connections; route-based connection selection implemented |

---

## Sources

- [SQLite WAL Mode Official Documentation](https://sqlite.org/wal.html) -- checkpoint starvation warning, concurrent access model (HIGH confidence)
- [SQLite Busy Timeout API Reference](https://sqlite.org/c3ref/busy_timeout.html) -- per-connection pragma, default 0, retry behavior (HIGH confidence)
- [better-sqlite3 Performance Documentation](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/performance.md) -- WAL mode recommendation, synchronous driver behavior (HIGH confidence)
- [better-sqlite3 API Documentation](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md) -- readonly flag, Database constructor options (HIGH confidence)
- [Next.js Memory Usage Guide](https://nextjs.org/docs/app/guides/memory-usage) -- max-old-space-size, preloadEntriesOnStart, cacheMaxMemorySize (HIGH confidence)
- [Next.js Self-Hosting Guide](https://nextjs.org/docs/app/guides/self-hosting) -- standalone output, environment configuration (HIGH confidence)
- [Next.js Hydration Error Documentation](https://nextjs.org/docs/messages/react-hydration-error) -- server/client mismatch causes and fixes (HIGH confidence)
- [SQLite Checkpoint Starvation Forum Thread](https://sqlite.org/forum/info/7da967e0141c7a1466755f8659f7cb5e38ddbdb9aec8c78df5cb0fea22f75cf6) -- real-world reports of WAL growth (MEDIUM confidence)
- [SQLITE_BUSY Despite Setting Timeout](https://berthub.eu/articles/posts/a-brief-post-on-sqlite3-database-locked-despite-timeout/) -- deferred transaction upgrade deadlock (MEDIUM confidence)
- [SQLite Performance Tuning -- phiresky](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/) -- WAL, busy_timeout, cache_size recommendations (MEDIUM confidence)
- [Fly.io: How SQLite Scales Read Concurrency](https://fly.io/blog/sqlite-internals-wal/) -- WAL internals, checkpoint behavior (MEDIUM confidence)
- [Next.js Memory Issues -- GitHub Discussion #65908](https://github.com/vercel/next.js/discussions/65908) -- baseline requirements for self-hosting (MEDIUM confidence)
- [Taming Next.js on a Budget](https://medium.com/@piash.tanjin/taming-next-js-0a71e29fbb61) -- low-memory server optimization strategies (MEDIUM confidence)
- [Next.js High Memory Usage -- Issue #79588](https://github.com/vercel/next.js/issues/79588) -- production build memory spikes (MEDIUM confidence)
- [SQLite on Networked Storage -- GoToSocial](https://docs.gotosocial.org/en/latest/advanced/sqlite-networked-storage/) -- EBS filesystem considerations (MEDIUM confidence)
- [High Performance SQLite -- Recommended Pragmas](https://highperformancesqlite.com/articles/sqlite-recommended-pragmas) -- comprehensive pragma configuration guide (MEDIUM confidence)
- Project MEMORY.md -- "Hydration fix: new Date() deferred to client-side via useEffect" (confirmed project-specific pitfall)
- Project MEMORY.md -- "OOM protection: OOMScoreAdjust=-900 on tailscaled and sshd" (confirmed project-specific configuration)
- Project MEMORY.md -- "Disk: EC2 at ~55% (13GB free of 30GB)" (confirmed resource constraint, though NOTE: EBS is 40GB per PROJECT.md)

---
*Pitfalls research for: pops-claw v2.5 Mission Control Dashboard*
*Researched: 2026-02-20*
