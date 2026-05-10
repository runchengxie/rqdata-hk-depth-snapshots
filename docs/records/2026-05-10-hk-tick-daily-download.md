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

下一轮最值得继续下载的是 Core200 中尚未覆盖的下一组 15-20 个标的，从
`02228.XHKG`、`06651.XHKG`、`09626.XHKG` 开始，继续按 rank 顺序扩展。
