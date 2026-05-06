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

## Documentation Sync Rules

- Update README and docs when CLI arguments, output layout, metadata, audit fields, or quality checks change.
- Keep README short and link detailed docs from `docs/`.
- Keep playbooks dated when they include account-specific quota, provider behavior, or sample estimates.
- Do not add secrets, local credentials, or private tokens to docs, tests, metadata examples, or code.
