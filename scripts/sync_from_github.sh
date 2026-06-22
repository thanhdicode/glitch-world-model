#!/usr/bin/env bash
# sync_from_github.sh — Pull the latest code from the configured GitHub remote.
#
# Usage:
#   bash scripts/sync_from_github.sh [--remote REMOTE] [--branch BRANCH] [--dry-run]
#
# Options:
#   --remote REMOTE   Git remote name (default: origin)
#   --branch BRANCH   Branch to sync from (default: current branch)
#   --dry-run         Show what would happen without making any changes
#
# Safety rules enforced by this script:
#   1. Refuses to run with uncommitted local changes unless --dry-run.
#   2. Prints the before/after commit SHAs for auditing.
#   3. Validates that no data files, credentials, or outputs leak in (per CONVENTIONS.md).

set -euo pipefail

REMOTE="origin"
BRANCH=""
DRY_RUN=false
ALLOW_DIRTY=false

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)       REMOTE="$2"; shift 2 ;;
    --branch)       BRANCH="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    --allow-dirty)  ALLOW_DIRTY=true; shift ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--remote REMOTE] [--branch BRANCH] [--dry-run] [--allow-dirty]" >&2
      exit 1
      ;;
  esac
done

# --- Resolve branch ---
if [[ -z "$BRANCH" ]]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

echo "=== Replit → GitHub sync ==="
echo "Remote : $REMOTE"
echo "Branch : $BRANCH"
echo "Dry run: $DRY_RUN"
echo ""

# --- Safety: check for uncommitted changes ---
if ! git diff --quiet || ! git diff --cached --quiet; then
  if [[ "$DRY_RUN" == true ]]; then
    echo "[WARN] Uncommitted local changes detected (dry-run; continuing)."
  elif [[ "$ALLOW_DIRTY" == true ]]; then
    echo "[WARN] Uncommitted local changes detected (--allow-dirty; continuing)."
    git status --short
  else
    echo "[ERROR] You have uncommitted local changes. Commit or stash them first." >&2
    echo "        Run with --dry-run to preview without making changes." >&2
    echo "        Run with --allow-dirty to skip this check." >&2
    git status --short
    exit 1
  fi
fi

# --- Record before-SHA ---
BEFORE_SHA=$(git rev-parse HEAD)
echo "Before SHA : $BEFORE_SHA"

# --- Fetch ---
echo ""
echo "Fetching $REMOTE/$BRANCH ..."
if [[ "$DRY_RUN" == true ]]; then
  echo "[DRY-RUN] Would fetch $REMOTE $BRANCH."
  REMOTE_SHA=$(git ls-remote "$REMOTE" "refs/heads/$BRANCH" | awk '{print $1}')
  if [[ -z "$REMOTE_SHA" ]]; then
    echo "[ERROR] Could not resolve $REMOTE refs/heads/$BRANCH — check remote URL and auth." >&2
    exit 1
  fi
  echo "Remote SHA : $REMOTE_SHA"
  if [[ "$BEFORE_SHA" == "$REMOTE_SHA" ]]; then
    echo "[DRY-RUN] Already up to date. Nothing would change."
  else
    AHEAD=$(git rev-list --count "$REMOTE_SHA" ^HEAD 2>/dev/null || echo "?")
    echo "[DRY-RUN] $AHEAD new commit(s) would be merged into $BRANCH."
  fi
  echo "[DRY-RUN] No changes applied."
  exit 0
fi

git fetch "$REMOTE" "$BRANCH"

REMOTE_SHA=$(git rev-parse "$REMOTE/$BRANCH")
echo "Remote SHA : $REMOTE_SHA"

if [[ "$BEFORE_SHA" == "$REMOTE_SHA" ]]; then
  echo ""
  echo "Already up to date. Nothing to do."
  exit 0
fi

# --- Clean stale git lock files ---
GIT_DIR=$(git rev-parse --git-dir)
for lockfile in ORIG_HEAD.lock MERGE_HEAD.lock index.lock; do
  if [[ -f "$GIT_DIR/$lockfile" ]]; then
    echo "[INFO] Removing stale lock file: $GIT_DIR/$lockfile"
    rm -f "$GIT_DIR/$lockfile"
  fi
done

# --- Merge (fast-forward preferred, fallback to merge commit) ---
echo ""
echo "Merging $REMOTE/$BRANCH into $BRANCH ..."
if git merge --ff-only "$REMOTE/$BRANCH" 2>/dev/null; then
  echo "Fast-forward merge succeeded."
else
  echo "[INFO] Branches have diverged — fast-forward not possible."
  echo "       Falling back to merge commit ..."
  if ! git merge --no-edit -m "sync: merge $REMOTE/$BRANCH into $BRANCH" "$REMOTE/$BRANCH"; then
    echo "" >&2
    echo "[ERROR] Merge failed — likely a conflict that requires manual resolution." >&2
    echo "        Resolve conflicts, commit, then re-run this script." >&2
    exit 1
  fi
  echo "Merge commit created successfully."
fi

AFTER_SHA=$(git rev-parse HEAD)
echo ""
echo "=== Sync complete ==="
echo "Before SHA : $BEFORE_SHA"
echo "After  SHA : $AFTER_SHA"
echo ""

# --- Validate no forbidden files snuck in ---
FORBIDDEN_PATTERNS=(
  "\.lance$"
  "\.ckpt$"
  "\.pt$"
  "\.pth$"
  "kaggle\.json"
  "\.env$"
  "scores\.csv$"
  "metrics\.json$"
)

echo "Checking for forbidden file types introduced by this merge ..."
CHANGED_FILES=$(git diff --name-only "$BEFORE_SHA" "$AFTER_SHA")
VIOLATIONS=()
for file in $CHANGED_FILES; do
  for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if echo "$file" | grep -qE "$pattern"; then
      VIOLATIONS+=("$file (matches /$pattern/)")
    fi
  done
done

if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
  echo "" >&2
  echo "[WARN] The following files match forbidden patterns (check CONVENTIONS.md):" >&2
  for v in "${VIOLATIONS[@]}"; do
    echo "  - $v" >&2
  done
  echo "Review and remove them before committing research outputs." >&2
else
  echo "No forbidden files detected. ✓"
fi

echo ""
echo "Files changed in this sync:"
git diff --name-only "$BEFORE_SHA" "$AFTER_SHA" | sed 's/^/  /'
