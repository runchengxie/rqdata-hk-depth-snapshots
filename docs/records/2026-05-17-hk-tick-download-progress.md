# 港股 Tick 下载进展：2026-05-17

状态：今日 quota 已重置，先补齐 Core300 尾段 `rank261..300`，随后按
`core300_selection_20260506.csv` 的成交额排序继续下载扩展候选
`rank301..340`，在 95% quota guard 正常截停。

记录日期：2026-05-17。当天为周日，无新的港股交易日；下载窗口继续以最新已确认
交易日 `2026-05-15` 收口。

本轮开始前 quota：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 9 |
| bytes used | 0 B |
| bytes remaining | 1.00GB |
| used pct | 0.00% |

## 下载顺序

1. Resume Core300 `rank261..300` 历史 partial，补齐正式 Core300 到
   `2026-05-15`。
2. Core300 完整后，按同一 selection 文件继续下载下一档扩展候选
   `rank301..340`。

两轮均使用 `symbol-date` raw layout、`zstd` level 3 parquet、provider 交易日历、
`--resume`、`--continue-on-error`、`batch_size=1`、`--quota-stop-ratio 0.95`
和 `--quota-safety-multiplier 1.2`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core300 `rank261..300` resume/full | 40 | `2025-04-01` 到 `2026-05-15` | 9,577 | 1,311 | 112 | 0 | 16,962,346 new rows / 17,185,356 total | pass | 9,689 |
| Core400 candidate `rank301..340` partial | 40 | `2025-04-01` 到 `2026-05-15` | 6,725 | 791 | 0 | 3,484 | 9,589,148 | pass | 6,725 |

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core300 `rank261..300` resume/full | `artifacts/cache/rqdata/hk_tick_depth/core300_rank261_300_20250401_20260515/meta/download_20260516_232545.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_rank261_300_20250401_20260515/audit/download_20260516_232543_e69bf6d7.csv` |
| Core400 candidate `rank301..340` partial | `artifacts/cache/rqdata/hk_tick_depth/core400_rank301_340_20250401_20260515/meta/download_20260516_235933.json` | `artifacts/cache/rqdata/hk_tick_depth/core400_rank301_340_20250401_20260515/audit/download_20260516_235933_c6d5e1df.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core300 `rank261..300` full | `artifacts/reports/tick_health_core300_rank261_300_20250401_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_rank261_300_20250401_20260515/data.parquet` |
| Core400 candidate `rank301..340` partial | `artifacts/reports/tick_health_core400_rank301_340_20250401_20260515_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core400_rank301_340_20250401_20260515_partial/data.parquet` |

两份 health 报告均为 `status=pass`，无 warning 或 failure。

## Quota

本轮最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 9 |
| bytes used | 972.32MB |
| bytes remaining | 51.68MB |
| used pct | 94.95% |

`rank301..340` 在 95% guard 下正常截停。截停时下一单安全估算为
2,425,065 bytes；继续请求会越过 95% 阈值，因此保留约 5.05% 安全余量。

## 覆盖状态

- Core300 `rank261..300` 已完整覆盖 `2025-04-01` 到 `2026-05-15`。
- 正式 Core300 已完整覆盖到 `2026-05-15`。
- Core400 candidate `rank301..340` 已下载 partial；已写出 6,725 个非空
  symbol-date 单元，剩余 3,484 个 symbol-date 单元等待下一次 quota 重置后对同一
  目录使用 `--resume` 补齐。
