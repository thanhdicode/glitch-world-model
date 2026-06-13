# R3 Seed 42 Artifact Retrieval

After the cloud run completes, copy the output directory from the GPU VM:

```bash
rsync -avP "$LEWM_OUTPUT_ROOT/" ./r3_seed42_artifacts/
```

If using a remote host:

```bash
rsync -avP user@host:/workspace/lewm_outputs/r3_seed42/ ./outputs/r3_seed42_cloud_download/
```

Do not commit downloaded outputs, checkpoints, Lance datasets, or logs.
