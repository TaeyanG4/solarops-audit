# SolarOps Audit

The user's current request authorizes completing the project and installing required
tools/data. The archived plan's M0-only example and per-stage stop wording do not
limit this request. Keep its technical acceptance gates and report actual evidence.

- Preserve original files and raw data. Ask the user before sensitive/destructive deletion.
- The user authorized a GitHub repository and code pushes. Keep it private unless requested otherwise.
- No customer data, external messages, paid services or public service deployment.
- Use Python 3.12, locked dependencies, shared CLI for Airflow and Kubernetes.
- Preserve interpolation/sample counts and source lineage. Energy is estimated;
  performance flags are review candidates, never confirmed failures or financial losses.
- Publish only complete validated partitions; org scope applies to all storage/queries.
- Offline tests must never fetch the full dataset. Never commit secrets or raw datasets.
- Test parsing, duplicate conflicts, UTC, missing slots, replay and failed publication.
- Distinguish executed checks from unverified infrastructure and business hypotheses.

## Planning and continuity (user requested)

- Read AGENTS.md, discoveries.md, handoff.md, then plan.md when resuming.
- Keep plan.md as the active scored queue, discoveries.md as findings/evidence,
  and handoff.md as shared state, append-only completed events and the resume point.
- Score each factor 0–3: Priority = 2*Impact + 2*Information + Confidence +
  Unblock + Diversity + (3-Cost). Work highest eligible score first; ties use
  lower Cost, then higher Information. Explain dependency-based deferrals.
- Finish with evidence, log the result, remove completed queue entries and rescore
  affected work. Keep actual test results separate from independent review status.
- Use slot A for this single-agent workflow. Do not create agents merely to fill slots.
- Existing AGENTS.md is the stable rules file (agents.md resolves here on Windows);
  preserve this Git spelling for Codex/Linux rather than create a case-only duplicate.
