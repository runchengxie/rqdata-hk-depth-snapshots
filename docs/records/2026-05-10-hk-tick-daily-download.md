# 港股 Tick 日常补下载：2026-05-10

状态：已完成。

记录日期：2026-05-10。

## 目标

本轮继续扩展正式 Core200 tick-depth 池。优先选择 Core200 中尚未覆盖的下一组
15 个高成交标的，即 `rank050..064` 切片，并从 provider 当前 tick 权限起点
`2025-04-01` 连续下载到 selection date `2026-05-06`。

标的文件：

`configs/universe/hk_tick_depth_core200_rank050_064.txt`

标的列表：

| # | RQData code |
| ---: | --- |
| 1 | `02015.XHKG` |
| 2 | `09863.XHKG` |
| 3 | `00020.XHKG` |
| 4 | `01088.XHKG` |
| 5 | `01171.XHKG` |
| 6 | `00386.XHKG` |
| 7 | `00522.XHKG` |
| 8 | `06181.XHKG` |
| 9 | `06809.XHKG` |
| 10 | `03808.XHKG` |
| 11 | `09880.XHKG` |
| 12 | `00016.XHKG` |
| 13 | `01288.XHKG` |
| 14 | `00669.XHKG` |
| 15 | `09696.XHKG` |

## Quota

今天开跑前 quota 已重置。

| 时点 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 开跑前查询 | 0 | 1,073,741,824 | 0.00% |
| `2026-03-02` 到 `2026-05-06` 后 | 106,290,799 | 967,451,025 | 9.90% |
| `2025-11-07` 到 `2026-02-27` 后 | 253,804,150 | 819,937,674 | 23.64% |
| `2025-08-01` 到 `2025-11-06` 后 | 432,580,512 | 641,161,312 | 40.29% |
| `2025-04-01` 到 `2025-07-31` 后 | 596,941,677 | 476,800,147 | 55.59% |
| 最终查询 | 599,426,501 | 474,315,323 | 55.83% |

最终剩余约 `452.34MB`。

## 下载结果

所有下载均使用 `symbol-date` raw layout、provider calendar、`--resume`、
`--continue-on-error`、`--retry-max-attempts 3` 和 quota guard。

| 窗口 | output root | planned | written | empty remote | failed | quota blocked | raw rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_20260302_20260506` | 660 | 660 | 0 | 0 | 0 | 2,994,097 |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20251107_20260227` | 1,125 | 1,061 | 64 | 0 | 0 | 4,374,358 |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20250801_20251106` | 1,005 | 938 | 67 | 0 | 0 | 5,048,045 |
| `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20250401_20250731` | 1,230 | 1,148 | 82 | 0 | 0 | 4,844,981 |

本轮合计写入 3,807 个 symbol-date parquet 分片，raw rows 合计 17,261,481。

## 质量与聚合

所有 health 检查均为 `pass`，没有 failure。warning 与前几轮一致，主要是个别
symbol-date 单元内时间戳非单调、累计成交量或累计成交额回落。

| 数据集 | health rows | parts | symbols | dates | warnings | aggregate rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `2026-03-02` 到 `2026-05-06` | 2,994,097 | 660 | 15 | 44 | turnover decrease | 660 |
| `2025-11-07` 到 `2026-02-27` | 4,374,358 | 1,125 | 15 | 75 | timestamp；volume；turnover | 1,061 |
| `2025-08-01` 到 `2025-11-06` | 5,048,045 | 1,005 | 14 | 67 | timestamp；volume；turnover | 938 |
| `2025-04-01` 到 `2025-07-31` | 4,844,981 | 1,230 | 14 | 82 | timestamp；volume；turnover | 1,148 |

## 输出记录

| 数据集 | download metadata | health report | daily aggregate |
| --- | --- | --- | --- |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_20260302_20260506/meta/download_20260510_063704.json` | `artifacts/reports/tick_health_core200_rank050_064_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank050_064_20260302_20260506/data.parquet` |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20251107_20260227/meta/download_20260510_063825.json` | `artifacts/reports/tick_health_core200_rank050_064_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank050_064_backfill_20251107_20260227/data.parquet` |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20250801_20251106/meta/download_20260510_064020.json` | `artifacts/reports/tick_health_core200_rank050_064_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank050_064_backfill_20250801_20251106/data.parquet` |
| `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank050_064_backfill_20250401_20250731/meta/download_20260510_064222.json` | `artifacts/reports/tick_health_core200_rank050_064_backfill_20250401_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank050_064_backfill_20250401_20250731/data.parquet` |

## 结论

本轮完成 Core200 `rank050..064` 的连续历史补齐。Core200 本地 tick 覆盖从
50/200 提升到 65/200，覆盖比例从 25.00% 提升到 32.50%。

## 追加下载：Core200 rank065..074

同日继续用剩余额度下载 Core200 下一组 10 个标的。由于追加前 quota 只剩约
`452.34MB`，本轮先用 10 个标的而不是 15 个标的，以提高完整回填概率。

标的文件：

`configs/universe/hk_tick_depth_core200_rank065_074.txt`

标的列表：

| # | RQData code |
| ---: | --- |
| 1 | `02228.XHKG` |
| 2 | `06651.XHKG` |
| 3 | `09626.XHKG` |
| 4 | `01109.XHKG` |
| 5 | `03330.XHKG` |
| 6 | `06088.XHKG` |
| 7 | `01072.XHKG` |
| 8 | `02208.XHKG` |
| 9 | `02600.XHKG` |
| 10 | `02655.XHKG` |

### 追加 quota

| 时点 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 追加开跑前查询 | 599,426,501 | 474,315,323 | 55.83% |
| `2026-03-02` 到 `2026-05-06` 后 | 700,549,306 | 373,192,518 | 65.24% |
| `2025-11-07` 到 `2026-02-27` 后 | 823,991,859 | 249,749,965 | 76.74% |
| `2025-08-01` 到 `2025-11-06` 后 | 946,794,592 | 126,947,232 | 88.18% |
| `2025-06-02` 到 `2025-07-31` 后 | 1,006,895,682 | 66,846,142 | 93.77% |
| `2025-05-02` 到 `2025-05-30` 后 | 1,023,025,124 | 50,716,700 | 95.28% |
| `2025-04-01` 到 `2025-04-30` 后 | 1,042,560,224 | 31,181,600 | 97.10% |
| 最终查询 | 1,043,517,656 | 30,224,168 | 97.19% |

最终剩余约 `28.82MB`。

### 追加下载结果

近期和中段窗口使用 `batch-size=5`、`--quota-stop-ratio 0.95`。进入 quota
尾部后，`2025-06-02` 起的三个小窗口使用 `batch-size=1` 和
`--quota-stop-ratio 0.99`，按完整小窗口续补。

| 窗口 | output root | planned | written | empty remote | failed | quota blocked | raw rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_20260302_20260506` | 440 | 440 | 0 | 0 | 0 | 2,668,467 |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20251107_20260227` | 750 | 688 | 62 | 0 | 0 | 3,004,969 |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250801_20251106` | 670 | 536 | 134 | 0 | 0 | 3,372,269 |
| `2025-06-02` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250602_20250731` | 430 | 344 | 86 | 0 | 0 | 1,473,163 |
| `2025-05-02` 到 `2025-05-30` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250502_20250530` | 200 | 160 | 40 | 0 | 0 | 448,907 |
| `2025-04-01` 到 `2025-04-30` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250401_20250430` | 190 | 152 | 38 | 0 | 0 | 469,786 |

追加合计写入 2,320 个 symbol-date parquet 分片，raw rows 合计 11,437,561。

### 追加质量与聚合

所有 health 检查均为 `pass`，没有 failure。warning 仍是少量时间戳非单调、
累计成交量回落或累计成交额回落。

| 数据集 | health rows | parts | symbols | dates | warnings | aggregate rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `2026-03-02` 到 `2026-05-06` | 2,668,467 | 440 | 10 | 44 | 无 | 440 |
| `2025-11-07` 到 `2026-02-27` | 3,004,969 | 750 | 10 | 75 | timestamp；volume；turnover | 688 |
| `2025-08-01` 到 `2025-11-06` | 3,372,269 | 670 | 8 | 67 | timestamp；volume；turnover | 536 |
| `2025-06-02` 到 `2025-07-31` | 1,473,163 | 430 | 8 | 43 | timestamp；volume；turnover | 344 |
| `2025-05-02` 到 `2025-05-30` | 448,907 | 200 | 8 | 20 | 无 | 160 |
| `2025-04-01` 到 `2025-04-30` | 469,786 | 190 | 8 | 19 | 无 | 152 |

### 追加输出记录

| 数据集 | download metadata | health report | daily aggregate |
| --- | --- | --- | --- |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_20260302_20260506/meta/download_20260510_065422.json` | `artifacts/reports/tick_health_core200_rank065_074_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_20260302_20260506/data.parquet` |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20251107_20260227/meta/download_20260510_065534.json` | `artifacts/reports/tick_health_core200_rank065_074_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_backfill_20251107_20260227/data.parquet` |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250801_20251106/meta/download_20260510_065706.json` | `artifacts/reports/tick_health_core200_rank065_074_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_backfill_20250801_20251106/data.parquet` |
| `2025-06-02` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250602_20250731/meta/download_20260510_065908.json` | `artifacts/reports/tick_health_core200_rank065_074_backfill_20250602_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_backfill_20250602_20250731/data.parquet` |
| `2025-05-02` 到 `2025-05-30` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250502_20250530/meta/download_20260510_070104.json` | `artifacts/reports/tick_health_core200_rank065_074_backfill_20250502_20250530.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_backfill_20250502_20250530/data.parquet` |
| `2025-04-01` 到 `2025-04-30` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank065_074_backfill_20250401_20250430/meta/download_20260510_070200.json` | `artifacts/reports/tick_health_core200_rank065_074_backfill_20250401_20250430.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank065_074_backfill_20250401_20250430/data.parquet` |

### 追加结论

追加下载完成 Core200 `rank065..074` 的连续历史补齐。Core200 本地 tick 覆盖从
65/200 提升到 75/200，覆盖比例从 32.50% 提升到 37.50%。

下一轮最值得继续下载的是 Core200 中尚未覆盖的下一组 10-15 个标的，从
`01336.XHKG`、`09995.XHKG`、`00763.XHKG` 开始，继续按 rank 顺序扩展。
