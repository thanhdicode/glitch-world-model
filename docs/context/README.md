# Context Cache

Generated: 2026-06-22T03:15:03+00:00
Commit: `3cc0929bbe7884c3ad856591a0dfc4428df550de`

This directory is the fast-start layer for coding agents. It keeps routine tasks from re-reading
the full repository and long playbook unless the task truly needs deep context.

## Files

- `BOOT.md`: first compact boot context.
- `PROJECT_STATE.md`: current gate and claim status.
- `NEXT_ACTION.md`: exactly one priority task.
- `LAST_HANDOFF.md`: latest completed-task handoff.
- `REPO_MAP.md`: generated repository and symbol map.
- `TASK_ROUTER.md`: task type to files-to-read map.
- `CONTEXT_POLICY.md`: maintenance and token-budget rules.

Regenerate with:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
```
