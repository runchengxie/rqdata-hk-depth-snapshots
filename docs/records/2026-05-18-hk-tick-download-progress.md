# 港股 Tick 下载进展：2026-05-18

状态：先按 95% quota guard 补齐 Core400 candidate `rank301..340`，完成
`rank341..380`，并推进 `rank381..400` 到 quota guard 截停点；随后按用户指令
把当日 quota 使用率推进到 99.48%，补齐 `rank381..400` 并启动下一档
Core500 candidate `rank401..420` partial。

记录日期：2026-05-18。下载窗口继续以最新已确认完整交易日
`2026-05-15` 收口。

本轮开始前 quota 已重置：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 8 |
| bytes used | 0 B |
| bytes remaining | 1.00GB |
| used pct | 0.00% |

## 下载顺序

1. Resume Core400 candidate `rank301..340` 历史 partial，补齐到
   `2026-05-15`。
2. 继续按 `core300_selection_20260506.csv` 成交额排序下载
   `rank341..380`。
3. 在 `rank341..380` 完成后启动 `rank381..400`，并在 95% quota guard
   正常截停。

三轮均使用 `symbol-date` raw layout、`zstd` level 3 parquet、provider 交易日历、
`--resume`、`--continue-on-error`、`batch_size=1`、`--quota-stop-ratio 0.95`
和 `--quota-safety-multiplier 1.2`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core400 candidate `rank301..340` resume/full | 40 | `2025-04-01` 到 `2026-05-15` | 3,455 | 820 | 6,725 | 0 | 4,596,637 new / 14,185,785 total | pass | 10,180 |
| Core400 candidate `rank341..380` full | 40 | `2025-04-01` 到 `2026-05-15` | 10,538 | 462 | 0 | 0 | 16,278,628 | pass / warning | 10,538 |
| Core400 candidate `rank381..400` partial | 20 | `2025-04-01` 到 `2026-05-15` | 4,734 | 502 | 0 | 264 | 5,698,703 | pass | 4,734 |

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core400 `rank301..340` resume/full | `artifacts/cache/rqdata/hk_tick_depth/core400_rank301_340_20250401_20260515/meta/download_20260518_015844.json` | `artifacts/cache/rqdata/hk_tick_depth/core400_rank301_340_20250401_20260515/audit/download_20260518_015742_cd40e142.csv` |
| Core400 `rank341..380` full | `artifacts/cache/rqdata/hk_tick_depth/core400_rank341_380_20250401_20260515/meta/download_20260518_021102.json` | `artifacts/cache/rqdata/hk_tick_depth/core400_rank341_380_20250401_20260515/audit/download_20260518_021102_cafb4d35.csv` |
| Core400 `rank381..400` partial | `artifacts/cache/rqdata/hk_tick_depth/core400_rank381_400_20250401_20260515/meta/download_20260518_024350.json` | `artifacts/cache/rqdata/hk_tick_depth/core400_rank381_400_20250401_20260515/audit/download_20260518_024350_52b27d3e.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core400 `rank301..340` full | `artifacts/reports/tick_health_core400_rank301_340_20250401_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core400_rank301_340_20250401_20260515/data.parquet` |
| Core400 `rank341..380` full | `artifacts/reports/tick_health_core400_rank341_380_20250401_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core400_rank341_380_20250401_20260515/data.parquet` |
| Core400 `rank381..400` partial | `artifacts/reports/tick_health_core400_rank381_400_20250401_20260515_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core400_rank381_400_20250401_20260515_partial/data.parquet` |

`rank301..340` 和 `rank381..400` partial health 均为 `status=pass`，无 warning
或 failure。`rank341..380` health 为 `status=pass`，有 3 个 warning 级检查，
集中在 2 个 symbol-date 单元：

- `01359.XHKG` / `20251118`：timestamp 非单调、累计成交量回落、累计成交额回落。
- `01921.XHKG` / `20260429`：timestamp 非单调、累计成交量回落、累计成交额回落。

所有 health 检查均无 failure。

## Quota

本轮最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 8 |
| bytes used | 971.71MB |
| bytes remaining | 52.29MB |
| used pct | 94.89% |

`rank381..400` 在 95% guard 下正常截停，截停时下一单安全估算为
2,214,423 bytes。

## 覆盖状态

- Core400 `rank301..340` 已完整覆盖 `2025-04-01` 到 `2026-05-15`。
- Core400 `rank341..380` 已完整覆盖 `2025-04-01` 到 `2026-05-15`。
- Core400 `rank381..400` 已完整覆盖到 `2026-04-24`；`2026-04-27`
  有 4 个 symbol-date 单元被 quota guard 拦截，`2026-04-28` 到
  `2026-05-15` 的 20 个标的全部等待下次 quota 重置后对同一目录使用
  `--resume` 补齐。

## 追加下载到 99.5%

用户要求继续把当日 quota 用到约 99.5%。追加前 live quota 为：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 8 |
| bytes used | 971.71MB |
| bytes remaining | 52.29MB |
| used pct | 94.89% |

追加顺序：

1. 对 Core400 candidate `rank381..400` 原目录使用 `--resume` 补齐昨日
   95% guard 留下的缺口。
2. Core400 candidate 补齐后，按 `core300_selection_20260506.csv` 成交额
   排序继续下载下一档 Core500 candidate `rank401..420`，并在 99.5% quota
   guard 附近截停。

两轮均使用 `symbol-date` raw layout、`zstd` level 3 parquet、provider 交易日历、
`--resume`、`--continue-on-error`、`batch_size=1`、`--quota-stop-ratio 0.995`
和 `--quota-safety-multiplier 0.8`。

### 追加下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core400 candidate `rank381..400` resume/full | 20 | `2025-04-01` 到 `2026-05-15` | 264 | 502 | 4,734 | 0 | 282,755 new / 5,981,458 total | pass | 4,998 |
| Core500 candidate `rank401..420` partial | 20 | `2025-04-01` 到 `2026-05-15` | 665 | 158 | 0 | 4,677 | 983,886 | pass | 665 |

### 追加 Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core400 `rank381..400` resume/full | `artifacts/cache/rqdata/hk_tick_depth/core400_rank381_400_20250401_20260515/meta/download_20260518_151221.json` | `artifacts/cache/rqdata/hk_tick_depth/core400_rank381_400_20250401_20260515/audit/download_20260518_151137_b4ba9a0e.csv` |
| Core500 `rank401..420` partial | `artifacts/cache/rqdata/hk_tick_depth/core500_rank401_420_20250401_20260515/meta/download_20260518_151509.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank401_420_20250401_20260515/audit/download_20260518_151509_54f0de30.csv` |

### 追加质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core400 `rank381..400` full | `artifacts/reports/tick_health_core400_rank381_400_20250401_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core400_rank381_400_20250401_20260515/data.parquet` |
| Core500 `rank401..420` partial | `artifacts/reports/tick_health_core500_rank401_420_20250401_20260515_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank401_420_20250401_20260515_partial/data.parquet` |

两份追加 health 报告均为 `status=pass`，无 warning 或 failure。

### 追加 Quota

追加下载后的最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 8 |
| bytes used | 1018.66MB |
| bytes remaining | 5.34MB |
| used pct | 99.48% |

`rank401..420` 在 99.5% guard 下正常截停，截停时下一单安全估算为
1,438,307 bytes。

### 追加覆盖状态

- Core400 candidate `rank381..400` 已完整覆盖 `2025-04-01` 到
  `2026-05-15`。
- Core500 candidate `rank401..420` 已完整覆盖到 `2025-06-03`；`2025-06-04`
  已写入前 3 个 symbol-date 单元，剩余 17 个 symbol-date 单元被 quota guard
  拦截；`2025-06-05` 到 `2026-05-15` 等待下次 quota 重置后对同一目录使用
  `--resume` 补齐。
