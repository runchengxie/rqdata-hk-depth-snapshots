# 港股 Tick 日常补下载：2026-05-09

状态：已完成。

记录日期：2026-05-09。

说明：下载 metadata 文件名中的 `20260509` 来自运行时 UTC 时间戳；本文按本地
`Asia/Shanghai` 日期记录。

## 目标

今天按“先补连续历史，再扩高成交横截面”的顺序使用 trial quota：

1. 补齐 `core_active10_addon2` 从 provider 最早 tick 日 `2025-04-01` 到
   `2025-07-31` 的早期窗口。
2. 新增第三组高成交港股通 add-on 标的 `core_active15_addon3`。
3. 将 add-on3 从近期窗口向前回填到 `2025-04-01`。

所有下载均使用 `symbol-date` raw layout、provider calendar、`--resume`、
`--continue-on-error` 和 quota guard。

## Quota

| 时点 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 开跑前 | 18,782,752 | 1,054,959,072 | 1.75% |
| add-on2 `2025-04-01` 到 `2025-07-31` 后 | 102,354,813 | 971,387,011 | 9.53% |
| add-on3 `2026-03-02` 到 `2026-05-06` 后 | 274,698,399 | 799,043,425 | 25.58% |
| add-on3 `2025-11-07` 到 `2026-02-27` 后 | 490,707,429 | 583,034,395 | 45.70% |
| add-on3 `2025-08-01` 到 `2025-11-06` 后 | 744,266,963 | 329,474,861 | 69.32% |
| add-on3 `2025-06-02` 到 `2025-07-31` 后 | 899,960,038 | 173,781,786 | 83.82% |
| add-on3 `2025-05-02` 到 `2025-05-30` 后 | 965,763,298 | 107,978,526 | 89.94% |
| add-on3 `2025-04-01` 到 `2025-04-30` 首次后 | 1,012,749,856 | 60,991,968 | 94.32% |
| add-on3 `2025-04-14` 到 `2025-04-30` 尾部续补后 | 1,042,616,782 | 31,125,042 | 97.10% |
| 最终查询 | 1,046,804,806 | 26,937,018 | 97.49% |

最终剩余约 `25.69MB`。4 月首次下载使用 `--quota-stop-ratio 0.95`，随后用
`batch-size=1` 和 `--quota-stop-ratio 0.99` 续补尾部，因此最终高于 95%。

## Add-on2 早期回填

标的文件：`configs/universe/hk_tick_depth_core_active10_addon2.txt`。

| 窗口 | output root | planned | written | empty remote | quota blocked | raw rows | health | aggregate rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250401_20250731` | 820 | 492 | 328 | 0 | 2,425,484 | pass / warning | 492 |

该窗口完成后，add-on2 已覆盖从 `2025-04-01` 到 `2026-05-06` 的目标区间。

## Add-on3 标的

新建标的文件：`configs/universe/hk_tick_depth_core_active15_addon3.txt`。

选择方法：

1. 使用 `2026-05-06` 的 active HK CS instruments。
2. 仅保留 `stock_connect` 非空标的。
3. 排除 Round 1 20、`core_active15_addon` 和 `core_active10_addon2`。
4. 按 `2026-04-01` 到 `2026-05-06` 日频 `total_turnover` 排序取前 15。

| # | RQData code | 名称 | 排序窗口 total_turnover |
| ---: | --- | --- | ---: |
| 1 | `00568.XHKG` | 山东墨龙 | 20,936,840,000 |
| 2 | `01530.XHKG` | 三生制药 | 20,384,860,000 |
| 3 | `09868.XHKG` | 小鹏集团-W | 20,069,800,000 |
| 4 | `03993.XHKG` | 洛阳钼业 | 19,494,740,000 |
| 5 | `02269.XHKG` | 药明生物 | 19,369,390,000 |
| 6 | `03986.XHKG` | 兆易创新 | 18,813,540,000 |
| 7 | `02382.XHKG` | 舜宇光学科技 | 17,725,630,000 |
| 8 | `02338.XHKG` | 潍柴动力 | 16,597,100,000 |
| 9 | `03968.XHKG` | 招商银行 | 16,509,970,000 |
| 10 | `09660.XHKG` | 地平线机器人-W | 16,081,090,000 |
| 11 | `03896.XHKG` | 金山云 | 15,886,690,000 |
| 12 | `02020.XHKG` | 安踏体育 | 15,844,310,000 |
| 13 | `02359.XHKG` | 药明康德 | 15,567,640,000 |
| 14 | `06160.XHKG` | 百济神州 | 15,241,180,000 |
| 15 | `01093.XHKG` | 石药集团 | 15,240,190,000 |

## Add-on3 下载结果

| 窗口 | output root | planned | completed parts | written | empty remote | quota blocked | raw rows | health | aggregate rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_20260302_20260506` | 660 | 660 | 660 | 0 | 0 | 4,472,957 | pass / warning | 660 |
| `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20251107_20260227` | 1,125 | 1,125 | 1,081 | 44 | 0 | 6,062,479 | pass / none | 1,081 |
| `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250801_20251106` | 1,005 | 1,005 | 938 | 67 | 0 | 6,968,986 | pass / warning | 938 |
| `2025-06-02` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250602_20250731` | 645 | 645 | 602 | 43 | 0 | 4,503,184 | pass / warning | 602 |
| `2025-05-02` 到 `2025-05-30` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250502_20250530` | 300 | 300 | 280 | 20 | 0 | 1,874,529 | pass / warning | 280 |
| `2025-04-01` 到 `2025-04-30` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250401_20250430` | 285 | 285 | 266 | 19 | 0 | 2,052,895 | pass / warning | 266 |

4 月窗口先被 0.95 quota guard 截在 `2025-04-14` 之后，随后用 `batch-size=1`、
`--quota-stop-ratio 0.99` 从 `2025-04-14` 继续，最终计划单元已全部处理。尾部续补
metadata 中的 `skipped_existing=8` 是首次下载已经写入的 `2025-04-14` 分片。

## 质量与聚合

所有 health 检查均为 `pass`，没有 failure。warning 均为少量累计字段回落或时间戳
非单调诊断；无 duplicate key、quote ladder invalid、negative depth volume 或
outside session rows。

| 数据集 | health rows | parts | symbols | dates | warnings | failures |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| add-on2 `2025-04-01` 到 `2025-07-31` | 2,425,484 | 820 | 6 | 82 | timestamp 1；volume 1；turnover 1 | 0 |
| add-on3 `2026-03-02` 到 `2026-05-06` | 4,472,957 | 660 | 15 | 44 | timestamp 1；volume 1；turnover 1 | 0 |
| add-on3 `2025-11-07` 到 `2026-02-27` | 6,062,479 | 1,125 | 15 | 75 | 无 | 0 |
| add-on3 `2025-08-01` 到 `2025-11-06` | 6,968,986 | 1,005 | 14 | 67 | timestamp 1；volume 1；turnover 1 | 0 |
| add-on3 `2025-06-02` 到 `2025-07-31` | 4,503,184 | 645 | 14 | 43 | timestamp 1；volume 1；turnover 1 | 0 |
| add-on3 `2025-05-02` 到 `2025-05-30` | 1,874,529 | 300 | 14 | 20 | timestamp 1；volume 1；turnover 1 | 0 |
| add-on3 `2025-04-01` 到 `2025-04-30` | 2,052,895 | 285 | 14 | 19 | timestamp 1；volume 1；turnover 1 | 0 |

## 输出记录

| 数据集 | download metadata | download audit |
| --- | --- | --- |
| add-on2 `2025-04-01` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250401_20250731/meta/download_20260509_130119.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active10_addon2_backfill_20250401_20250731/audit/download_20260509_130119_8d286592.csv` |
| add-on3 `2026-03-02` 到 `2026-05-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_20260302_20260506/meta/download_20260509_130454.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_20260302_20260506/audit/download_20260509_130454_09ca1fe2.csv` |
| add-on3 `2025-11-07` 到 `2026-02-27` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20251107_20260227/meta/download_20260509_130734.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20251107_20260227/audit/download_20260509_130734_dc61bd0c.csv` |
| add-on3 `2025-08-01` 到 `2025-11-06` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250801_20251106/meta/download_20260509_131117.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250801_20251106/audit/download_20260509_131117_b9a1f651.csv` |
| add-on3 `2025-06-02` 到 `2025-07-31` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250602_20250731/meta/download_20260509_131523.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250602_20250731/audit/download_20260509_131523_113f4276.csv` |
| add-on3 `2025-05-02` 到 `2025-05-30` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250502_20250530/meta/download_20260509_131812.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250502_20250530/audit/download_20260509_131812_a1e4db57.csv` |
| add-on3 `2025-04-01` 到 `2025-04-30` 首次 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250401_20250430/meta/download_20260509_131941.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250401_20250430/audit/download_20260509_131941_821fff8e.csv` |
| add-on3 `2025-04-14` 到 `2025-04-30` 尾部续补 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250401_20250430/meta/download_20260509_132048.json` | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon3_backfill_20250401_20250430/audit/download_20260509_132046_b78fcc7f.csv` |

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| add-on2 `2025-04-01` 到 `2025-07-31` | `artifacts/reports/tick_health_core_active10_addon2_backfill_20250401_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active10_addon2_backfill_20250401_20250731/data.parquet` |
| add-on3 `2026-03-02` 到 `2026-05-06` | `artifacts/reports/tick_health_core_active15_addon3_20260302_20260506.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_20260302_20260506/data.parquet` |
| add-on3 `2025-11-07` 到 `2026-02-27` | `artifacts/reports/tick_health_core_active15_addon3_backfill_20251107_20260227.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_backfill_20251107_20260227/data.parquet` |
| add-on3 `2025-08-01` 到 `2025-11-06` | `artifacts/reports/tick_health_core_active15_addon3_backfill_20250801_20251106.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_backfill_20250801_20251106/data.parquet` |
| add-on3 `2025-06-02` 到 `2025-07-31` | `artifacts/reports/tick_health_core_active15_addon3_backfill_20250602_20250731.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_backfill_20250602_20250731/data.parquet` |
| add-on3 `2025-05-02` 到 `2025-05-30` | `artifacts/reports/tick_health_core_active15_addon3_backfill_20250502_20250530.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_backfill_20250502_20250530/data.parquet` |
| add-on3 `2025-04-01` 到 `2025-04-30` | `artifacts/reports/tick_health_core_active15_addon3_backfill_20250401_20250430.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon3_backfill_20250401_20250430/data.parquet` |

## 结论

今天完成两个连续性目标：

1. `core_active10_addon2` 已从 `2025-04-01` 连续覆盖到 `2026-05-06`。
2. 新增 `core_active15_addon3`，并已从 `2025-04-01` 连续覆盖到 `2026-05-06`。

最终 quota 用到 97.49%，剩余约 25.69MB。后续 quota 重置后，最值得继续做的是按
同一规则选择 add-on4，或者开始把更大的 Core 池拆成 15-20 标的一组向外扩展。
