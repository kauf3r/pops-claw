# Task 1 Results: Bun and gbrain Installation on EC2

**Executed:** 2026-04-15
**Status:** COMPLETE

## Installation Summary

### Bun Runtime
- **Version:** 1.3.12
- **Location:** ~/.bun/bin/bun
- **PATH:** Added to ~/.bashrc by installer

### gbrain CLI
- **Version:** 0.10.1
- **Repo:** ~/gbrain/ (cloned from garrytan/gbrain)
- **Symlink:** ~/.bun/bin/gbrain -> ../install/global/node_modules/gbrain/src/cli.ts
- **Dependencies:** 233 packages installed (PGLite 0.4.4, OpenAI SDK 4.104.0, etc.)

### Compiled Binary (Path A) - FAILED (PGLite WASM issue confirmed)
- **Binary:** ~/gbrain/bin/gbrain-linux-x64 (99MB standalone)
- **Build:** `bun build --compile --target=bun-linux-x64` completed in ~774ms
- **Version test:** `gbrain-linux-x64 --version` returned "gbrain 0.10.1" (works)
- **PGLite test:** `gbrain-linux-x64 search "..."` failed with `ENOENT: no such file or directory, open '/$bunfs/root/pglite.data'`
- **Status:** PATH A FAILED. Compiled binary cannot access PGLite WASM data files. Known bug confirmed (electric-sql/pglite#414, oven-sh/bun#15032).

**CRITICAL for Plan 02:** Path A (compiled binary) does NOT work for PGLite operations. Plan 02 MUST use Path B (Bun runtime bind-mount): bind-mount Bun binary + gbrain repo + wrapper script into Docker sandbox.
