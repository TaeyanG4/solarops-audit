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

## Proportionate validation (user requested)

- Do not add permanent regression tests or dedicated validation scripts by default
  for one-off, low-impact fixes such as UI styling or minor interactions. Prefer
  existing checks and a focused manual/browser check of the changed behavior.
- Add or extend regression coverage only when recurrence or impact justifies its
  maintenance cost, especially for data integrity, calculations, publication and
  security. Prefer extending a relevant existing test over creating another suite.
- Keep verification proportional to the change. Do not repeatedly run broad suites
  after relevant checks pass unless new changes, failures or unresolved risks warrant it.

## Planning and continuity (user requested)

- Read AGENTS.md, handoff.md, then plan.md when resuming; follow links to dated
  work logs only when their detail is relevant.
- This is software delivery, not research. Do not apply research-orchestrator-skill
  or require agent slots, hypotheses, discovery IDs, or independent-review queues.
- Keep plan.md for unfinished work, with priority scores and dependencies.
  Score each factor 0–3: Priority = 2*Impact + 2*Information + Confidence +
  Unblock + Diversity + (3-Cost). Work highest eligible score first; ties use
  lower Cost, then higher Information. Explain dependency-based deferrals.
- Keep handoff.md within 100 lines: current state, next action/blocker, and at
  most eight recent work summaries. Each summary links to its dated work log.
- Store detailed changes, decisions, commands, test results, limitations and
  evidence in docs/worklog/YYYY-MM-DD.md (Asia/Seoul). Summarize each work area
  in 3–6 lines; link existing benchmark/design documents instead of copying them.
  Split unusually large days into YYYY-MM-DD-topic.md and link the date index.
- Finish with actual evidence, update the handoff summary, and remove completed
  plan items. No mandatory research review status or discoveries.md maintenance.
- Preserve historical records under docs/worklog/archive/; they are historical
  evidence, not current instructions. Keep original data and docs/plan/ unchanged.
- Existing AGENTS.md is the stable rules file (agents.md resolves here on Windows);
  preserve this Git spelling rather than create a case-only duplicate.
