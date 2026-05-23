# 港股 Tick 下载进展：2026-05-22

状态：追加下载完成，quota guard 截停。

记录日期：2026-05-22（Asia/Shanghai）。

## 摘要

本轮按 95% quota 思路继续下载。由于 RQData tick 权限窗口拒绝早于
`2025-04-01` 的请求，未继续做 `2024-01-01..2025-03-31` 回填。当前本地
`2026-05-06` 港股通候选选择文件有 894 只；live RQData
`all_instruments("CS", market="hk", date="2026-05-21")` 显示 Active 普通股
2746 只，其中 `stock_connect` 非空 897 只。

新增处理：

- 补齐 Core820、Core860、Core894 历史窗口到 `2026-05-20`。
- 追加本地 894 只港股通候选的 `2026-05-21` 单日增量。
- 补当前 active 港股通相对本地 894 只选择缺失的 3 只：
  `01236.XHKG`、`02476.XHKG`、`03296.XHKG`。
- 生成非港股通 active 普通股扩展池，并按 `2026-04-20..2026-05-21`
  日频 `total_turnover` 排序下载 top100，直到 quota guard 停在 94.81%。

最终 quota：

| 项 | 值 |
| --- | ---: |
| bytes_used | 970.83 MB |
| bytes_remaining | 53.17 MB |
| used_pct | 94.81% |
| remaining_days | 4 |

## Universe 变更

新增配置文件：

| 文件 | 说明 |
| --- | --- |
| `configs/universe/hk_tick_depth/current/hk_tick_depth_hkconnect_active_selection_20260521.csv` | `2026-05-21` live active 港股通 selection 快照 |
| `configs/universe/hk_tick_depth/slices/hk_tick_depth_hkconnect_addon_20260521.txt` | 当前港股通相对本地 894 只选择新增的 3 只 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_selection_20260521.csv` | 非港股通 active 普通股成交额排序 selection |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_top100_20260521.txt` | 非港股通 top100 下载池 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank101_200_20260521.txt` | 非港股通 rank101..200 预备池，本轮未下载 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_top200_20260521.txt` | 非港股通 top200 预备池，本轮未下载 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_top300_20260521.txt` | 非港股通 top300 预备池，本轮未下载 |

`configs/universe/hk_tick_depth/manifest.yml` 已同步登记这些 TXT 清单。

## 下载结果

| 批次 | metadata | audit | 结果 |
| --- | --- | --- | --- |
| Core820 rank781..820 full | `artifacts/cache/rqdata/hk_tick_depth/core820_rank781_820_20250401_20260520/meta/download_20260521_154646.json` | `artifacts/cache/rqdata/hk_tick_depth/core820_rank781_820_20250401_20260520/audit/download_20260521_154646_bdced3df.csv` | written 10618, empty 502, rows 548957 |
| Core860 rank821..860 full | `artifacts/cache/rqdata/hk_tick_depth/core860_rank821_860_20250401_20260520/meta/download_20260521_161810.json` | `artifacts/cache/rqdata/hk_tick_depth/core860_rank821_860_20250401_20260520/audit/download_20260521_161810_b9c8ad10.csv` | written 10237, empty 883, rows 250276 |
| Core894 rank861..894 full | `artifacts/cache/rqdata/hk_tick_depth/core894_rank861_894_20250401_20260520/meta/download_20260521_164814.json` | `artifacts/cache/rqdata/hk_tick_depth/core894_rank861_894_20250401_20260520/audit/download_20260521_164814_a1f71a07.csv` | written 4465, empty 4987, rows 792948 |
| Core300 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260521/meta/download_20260521_171255.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260521/audit/download_20260521_171255_658781f0.csv` | written 300, rows 1272315 |
| Core500 rank301..500 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260521/meta/download_20260521_171434.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260521/audit/download_20260521_171434_ef189848.csv` | written 200, rows 233608 |
| Core600 rank501..540 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_increment_20260521/meta/download_20260521_171543.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_increment_20260521/audit/download_20260521_171543_d4f0e904.csv` | written 40, rows 27480 |
| Core600 rank541..580 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_increment_20260521/meta/download_20260521_171611.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_increment_20260521/audit/download_20260521_171611_c867d80b.csv` | written 40, rows 28806 |
| Core640 rank581..620 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_increment_20260521/meta/download_20260521_171636.json` | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_increment_20260521/audit/download_20260521_171636_e8817608.csv` | written 39, empty 1, rows 23477 |
| Core700 rank621..660 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_increment_20260521/meta/download_20260521_171703.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_increment_20260521/audit/download_20260521_171703_849e3d97.csv` | written 40, rows 8785 |
| Core700 rank661..700 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank661_700_increment_20260521/meta/download_20260521_171728.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank661_700_increment_20260521/audit/download_20260521_171728_aa5cf5f5.csv` | written 40, rows 4677 |
| Core740 rank701..740 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core740_rank701_740_increment_20260521/meta/download_20260521_171809.json` | `artifacts/cache/rqdata/hk_tick_depth/core740_rank701_740_increment_20260521/audit/download_20260521_171809_ccd00de7.csv` | written 40, rows 4868 |
| Core780 rank741..780 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core780_rank741_780_increment_20260521/meta/download_20260521_171829.json` | `artifacts/cache/rqdata/hk_tick_depth/core780_rank741_780_increment_20260521/audit/download_20260521_171829_cc7a75b0.csv` | written 39, empty 1, rows 1803 |
| Core820 rank781..820 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core820_rank781_820_increment_20260521/meta/download_20260521_171852.json` | `artifacts/cache/rqdata/hk_tick_depth/core820_rank781_820_increment_20260521/audit/download_20260521_171852_d0f7a5de.csv` | written 38, empty 2, rows 1007 |
| Core860 rank821..860 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core860_rank821_860_increment_20260521/meta/download_20260521_171914.json` | `artifacts/cache/rqdata/hk_tick_depth/core860_rank821_860_increment_20260521/audit/download_20260521_171914_ee67860b.csv` | written 34, empty 6, rows 809 |
| Core894 rank861..894 `2026-05-21` | `artifacts/cache/rqdata/hk_tick_depth/core894_rank861_894_increment_20260521/meta/download_20260521_171935.json` | `artifacts/cache/rqdata/hk_tick_depth/core894_rank861_894_increment_20260521/audit/download_20260521_171935_5002ed93.csv` | written 8, empty 26, rows 91 |
| HKConnect addon 3 | `artifacts/cache/rqdata/hk_tick_depth/hkconnect_addon_20260521_20250401_20260521/meta/download_20260521_172709.json` | `artifacts/cache/rqdata/hk_tick_depth/hkconnect_addon_20260521_20250401_20260521/audit/download_20260521_172709_d9a21813.csv` | written 51, empty 786, rows 299599 |
| Non-connect top100 partial | `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_20250401_20260521/meta/download_20260521_174248.json` | `artifacts/cache/rqdata/hk_tick_depth/non_connect_top100_20250401_20260521/audit/download_20260521_174222_017d1afa.csv` | written 15993, skipped 2685, empty 8612, quota_blocked 610, failed 0 |

说明：Non-connect top100 曾先以 `batch-size=1` 写入 2685 个 part，随后切换到
`batch-size=5` resume；metadata `rows` 仅统计第二次 resume run 的 18199570 行，
health 和 aggregate 的 `source_rows` 统计完整 raw cache，为 20847282 行。

## Health 与聚合

| 批次 | health | daily aggregate | 结果 |
| --- | --- | --- | --- |
| HKConnect addon 3 | `artifacts/reports/tick_health_hkconnect_addon_20260521_20250401_20260521.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/hkconnect_addon_20260521_20250401_20260521/data.parquet` | health pass, 299599 rows, 3 symbols, 22 data dates; aggregate 51 rows |
| Non-connect top100 partial | `artifacts/reports/tick_health_non_connect_top100_20250401_20260521_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_top100_20250401_20260521_partial/data.parquet` | health pass with warnings, 20847282 rows, 97 symbols, 273 data dates; aggregate 18678 rows |

Non-connect top100 health warning 类型：

- `timestamp_non_monotonic_count`
- `volume_decrease_count`
- `turnover_decrease_count`

这些 warning 与既有 raw tick 质量边界一致，未触发 error gate。

## 覆盖结论

- 本地 `2026-05-06` 选择的 894 只港股通候选已覆盖到 `2026-05-21`。
- RQData `2026-05-21` live active 港股通口径为 897 只，本轮补了相对本地选择缺失的
  3 只，但这些新标的只有 22 个交易日返回非空 tick。
- 非港股通 top100 扩展池在 quota guard 前覆盖到 `2026-05-13`，剩余
  `2026-05-14..2026-05-21` 的部分 unit 被 quota guard 阻断。
- 账户 tick quota 停在 94.81%，不再继续发起 provider 下载。

