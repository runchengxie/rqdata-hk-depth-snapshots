# 港股 Tick 日常补下载：2026-05-11

状态：已完成。

记录日期：2026-05-11。

## 目标

本轮继续按 Core200 成交额 rank 顺序扩展 tick-depth 覆盖：

1. 下载 Core200 `rank075..090` 切片，跳过已在本地 tick pool 中覆盖的
   `00001.XHKG`，共 15 个新增标的。
2. 在 quota 仍充足时，继续下载 Core200 `rank091..100` 切片，共 10 个新增标的。
3. 追加补齐 Core100 在 `2026-05-07` 到 `2026-05-08` 的两日增量。
4. 用剩余 quota 做低成交港股通尾部 25 只 sizing probe，验证小微盘 tick-depth 数据量。
5. 继续做低成交但非零成交的 25 只 sizing probe，和极尾部空返回密集池对照。
6. 在 quota 尾部阶段继续补 Core200 `rank101`，推进主池覆盖。

Core200 `rank075..100` 从 provider 当前 tick 权限起点 `2025-04-01` 连续下载到
selection date `2026-05-06`；Core200 `rank101` 下载到 `2026-05-08`。两组低成交
probe 均下载 `2026-03-02` 到 `2026-05-08`。所有下载均使用 `symbol-date` raw
layout、provider calendar、`--resume`、`--continue-on-error`、
`--retry-max-attempts 3` 和 quota guard。

## 标的

`configs/universe/hk_tick_depth_core200_rank075_090.txt`：

| # | RQData code |
| ---: | --- |
| 1 | `01336.XHKG` |
| 2 | `09995.XHKG` |
| 3 | `00763.XHKG` |
| 4 | `01788.XHKG` |
| 5 | `01138.XHKG` |
| 6 | `00148.XHKG` |
| 7 | `02388.XHKG` |
| 8 | `00027.XHKG` |
| 9 | `01177.XHKG` |
| 10 | `02328.XHKG` |
| 11 | `03858.XHKG` |
| 12 | `02423.XHKG` |
| 13 | `06690.XHKG` |
| 14 | `02331.XHKG` |
| 15 | `00358.XHKG` |

`configs/universe/hk_tick_depth_core200_rank091_100.txt`：

| # | RQData code |
| ---: | --- |
| 1 | `01428.XHKG` |
| 2 | `01989.XHKG` |
| 3 | `02465.XHKG` |
| 4 | `01787.XHKG` |
| 5 | `03692.XHKG` |
| 6 | `01818.XHKG` |
| 7 | `02477.XHKG` |
| 8 | `02057.XHKG` |
| 9 | `06090.XHKG` |
| 10 | `00241.XHKG` |

`configs/universe/hk_tick_depth_micro_tail25_probe_20260506.txt`：

`01253.XHKG`, `00059.XHKG`, `00468.XHKG`, `00607.XHKG`, `00612.XHKG`,
`00658.XHKG`, `00754.XHKG`, `00845.XHKG`, `00976.XHKG`, `01165.XHKG`,
`01176.XHKG`, `01188.XHKG`, `01293.XHKG`, `01448.XHKG`, `01636.XHKG`,
`01668.XHKG`, `01728.XHKG`, `01755.XHKG`, `02280.XHKG`, `02362.XHKG`,
`02627.XHKG`, `02629.XHKG`, `06623.XHKG`, `06639.XHKG`, `06878.XHKG`。

`configs/universe/hk_tick_depth_low_turnover_nonzero25_probe_20260506.txt`：

`02415.XHKG`, `06968.XHKG`, `02329.XHKG`, `00163.XHKG`, `00120.XHKG`,
`00691.XHKG`, `01778.XHKG`, `03699.XHKG`, `01098.XHKG`, `03368.XHKG`,
`06068.XHKG`, `00832.XHKG`, `01680.XHKG`, `02048.XHKG`, `01551.XHKG`,
`00496.XHKG`, `00846.XHKG`, `01315.XHKG`, `00989.XHKG`, `00185.XHKG`,
`01608.XHKG`, `02326.XHKG`, `00718.XHKG`, `01996.XHKG`, `01817.XHKG`。

`configs/universe/hk_tick_depth_core200_rank101.txt`：

| # | RQData code |
| ---: | --- |
| 1 | `02601.XHKG` |

## Quota

| 时点 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 开跑前查询 | 0 | 1,073,741,824 | 0.00% |
| rank075..090 `2026-03-02` 到 `2026-05-06` 后 | 94,584,226 | 979,157,598 | 8.81% |
| rank075..090 `2025-11-07` 到 `2026-02-27` 后 | 237,127,018 | 836,614,806 | 22.08% |
| rank075..090 `2025-08-01` 到 `2025-11-06` 后 | 424,326,129 | 649,415,695 | 39.52% |
| rank075..090 `2025-04-01` 到 `2025-07-31` 后 | 589,526,752 | 484,215,072 | 54.90% |
| rank091..100 `2026-03-02` 到 `2026-05-06` 后 | 662,887,838 | 410,853,986 | 61.74% |
| rank091..100 `2025-11-07` 到 `2026-02-27` 后 | 728,896,975 | 344,844,849 | 67.88% |
| rank091..100 `2025-08-01` 到 `2025-11-06` 后 | 808,373,187 | 265,368,637 | 75.29% |
| rank091..100 `2025-04-01` 到 `2025-07-31` 后 | 887,567,637 | 186,174,187 | 82.66% |
| Core100 `2026-05-07` 到 `2026-05-08` 增量后 | 948,198,889 | 125,542,935 | 88.31% |
| 低成交尾部 25 probe `2026-03-02` 到 `2026-05-08` 后 | 957,118,114 | 116,623,710 | 89.14% |
| 低成交非零 25 probe `2026-03-02` 到 `2026-05-08` 后 | 958,938,988 | 114,802,836 | 89.31% |
| Core200 rank101 `2025-04-01` 到 `2026-05-08` 后 | 1,008,972,047 | 64,769,777 | 93.97% |
| 最终查询 | 1,013,114,070 | 60,627,754 | 94.35% |

最终剩余约 `57.82MB`。本轮未触发 quota guard。最终 used_pct 已到 `94.35%`，
距离 `95%` stop ratio 只剩约 `6.6MB` 的可启动空间，因此不再继续 Core200 rank102。

## 下载结果

| 数据集 | output root | planned | written | empty remote | failed | quota blocked | raw rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rank075..090 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_20260302_20260506` | 660 | 660 | 0 | 0 | 0 | 2,483,402 |
| rank075..090 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20251107_20260227` | 1,125 | 1,125 | 0 | 0 | 0 | 3,839,208 |
| rank075..090 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20250801_20251106` | 1,005 | 986 | 19 | 0 | 0 | 4,837,500 |
| rank075..090 `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20250401_20250731` | 1,230 | 1,148 | 82 | 0 | 0 | 5,078,513 |
| rank091..100 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_20260302_20260506` | 440 | 425 | 15 | 0 | 0 | 1,685,973 |
| rank091..100 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20251107_20260227` | 750 | 675 | 75 | 0 | 0 | 1,831,915 |
| rank091..100 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20250801_20251106` | 670 | 566 | 104 | 0 | 0 | 2,029,132 |
| rank091..100 `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20250401_20250731` | 820 | 652 | 168 | 0 | 0 | 2,109,312 |
| Core100 `2026-05-07` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/core100_increment_20260507_20260508` | 200 | 200 | 0 | 0 | 0 | 1,618,557 |
| 低成交尾部 25 probe `2026-03-02` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/micro_tail25_probe_20260302_20260508` | 1,150 | 184 | 966 | 0 | 0 | 111,992 |
| 低成交非零 25 probe `2026-03-02` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/low_turnover_nonzero25_probe_20260302_20260508` | 1,150 | 797 | 353 | 0 | 0 | 5,837 |
| Core200 rank101 `2025-04-01` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank101_20250401_20260508` | 270 | 270 | 0 | 0 | 0 | 1,624,038 |

本轮合计处理 9,470 个 symbol-date 单元，写入 7,688 个非空 parquet 分片，
记录 1,782 个 provider 空返回，raw rows 合计 27,255,379。

`empty_remote` 主要来自上市前或 provider 空返回覆盖记录，例如：

- `03858.XHKG` 在 `2025-08-28` 上市，rank075..090 早期窗口有上市前空返回。
- `01989.XHKG` 在 `2026-03-20` 上市，rank091..100 早期和中段窗口为空。
- `06090.XHKG` 在 `2025-09-23` 上市，rank091..100 早期窗口有上市前空返回。

## 质量与聚合

所有 health 检查均为 `pass`，没有 failure。rank075..090 的 warning 和前几轮一致，
主要是少量时间戳非单调、累计成交量或累计成交额回落。rank091..100 只有最早窗口
出现 1 个 warning。

| 数据集 | health rows | parts | symbols | dates | warnings | aggregate rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| rank075..090 `2026-03-02` 到 `2026-05-06` | 2,483,402 | 660 | 15 | 44 | 3 | 660 |
| rank075..090 `2025-11-07` 到 `2026-02-27` | 3,839,208 | 1,125 | 15 | 75 | 3 | 1,125 |
| rank075..090 `2025-08-01` 到 `2025-11-06` | 4,837,500 | 1,005 | 15 | 67 | 1 | 986 |
| rank075..090 `2025-04-01` 到 `2025-07-31` | 5,078,513 | 1,230 | 14 | 82 | 3 | 1,148 |
| rank091..100 `2026-03-02` 到 `2026-05-06` | 1,685,973 | 440 | 10 | 44 | 0 | 425 |
| rank091..100 `2025-11-07` 到 `2026-02-27` | 1,831,915 | 750 | 9 | 75 | 0 | 675 |
| rank091..100 `2025-08-01` 到 `2025-11-06` | 2,029,132 | 670 | 9 | 67 | 0 | 566 |
| rank091..100 `2025-04-01` 到 `2025-07-31` | 2,109,312 | 820 | 8 | 82 | 1 | 652 |
| Core100 `2026-05-07` 到 `2026-05-08` | 1,618,557 | 200 | 100 | 2 | 0 | 200 |
| 低成交尾部 25 probe `2026-03-02` 到 `2026-05-08` | 111,992 | 1,150 | 10 | 24 | 0 | 184 |
| 低成交非零 25 probe `2026-03-02` 到 `2026-05-08` | 5,837 | 1,150 | 25 | 46 | 0 | 797 |
| Core200 rank101 `2025-04-01` 到 `2026-05-08` | 1,624,038 | 270 | 1 | 270 | 0 | 270 |

## 输出记录

| 数据集 | download metadata | health report | daily aggregate |
| --- | --- | --- | --- |
| rank075..090 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_20260302_20260506/meta/download_20260511_003621.json` | `artifacts/reports/tick_health_core200_rank075_090_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank075_090_20260302_20260506/data.parquet` |
| rank075..090 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20251107_20260227/meta/download_20260511_003730.json` | `artifacts/reports/tick_health_core200_rank075_090_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank075_090_backfill_20251107_20260227/data.parquet` |
| rank075..090 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20250801_20251106/meta/download_20260511_004651.json` | `artifacts/reports/tick_health_core200_rank075_090_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank075_090_backfill_20250801_20251106/data.parquet` |
| rank075..090 `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank075_090_backfill_20250401_20250731/meta/download_20260511_004846.json` | `artifacts/reports/tick_health_core200_rank075_090_backfill_20250401_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank075_090_backfill_20250401_20250731/data.parquet` |
| rank091..100 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_20260302_20260506/meta/download_20260511_013439.json` | `artifacts/reports/tick_health_core200_rank091_100_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank091_100_20260302_20260506/data.parquet` |
| rank091..100 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20251107_20260227/meta/download_20260511_013607.json` | `artifacts/reports/tick_health_core200_rank091_100_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank091_100_backfill_20251107_20260227/data.parquet` |
| rank091..100 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20250801_20251106/meta/download_20260511_013723.json` | `artifacts/reports/tick_health_core200_rank091_100_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank091_100_backfill_20250801_20251106/data.parquet` |
| rank091..100 `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank091_100_backfill_20250401_20250731/meta/download_20260511_014359.json` | `artifacts/reports/tick_health_core200_rank091_100_backfill_20250401_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank091_100_backfill_20250401_20250731/data.parquet` |
| Core100 `2026-05-07` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/core100_increment_20260507_20260508/meta/download_20260511_023112.json` | `artifacts/reports/tick_health_core100_increment_20260507_20260508.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core100_increment_20260507_20260508/data.parquet` |
| 低成交尾部 25 probe `2026-03-02` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/micro_tail25_probe_20260302_20260508/meta/download_20260511_024248.json` | `artifacts/reports/tick_health_micro_tail25_probe_20260302_20260508.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/micro_tail25_probe_20260302_20260508/data.parquet` |
| 低成交非零 25 probe `2026-03-02` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/low_turnover_nonzero25_probe_20260302_20260508/meta/download_20260511_030225.json` | `artifacts/reports/tick_health_low_turnover_nonzero25_probe_20260302_20260508.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/low_turnover_nonzero25_probe_20260302_20260508/data.parquet` |
| Core200 rank101 `2025-04-01` 到 `2026-05-08` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank101_20250401_20260508/meta/download_20260511_035831.json` | `artifacts/reports/tick_health_core200_rank101_20250401_20260508.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank101_20250401_20260508/data.parquet` |

## 结论

本轮将 Core200 本地 tick 覆盖从 75/200 提升到 101/200，覆盖比例从 37.50%
提升到 50.50%。随后已将 Core100 追加更新到 `2026-05-08`。

低成交尾部 25 只 probe 消耗约 `6.0MB` quota，1150 个计划 symbol-date 中只有
184 个非空，说明这类小微盘/停牌密集池的数据量确实很小，但有效覆盖也很稀疏。

低成交非零 25 只 probe 消耗约 `1.7MB` quota，1150 个计划 symbol-date 中有
797 个非空，但 raw rows 只有 5,837。相比极尾部 probe，它的覆盖更均匀
（25 个标的、46 个交易日都有有效数据），但每个非空 symbol-date 的 tick 行数
很少。极尾部 probe 的 111,992 rows 主要由 `02629.XHKG`、`02627.XHKG`、
`01448.XHKG` 等少数标的贡献，说明 selection-window 成交额排序不能单独预测
历史 tick rows。

Core200 `rank101` 单票完整窗口消耗约 `47.6MB` provider quota，生成 270 个非空
symbol-date 分片和 1,624,038 行 raw tick，health 为 `pass` 且无 warning。

最终 quota 剩余约 `57.82MB`，但 used_pct 已到 `94.35%`，距离 `95%` quota guard
停止线只剩约 `6.6MB`。今天不再开启 `rank102` 或新的完整 Core 下载。后续 quota
重置后，最值得继续下载的是 Core200 `rank102..110` 或按 10 标的一组继续推进。
