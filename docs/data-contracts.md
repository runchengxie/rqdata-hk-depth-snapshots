# 数据契约

本页描述项目读写的稳定文件契约。数据研究语义见
[Tick-depth 数据说明](tick-depth-data.md)，术语见 [术语表](terminology.md)，命令参数见
[CLI 参考](cli.md)。

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

新 raw parquet 默认使用 `zstd` level 3 无损压缩。metadata 和 coverage 输出会记录实际
parquet codec 与 level，旧 `snappy` 分片仍可与新分片一起读取。

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

## Raw Recompression Metadata

`recompress-raw` 将 raw parquet 分片无损重编码到新目录，并保留 `parts/...` 相对路径。
每次执行写出：

```text
meta/recompress_raw_<timestamp>.json
audit/recompress_raw_<timestamp>.csv
```

metadata 记录源目录、输出目录、目标 parquet 配置、输入/输出字节数、处理分片数、
失败分片和 audit 路径。audit 按 parquet part 记录 `rewritten`、`copied`、
`skipped_existing` 或 `failed`，并记录源/目标 codec、行数和字节数。

## Cold Compact Output

`compact-raw` 从 `symbol-date` raw cache 写出冷归档派生物。该输出用于压缩实验和
冷备份，下载 resume 与常规 raw 操作继续基于默认 raw cache。布局按参数选择：

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
- archive 格式、压缩等级、raw 去重模式。
- 被选中的 source paths 和缺失 source paths。
- 每个 tarball 的 part、chunk 序号、输入字节数、压缩后字节数、文件数和 `sha256`。
- 每个 tarball 的前几个 archive entry，便于快速确认路径布局。

`<ext>` 默认为 `tar`，也可显式选择 `tar.zst` 或 `tar.gz`。后两种格式的压缩等级
只作用于外层 archive；raw parquet codec 和压缩等级由下载或 `recompress-raw` 阶段
决定。启用 `raw_dedupe=symbol-date` 时，raw parquet part 会按
`trade_date + order_book_id` 分组，manifest 的 `dedupe.raw`
记录候选、保留和丢弃数量以及样例。重复候选按文件修改时间、文件大小和 archive path
排序后选择保留项。

tarball 内部路径以 part 为第一层，例如 `raw/<source_name>/...`、`daily/<source_name>/...`
和 config part 下的 `<source_name>/...`。恢复时先解压到工作目录，再把研究或检查命令指向解压后的
raw、daily、reports 或 configs 路径。

## 低内存约束

`health`、`aggregate-daily`、`reconcile-daily` 和 raw `emit-asset` 应按分片扫描 raw cache。峰值内存应接近一个 parquet 分片加紧凑诊断或日频行。
