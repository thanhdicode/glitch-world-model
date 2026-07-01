# Context Cache

Generated: 2026-07-01T09:13:08+00:00
Commit: `5be9ede79fde67c04390b68af05c71cc558f097d`

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
