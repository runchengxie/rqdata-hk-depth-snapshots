# 港股 Tick 下载进展：2026-05-23

状态：最新交易日增量完成，non-connect 扩展在 99.5% quota guard 前收口。

记录日期：2026-05-23（Asia/Shanghai）。本轮最新已确认可取交易日为
`2026-05-22`。

## 摘要

- 真实 quota 已刷新；开工时已用 `31.08 MB`（`3.04%`），trial 剩余 3 天。
- 以 `00700.XHKG` 探测 `2026-05-22` 返回 28,464 行，确认最新完整交易日可取。
- 以 `2026-05-21` live active 港股通选择口径为基础，将本地 Core894 加 3 只
  addon 共 897 只标的推进到 `2026-05-22`。
- 续完 non-connect top100 在上一轮 quota guard 前留下的历史缺口，并补
  `2026-05-22` 增量。
- 下载 non-connect rank101..200 和 rank201..300 的完整窗口
  `2025-04-01..2026-05-22`；配合 top100 缓存，形成可组合的 top300 扩展覆盖。
- 本次接续开始前，本地 raw metadata 还显示 non-connect `rank301..1200`
  已按同一排序口径完整下载；本次继续完成 `rank1201..1300`，并将
  `rank1301..1400` 推进至 quota guard 截停点。
- 本次新增验证的 `rank1201..1300` full 与 `rank1301..1400` partial
  health 均为 `status=pass`，无 warning 或 failure。
- `rank1301..1400` 从 `2025-10-28` 起被 `0.995` quota guard 拦截；
  最终 quota 为 `99.48%`，继续请求一个有数据的 tick batch 已不合理。

最终 quota：

| 项 | 值 |
| --- | ---: |
| bytes_used | 1018.65 MB |
| bytes_remaining | 5.35 MB |
| used_pct | 99.48% |
| remaining_days | 3 |

## Universe 变更

新增文件并同步登记到 `configs/universe/hk_tick_depth/manifest.yml`：

| 文件 | 说明 |
| --- | --- |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank201_300_20260521.txt` | 从既有 non-connect top300 selection 取 rank201..300 的独立下载池，避免重复下载 top200 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank1201_1300_20260521.txt` | 从既有 non-connect selection 取 rank1201..1300 的完整历史下载池 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank1301_1400_20260521.txt` | 从既有 non-connect selection 取 rank1301..1400 的 quota-guarded 历史下载池 |

## 港股通最新日增量

以下 raw root 均位于 `artifacts/cache/rqdata/hk_tick_depth/`；每个目录内保存本轮
`meta/download_*.json` 和 `audit/download_*.csv`。

| 数据集 | 结果 | raw rows |
| --- | --- | ---: |
| `core300_increment_20260522` | written 300 | 1,115,527 |
| `core500_rank301_500_increment_20260522` | written 200 | 223,658 |
| `core600_rank501_540_increment_20260522` | written 40 | 20,679 |
| `core600_rank541_580_increment_20260522` | written 40 | 19,182 |
| `core640_rank581_620_increment_20260522` | written 40 | 16,675 |
| `core700_rank621_660_increment_20260522` | written 40 | 7,809 |
| `core700_rank661_700_increment_20260522` | written 40 | 4,380 |
| `core740_rank701_740_increment_20260522` | written 40 | 4,935 |
| `core780_rank741_780_increment_20260522` | written 39, empty 1 | 1,767 |
| `core820_rank781_820_increment_20260522` | written 39, empty 1 | 1,601 |
| `core860_rank821_860_increment_20260522` | written 36, empty 4 | 538 |
| `core894_rank861_894_increment_20260522` | written 6, empty 28 | 54 |
| `hkconnect_addon_20260521_increment_20260522` | written 3 | 18,002 |
| **合计** | **written 863, empty 34, failed 0** | **1,434,807** |

这 13 个增量目录均生成对应 `artifacts/reports/tick_health_*.json` 与
`artifacts/cache/rqdata/hk_tick_depth_daily/<dataset>/data.parquet`；health 全部
`pass` 且无 warning，日频有数据行合计 863。

## Non-connect 扩展

| 数据集 | metadata / audit | 结果 |
| --- | --- | --- |
| Top100 history resume through `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_20250401_20260521/meta/download_20260523_110012.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_20250401_20260521/audit/download_20260523_105702_44c28ce6.csv` | written 597, skipped 18,678, empty 8,625, failed 0; new raw rows 751,808 |
| Top100 `2026-05-22` increment | `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_increment_20260522/meta/download_20260523_110559.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_increment_20260522/audit/download_20260523_110559_458d8fb5.csv` | written 100, raw rows 145,899 |
| Rank101..200 full | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank101_200_20250401_20260522/meta/download_20260523_110736.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank101_200_20250401_20260522/audit/download_20260523_110736_4e62e947.csv` | written 25,086, empty 2,914, raw rows 4,731,570 |
| Rank201..300 full | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank201_300_20250401_20260522/meta/download_20260523_112519.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank201_300_20250401_20260522/audit/download_20260523_112518_7fbff2c7.csv` | written 24,538, empty 3,462, raw rows 2,322,999 |

## 同日续接至 99.5% quota guard

以下 raw cache 均使用窗口 `2025-04-01..2026-05-22`。`rank301..1200`
是在本次接续开始前已存在并从 metadata 核验的下载产物；`rank1201..1400`
为本次接续新增。

| 数据集 | 结果 | raw rows |
| --- | --- | ---: |
| Rank301..400 full | written 25,717, empty 2,283, failed 0 | 1,513,503 |
| Rank401..500 full | written 25,166, empty 2,834, failed 0 | 1,390,029 |
| Rank501..800 full | written 73,125, empty 10,875, failed 0 | 2,357,382 |
| Rank801..1200 full | written 88,176, empty 23,824, failed 0 | 1,605,891 |
| Rank1201..1300 full | written 20,375, empty 7,625, failed 0 | 324,728 |
| Rank1301..1400 partial | written 9,695, empty 4,505, quota blocked 13,800, failed 0 | 169,622 |

本次新增 run 级产物：

| 数据集 | metadata / audit |
| --- | --- |
| Rank1201..1300 full | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1201_1300_20250401_20260522/meta/download_20260523_145919.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1201_1300_20250401_20260522/audit/download_20260523_145919_0eccfbf4.csv` |
| Rank1301..1400 partial | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1301_1400_20250401_20260522/meta/download_20260523_152106.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1301_1400_20250401_20260522/audit/download_20260523_152105_ef4ea52d.csv` |

## Health 与聚合

| 数据集 | health / daily aggregate | 结果 |
| --- | --- | --- |
| Non-connect top100 history through `2026-05-21` | `artifacts/reports/tick_health_non_connect_top100_20250401_20260521.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_top100_20250401_20260521/data.parquet` | pass with warnings; 21,599,090 raw rows, 19,275 daily rows |
| Non-connect top100 `2026-05-22` | `artifacts/reports/tick_health_non_connect_top100_increment_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_top100_increment_20260522/data.parquet` | pass; 145,899 raw rows, 100 daily rows |
| Non-connect rank101..200 | `artifacts/reports/tick_health_non_connect_rank101_200_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank101_200_20250401_20260522/data.parquet` | pass with warnings; 4,731,570 raw rows, 25,086 daily rows |
| Non-connect rank201..300 | `artifacts/reports/tick_health_non_connect_rank201_300_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank201_300_20250401_20260522/data.parquet` | pass with warnings; 2,322,999 raw rows, 24,538 daily rows |
| Non-connect rank1201..1300 | `artifacts/reports/tick_health_non_connect_rank1201_1300_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank1201_1300_20250401_20260522/data.parquet` | pass; 324,728 raw rows, 20,375 daily rows |
| Non-connect rank1301..1400 partial | `artifacts/reports/tick_health_non_connect_rank1301_1400_20250401_20260522_partial.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank1301_1400_20250401_20260522_partial/data.parquet` | pass; 169,622 raw rows, 9,695 daily rows |

warning 类型及计数：

| 数据集 | warning |
| --- | --- |
| Non-connect top100 history | `timestamp_non_monotonic_count=5`、`volume_decrease_count=5`、`turnover_decrease_count=9` |
| Non-connect rank101..200 | `turnover_decrease_count=1` |
| Non-connect rank201..300 | `turnover_decrease_count=6` |

这些 warning 与既有 raw tick 质量边界一致，未触发 error gate。

`rank301..1200` 的 raw cache 在本次接续开始前已存在；本次未为这四个较大段
补做 health 或 aggregate，应在后续离线整理阶段补齐。

## 覆盖结论

- 基于 `2026-05-21` live active 港股通选择快照的 897 只标的已覆盖至
  `2026-05-22`。
- Non-connect top100 已有历史缓存到 `2026-05-21` 并单独补齐
  `2026-05-22` 增量；rank101..1300 已下载完整窗口
  `2025-04-01..2026-05-22`，其中 rank301..1200 待补离线质量产物。
- Rank1301..1400 已完整落盘至 `2025-10-27`，`2025-10-28` 起的剩余
  13,800 个 symbol-date 单元可在 quota 重置后以 `--resume` 补齐。
- 覆盖按多个 raw/daily cache 目录组合使用；本轮不改写或合并既有 cache。
- 下一优先级为下一个可确认完整交易日的 897 只港股通增量、non-connect
  已覆盖池增量，以及 `rank1301..1400` 的历史 resume。
