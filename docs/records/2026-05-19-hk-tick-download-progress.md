# 港股 Tick 下载进展：2026-05-19

状态：今日 quota 重置后，先补齐 Core500 candidate `rank401..420`，再完整下载
`rank421..460`，最后继续同一成交额排序池下载 `rank461..500`，并在 95% quota
guard 附近正常截停。

记录日期：2026-05-19。下载窗口以最新已确认完整交易日 `2026-05-18` 收口；接手时
`rank401..420` 仍沿用前一日 partial 目录，窗口为 `2025-04-01` 到 `2026-05-15`。

本轮最终 live quota：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 7 |
| bytes used | 971.55MB |
| bytes remaining | 52.45MB |
| used pct | 94.88% |

## 下载顺序

1. Resume Core500 candidate `rank401..420` 历史 partial，补齐到
   `2026-05-15`。
2. 继续按 `hk_tick_depth_core300_selection_20260506.csv` 成交额排序下载
   Core500 candidate `rank421..460`，完整覆盖到 `2026-05-18`。
3. 下载下一档 `rank461..500`，使用 `--quota-stop-ratio 0.95` 和
   `--quota-safety-multiplier 1.2`，在 quota guard 处截停。

三轮均使用 `symbol-date` raw layout、`zstd` level 3 parquet、provider 交易日历、
`--resume`、`--continue-on-error` 和 `batch_size=1`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core500 candidate `rank401..420` resume/full | 20 | `2025-04-01` 到 `2026-05-15` | 4,171 | 664 | 665 | 0 | 6,208,111 total | pass | 4,836 |
| Core500 candidate `rank421..460` full | 40 | `2025-04-01` 到 `2026-05-18` | 10,398 | 642 | 0 | 0 | 10,513,036 | pass | 10,398 |
| Core500 candidate `rank461..500` partial | 40 | `2025-04-01` 到 `2026-05-18` | 9,590 | 403 | 0 | 1,047 | 7,933,147 | pass / warning | 9,590 |

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core500 `rank401..420` resume/full | `artifacts/cache/rqdata/hk_tick_depth/core500_rank401_420_20250401_20260515/meta/download_20260519_021740.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank401_420_20250401_20260515/audit/download_20260519_021735_76949a8e.csv` |
| Core500 `rank421..460` full | `artifacts/cache/rqdata/hk_tick_depth/core500_rank421_460_20250401_20260518/meta/download_20260519_023246.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank421_460_20250401_20260518/audit/download_20260519_023246_822fda3e.csv` |
| Core500 `rank461..500` partial | `artifacts/cache/rqdata/hk_tick_depth/core500_rank461_500_20250401_20260518/meta/download_20260519_053447.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank461_500_20250401_20260518/audit/download_20260519_053447_81cc52e8.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core500 `rank401..420` full | `artifacts/reports/tick_health_core500_rank401_420_20250401_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank401_420_20250401_20260515/data.parquet` |
| Core500 `rank421..460` full | `artifacts/reports/tick_health_core500_rank421_460_20250401_20260518.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank421_460_20250401_20260518/data.parquet` |
| Core500 `rank461..500` partial | `artifacts/reports/tick_health_core500_rank461_500_20250401_20260518_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank461_500_20250401_20260518_partial/data.parquet` |

`rank401..420` 和 `rank421..460` health 均为 `status=pass`，无 warning 或 failure。
`rank461..500` health 为 `status=pass`，无 failure；有 3 个 warning 级检查，集中在
2 个 symbol-date 单元：

- `02858.XHKG` / `20250415`：timestamp 非单调、累计成交量回落、累计成交额回落。
- `00323.XHKG` / `20250430`：累计成交额回落。

## 覆盖状态

- Core500 candidate `rank401..420` 已完整覆盖 `2025-04-01` 到 `2026-05-15`。
- Core500 candidate `rank421..460` 已完整覆盖 `2025-04-01` 到 `2026-05-18`。
- Core500 candidate `rank461..500` 已完整覆盖到 `2026-04-08`；`2026-04-09`
  已写入前 33 个 symbol-date 单元，剩余 7 个单元被 quota guard 拦截；
  `2026-04-10` 到 `2026-05-18` 等待下次 quota 重置后对同一目录使用
  `--resume` 补齐。
