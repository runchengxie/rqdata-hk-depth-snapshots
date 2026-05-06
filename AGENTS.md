# AGENTS.md

## Project Scope

This project probes, downloads, validates, reconciles, aggregates, and emits RQData Hong Kong historical tick-depth snapshot data.

Project boundaries:

- It handles historical tick-depth snapshots.
- It does not rebuild order books.
- It does not process order-event streams.
- It does not simulate queue position.
- It does not provide live trading execution.

## Standard Commands

Install offline development dependencies:

```bash
uv sync --group dev
```

Run offline tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check .
```

Install live RQData extras when provider access is needed:

```bash
uv sync --extra rqdata --group dev
```

## Data Layout

The default raw layout is `symbol-date`:

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

The `batch` raw layout remains readable for historical compatibility. New downloads should use `symbol-date`; new `raw_layout=batch` downloads are deprecated and recorded in metadata.

## Quality Boundaries

- `health` checks raw tick data quality.
- `reconcile-daily` compares raw tick aggregates with an external daily reference asset.
- `raw-daily` is the preferred gate reference when daily data uses the same raw quote basis.
- `cross-clean` is for research clean asset coverage checks; numeric price or volume basis differences are recorded as `info`.
- `aggregate-daily` creates research-oriented daily features and quality flags.

## Large Data And OOM Rules

- Treat full-period tick downloads, health scans, aggregation, reconciliation, and asset emission as long I/O tasks.
- Keep raw layout at `symbol-date` for new downloads. It is the operational unit for resume, health diagnostics, aggregation, and low-memory scans.
- Prefer chunk sizes around `300MB-700MB` estimated quota for live RQData runs. Use `--resume`, `--continue-on-error`, quota guard, and audit output as the progress record.
- Before restarting a task that vanished without traceback, inspect the target output first:
  - `meta/download_*.json`
  - `audit/download_*.csv`
  - any `artifacts/reports/*.json`
  - `free -h`
  - `dmesg -T | tail`
  - `ps -eo pid,ppid,stat,etime,pcpu,pmem,args`
- A silent shell or Codex session disappearance should be treated as possible OOM until ruled out by logs or kernel messages.
- Avoid ad hoc whole-cache reads of raw tick parquet directories in agents or scripts. Use the CLI/reporting entry points, which scan raw parquet parts incrementally.
- `health`, `aggregate-daily`, `reconcile-daily`, and raw `emit-asset` should keep peak memory close to one parquet part plus compact diagnostics or daily rows.
- For very large pools, write reports to `artifacts/reports/` and inspect the JSON/CSV outputs after completion. Do not depend on interactive stdout as the only record.
- If a run fails during health, aggregation, reconciliation, or asset emission, reduce the task by date or symbol first and preserve the existing raw cache for resume.

## Documentation Sync Rules

- Update README and docs when CLI arguments, output layout, metadata, audit fields, or quality checks change.
- Keep README short and link detailed docs from `docs/`.
- Keep dated account-specific quota, provider behavior, download coverage, or sample estimates under `docs/records/`.
- Keep stable docs organized around `docs/workflow.md`, `docs/data-contracts.md`, `docs/quality-gates.md`, `docs/providers-rqdata.md`, and `docs/development.md`.
- Keep copied provider API snapshots under `docs/vendor/` and avoid presenting them as project support scope.
- Do not add secrets, local credentials, or private tokens to docs, tests, metadata examples, or code.
