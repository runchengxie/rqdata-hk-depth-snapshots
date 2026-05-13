# 港股 Tick 下载进展：2026-05-13

状态：新增 Core200 历史覆盖。

记录日期：2026-05-13。

本轮继续推进 Core200 流动性排序后的正式池，优先补齐已有两日增量的 `rank102..110`，
然后利用剩余 quota 继续覆盖 `rank111..120` 和 `rank121..125`。详细 run 级事实以 raw
cache 下的 `meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json`
为准。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | planned | non-empty | empty remote | raw rows | raw size | health |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Core200 rank102..110 | 9 | `2025-04-01` 到 `2026-05-08` | 2,430 | 2,410 | 20 | 8,597,927 | 417MB | pass / warning |
| Core200 rank111..120 | 10 | `2025-04-01` 到 `2026-05-08` | 2,700 | 2,644 | 56 | 10,606,026 | 513MB | pass |
| Core200 rank121..125 | 5 | `2025-04-01` 到 `2026-05-08` | 1,350 | 1,350 | 0 | 4,217,490 | 207MB | pass |

所有三批均为 `symbol-date` raw layout，`zstd` level 3 parquet，下载命令均使用
`--resume`、`--continue-on-error`、quota guard 和 provider 交易日历。

## 质量与聚合

| 数据集 | health report | daily aggregate rows | 备注 |
| --- | --- | ---: | --- |
| Core200 rank102..110 | `artifacts/reports/tick_health_core200_rank102_110_20250401_20260508.json` | 2,410 | 3 类 warning：timestamp 非单调、累计成交量回落、累计成交额回落 |
| Core200 rank111..120 | `artifacts/reports/tick_health_core200_rank111_120_20250401_20260508.json` | 2,644 | 无 warning |
| Core200 rank121..125 | `artifacts/reports/tick_health_core200_rank121_125_20250401_20260508.json` | 1,350 | 无 warning |

日频聚合产物位于：

- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank102_110_20250401_20260508/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank111_120_20250401_20260508/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank121_125_20250401_20260508/`

## Quota

本轮开始前 quota 近似为空。最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 13 |
| bytes used | 848.28MB |
| bytes remaining | 175.72MB |
| used pct | 82.84% |

剩余额度不适合继续开启新的完整历史切片。下一次优先用 `--resume` 继续 Core200
`rank126..135` 或更小切片，等待 quota 重置后再按 10 到 15 个标的一组推进。

## 覆盖状态

Core200 完整历史覆盖从 `rank101` 推进到 `rank125`。截至本记录，正式 Core200 已有
125/200 个标的覆盖 `2025-04-01` 到 `2026-05-08`。
