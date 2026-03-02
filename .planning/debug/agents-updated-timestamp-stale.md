---
status: diagnosed
trigger: "Investigate why the 'Updated X ago' timestamp on the Mission Control /agents page appears stale (showing '80s ago' instead of resetting after each SWR refresh)."
created: 2026-03-02T00:00:00Z
updated: 2026-03-02T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - SWR returns same object reference on re-fetch when data is unchanged, so the useEffect([data]) dependency never fires, so lastUpdated timestamp never resets, so FreshnessIndicator's interval keeps incrementing indefinitely
test: verified by reading all three files: agents/page.tsx, providers.tsx, freshness-indicator.tsx
expecting: N/A - root cause confirmed
next_action: return diagnosis

## Symptoms

expected: "Updated X ago" resets each time SWR refetches (every 30s), showing something like "0s ago" or "just now" after each refresh
actual: Shows "Updated 80s ago" — stale, not resetting after SWR refetch
errors: none reported
reproduction: open /agents page, observe the "Updated X ago" label over time
started: observed by user, unclear if always broken

## Eliminated

- hypothesis: FreshnessIndicator has no reactive interval (only updates on prop change)
  evidence: freshness-indicator.tsx line 14 — it does have a setInterval updating elapsed every 1s, restarted on lastUpdated change
  timestamp: 2026-03-02

- hypothesis: SWR refreshInterval is wrong
  evidence: providers.tsx line 15 — refreshInterval: 30000 is correctly set
  timestamp: 2026-03-02

- hypothesis: API route is cached / not refetching fresh data
  evidence: agents/route.ts line 3 — `export const dynamic = "force-dynamic"` ensures no SSR caching
  timestamp: 2026-03-02

## Evidence

- timestamp: 2026-03-02
  checked: agents/page.tsx lines 11-18
  found: |
    const [lastUpdated, setLastUpdated] = useState(Date.now());
    useEffect(() => {
      if (data) setLastUpdated(Date.now());
    }, [data]);
  implication: |
    The useEffect depends on the `data` object reference. It fires ONLY when
    `data` changes reference identity. SWR by default returns the *same object
    reference* when refetched data is deeply equal to the previous data. So if
    the agents data doesn't change between polls, `data` never gets a new
    reference, the useEffect never runs, setLastUpdated never fires, and
    lastUpdated stays frozen at the initial page-load time.

- timestamp: 2026-03-02
  checked: freshness-indicator.tsx lines 12-18
  found: |
    useEffect(() => {
      setElapsed(0);
      const interval = setInterval(() => {
        setElapsed(Math.floor((Date.now() - lastUpdated) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    }, [lastUpdated]);
  implication: |
    FreshnessIndicator correctly resets elapsed to 0 and restarts its interval
    whenever lastUpdated prop changes. BUT because lastUpdated never changes
    (see above), the interval keeps incrementing from the original page-load
    time indefinitely. The component itself is correct; the problem is upstream.

- timestamp: 2026-03-02
  checked: providers.tsx - SWR global config
  found: refreshInterval 30000, revalidateOnFocus true, dedupingInterval 5000
  implication: SWR IS refetching every 30s. The refetch happens but the data
    reference doesn't change, so the page-level useEffect doesn't notice.

## Resolution

root_cause: |
  Two interacting issues:

  1. PRIMARY: agents/page.tsx useEffect([data]) depends on SWR's `data`
     object reference. SWR reuses the same reference when re-fetched data is
     structurally identical to cached data (this is SWR's default behavior —
     it does NOT create a new object on every fetch). So when the agents data
     is stable between polls, the useEffect never fires and lastUpdated is
     never reset to Date.now().

  2. CONSEQUENCE: Because lastUpdated stays frozen at the time the page first
     loaded (or last changed data), FreshnessIndicator's elapsed counter keeps
     counting up indefinitely from that stale baseline. This produces values
     like "80s ago" even though SWR has been polling correctly every 30s.

  The fundamental design flaw: using a React state variable (`lastUpdated`)
  updated via `useEffect([data])` to track "when did SWR last fetch" is wrong.
  SWR provides dedicated callbacks for this: the `onSuccess` option fires on
  EVERY successful fetch, regardless of whether data changed. `useEffect([data])`
  fires only when React considers `data` a new value — which requires reference
  identity change, not just a successful network call.

fix: |
  Replace the useEffect approach with SWR's onSuccess callback, which fires on
  every successful revalidation:

  CURRENT (broken):
    const { data, error, isLoading } = useSWR<AgentBoardSummary>("/api/agents");
    useEffect(() => {
      if (data) setLastUpdated(Date.now());
    }, [data]);

  FIXED:
    const { data, error, isLoading } = useSWR<AgentBoardSummary>("/api/agents", {
      onSuccess: () => setLastUpdated(Date.now()),
    });
    // Remove the useEffect entirely

  This ensures lastUpdated resets on every successful SWR fetch, regardless
  of whether the returned data differs from the cached copy.

verification:
files_changed:
  - ~/clawd/mission-control/src/app/agents/page.tsx
