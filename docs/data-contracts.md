# 数据契约

本页描述项目读写的稳定文件契约。字段级研究语义见 [术语表](terminology.md)，命令参数见 [CLI 参考](cli.md)。

## Raw Cache

默认 raw layout 是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

这个布局以一个标的、一个交易日为最小操作单元。下载器在 `--resume` 跳过本地文件前会校验：

- parquet 可读性。
- 必要字段存在。
- `order_book_id` 与路径一致。
- `trade_date` 与路径一致。
- 请求字段覆盖本地文件字段。

## Legacy Batch

历史 batch layout：

```text
parts/trade_date=YYYYMMDD/batch_0000.parquet
```

该布局保留读取兼容。新下载应使用 `symbol-date`；新 `--raw-layout batch` / `raw_layout=batch` 下载会在 metadata 的 `deprecations` 字段记录提示。

## Download Metadata

每次 `download` 写出：

```text
meta/download_<timestamp>.json
```

metadata 记录：

- 请求参数：symbols、dates、fields、batch size、raw layout、calendar、parquet 配置。
- provider 类型和 retry 配置。
- quota guard 配置和 quota snapshot。
- 下载计划和交易日范围。
- 状态统计：`written`、`skipped_existing`、`empty_remote`、`failed`、`quota_blocked`。
- audit 文件路径。
- deprecations 和错误摘要。

metadata 是恢复和复核下载进度的主要记录。

## Download Audit

每次 `download` 写出：

```text
audit/download_<timestamp>_<run>.csv
```

audit 按 `trade_date + order_book_id` 记录下载单元状态。常见状态：

- `written`
- `skipped_existing`
- `empty_remote`
- `failed`
- `quota_blocked`

audit 用于定位失败单元、empty remote 单元、quota 截停位置和 resume 进度。

## Daily Aggregate

`aggregate-daily` 输出一份日频 parquet。常见字段类别：

- 标识：`trade_date`、`order_book_id`、`symbol`。
- OHLCV：open、high、low、close、volume、total_turnover。
- 报价特征：spread、depth、imbalance。
- VWAP 和成交质量特征。
- 质量标记：`quote_quality_flag`、`vwap_quality_flag`、`coverage_quality_flag`、`tick_count_quality_flag`、`is_usable_for_research`、`is_usable_for_cost_model`。

`--meta-output` 可写出聚合 metadata，记录：

- `source_rows`
- `source_parts`
- `source_fields`
- 输出行数
- 缺失源字段

聚合输入按 parquet 分片增量读取，适合全周期小样本和核心池质量门禁。

## Asset Output

`emit-asset` 输出 asset-compatible 目录：

```text
manifest.yml
meta.json
symbols.txt
fields.txt
```

raw asset 保留 raw parquet 分片；daily asset 保存聚合后的 parquet。`symbols.txt` 和 `fields.txt` 用于快速检查覆盖范围，`manifest.yml` 和 `meta.json` 用于发布和复核。

## 低内存约束

`health`、`aggregate-daily`、`reconcile-daily` 和 raw `emit-asset` 应按分片扫描 raw cache。峰值内存应接近一个 parquet 分片加紧凑诊断或日频行。
