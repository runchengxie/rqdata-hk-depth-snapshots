# RQData 港股十档 Tick 数据下载工具

本项目用于探查、下载、校验、对账和聚合 RQData 港股历史 Tick 深度快照数据。项目边界很明确：它处理历史快照数据，不重建订单簿，不处理逐笔订单事件，不模拟排队位置，也不提供实盘交易执行功能。

## 安装

离线开发和测试：

```bash
uv sync --group dev
```

运行测试和 lint：

```bash
uv run pytest
uv run ruff check .
```

调用真实 RQData provider 时安装可选依赖：

```bash
uv sync --extra rqdata --group dev
```

测试和离线 CLI smoke 使用 `FakeProvider`，不需要 RQData 账号。真实 provider 使用本地 `rqdatac` 配置或环境变量认证。

线上下载前先查看 quota：

```bash
rqdata-tick quota --pretty
```

## 常用流程

单标的单日 probe：

```bash
rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

离线下载演示：

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

线上分批下载：

```bash
rqdata-tick download \
  --symbols-file symbols_core.txt \
  --start-date 20250401 \
  --end-date 20260506 \
  --out artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --batch-size 5 \
  --retry-max-attempts 3 \
  --retry-backoff-seconds 2 \
  --quota-stop-ratio 0.95 \
  --quota-safety-multiplier 1.2 \
  --resume
```

`--symbols` 和 `--symbols-file` 会把 `700`、`00700.HK`、`00700.XHKG` 统一成 RQData 的 `00700.XHKG`。符号文件支持 TXT、CSV 和 Parquet。

## 输出布局

默认 raw layout 是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

断点续传会在跳过本地文件前校验 parquet 可读性、字段、标的和交易日期。历史 batch layout 仍可读取：

```text
parts/trade_date=YYYYMMDD/batch_0000.parquet
```

新下载建议使用 `symbol-date`。`--raw-layout batch` / `raw_layout=batch` 已标记为 deprecated，metadata 会记录替代布局。

每次下载会生成 metadata 和 audit：

```text
<output>/meta/download_<timestamp>.json
<output>/audit/download_<timestamp>_<run>.csv
```

audit 按 `trade_date + order_book_id` 记录 `written`、`skipped_existing`、`empty_remote`、`failed`、`quota_blocked` 等状态。

## 数据质量

raw tick health：

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --fail-on-severity warning \
  --out-units artifacts/reports/tick_health_units.csv
```

`health` 会输出数据集级 summary，并可写出 symbol-date 级诊断。检查范围包括 timestamp、重复 key、同 timestamp 冲突、盘口阶梯、负深度量、累计成交量/成交额回落、session phase 等。

日频聚合：

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet
```

聚合结果包含价差、深度、订单不平衡、VWAP 和质量标记，例如 `quote_quality_flag`、`vwap_quality_flag`、`is_usable_for_research`。

## Tick 与日频对账

下载质量门禁建议使用同报价口径的 raw daily reference：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_raw/hk_tick_gate_20250401_20260506 \
  --out artifacts/reports/tick_daily_reconcile_raw_gate.json \
  --reference-policy raw-daily \
  --fail-on-severity warning
```

与 cross daily clean 研究底座做覆盖检查时使用 `cross-clean`：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir /home/richard/code/cross-sectional-hk-tree/artifacts/assets/rqdata/hk/daily/hk_all_2000_20260504_daily_clean_refetched_latest \
  --out artifacts/reports/tick_daily_reconcile_cross_clean.json \
  --reference-policy cross-clean \
  --fail-on-severity warning
```

`cross-clean` 会把价格、成交量、成交额的口径差异记录为 `info`。覆盖缺口仍按 warning 进入门禁。

## Asset 输出

```bash
rqdata-tick emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/assets/rqdata/hk/tick_depth/demo

rqdata-tick emit-asset \
  --kind daily \
  --source artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet \
  --output artifacts/assets/rqdata/hk/tick_depth_daily/demo
```

asset 目录包含 `manifest.yml`、`meta.json`、`symbols.txt` 和 `fields.txt`。

## 文档

详细说明见 [docs/README.md](docs/README.md)：

- [CLI reference](docs/cli.md)
- [Data layout](docs/data-layout.md)
- [Quality checks](docs/quality-checks.md)
- [Reconciliation](docs/reconciliation.md)
- [Providers](docs/providers.md)
- [Testing](docs/testing.md)
- [Terminology](docs/terminology.md)
- [下载规模估算快照](docs/playbooks/hk-tick-download-sizing.md)

低频量化研究建议使用日度聚合结果，并对同日聚合特征做 lag 或严格 point-in-time 控制。raw tick parquet 主要作为审计、校准和重新聚合的基础资产。
