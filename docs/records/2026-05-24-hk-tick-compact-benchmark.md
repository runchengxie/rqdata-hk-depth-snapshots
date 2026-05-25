# 港股 Tick 冷归档 Compact Benchmark：2026-05-24

记录日期：2026-05-24（Asia/Shanghai）。

## 目的

本次实验评估已重编码为 parquet `zstd` level 12 的 `symbol-date` raw cache 在冷归档
场景下继续合并后的空间收益。样本取自 Core400 `rank341..380` 完整窗口，共
`40` 只标的、`275` 个交易日和 `11,000` 个源 parquet part。

源路径：

```text
artifacts/cache/rqdata/hk_tick_depth_cold_zstd12/core400_rank341_380_20250401_20260515
```

## 实验配置

| 输出方案 | grouping | row group 策略 | 输出路径 |
| --- | --- | --- | --- |
| 日级 row group 对照 | `symbol-year` | `row_group_days=1` | `artifacts/cache/rqdata/hk_tick_depth_compact_bench/core400_rank341_380_symbol_year_rg1_zstd12` |
| 季度 compact | `symbol-quarter` | `row_group_days=60` | `artifacts/cache/rqdata/hk_tick_depth_compact_bench/core400_rank341_380_symbol_quarter_rg60_zstd12` |

两组输出均使用 parquet `zstd` level 12。季度方案最多缓冲同一标的 `60` 个源交易日
part 后写入一个 row group。

## 字节结果

| 方案 | parquet part 数 | 字节数 | 相对源减少 | 相对源压缩比 |
| --- | ---: | ---: | ---: | ---: |
| 源 `symbol-date + zstd12` | 11,000 | 972,948,263 | - | 1.0000 |
| `symbol-year + zstd12 + rg1` | 80 | 768,357,755 | 204,590,508 (`21.0%`) | 0.7897 |
| `symbol-quarter + zstd12 + rg60` | 200 | 600,244,191 | 372,704,072 (`38.3%`) | 0.6169 |

季度大 row group 相比日级 row group 对照继续减少 `168,113,564` bytes，说明该样本
中跨日列页压缩的收益明显高于仅合并文件封装的收益。

对应 metadata：

```text
artifacts/cache/rqdata/hk_tick_depth_compact_bench/core400_rank341_380_symbol_year_rg1_zstd12/meta/compact_raw_20260524_122751.json
artifacts/cache/rqdata/hk_tick_depth_compact_bench/core400_rank341_380_symbol_quarter_rg60_zstd12/meta/compact_raw_20260524_123057.json
```

## Schema 情况

源样本包含两种 parquet schema：

| schema 类型 | 源 part 数 |
| --- | ---: |
| 正常 typed schema | 10,538 |
| 全空 `null`-typed schema | 462 |

`compact-raw` 在单个输出 compact part 内采用 permissive schema unification，两个输出
方案各有 `5` 个 compact part 发生 schema 统一；源文件保持原样。

## 全 Cold Cache 重复盘点

全量 zstd12 cold cache 用于既有 tar 打包时包含 retry、refetch 和 probe 等历史 root：

```text
artifacts/cache/rqdata/hk_tick_depth_cold_zstd12
```

先按 `trade_date + order_book_id` 对所有 parquet 路径盘点，再仅对发生重复的文件
读取 SHA-256 与 parquet 行数：

| 项目 | 数量 |
| --- | ---: |
| 候选 parquet part | 792,672 |
| 唯一日期-标的单元 | 787,570 |
| 含重复的日期-标的单元 | 4,823 |
| 需要丢弃的重复 part | 5,102 |
| 候选输入字节数 | 40,075,148,359 |
| 选择后输入字节数 | 39,760,427,880 |
| 丢弃重复字节数 | 314,720,479 |
| 预计季度 compact part | 14,157 |

重复单元的内容分类如下：

| 分类 | 单元数 | 可选规则 |
| --- | ---: | --- |
| 文件字节完全一致 | 3,758 | 保留任一副本 |
| 全部为零行，schema 或 metadata 不同 | 938 | 优先保留 typed schema 空分片 |
| 空 retry 与非空 refetch 并存，非空内容唯一 | 127 | 保留非空 refetch |
| 两个内容不同的非空副本 | 0 | 若出现则停止 |

因此全量 compact 不需要维护按 root 的人工覆盖清单。`compact-raw
--duplicate-policy prefer-nonempty-identical` 将上述可验证规则机械化，并在
metadata 的 `duplicate_resolution` 中保留计数和选择样例。

## 全量 Compact 输出

在 `2026-05-24` 晚间以保守重复策略生成全量季度 compact：

```bash
rqdata-tick compact-raw \
  --input artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --output artifacts/cache/rqdata/hk_tick_depth_cold_compact_zstd12_q_rg60 \
  --grouping symbol-quarter \
  --compression zstd \
  --compression-level 12 \
  --row-group-days 60 \
  --duplicate-policy prefer-nonempty-identical \
  --resume \
  --progress
```

结果：

| 项目 | 值 |
| --- | ---: |
| 选择后 `symbol-date` part 数 | 787,570 |
| 输出 compact part 数 | 14,157 |
| 行数 | 445,397,450 |
| 选择后输入字节数 | 39,760,427,880 |
| 输出字节数 | 15,898,022,941 |
| 相对选择后输入减少 | 23,862,404,939 (`60.02%`) |
| 相对原候选输入减少（含重复副本） | 24,177,125,418 (`60.33%`) |
| 含 schema variant 的输出 part | 7,098 |
| 运行时间 | 3,649.8 秒（约 `60.8` 分钟） |

文件系统汇总为源目录约 `40G`、compact 输出约 `15G`。执行产物：

```text
artifacts/cache/rqdata/hk_tick_depth_cold_compact_zstd12_q_rg60/meta/compact_raw_20260524_133547.json
artifacts/cache/rqdata/hk_tick_depth_cold_compact_zstd12_q_rg60/audit/compact_raw_20260524_133547.csv
```

## Health 对照

季度 compact 输出已执行 `health --fail-on-severity none`：

```text
artifacts/reports/compact_bench/core400_rank341_380_symbol_quarter_rg60_zstd12_health.json
artifacts/reports/compact_bench/core400_rank341_380_symbol_quarter_rg60_zstd12_health_units.csv
```

其汇总与既有源 health 报告一致：

| 指标 | 源报告 | 季度 compact |
| --- | ---: | ---: |
| status | `pass` | `pass` |
| rows | 16,278,628 | 16,278,628 |
| symbols | 40 | 40 |
| dates | 275 | 275 |
| duplicate key count | 0 | 0 |
| timestamp non-monotonic count | 2 | 2 |
| volume decrease count | 2 | 2 |
| turnover decrease count | 2 | 2 |
| parquet part count | 11,000 | 200 |

两者的 quality checks 都是相同的 `3` 项 warning，且没有 failure。

## 全量 Health 验收

全量 compact 输出的 health 扫描于 `2026-05-25`（Asia/Shanghai）完成：

```text
artifacts/reports/compact_bench/hk_tick_depth_cold_compact_zstd12_q_rg60_health.json
artifacts/reports/compact_bench/hk_tick_depth_cold_compact_zstd12_q_rg60_health_units.csv
```

| 指标 | 全量 compact |
| --- | ---: |
| status | `pass` |
| rows | 445,397,450 |
| symbols with non-empty rows | 2,732 |
| dates with non-empty rows | 280 |
| duplicate key count | 0 |
| timestamp non-monotonic count | 64 |
| volume decrease count | 64 |
| turnover decrease count | 127 |
| best spread cross count | 2 |
| quote ladder invalid count | 2 |
| failures | 0 |

warnings 为 `timestamp_non_monotonic_count`、`best_spread_cross_count`、
`quote_ladder_invalid_count`、`volume_decrease_count`、`turnover_decrease_count`
和 `turnover_large_drop_count`。扫描墙钟时间约 `2` 小时 `21` 分钟；当前 health
实现会同时写出全量 unit diagnostics，产生约 `841M` JSON 和约 `101M` CSV。这再次
表明 compact 输出适合冷归档验收和交付，不适合作为频繁日常 health 的操作布局。

## 分包输出

在 `2026-05-25` 将已压缩的 compact parquet 仅封装为未外层压缩的 tar 分包：

```bash
rqdata-tick package-assets \
  --name hk_tick_depth_cold_compact_zstd12_q_rg60 \
  --as-of 20260525 \
  --tar-dir artifacts/releases/hk_tick_depth_cold_compact_zstd12_q_rg60_20260525_tarballs \
  --part raw \
  --raw-source artifacts/cache/rqdata/hk_tick_depth_cold_compact_zstd12_q_rg60 \
  --max-tar-bytes 1900000000 \
  --archive-format tar \
  --raw-dedupe none \
  --progress
```

分包目录：

```text
artifacts/releases/hk_tick_depth_cold_compact_zstd12_q_rg60_20260525_tarballs
```

| 项目 | 值 |
| --- | ---: |
| tar 包数 | 9 |
| tar 内条目数 | 14,159 |
| tar 总字节数 | 15,926,087,680 |
| 最大单包字节数 | 1,851,801,600 |
| archive format | `tar` |
| 外层重新压缩 | 否 |
| 独立 SHA-256 复核 | 9 / 9 通过 |

tar 内条目包括 `14,157` 个 compact parquet 以及 compact 自带的 metadata 与 audit。
`manifest.json` 记录了每个 tar 包的字节数和 SHA-256。

已于 `2026-05-25` 创建不带附件的 GitHub draft release，等待手动上传上述九个 tar：

```text
tag: hk_tick_depth_cold_compact_20260525
title: HK Tick Depth Cold Compact Assets 20260525
url: https://github.com/runchengxie/rqdata-hk-depth-snapshots/releases/tag/untagged-ddca45b251a6c0cdae68
assets at creation: 0
```

## 操作结论

- `symbol-quarter + row_group_days=60 + zstd12` 对该代表性样本节省 `38.3%`，值得
  继续作为全量 cold asset 候选方案；全量实际相对去重后输入节省 `60.02%`。
- compact 输出用于冷归档和交付压缩；下载 resume、日常 health、aggregate 与对账仍
  使用 `symbol-date` raw cache。
- 对季度 compact 执行 health 时，观察到 Python RSS 约为系统 `7.8 GiB` 内存的
  `13.9%`，约 `1.1 GiB`；该扫描代价高于原 operational layout，与冷归档定位一致。
