# SolarOps Audit — Codex repository instructions

Before making changes, read `00_START_HERE.md`, `01_MASTER_PRD.md`, and `02_CODEX_EXECUTION.md` (or their equivalents in `docs/plan/`).

## Operating rules
- Work on **one M-stage at a time** and stop after tests; do not implement the entire backlog in one run.
- Inspect `git status` and existing project structure. Never overwrite unrelated project files or delete user data without approval.
- Primary target: Python 3.12, Linux/WSL2, pinned dependencies, offline fixtures for fast unit tests.
- Build a pure Python CLI first; Airflow should orchestrate this same CLI, not duplicate business logic.
- Airflow plus Kubernetes are requirements for the **portfolio build**. Production deployment remains cost-driven.
- Never invent source data, customer measurements, training labels, or the result of tests.
- BR-PVGen is a preprocessed historical dataset; preserve interpolated flag fields and source lineage.
- Treat alarms as **review candidates**, not confirmed equipment faults; energy numbers are estimates.
- Don't automatically download large public archives, use customer files, or send data to a network destination without an explicit user command/permission.
- No credentials, `.env`, customer CSVs, dataset ZIPs, or sensitive logs in Git.
- All pipeline writes should be idempotent and version-aware; failed writes should not publish partial marts or reports.
- Separate application Postgres/MinIO from Airflow metadata DB; isolate Compose and kind environments.
- Make tests for key parsing, units, UTC timestamps, duplicates, source interpolation, late arrivals, failures and replays.
- Record commands actually executed, exit codes and test results. Be transparent about unrun checks.
- Finish a stage with `RESULT / CHANGES / VALIDATION / BLOCKERS / NEXT STAGE`.

## Stop and ask before
- Deploying to a public IP/domain, starting paid services, publishing to a public repository, or accessing customer data.
- Large irreversible schema migrations or destructive filesystem operations.
- Changing the validated source dataset or silently relaxing quality gates.
