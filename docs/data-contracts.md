# 数据契约

本页描述项目读写的稳定文件契约。数据研究语义见
[十档盘口快照数据说明](depth-snapshot-data.md)，术语见 [术语表](terminology.md)，命令参数见
[CLI 参考](cli.md)。

## 原始快照缓存

默认原始快照布局是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

这个布局以一个标的、一个交易日为最小操作单元。下载器在 `--resume` 跳过本地文件前会校验：

- parquet 可读性。
- 必要字段存在。
- `order_book_id` 与路径一致。
- `trade_date` 与路径一致。
- 请求字段覆盖本地文件字段。

新原始快照 parquet 默认使用 `zstd` level 3 无损压缩。metadata 和 coverage 输出会记录实际
parquet codec 与 level，旧 `snappy` 分片仍可与新分片一起读取。

## Legacy Batch

历史 batch 布局：

```text
parts/trade_date=YYYYMMDD/batch_0000.parquet
```

该布局保留读取兼容。新下载应使用 `symbol-date`；新 `--raw-layout batch` / `raw_layout=batch` 下载会在 metadata 的 `deprecations` 字段记录提示。

## Download Metadata

非 `dry-run` 的 `download` 写出可持续更新的 checkpoint：

```text
meta/download_<timestamp>.json
```

metadata 记录：

- 请求参数：symbols、dates、fields、batch size、原始快照布局 `raw_layout`、calendar、parquet 配置。
- provider 类型和 retry 配置。
- quota guard 配置和 quota snapshot。
- 下载计划和交易日范围。
- 状态统计：`written`、`skipped_existing`、`empty_remote`、`failed`、`quota_blocked`。
- audit 文件路径。
- 完整明细 JSONL 路径 `detail_records_path`、各集合计数 `detail_counts` 和内联样例截断标记 `detail_lists_truncated`。
- 当前运行状态 `run_status`；live 下载按已完成批次更新 checkpoint。
- deprecations 和错误摘要。

metadata JSON 保留汇总和有界明细样例，默认每类最多 `1000` 条。完整计划、完成、
跳过、无效、失败和 quota 截停明细按行写入：

```text
meta/download_details_<run>.jsonl
```

每行包含 `collection` 和对应明细字段。该 JSONL 与 audit 用于复核完整进度，metadata
JSON 用于快速查看 checkpoint 与汇总。`dry-run` 返回有界摘要并写完整计划 JSONL，
无需创建 live checkpoint。

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

非 `dry-run` 下载在每个 provider 批次结束后追加对应 audit 行，并原子更新 metadata
checkpoint，因此长任务运行中即可查看已完成批次和截停位置。audit 用于定位失败单元、
empty remote 单元、quota 截停位置和 resume 进度。

## Raw Recompression Metadata

`recompress-raw` 将原始快照 parquet 分片无损重编码到新目录，并保留 `parts/...` 相对路径。
每次执行写出：

```text
meta/recompress_raw_<timestamp>.json
audit/recompress_raw_<timestamp>.csv
```

metadata 记录源目录、输出目录、目标 parquet 配置、输入/输出字节数、处理分片数、
失败分片和 audit 路径。audit 按 parquet part 记录 `rewritten`、`copied`、
`skipped_existing` 或 `failed`，并记录源/目标 codec、行数和字节数。

## Cold Compact Output

`compact-raw` 从 `symbol-date` 原始快照缓存写出冷归档派生物。该输出用于压缩实验和
冷备份，下载 resume 与常规操作继续基于默认原始快照缓存。布局按参数选择：

```text
parts/order_book_id=00001.XHKG/year=2025/quarter=Q2.parquet
parts/order_book_id=00001.XHKG/year=2025.parquet
```

第一种对应 `grouping=symbol-quarter`，第二种对应 `grouping=symbol-year`。每次执行写出：

```text
meta/compact_raw_<timestamp>.json
audit/compact_raw_<timestamp>.csv
```

metadata 记录 `layout_version`、`grouping`、`row_group_days`、parquet 配置、输入和
输出字节数、节省字节数、压缩比、输出 compact part 数以及失败摘要。audit 以输出
compact part 为单位记录标的、时间段、源 part 数、行数、字节数、输出 row group 数
、schema variant 数和处理状态。输入组存在全空 `null` schema 分片时，输出在该
compact part 范围内使用 permissive schema unification，metadata 的
`schema_variant_compact_parts` 记录受影响输出数量。

默认 `duplicate_policy=error`，输入出现重复 `trade_date + order_book_id` 时拒绝
生成输出。显式使用 `duplicate_policy=prefer-nonempty-identical` 时，仅允许以下
可审计选择：字节一致副本折叠；所有副本为空时优先保留 typed schema；空 retry 与
一个或多个字节一致的非空副本并存时保留非空副本。存在不同内容的非空副本时仍失败。
metadata 的 `duplicate_resolution` 记录候选/选定/丢弃 part 数、按规则分类计数、
字节数和选择样例。

`row_group_days=1` 保持一个源交易日对应一个输出 row group；更大的值以有限缓存将
相邻交易日合并到一个 row group，以便测试跨日压缩收益。

## Daily Aggregate

`aggregate-daily` 从原始快照输出一份日频 parquet。常见字段类别：

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

## Health Report

`health` 的 JSON 报告包含数据集汇总、质量门禁结论和有限异常样例：

- `unit_count`：扫描到的 symbol-date 单元总数。
- `anomalous_unit_count`：存在 warning 检查项的 symbol-date 单元数。
- `unit_diagnostic_sample_limit`：JSON 中的异常样例上限，默认 `20`。
- `unit_diagnostics_truncated`：异常样例是否因上限被截断。
- `unit_diagnostics`：有界异常样例，不承载完整全量明细。

使用 `--out-units <path>.csv` 时，完整 symbol-date 明细在扫描过程中写到 CSV。大规模
数据集应使用 CSV 输出；`.parquet` 明细输出保留兼容支持，当前会在完成扫描后集中写入。

## 交付目录输出

`emit-asset` 输出可交付目录：

```text
manifest.yml
meta.json
symbols.txt
fields.txt
```

原始快照交付目录保留原始 parquet 分片；日频交付目录保存聚合后的 parquet。`symbols.txt` 和 `fields.txt` 用于快速检查覆盖范围，`manifest.yml` 和 `meta.json` 用于发布和复核。

## Backup Tarballs

`package-assets` 输出本地备份目录：

```text
manifest.yml
manifest.json
README.md
<name>_<as_of>_release_notes.txt
<name>-<as_of>-raw-part001.<ext>
<name>-<as_of>-daily.<ext>
<name>-<as_of>-metadata.<ext>
<name>-<as_of>-reports.<ext>
<name>-<as_of>-configs.<ext>
```

`manifest.yml` 记录：

- 分发名称、`as_of`、生成时间和 generator 版本。
- archive 格式、压缩等级、原始快照去重模式。
- 被选中的 source paths 和缺失 source paths。
- 每个 tarball 的 part、chunk 序号、输入字节数、压缩后字节数、文件数和 `sha256`。
- 每个 tarball 的前几个 archive entry，便于快速确认路径布局。

`<ext>` 默认为 `tar`，也可显式选择 `tar.zst` 或 `tar.gz`。后两种格式的压缩等级
只作用于外层 archive；原始快照 parquet codec 和压缩等级由下载或 `recompress-raw` 阶段
决定。启用 `raw_dedupe=symbol-date` 时，原始快照 parquet part 会按
`trade_date + order_book_id` 分组，manifest 的 `dedupe.raw`
记录候选、保留和丢弃数量、解析规则分类以及样例。字节一致副本可折叠；全空副本优先
保留带字段类型的 schema；空副本与字节一致的非空副本并存时保留非空副本。不同内容的
非空副本会使打包失败。

tarball 内部路径以 part 为第一层，例如 `raw/<source_name>/...`、`daily/<source_name>/...`
和 config part 下的 `<source_name>/...`。恢复时先解压到工作目录，再把研究或检查命令指向解压后的
原始快照、daily、reports 或 configs 路径。

## 低内存约束

`health`、`aggregate-daily`、`reconcile-daily` 和原始快照 `emit-asset` 应按分片扫描原始快照缓存。`health` 默认 JSON 报告与 CSV 明细输出不保留全量诊断列表；峰值内存应接近一个 parquet 分片加有限诊断或日频行。
