# Context Cache

Generated: 2026-06-24T08:15:50+00:00
Commit: `8853fc5de1ad85e0fe874f72a9a0ebcd745d01f3`

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
