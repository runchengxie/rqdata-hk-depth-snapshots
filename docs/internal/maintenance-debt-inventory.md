# Maintenance Debt Inventory

Status date: 2026-05-06.

This inventory records cleanup targets that are allowed to exist temporarily while the project keeps CLI compatibility.

| Area | Current issue | Action | Verification |
| --- | --- | --- | --- |
| `src/rqdata_tick_data/downloader.py` | Large module with long symbol-date and legacy batch paths. | Keep public API stable, introduce `DownloadConfig`, and extract shared helpers before deeper splitting. | `tests/test_downloader_storage_cli.py`; maintainability contract test. |
| `_download_symbol_date_tick_depth` | Long function that owns resume, quota guard, retry, write, audit, and metadata updates. | Stage extraction into shared helpers and result objects. | Downloader tests and audit metadata tests. |
| `_download_batch_tick_depth` | Legacy layout path duplicates much of the symbol-date execution flow. | Keep compatibility, mark new batch downloads deprecated, and reduce duplicated helper behavior. | Legacy layout compatibility test and batch deprecation test. |
| `src/rqdata_tick_data/reconcile.py` | Long reconciliation function mixes raw checks, daily loading, merge checks, and verdict logic. | Move gate and quote checks to `quality.py`; keep future function splitting visible. | Reconciliation tests and quality gate tests. |
| `src/rqdata_tick_data/cli.py` | Parser and command dispatch live in one file. | Split dispatch into command handler functions while preserving CLI behavior. | CLI help and offline smoke tests. |
| `src/rqdata_tick_data/health.py` | Health checks were dataset-level and duplicated gate helpers. | Add symbol-date diagnostics and use shared quality helpers. | Health diagnostic tests. |
| `src/rqdata_tick_data/coverage.py` | `inspect_raw_part` is long because it validates parquet identity, schema, field coverage, and path consistency in one pass. | Keep listed for now; split if coverage validation expands. | Coverage and resume tests. |
| `project_tools/export_repo_source.py` | Maintenance/export utility, not runtime behavior. | Keep in `project_tools/` and document as maintenance-only. | Docs contract test. |
| `project_tools/package.sh` | Maintenance packaging utility, not runtime behavior. | Keep in `project_tools/` and document as maintenance-only. | Docs contract test. |
| `SchemaError` | Unused exception class. | Removed. | `rg SchemaError` returns no runtime references. |
| `cache_dataset_root` | Unused storage helper. | Removed. | `rg cache_dataset_root` returns no runtime references. |

The maintainability test reports large functions and fails only when they are not listed here. That keeps the debt visible without forcing a risky rewrite in the same change that improves data-quality behavior.
