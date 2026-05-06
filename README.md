# RQData HK Tick Depth Lab

Standalone tooling for probing, downloading, validating, and aggregating RQData Hong Kong historical tick snapshots with ten-level bid/ask depth.

This project treats RQData HK tick data as historical tick-depth snapshots, not as a complete order-level Level 2 feed. It does not reconstruct order books, consume order events, simulate queue position, or provide live execution tooling.

## Install

```bash
uv sync --group dev
```

Install the optional RQData dependency when you want to call the live provider:

```bash
uv sync --extra rqdata --group dev
```

Credentials can come from your local `rqdatac` configuration or environment variables documented in `.env.example`.

## Probe-First Workflow

Start small and measure entitlement, fields, row counts, and disk footprint before scaling:

1. One symbol, one day.
2. Several symbols, one day.
3. Several symbols, one month.
4. Larger datasets only after health checks and aggregation are stable.

Example probe:

```bash
rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

Example dry-run download plan:

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --batch-size 2 \
  --dry-run
```

Example resumable download:

```bash
rqdata-tick download \
  --symbols-file symbols.txt \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --batch-size 5 \
  --resume
```

New raw downloads default to a symbol-date layout:

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

Resume validates readable parquet contents, requested fields, symbol identity, and trading date
before skipping local data. This makes incremental reruns safe for adding symbols or repairing
bad parts without redownloading already valid symbol-date units.

The legacy batch layout remains available for compatibility:

```bash
rqdata-tick download \
  --symbols-file symbols.txt \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --raw-layout batch
```

Parquet output uses explicit writer settings. The default is pyarrow + snappy, which is a good
download and research-stage default. Use zstd only after benchmarking a representative tick
sample for file size, write time, and read time:

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --compression zstd \
  --compression-level 3
```

Example health check:

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/hk_probe
```

Example daily aggregation:

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/hk_probe/data.parquet
```

Example asset emission:

```bash
rqdata-tick emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --output artifacts/assets/rqdata/hk/tick_depth/hk_probe

rqdata-tick emit-asset \
  --kind daily \
  --source artifacts/cache/rqdata/hk_tick_depth_daily/hk_probe/data.parquet \
  --output artifacts/assets/rqdata/hk/tick_depth_daily/hk_probe
```

## Downstream Use

Raw tick parquet parts are an inspection and calibration asset. Low-frequency research pipelines should consume daily aggregate outputs such as spreads, depth, imbalance, and VWAP features instead of raw snapshots.

Any same-day daily aggregate used for predictive modeling must be lagged or otherwise point-in-time controlled. The safest initial use is execution-cost calibration and liquidity filtering.
