---
name: LAST_HANDOFF.md structure rules
description: Required headings, forbidden content, and validation rules for docs/context/LAST_HANDOFF.md enforced by scripts/update_context_cache.py context_validation_errors().
---

## Required headings (all must appear verbatim)
- `Last completed task:`
- `Commit:`
- `Date:`
- `## What Changed`
- `## Checks Passed`
- `## Safety Status`
- `## Gate Status After Task`
- `## Open Blockers`
- `## Next Recommended Task`
- `## Files Likely Relevant Next`

## Forbidden content (causes validation error)
- Any TEXT_CREDENTIAL_PATTERNS: `kaggle.json`, `access_token`, `api_key`, `private_key`, `id_rsa`, `id_ed25519` (case-insensitive match on lowercased text)
- Any `outputs/` path reference (the word `outputs/` anywhere in the file)

**Why:** `scripts/update_context_cache.py::context_validation_errors()` enforces these rules for LAST_HANDOFF.md and REPO_MAP.md. The validator lowercases the text before pattern matching. `outputs/` restriction prevents agents from treating gitignored output paths as durable context.

**How to apply:** Before writing LAST_HANDOFF.md, check: (1) all headings present, (2) no `kaggle.json` or similar words, (3) replace any `outputs/r5_...` paths with generic descriptions like "R5 output directory".
