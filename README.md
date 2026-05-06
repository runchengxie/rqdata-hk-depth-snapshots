# RQData 港股十档 Tick 数据下载工具

本项目是一个独立的工具集，专门用于探查、下载、校验和聚合带有十档买卖深度的 RQData 港股历史 Tick 快照数据。

**注意**：本项目将 RQData 的港股 Tick 数据视为**历史 Tick 深度快照**，而非完整的逐笔订单 L2（Level 2）行情数据流。因此，本工具**不会**重建订单簿、处理订单事件、模拟排队位置，也不提供实盘交易执行工具。

## 安装

```bash
uv sync --group dev
```

如果需要调用线上数据源，请安装包含 RQData 的可选依赖：

```bash
uv sync --extra rqdata --group dev
```

API 认证信息可以通过本地的 `rqdatac` 配置获取，也可以通过环境变量配置（具体请参考 `.env.example` 文件）。

线上下载前先查看 quota：

```bash
rqdata-tick quota --pretty
```

下载规模、quota 和分批策略的现场估算记录见
[`docs/playbooks/hk-tick-download-sizing.md`](docs/playbooks/hk-tick-download-sizing.md)。

## “探查先行”工作流

在进行大规模下载前，建议先从小数据量试水，以评估你的账号数据权限、可用字段、数据行数以及磁盘占用情况，再逐步扩大规模：

1. 单只标的，单日数据。
2. 多只标的，单日数据。
3. 多只标的，单月数据。
4. 在数据健康检查通过且聚合逻辑稳定后，再扩展至更大规模的数据集。

探查（Probe）示例：

```bash
rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

模拟下载预演（Dry-run）示例：

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --batch-size 2 \
  --dry-run
```

断点续传下载示例：

```bash
rqdata-tick download \
  --symbols-file symbols.txt \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --batch-size 5 \
  --resume
```

下载命令会为每次 run 生成 chunk/unit 级审计表，默认写入：

```text
<output>/audit/download_<timestamp>_<run>.csv
```

审计表按 `trade_date + order_book_id` 记录 `written`、`skipped_existing`、`empty_remote`、`failed`、`quota_blocked` 等状态，并记录可用时的 `quota_before`、`quota_after` 和 `quota_delta`。`download_*.json` metadata 会引用 audit 路径并汇总各状态数量。

线上大规模下载建议打开默认 quota guard，并为 retry/backoff 留出配置：

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

当最近 chunk 的实测 quota delta 推断下一个 chunk 可能接近当日阈值时，系统会跳过 provider 请求并把对应 unit 标记为 `quota_blocked`，方便下一天直接续跑。

`--symbols` 和 `--symbols-file` 会把 `700`、`00700.HK`、`00700.XHKG` 统一规范成 RQData 的 `00700.XHKG`。符号文件支持 TXT、CSV 和 Parquet；表格文件会优先读取 `order_book_id`、`symbol`、`stock_ticker` 或 `ts_code` 列，方便复用 cross 项目的 universe/symbol 产物。

真实 provider 下载时，默认使用 RQData 港股交易日历，只对交易日发请求，避免周末和休市日空请求消耗 quota。离线预演如果不想初始化 provider，可以显式使用自然日：

```bash
rqdata-tick download \
  --symbols 00001.XHKG \
  --start-date 20250301 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/weekend_probe \
  --dry-run \
  --calendar calendar
```

Tick 深度数据默认按 `adjust_type=none` 拉取，保留盘口原始报价口径；如确实需要复权口径，可以显式传入 `--adjust-type pre` 等 RQData 支持的取值。

全新的原始数据下载默认采用按“标的-日期”划分的目录结构：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

在跳过本地已有数据之前，断点续传（Resume）机制会严格校验 Parquet 文件的可读性、请求的字段、标的代码以及交易日期。这保证了增量重跑的绝对安全——无论是追加新标的，还是修复损坏的数据分片，都不会去重复下载那些已经校验合格的“标的-日期”单元。

为了保持向后兼容，旧版的批处理目录结构依然可用：

```bash
rqdata-tick download \
  --symbols-file symbols.txt \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --raw-layout batch
```

Parquet 文件的输出使用了明确的写入配置。默认采用 `pyarrow + snappy` 压缩，这是适用于下载和投研阶段的优秀默认组合。如果你打算使用 `zstd` 压缩，建议先提取具有代表性的 Tick 样本，对文件大小、读写时间进行基准测试后，再做决定：

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250307 \
  --out artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --compression zstd \
  --compression-level 3
```

数据健康检查示例：

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/hk_probe
```

如果希望把重复 tick、盘口交叉、累计成交量回落等 warning 也作为门禁失败：

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --fail-on-severity warning
```

Tick 与 cross 日频资产对账示例：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir /home/richard/code/cross-sectional-hk-tree/artifacts/assets/rqdata/hk/daily/hk_all_2000_20260504_daily_clean_refetched_latest \
  --out artifacts/reports/tick_daily_reconcile_core.json \
  --fail-on-severity warning
```

`reconcile-daily` 会只读 raw tick 和外部 daily clean asset，不会复制或修改 cross 日频资产，也不会覆盖 raw tick。报告会检查 tick 聚合出的 close、累计 volume、累计 total_turnover 是否能和日频数据对上，并检查 OHLC 边界、盘口档位规则和港股 session 时间异常。

日度数据聚合示例：

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/hk_probe \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/hk_probe/data.parquet
```

数据资产导出 (Asset Emission) 示例：

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

raw 和 daily asset 输出都会包含 `manifest.yml`、`meta.json`、`symbols.txt` 和 `fields.txt`，便于后续脚本稳定引用。

## 下游应用建议

原始的 Tick Parquet 数据分片主要作为数据核查与校准的基础资产。对于低频量化研究流水线，建议直接使用日度聚合后的输出结果（例如买卖价差 Spread、深度 Depth、订单不平衡量 Imbalance 以及 VWAP 特征等），而不是直接去处理海量的原始快照。

**核心提示**：在预测模型中引入任何同日的日度聚合数据时，必须进行滞后处理（Lag）或引入严格的时间点（Point-in-Time）控制，以杜绝未来函数。最安全、最基础的首选应用场景，是将其用于**交易成本测算**和**流动性过滤**。
