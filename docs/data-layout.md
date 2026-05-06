# Data Layout

## Raw Layout

默认 raw layout 是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

这个布局以一个标的、一个交易日为最小 resume 单元。下载器会在跳过本地文件前校验 parquet 可读性、字段、标的和交易日期。

## Legacy Batch Layout

历史 batch layout：

```text
parts/trade_date=YYYYMMDD/batch_0000.parquet
```

该布局仍可读取，用于历史兼容。新下载应使用 `symbol-date`；新 batch 下载会在 metadata 的 `deprecations` 字段中记录弃用提示。

## Metadata And Audit

每次下载会写入：

```text
meta/download_<timestamp>.json
audit/download_<timestamp>_<run>.csv
```

metadata 记录请求参数、字段、交易日、layout、parquet 配置、quota guard、状态统计和 audit 路径。

audit 按 `trade_date + order_book_id` 记录 `written`、`skipped_existing`、`empty_remote`、`failed`、`quota_blocked` 等状态。

`aggregate-daily` metadata 记录 `source_rows`、`source_parts`、`source_fields`、输出行数和缺失源字段。
这些统计来自分片级扫描，适合 raw cache 较大时复核聚合输入规模。

## Asset Output

`emit-asset` 会输出 `manifest.yml`、`meta.json`、`symbols.txt` 和 `fields.txt`。raw asset 保留 parquet 分片；daily asset 保存聚合后的 parquet。
