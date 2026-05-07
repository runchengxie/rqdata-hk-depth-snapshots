# 港股 Tick Core Active15 Add-on：2026-05-07

状态：已完成。

记录日期：2026-05-07。

## 目标

在 Round 1 20 标的全周期完成后，用剩余 trial quota 扩展一个更活跃的横截面样本。
本轮不补全历史，只下载近期窗口，用于验证高流动性 add-on 标的的 tick 密度、质量门禁和
daily aggregate 形态。

## 标的选择

标的文件：`configs/universe/hk_tick_depth_core_active15_addon.txt`。

选择方法：

1. 使用 RQData `all_instruments('CS', market='hk', date='2026-05-06')`。
2. 仅保留 `status=Active` 且 `stock_connect` 非空的普通股。
3. 排除 `configs/universe/hk_tick_depth_round1_20.txt` 已覆盖标的。
4. 用 `2026-04-01` 到 `2026-05-06` 日频 `total_turnover` 排序，取前 15。

| # | RQData code | 说明 |
| ---: | --- | --- |
| 1 | `00981.XHKG` | 中芯国际 |
| 2 | `06869.XHKG` | 长飞光纤光缆 |
| 3 | `03750.XHKG` | 宁德时代 |
| 4 | `09992.XHKG` | 泡泡玛特 |
| 5 | `01211.XHKG` | 比亚迪股份 |
| 6 | `00883.XHKG` | 中国海洋石油 |
| 7 | `01347.XHKG` | 华虹半导体 |
| 8 | `00939.XHKG` | 建设银行 |
| 9 | `00175.XHKG` | 吉利汽车 |
| 10 | `02899.XHKG` | 紫金矿业 |
| 11 | `01024.XHKG` | 快手-W |
| 12 | `01398.XHKG` | 工商银行 |
| 13 | `02628.XHKG` | 中国人寿 |
| 14 | `00857.XHKG` | 中国石油股份 |
| 15 | `01378.XHKG` | 中国宏桥 |

## 下载范围

```text
日期范围：2026-03-02 到 2026-05-06
交易日：44
标的数：15
symbol-days：660
输出目录：artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_20260302_20260506
raw layout：symbol-date
batch size：3
```

下载命令：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick download \
  --symbols-file configs/universe/hk_tick_depth_core_active15_addon.txt \
  --start-date 20260302 \
  --end-date 20260506 \
  --out artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_20260302_20260506 \
  --batch-size 3 \
  --raw-layout symbol-date \
  --calendar provider \
  --resume \
  --continue-on-error \
  --retry-max-attempts 3 \
  --retry-backoff-seconds 2 \
  --retry-max-backoff-seconds 60
```

## 下载结果

| 项 | 结果 |
| --- | ---: |
| written symbol-days | 660 |
| empty remote symbol-days | 0 |
| skipped existing symbol-days | 0 |
| quota blocked symbol-days | 0 |
| failed | 0 |
| raw rows | 7,168,120 |
| raw parquet 分片 | 660 |
| raw cache 大小 | 约 360M |

quota 记录：

| 项 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| tick 下载前 | 471,516,431 | 602,225,393 | 43.91% |
| tick 下载后 | 722,341,942 | 351,399,882 | 67.27% |
| 记录时最新查询 | 724,412,988 | 349,328,836 | 67.47% |

输出记录：

| 类型 | 路径 |
| --- | --- |
| download metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_20260302_20260506/meta/download_20260506_233122.json` |
| download audit | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_20260302_20260506/audit/download_20260506_233122_26849076.csv` |
| health report | `artifacts/reports/tick_health_core_active15_addon_20260302_20260506.json` |
| health unit diagnostics | `artifacts/reports/tick_health_core_active15_addon_20260302_20260506_units.csv` |
| daily aggregate | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_20260302_20260506/data.parquet` |
| daily aggregate metadata | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_20260302_20260506/meta/aggregate_daily.json` |

## Health

| 项 | 结果 |
| --- | --- |
| dataset status | pass |
| overall severity | warning |
| failing issue count | 0 |
| raw rows | 7,168,120 |
| symbols | 15 |
| dates | 44 |
| timestamp range | 2026-03-02 09:20:34.806 到 2026-05-06 16:08:08.539 |
| warning checks | `timestamp_non_monotonic`、`volume_decrease_count`、`turnover_decrease_count` |
| timestamp 回退 | 1 |
| volume 回落 | 1 |
| turnover 回落 | 1 |
| duplicate key | 0 |
| quote ladder invalid | 0 |
| negative depth volume | 0 |
| outside session rows | 0 |

## Daily Aggregate

| 项 | 结果 |
| --- | ---: |
| aggregate rows | 660 |
| source rows | 7,168,120 |
| symbols | 15 |
| date range | 20260302 到 20260506 |
| `quote_quality_flag` | pass 660 |
| `vwap_quality_flag` | pass 659 / warning 1 |
| `coverage_quality_flag` | pass 660 |
| `tick_count_quality_flag` | pass 660 |
| `is_usable_for_research` | true 660 |
| `is_usable_for_cost_model` | true 660 |

tick rows by symbol：

| RQData code | aggregate rows | tick rows |
| --- | ---: | ---: |
| `00175.XHKG` | 44 | 443,698 |
| `00857.XHKG` | 44 | 314,024 |
| `00883.XHKG` | 44 | 768,123 |
| `00939.XHKG` | 44 | 322,139 |
| `00981.XHKG` | 44 | 776,228 |
| `01024.XHKG` | 44 | 600,903 |
| `01211.XHKG` | 44 | 586,487 |
| `01347.XHKG` | 44 | 322,723 |
| `01378.XHKG` | 44 | 431,789 |
| `01398.XHKG` | 44 | 275,887 |
| `02628.XHKG` | 44 | 308,531 |
| `02899.XHKG` | 44 | 306,538 |
| `03750.XHKG` | 44 | 309,606 |
| `06869.XHKG` | 44 | 663,909 |
| `09992.XHKG` | 44 | 737,535 |

## 配额补用回填

在最近窗口验证通过后，继续沿用同一 active15 池向前回填，并用下载器的 quota guard
将配额控制在 95% 附近。

回填命令模板：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick download \
  --symbols-file configs/universe/hk_tick_depth_core_active15_addon.txt \
  --start-date <YYYYMMDD> \
  --end-date <YYYYMMDD> \
  --out artifacts/cache/rqdata/hk_tick_depth/<run-name> \
  --batch-size 2 \
  --raw-layout symbol-date \
  --calendar provider \
  --resume \
  --continue-on-error \
  --retry-max-attempts 3 \
  --retry-backoff-seconds 2 \
  --retry-max-backoff-seconds 60 \
  --quota-stop-ratio 0.95 \
  --quota-safety-multiplier 1.2
```

下载结果：

| 窗口 | 输出目录 | 交易日 | final written | final missing | raw rows | quota after |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2025-12-11 到 2026-02-27 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251211_20260227` | 51 | 765 | 0 | 6,596,465 | 89.25% |
| 2025-11-24 到 2025-12-10 | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251124_20251210` | 13 | 195 | 0 | 1,605,800 | 94.81% |

第二个窗口原计划 195 个 symbol-days，`01378.XHKG` 在 `2025-12-10` 被 quota guard
先被 0.95 quota guard 拦下；随后单独用 `--symbols 01378.XHKG`、`2025-12-10` 和
`--quota-stop-ratio 0.99` 补齐。该单格新增 8,745 行。

quota 记录：

| 项 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 回填前最新查询 | 724,412,988 | 349,328,836 | 67.47% |
| 2025-12-11 到 2026-02-27 后 | 958,312,525 | 115,429,299 | 89.25% |
| 2025-11-24 到 2025-12-10 初次回填后 | 1,017,115,185 | 56,626,639 | 94.73% |
| 补齐 `01378.XHKG` / `2025-12-10` 后 | 1,017,983,058 | 55,758,766 | 94.81% |

回填输出记录：

| 类型 | 2025-12-11 到 2026-02-27 | 2025-11-24 到 2025-12-10 |
| --- | --- | --- |
| download metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251211_20260227/meta/download_20260506_233907.json` | 初次：`artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251124_20251210/meta/download_20260506_234520.json`；补丁：`artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251124_20251210/meta/download_20260507_005243.json` |
| download audit | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251211_20260227/audit/download_20260506_233907_51abd0af.csv` | 初次：`artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251124_20251210/audit/download_20260506_234520_7e2e3657.csv`；补丁：`artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251124_20251210/audit/download_20260507_005240_2794888b.csv` |
| health report | `artifacts/reports/tick_health_core_active15_addon_backfill_20251211_20260227.json` | `artifacts/reports/tick_health_core_active15_addon_backfill_20251124_20251210.json` |
| health unit diagnostics | `artifacts/reports/tick_health_core_active15_addon_backfill_20251211_20260227_units.csv` | `artifacts/reports/tick_health_core_active15_addon_backfill_20251124_20251210_units.csv` |
| daily aggregate | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251211_20260227/data.parquet` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251124_20251210/data.parquet` |
| daily aggregate metadata | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251211_20260227/meta/aggregate_daily.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251124_20251210/meta/aggregate_daily.json` |

回填健康检查：

| 窗口 | status | overall severity | warnings | failures | duplicate key | quote ladder invalid | negative depth volume | outside session rows |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2025-12-11 到 2026-02-27 | pass | warning | `timestamp_non_monotonic_count=3`、`volume_decrease_count=3`、`turnover_decrease_count=3` | 0 | 0 | 0 | 0 | 0 |
| 2025-11-24 到 2025-12-10 | pass | none | 无 | 0 | 0 | 0 | 0 | 0 |

回填日频聚合：

| 窗口 | aggregate rows | source rows | symbols | date range | quality flags |
| --- | ---: | ---: | ---: | --- | --- |
| 2025-12-11 到 2026-02-27 | 765 | 6,596,465 | 15 | 20251211 到 20260227 | quote pass 765；vwap pass 762 / warning 3；coverage pass 765；tick count pass 765；research true 765；cost model true 765 |
| 2025-11-24 到 2025-12-10 | 195 | 1,605,800 | 15 | 20251124 到 20251210 | quote pass 195；vwap pass 195；coverage pass 195；tick count pass 195；research true 195；cost model true 195 |

## 追加补用到 99.79%

在 `2025-11-24` 到 `2026-05-06` 连续样本完成后，继续优先补同一 active15 池的
更早窗口；未再开启次选池，因为首选窗口已经把 quota 用到 99.79%，剩余硬配额只有
约 2.11MB。

下载策略：

1. 先跑 `2025-11-07` 到 `2025-11-21` 全 active15，`batch-size=2`，
   `--quota-stop-ratio 0.99`。
2. quota guard 后，改用 `batch-size=1` 逐日补齐 `2025-11-19`、`2025-11-20`。
3. 最后用 `batch-size=1` 尝试 `2025-11-21`，`--quota-stop-ratio 0.999`，
   在 6 个 symbol-days 后停止。

下载结果：

| 步骤 | 日期 | written | quota blocked | raw rows | quota after |
| --- | --- | ---: | ---: | ---: | ---: |
| 初次窗口 | 2025-11-07 到 2025-11-21 | 124 | 41 | 1,123,256 | 98.51% |
| 单日补齐 | 2025-11-19 | 11 | 0 | 75,243 | 98.75% |
| 单日补齐 | 2025-11-20 | 15 | 0 | 152,527 | 99.25% |
| 单日尝试 | 2025-11-21 | 6 | 9 | 82,999 | 99.79% |

最终覆盖：

| 项 | 结果 |
| --- | ---: |
| output root | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121` |
| raw rows | 1,434,025 |
| parquet 分片 | 156 |
| expected symbol-days | 165 |
| completed symbol-days | 156 |
| missing symbol-days | 9 |
| final quota used | 1,071,525,077 bytes / 99.79% |
| final quota remaining | 2,216,747 bytes / 2.11MB |

缺失单元均在 `2025-11-21`：

```text
00175.XHKG, 00857.XHKG, 00939.XHKG, 01024.XHKG, 01347.XHKG,
01378.XHKG, 01398.XHKG, 02628.XHKG, 02899.XHKG
```

输出记录：

| 类型 | 路径 |
| --- | --- |
| initial metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/meta/download_20260507_010910.json` |
| 2025-11-19 patch metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/meta/download_20260507_011109.json` |
| 2025-11-20 patch metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/meta/download_20260507_011142.json` |
| 2025-11-21 patch metadata | `artifacts/cache/rqdata/hk_tick_depth/core_active15_addon_backfill_20251107_20251121/meta/download_20260507_011207.json` |
| health report | `artifacts/reports/tick_health_core_active15_addon_backfill_20251107_20251121.json` |
| health unit diagnostics | `artifacts/reports/tick_health_core_active15_addon_backfill_20251107_20251121_units.csv` |
| daily aggregate | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251107_20251121/data.parquet` |
| daily aggregate metadata | `artifacts/cache/rqdata/hk_tick_depth_daily/core_active15_addon_backfill_20251107_20251121/meta/aggregate_daily.json` |

健康检查：

| 项 | 结果 |
| --- | --- |
| status | pass |
| overall severity | warning |
| raw rows | 1,434,025 |
| symbols | 15 |
| dates | 11 |
| warnings | `timestamp_non_monotonic_count=1`、`volume_decrease_count=1`、`turnover_decrease_count=1` |
| failures | 0 |
| duplicate key | 0 |
| quote ladder invalid | 0 |
| negative depth volume | 0 |
| outside session rows | 0 |

日频聚合：

| 项 | 结果 |
| --- | ---: |
| aggregate rows | 156 |
| source rows | 1,434,025 |
| date range | 20251107 到 20251121 |
| completed full dates | 20251107 到 20251120 |
| partial date | 20251121：6 / 15 symbol-days |
| `quote_quality_flag` | pass 156 |
| `vwap_quality_flag` | pass 155 / warning 1 |
| `coverage_quality_flag` | pass 156 |
| `tick_count_quality_flag` | pass 156 |
| `is_usable_for_research` | true 156 |
| `is_usable_for_cost_model` | true 156 |

## 结论

这批 add-on 样本比 Round 1 的尾部/empty 样本更适合作为核心池扩展候选。15 个标的
在最近 44 个交易日全部有 tick 数据，质量门禁通过，且每日聚合全部可用于 research。
本轮额外把同一池回填到 `2025-11-24`，并补齐 0.95 guard 最初拦下的
`01378.XHKG` / `2025-12-10`。随后继续向前补到 `2025-11-07`，最终配额停在
99.79%。active15 已完整覆盖 `2025-11-07` 到 `2026-05-06`，但 `2025-11-21`
还有 9 个 symbol-days 因 quota guard 未取；若只使用完整面板，可从 `2025-11-24`
开始。后续 quota 重置后，可以优先补齐 `2025-11-21` 剩余 9 格，再把这 15 个标的
继续向前补到 `2025-04-01`，或者按相同方法继续筛选下一组 active add-on。
