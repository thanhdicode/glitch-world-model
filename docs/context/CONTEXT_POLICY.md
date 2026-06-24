# CONTEXT_POLICY.md

## Default Rule

Do not read the whole repo for routine tasks. Start with the fast context files, then follow
`TASK_ROUTER.md` and targeted `rg` searches.

## PLAYBOOK.md

`PLAYBOOK.md` is the long-form operating bible. Open it for roadmap, paper, claim, gate-status,
safety ambiguity, or stale-cache resolution. Do not auto-load it for every small code edit.
Use `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` as the current execution roadmap.

## Cache Maintenance

- Update `LAST_HANDOFF.md` at the end of each task.
- Run `python scripts/update_context_cache.py --refresh-boot` before final verification.
- Run `python scripts/validate_context_cache.py` before commit.
- If generated context conflicts with checked artifacts, trust the artifact and refresh context.

## Safety Visibility

Safety rules must remain visible in `BOOT.md`; reducing token use must not hide Kaggle,
locked-test, artifact, credential, or claim restrictions.

## Token Budget Target

Keep `BOOT.md` under 200 lines. Use `REPO_MAP.md` and `TASK_ROUTER.md` to select files rather
than reading broad directories.
