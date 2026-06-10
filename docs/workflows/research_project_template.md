# Research Project Template

## Suggested Structure

```text
.
|-- AGENTS.md
|-- configs/
|-- docs/research/
|   |-- claim_registry.md
|   `-- experiment_protocol.md
|-- docs/workflows/
|-- paper/
|   |-- figures/
|   `-- tables/
|-- scripts/
|-- src/
|-- tests/
|-- .github/workflows/
|-- .pre-commit-config.yaml
`-- pyproject.toml
```

## Required Governance

AGENTS.md must define project identity, current evidence, prohibited claims, data/checkpoint
policy, experiment gates, verification commands, and final reporting. The claim registry uses:
`verified`, `experiment-pending`, `citation-needed`, `rejected`, and `future-work`.

## Release Gates

1. Protocol and dataset gate.
2. Validation selection gate.
3. Explicit locked-test gate.
4. Claim and artifact validation gate.
5. Tests, lint, formatting, CI, and paper checks.

## Artifact Policy

Track code, docs, configs, tests, small summary tables, and paper source. Ignore raw data,
processed data, outputs, checkpoints, credentials, caches, and experiment-tracker stores.

## Codex Prompt Template

```text
Read AGENTS.md, roadmap, claim registry, and current Git state.
Do not touch locked test, run GPU training, upload data, or change scientific claims unless the
task explicitly opens those gates. Implement with tests first. Run the required verification,
audit tracked files, update claims/docs honestly, and report evidence plus remaining risks.
```
