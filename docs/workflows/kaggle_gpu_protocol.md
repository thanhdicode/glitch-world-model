# Kaggle GPU Protocol

1. Keep `kaggle.json` outside the repository and never print credentials.
2. Dry-run data/package/protocol checks locally.
3. Scan the upload package for credentials and prohibited files.
4. Require a fingerprint-bound approval before private dataset upload.
5. Require a separate fingerprint-bound approval before each GPU kernel push.
6. Poll without duplicate pushes; download only required artifacts.
7. Validate artifacts locally before making claims.
8. Never touch locked test unless its release gate is explicitly opened.

No Kaggle upload, kernel push, or GPU training is authorized by documentation changes alone.
