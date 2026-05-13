# 港股 Tick 下载进展：2026-05-13

状态：新增 Core200 历史覆盖；追加 Core125 增量与 Core200 rank126..128。

记录日期：2026-05-13。

本轮继续推进 Core200 流动性排序后的正式池，优先补齐已有两日增量的 `rank102..110`，
然后利用剩余 quota 继续覆盖 `rank111..120` 和 `rank121..125`。详细 run 级事实以 raw
cache 下的 `meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json`
为准。

追加执行中，先把已完成 Core125 补到 `2026-05-11` 到 `2026-05-13`，再用剩余
quota 尝试 Core200 `rank126` 单标的完整历史窗口。`2026-05-13` provider tick 返回
为空，增量有效数据截至 `2026-05-12`。

在用户确认可用到 99% quota guard 后，重试 Core126 的 `2026-05-13` 单日增量；
provider 仍返回全空。随后继续推进 Core200 `rank127`，并尝试 `rank128`。`rank128`
在 99% guard 前正常截停，后续可用 `--resume` 继续。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | planned | non-empty | empty remote | raw rows | raw size | health |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Core200 rank102..110 | 9 | `2025-04-01` 到 `2026-05-08` | 2,430 | 2,410 | 20 | 8,597,927 | 417MB | pass / warning |
| Core200 rank111..120 | 10 | `2025-04-01` 到 `2026-05-08` | 2,700 | 2,644 | 56 | 10,606,026 | 513MB | pass |
| Core200 rank121..125 | 5 | `2025-04-01` 到 `2026-05-08` | 1,350 | 1,350 | 0 | 4,217,490 | 207MB | pass |
| Core125 increment | 125 | `2026-05-11` 到 `2026-05-13` | 375 | 250 | 125 | 1,671,630 | 70MB | pass / warning |
| Core200 rank126 | 1 | `2025-04-01` 到 `2026-05-13` | 273 | 207 | 66 | 892,819 | 41MB | pass |
| Core126 `2026-05-13` retry | 126 | `2026-05-13` | 126 | 0 | 126 | 0 | 3MB | n/a |
| Core200 rank127 | 1 | `2025-04-01` 到 `2026-05-13` | 273 | 263 | 10 | 633,944 | 33MB | pass |
| Core200 rank128 partial | 1 | `2025-04-01` 到 `2026-05-13` | 273 | 239 | 2 | 1,186,222 | 53MB | pass |

`rank128` 另有 32 个 symbol-date 单元被 99% quota guard 截停，未请求 provider；
第一条截停日期为 `2026-03-25`。

上述批次均为 `symbol-date` raw layout，`zstd` level 3 parquet，下载命令均使用
`--resume`、`--continue-on-error`、quota guard 和 provider 交易日历。

## 质量与聚合

| 数据集 | health report | daily aggregate rows | 备注 |
| --- | --- | ---: | --- |
| Core200 rank102..110 | `artifacts/reports/tick_health_core200_rank102_110_20250401_20260508.json` | 2,410 | 3 类 warning：timestamp 非单调、累计成交量回落、累计成交额回落 |
| Core200 rank111..120 | `artifacts/reports/tick_health_core200_rank111_120_20250401_20260508.json` | 2,644 | 无 warning |
| Core200 rank121..125 | `artifacts/reports/tick_health_core200_rank121_125_20250401_20260508.json` | 1,350 | 无 warning |
| Core125 increment | `artifacts/reports/tick_health_core125_increment_20260511_20260513.json` | 250 | 3 类 warning：timestamp 非单调、累计成交量回落、累计成交额回落 |
| Core200 rank126 | `artifacts/reports/tick_health_core200_rank126_20250401_20260513.json` | 207 | 无 warning |
| Core200 rank127 | `artifacts/reports/tick_health_core200_rank127_20250401_20260513.json` | 263 | 无 warning |
| Core200 rank128 partial | `artifacts/reports/tick_health_core200_rank128_20250401_20260513_partial.json` | 239 | 无 warning |

日频聚合产物位于：

- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank102_110_20250401_20260508/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank111_120_20250401_20260508/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank121_125_20250401_20260508/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core125_increment_20260511_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank126_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank127_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank128_20250401_20260513_partial/`

## Quota

本轮开始前 quota 近似为空。完成 `rank121..125` 后查询为 848.28MB used、
175.72MB remaining。追加 Core125 增量和 `rank126` 后查询为 941.20MB used、
82.80MB remaining。按 99% quota guard 继续追加 Core126 单日重试、`rank127` 和
`rank128` partial 后，最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 13 |
| bytes used | 1011.99MB |
| bytes remaining | 12.01MB |
| used pct | 98.83% |

剩余额度不适合继续开启新的下载。下一次优先 `--resume` Core200 `rank128`，补齐
`2026-03-25` 到 `2026-05-13` 的 32 个被 quota guard 截停单元，再继续 `rank129`。

## 覆盖状态

Core200 完整历史覆盖从 `rank101` 推进到 `rank127`。截至本记录，正式 Core200 已有
127/200 个标的覆盖 `2025-04-01` 到 `2026-05-08`；`rank128` 已部分覆盖到
`2026-03-24`，后续 32 个交易日等待 quota 重置后 resume。Core126 已追加有效增量到
`2026-05-12`，`2026-05-13` provider tick 返回为空。
