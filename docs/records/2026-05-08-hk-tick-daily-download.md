# 港股 Tick 日常补下载：2026-05-08

状态：已完成。

记录日期：2026-05-08。

说明：下载 metadata 文件名中的 `20260507` 来自运行时 UTC 时间戳；本文按本地
`Asia/Shanghai` 日期记录。

## 目标

今天按“首选优先、剩余配额再做次选”的顺序使用 trial quota：

1. 补齐 `core_active15_addon` 在 `2025-11-21` 剩余的 9 个 symbol-days。
2. 将同一 active15 池继续向前补到 `2025-04-01`。
3. 如 quota 仍充足，新增第二组 active add-on 标的，并优先覆盖近期窗口。

所有新下载均使用 `symbol-date` raw layout、provider calendar、`--resume`、
`--continue-on-error` 和 quota guard。

## Quota

| 时点 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 开跑前 | 0 | 1,073,741,824 | 0.00% |
| active15 2025-11-21 补丁后 | 2,310,336 | 1,071,431,488 | 0.22% |
| active15 2025-04-01 到 2025-11-06 后 | 691,901,697 | 381,840,127 | 64.44% |
| add-on2 2026-03-02 到 2026-05-06 后 | 803,335,101 | 270,406,723 | 74.82% |
| add-on2 2025-11-07 到 2026-02-27 后 | 909,668,741 | 164,073,083 | 84.72% |
| add-on2 2025-10-30 到 2025-11-06 尾部续补后 | 1,023,022,555 | 50,719,269 | 95.28% |
| 最终查询 | 1,023,481,808 | 50,260,016 | 95.32% |

最终剩余约 `47.93MB`。最早窗口的第一次下载使用 `--quota-stop-ratio 0.95`，
随后用 `batch-size=1` 和 `--quota-stop-ratio 0.99` 续补尾部，因此最终略高于 95%。

## Active15 修补与回填

标的文件：`configs/universe/hk_tick_depth_core_active15_addon.txt`。

今天先补齐上一轮 quota guard 留下的 `2025-11-21` 9 个 symbol-days，随后回填
`2025-04-01` 到 `2025-11-06`。

| 窗口 | output root | planned | written | empty remote | quota blocked | raw rows | health | aggregate rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `2025-11-21` 缺口补丁 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121` | 9 | 9 | 0 | 0 | 73,114 | pass / warning | 165 |
| `2025-04-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20250401_20251106` | 2,235 | 2,205 | 30 | 0 | 20,827,901 | pass / warning | 2,205 |

`2025-04-01` 到 `2025-11-06` 的 30 个 `empty_remote` 全部为
`03750.XHKG` 在 `2025-04-01` 到 `2025-05-19` 的 provider 空返回；下载器已落空
part 作为覆盖记录，不属于失败。

修补后 active15 在 `2025-04-01` 到 `2026-05-06` 覆盖 268 个交易日；其中
非空日频聚合行数为 3,990，另有 30 个 provider empty symbol-days。

## Add-on2 标的

新建标的文件：`configs/universe/hk_tick_depth_core_active10_addon2.txt`。

选择方法：

1. 使用 `2026-05-06` 的 active HK CS instruments。
2. 仅保留 `stock_connect` 非空标的。
3. 排除 Round 1 20 标的和 `core_active15_addon` 15 标的。
4. 按 `2026-04-01` 到 `2026-05-06` 日频 `total_turnover` 排序取前 10。

| # | RQData code | 名称 | 排序窗口 total_turnover |
| ---: | --- | --- | ---: |
| 1 | `06166.XHKG` | 剑桥科技 | 30,217,747,568 |
| 2 | `03317.XHKG` | 迅策 | 28,142,455,384 |
| 3 | `09926.XHKG` | 康方生物 | 27,462,603,143 |
| 4 | `00992.XHKG` | 联想集团 | 25,394,796,703 |
| 5 | `01801.XHKG` | 信达生物 | 23,694,428,036 |
| 6 | `01888.XHKG` | 建滔积层板 | 23,656,551,337 |
| 7 | `01772.XHKG` | 赣锋锂业 | 22,696,663,731 |
| 8 | `02259.XHKG` | 紫金黄金国际 | 22,376,394,882 |
| 9 | `03988.XHKG` | 中国银行 | 21,578,152,496 |
| 10 | `01384.XHKG` | 滴普科技 | 20,992,562,108 |

## Add-on2 下载结果

| 窗口 | output root | planned | completed parts | written | empty remote | quota blocked | raw rows | health | aggregate rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_20260302_20260506` | 440 | 440 | 440 | 0 | 0 | 2,710,077 | pass / none | 440 |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20251107_20260227` | 750 | 750 | 715 | 35 | 0 | 2,861,110 | pass / warning | 715 |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250801_20251106` | 670 | 670 | 441 | 229 | 0 | 3,007,318 | pass / none | 441 |

`2025-11-07` 到 `2026-02-27` 的 35 个 `empty_remote` 全部为
`03317.XHKG`。`2025-08-01` 到 `2025-11-06` 的 229 个 `empty_remote`
主要来自较晚上市或 provider 空返回标的：

| RQData code | empty remote |
| --- | ---: |
| `06166.XHKG` | 60 |
| `03317.XHKG` | 67 |
| `02259.XHKG` | 42 |
| `01384.XHKG` | 60 |

最后一个窗口第一次下载时被 0.95 quota guard 截停。随后用 `batch-size=1`、
`--quota-stop-ratio 0.99` 续补 `2025-10-30` 到 `2025-11-06`，计划单元已全部处理：

| 项 | 结果 |
| --- | ---: |
| planned | 60 |
| skipped existing | 7 |
| written | 47 |
| empty remote | 6 |
| quota blocked | 0 |
| failed | 0 |
| raw rows | 269,049 |

续补中的 6 个 `empty_remote` 均为 `03317.XHKG`，日期为 `2025-10-30`、
`2025-10-31`、`2025-11-03`、`2025-11-04`、`2025-11-05`、`2025-11-06`。

## 质量与聚合

所有 health 检查均为 `pass`，没有 failure。warning 均为少量累计字段回落或时间戳
非单调诊断；无 duplicate key、quote ladder invalid、negative depth volume 或
outside session rows。

| 数据集 | health rows | parts | symbols | dates | warnings | failures | daily quality flags |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| active15 `2025-04-01` 到 `2025-11-06` | 20,827,901 | 2,235 | 15 | 149 | timestamp 5；volume 5；turnover 6 | 0 | quote pass 2,205；vwap pass 2,199 / warning 6；research true 2,205 |
| active15 `2025-11-07` 到 `2025-11-21` | 1,507,139 | 165 | 15 | 11 | timestamp 1；volume 1；turnover 1 | 0 | quote pass 165；vwap pass 164 / warning 1；research true 165 |
| add-on2 `2026-03-02` 到 `2026-05-06` | 2,710,077 | 440 | 10 | 44 | 无 | 0 | quote pass 440；vwap pass 440；research true 440 |
| add-on2 `2025-11-07` 到 `2026-02-27` | 2,861,110 | 750 | 10 | 75 | turnover 1 | 0 | quote pass 715；vwap pass 714 / warning 1；research true 715 |
| add-on2 `2025-08-01` 到 `2025-11-06` | 3,007,318 | 670 | 9 | 67 | 无 | 0 | quote pass 441；vwap pass 441；research true 441 |

## 输出记录

| 数据集 | download metadata | download audit |
| --- | --- | --- |
| active15 `2025-11-21` 补丁 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/meta/download_20260507_220005.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/audit/download_20260507_220002_238203f4.csv` |
| active15 `2025-04-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20250401_20251106/meta/download_20260507_220027.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20250401_20251106/audit/download_20260507_220027_69d27a1c.csv` |
| add-on2 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_20260302_20260506/meta/download_20260507_221840.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_20260302_20260506/audit/download_20260507_221840_66f7b98c.csv` |
| add-on2 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20251107_20260227/meta/download_20260507_222028.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20251107_20260227/audit/download_20260507_222028_0d99ff6d.csv` |
| add-on2 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250801_20251106/meta/download_20260507_222253.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250801_20251106/audit/download_20260507_222253_372add03.csv` |
| add-on2 `2025-10-30` 到 `2025-11-06` 尾部续补 | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250801_20251106/meta/download_20260507_233118.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250801_20251106/audit/download_20260507_233111_f00d799f.csv` |

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| active15 `2025-11-07` 到 `2025-11-21` | `artifacts/reports/tick_health_core_active15_addon_backfill_20251107_20251121.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251107_20251121/data.parquet` |
| active15 `2025-04-01` 到 `2025-11-06` | `artifacts/reports/tick_health_core_active15_addon_backfill_20250401_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20250401_20251106/data.parquet` |
| add-on2 `2026-03-02` 到 `2026-05-06` | `artifacts/reports/tick_health_core_active10_addon2_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active10_addon2_20260302_20260506/data.parquet` |
| add-on2 `2025-11-07` 到 `2026-02-27` | `artifacts/reports/tick_health_core_active10_addon2_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active10_addon2_backfill_20251107_20260227/data.parquet` |
| add-on2 `2025-08-01` 到 `2025-11-06` | `artifacts/reports/tick_health_core_active10_addon2_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active10_addon2_backfill_20250801_20251106/data.parquet` |

## 结论

今天的首选任务已完成：active15 昨天剩余的 9 格已补齐，并已向前扩展到
`2025-04-01`。次选任务也完成了最近窗口和回填窗口；在额外放宽到 0.99 guard
后，`2025-08-01` 到 `2025-11-06` 的计划单元也已全部处理。最终停在 95.32%
quota，保留约 48MB 给后续小补丁或查询。

后续 quota 重置后，最值得优先做的是继续把 add-on2 往 `2025-04-01` 回填。
