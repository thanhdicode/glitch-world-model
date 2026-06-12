# Kaggle GPU Protocol

1. Keep `kaggle.json` outside the repository and never print credentials.
2. Dry-run data/package/protocol checks locally.
3. Scan the upload package for credentials and prohibited files.
4. Use standing authorization for non-locked-test dataset and kernel actions after validation.
5. Record content fingerprints as audit and idempotency keys.
6. Poll without duplicate pushes; download only required artifacts.
7. Validate artifacts locally before making claims.
8. Public release additionally requires a license, redistribution permission, and locked-test scan.
9. Never touch locked test without a separate direct user command.

Remote deletion, credential publication, unlicensed public data, and validator bypass are not
authorized.
