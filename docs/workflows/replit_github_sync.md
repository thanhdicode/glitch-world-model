# Replit ↔ GitHub Sync Workflow

## Overview

This project lives on Replit with the GitHub integration active (`github==1.0.0`).
Replit manages its own version-control layer (checkpoints, task merges), while GitHub
holds the canonical shared history.  This document explains how to keep them in sync
and what to do when they diverge.

---

## Everyday Workflow

```
GitHub (remote)
   ↑ push / PR merge
   |
   ↓ make sync-github  (pull latest into Replit)
Replit (local edits → Replit checkpoints)
```

1. **Make changes on Replit** — edit code, run tests, iterate.
2. **Replit auto-commits** changes as checkpoints (platform-managed).
3. **Push to GitHub** via the GitHub integration UI or `git push origin <branch>`.
4. **Pull from GitHub** into Replit using the sync script below whenever the remote
   has changes you need locally (e.g. a PR was merged on GitHub by a collaborator).

---

## Pulling the Latest Code from GitHub

### One-command (Makefile)

```bash
make sync-github
```

This runs a safe fetch + fast-forward merge.  It will refuse to proceed if you have
uncommitted local changes, preventing accidental overwrites.

### Preview first (dry-run)

```bash
make sync-github-dry
# or
bash scripts/sync_from_github.sh --dry-run
```

Dry-run fetches metadata and prints what *would* change without touching local files.

### Full options

```bash
bash scripts/sync_from_github.sh [--remote REMOTE] [--branch BRANCH] [--dry-run]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--remote` | `origin` | Git remote name |
| `--branch` | current branch | Branch to sync from |
| `--dry-run` | off | Preview only, no changes applied |

---

## Safety Guarantees

The sync script enforces these rules automatically:

| Check | What it does |
|-------|--------------|
| **Dirty working tree** | Refuses to merge if uncommitted changes exist (dry-run overrides) |
| **Fast-forward only** | Uses `git merge --ff-only`; aborts if branches have diverged |
| **Before/after SHAs** | Prints both SHAs so every sync is auditable |
| **Forbidden file scan** | Warns if the merge introduced `.lance`, `.ckpt`, `.pt`, `.env`, `kaggle.json`, `scores.csv`, or `metrics.json` (per `CONVENTIONS.md`) |

---

## When Branches Diverge

If `make sync-github` fails with *"Fast-forward merge failed"*, the local and remote
histories have diverged.  Choose one of:

```bash
# Option A — rebase local commits on top of remote (keeps linear history)
git fetch origin
git rebase origin/main

# Option B — create a merge commit
git fetch origin
git merge origin/main
```

Resolve any conflicts, run the test suite, then re-run the sync script to verify.

---

## Pushing Local Changes to GitHub

Replit's GitHub integration provides a UI button for push/PR creation.  You can also
use the terminal:

```bash
git push origin main          # push current branch
git push origin HEAD:my-feat  # push to a named branch for a PR
```

> **Never push** raw data, processed outputs, Lance datasets, checkpoints, or
> credentials to GitHub (see `CONVENTIONS.md` and `.gitignore`).

---

## Recommended Dev Loop

```
┌─────────────────────────────────────────────┐
│  1. make sync-github          (start fresh)  │
│  2. Edit code on Replit                      │
│  3. make test && make lint                   │
│  4. git push origin <branch>  (share work)   │
│  5. Open PR on GitHub → review → merge       │
│  6. make sync-github          (loop)         │
└─────────────────────────────────────────────┘
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `sync_from_github.sh: uncommitted changes` | Local edits not committed | `git stash` or commit first |
| `Fast-forward merge failed` | Branches diverged | Rebase or merge manually (see above) |
| `git fetch` auth error | GitHub remote not configured | Check `git remote -v`; re-link via Replit GitHub integration |
| Forbidden files warning | Merge brought in outputs | Remove the files and amend/reset the commit |

---

## Related Files

- `scripts/sync_from_github.sh` — the sync script
- `Makefile` — `sync-github` and `sync-github-dry` targets
- `.github/workflows/ci.yml` — GitHub Actions CI (runs on every push/PR)
- `CONVENTIONS.md` — what must never be committed
- `.gitignore` / `.dvcignore` — ignored paths
