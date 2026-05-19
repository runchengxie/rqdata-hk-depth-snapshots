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

## 追加下载到 99.5%

用户要求继续下载最重要数据到约 99.5% quota。本次追加优先级：

1. 先对 Core500 candidate `rank461..500` 原目录 `--resume`，补齐前一轮被
   quota guard 留下的历史缺口。
2. 确认 `2026-05-19` tick-depth 已可取后，优先下载 Core300 最新交易日
   `2026-05-19` 增量。
3. 由于 quota guard 在 99.19% 处按保守估算截停，随后只补最高排名的少量小批次，
   避免整目录续跑时因 provider quota 延迟更新而大幅越界。

最终 live quota：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 7 |
| bytes used | 1019.13MB |
| bytes remaining | 4.87MB |
| used pct | 99.52% |

`2026-05-19` 可取性 probe：`00700.XHKG` 返回 37,872 行，时间范围
`09:30:00.003` 到 `16:08:18.864`。probe 产生的 parquet 被放入
`core300_increment_20260519` 作为已存在分片，正式下载时由 `--resume` 跳过，
避免重复消耗 quota。

### 追加下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core500 candidate `rank461..500` resume/full | 40 | `2025-04-01` 到 `2026-05-18` | 1,047 | 403 | 9,590 | 0 | 649,116 new / 8,582,263 total | pass / warning | 10,637 |
| Core300 `2026-05-19` increment pass 1 | 300 | `2026-05-19` | 52 | 0 | 1 | 247 | 425,231 | pass | 65 total |
| Core300 `2026-05-19` increment pass 2 | 10 | `2026-05-19` | 10 | 0 | 0 | 0 | 46,226 | included above | included above |
| Core300 `2026-05-19` increment pass 3 | 2 | `2026-05-19` | 2 | 0 | 0 | 0 | 8,844 | included above | included above |

Core300 `2026-05-19` 最终本地覆盖为 rank 1..65，共 65 个 symbol-date 分片、
518,173 行；rank 66..300 等待下次 quota 重置后 resume。

### 追加 Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core500 `rank461..500` resume/full | `artifacts/cache/rqdata/hk_tick_depth/core500_rank461_500_20250401_20260518/meta/download_20260519_151139.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank461_500_20250401_20260518/audit/download_20260519_151019_0d4a1331.csv` |
| Core300 `2026-05-19` increment pass 1 | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/meta/download_20260519_151752.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/audit/download_20260519_151751_90d31d1f.csv` |
| Core300 `2026-05-19` increment pass 2 | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/meta/download_20260519_151959.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/audit/download_20260519_151958_a6d22ba7.csv` |
| Core300 `2026-05-19` increment pass 3 | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/meta/download_20260519_152042.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260519/audit/download_20260519_152041_fcdec90a.csv` |

### 追加质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core500 `rank461..500` full | `artifacts/reports/tick_health_core500_rank461_500_20250401_20260518.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank461_500_20250401_20260518/data.parquet` |
| Core300 `2026-05-19` partial | `artifacts/reports/tick_health_core300_increment_20260519_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_increment_20260519_partial/data.parquet` |

Core500 `rank461..500` health 为 `status=pass`，无 failure；warning 与 partial
阶段一致，共 3 个 warning，集中在 2 个 symbol-date 单元：

- `02858.XHKG` / `20250415`：timestamp 非单调、累计成交量回落、累计成交额回落。
- `00323.XHKG` / `20250430`：累计成交额回落。

Core300 `2026-05-19` partial health 为 `status=pass`，无 warning 或 failure。
