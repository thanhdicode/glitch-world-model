# WOB Protocol Metadata

This directory contains tracked, small protocol metadata required for Kaggle-native `WOB-P0`
audit execution without depending on ignored `outputs/gate3/world_of_bugs/` files.

Included files:

- `split.csv`
- `protocol_audit.json`
- `split.audit.json`
- `split.provenance.json`

These files are copied from the existing frozen World of Bugs protocol outputs and contain metadata
only. They do not contain raw episode payloads, do not materialize locked media, and do not open
locked-test access. Rows marked `split=test` remain metadata-only and must stay excluded by runner
scripts.
