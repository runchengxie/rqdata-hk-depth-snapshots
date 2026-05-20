# 港股 Tick 下载进展：2026-05-20

状态：今日 quota 重置后，先补齐 Core300 与 Core500 candidate 的最新完整交易日
`2026-05-19` 增量，再按成交额排序继续扩展历史覆盖到 rank 620，最后推进
rank 621..660 并在 95% quota guard 附近正常截停。

记录日期：2026-05-20。下载窗口以最新已确认完整交易日 `2026-05-19` 收口。

本轮最终 live quota：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 6 |
| bytes used | 972.06MB |
| bytes remaining | 51.94MB |
| used pct | 94.93% |

## 下载顺序

1. Resume Core300 `2026-05-19` 增量，补齐前一日 partial 后的 rank 66..300。
2. 下载 Core500 candidate rank 301..500 的 `2026-05-19` 日增量，使 Core500
   最新完整交易日覆盖到 rank 500。
3. 继续成交额排序池历史覆盖：rank 501..540、541..580、581..620，窗口均为
   `2025-04-01` 到 `2026-05-19`。
4. 推进 rank 621..660 同一历史窗口，并在 95% quota guard 附近截停。

所有 live 下载均使用 `symbol-date` raw layout、`zstd` level 3 parquet、
provider 交易日历、`--resume`、`--continue-on-error`、`batch_size=1`、
`--quota-stop-ratio 0.95` 和 `--quota-safety-multiplier 1.2`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core300 `2026-05-19` increment/full | 300 | `2026-05-19` | 235 | 0 | 65 | 0 | 661,401 new / 1,179,574 total | pass | 300 |
| Core500 candidate rank301..500 increment | 200 | `2026-05-19` | 200 | 0 | 0 | 0 | 276,431 | pass | 200 |
| Core600 candidate rank501..540 full | 40 | `2025-04-01` 到 `2026-05-19` | 9,910 | 1,170 | 0 | 0 | 8,402,074 | pass / warning | 9,910 |
| Core600 candidate rank541..580 full | 40 | `2025-04-01` 到 `2026-05-19` | 10,892 | 188 | 0 | 0 | 6,007,640 | pass / warning | 10,892 |
| Core640 candidate rank581..620 full | 40 | `2025-04-01` 到 `2026-05-19` | 10,997 | 83 | 0 | 0 | 6,117,260 | pass | 10,997 |
| Core700 candidate rank621..660 partial | 40 | `2025-04-01` 到 `2026-05-19` | 5,812 | 43 | 0 | 5,225 | 2,826,802 | pass | 5,812 |

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core300 `2026-05-19` increment/full | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/meta/download_20260520_050149.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/audit/download_20260520_050148_d8f26904.csv` |
| Core500 rank301..500 increment | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260519/meta/download_20260520_050429.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260519/audit/download_20260520_050429_27edfc95.csv` |
| Core600 rank501..540 full | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_20250401_20260519/meta/download_20260520_050539.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_20250401_20260519/audit/download_20260520_050538_29a2d99e.csv` |
| Core600 rank541..580 full | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_20250401_20260519/meta/download_20260520_053301.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_20250401_20260519/audit/download_20260520_053301_01aeb2a0.csv` |
| Core640 rank581..620 full | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_20250401_20260519/meta/download_20260520_060103.json` | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_20250401_20260519/audit/download_20260520_060103_8cefd40f.csv` |
| Core700 rank621..660 partial | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_20250401_20260519/meta/download_20260520_063232.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_20250401_20260519/audit/download_20260520_063232_402f9eac.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core300 `2026-05-19` increment/full | `artifacts/reports/tick_health_core300_increment_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_increment_20260519/data.parquet` |
| Core500 rank301..500 increment | `artifacts/reports/tick_health_core500_rank301_500_increment_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank301_500_increment_20260519/data.parquet` |
| Core600 rank501..540 full | `artifacts/reports/tick_health_core600_rank501_540_20250401_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core600_rank501_540_20250401_20260519/data.parquet` |
| Core600 rank541..580 full | `artifacts/reports/tick_health_core600_rank541_580_20250401_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core600_rank541_580_20250401_20260519/data.parquet` |
| Core640 rank581..620 full | `artifacts/reports/tick_health_core640_rank581_620_20250401_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core640_rank581_620_20250401_20260519/data.parquet` |
| Core700 rank621..660 partial | `artifacts/reports/tick_health_core700_rank621_660_20250401_20260519_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core700_rank621_660_20250401_20260519_partial/data.parquet` |

Core300、Core500 rank301..500、Core640 rank581..620 和 Core700 rank621..660
partial health 均为 `status=pass`，无 warning 或 failure。

Core600 rank501..540 health 为 `status=pass`，无 failure；有 3 个 warning 级检查：

- `01783.XHKG` / `20251021`：累计成交额回落 2 次。
- `01783.XHKG` / `20251028`：累计成交额回落 1 次。
- `01199.XHKG` / `20260423`：timestamp 非单调 1 次、累计成交量回落 1 次、
  累计成交额回落 1 次。

Core600 rank541..580 health 为 `status=pass`，无 failure；有 3 个 warning 级检查，
集中在 `00799.XHKG` / `20260202`：timestamp 非单调 1 次、累计成交量回落
1 次、累计成交额回落 1 次。

## 覆盖状态

- Core300 已完整覆盖最新完整交易日 `2026-05-19`。
- Core500 candidate rank301..500 已完整覆盖最新完整交易日 `2026-05-19`；
  结合 Core300 增量，Core500 candidate 最新日已覆盖 rank 1..500。
- Core600 candidate rank501..540、rank541..580 和 Core640 candidate
  rank581..620 均已完整覆盖 `2025-04-01` 到 `2026-05-19`。
- Core700 candidate rank621..660 已完整覆盖到 `2025-11-03`；`2025-11-04`
  已写入前 15 个 symbol-date 单元，剩余 25 个单元被 quota guard 拦截；
  `2025-11-05` 到 `2026-05-19` 等待下次 quota 重置后对同一目录使用
  `--resume` 补齐。

## 配置更新

本轮新增以下成交额排序切片配置，并同步 `configs/universe/hk_tick_depth/manifest.yml`：

- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core500_rank301_500.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core600_rank501_540.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core600_rank541_580.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core640_rank581_620.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core700_rank621_660.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core700_rank661_700.txt`
