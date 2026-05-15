# 港股 Tick 下载进展：2026-05-14

状态：补齐 `2026-05-13` provider 延迟返回的数据；完成 Core200 `rank128`
历史缺口；推进 Core200 `rank129..165`，并将 `rank166` 推进到 quota guard 截停点。

记录日期：2026-05-14。

本轮开始前重新查询 quota，TRIAL 账号日额度已重置为 1GB，remaining days 为 12。
先用 `00700.XHKG` 对 `2026-05-13` 做 live probe，provider 已返回 31,431 行，
确认 2026-05-13 的 tick-depth 数据可取。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | raw size | health |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Core128 increment refetch | 128 | `2026-05-13` | 128 | 0 | 0 | 0 | 856,108 | 36MB | pass |
| Core200 rank128 resume | 1 | `2025-04-01` 到 `2026-05-13` | 32 | 2 | 239 | 0 | 148,460 new rows | 63MB total | pass |
| Core200 rank129..140 | 12 | `2025-04-01` 到 `2026-05-13` | 3,041 | 235 | 0 | 0 | 10,040,757 | 490MB | pass / warning |
| Core200 rank141..160 | 20 | `2025-04-01` 到 `2026-05-13` | 5,057 | 403 | 0 | 0 | 14,129,862 | 711MB | pass / warning |
| Core200 rank161..165 | 5 | `2025-04-01` 到 `2026-05-13` | 1,365 | 0 | 0 | 0 | 2,908,836 | 160MB | pass / warning |
| Core200 rank166 partial | 1 | `2025-04-01` 到 `2026-05-13` | 256 | 0 | 0 | 17 | 629,488 | 37MB | pass |

`rank128` 本轮接续前一轮被 quota guard 截停的 32 个单元；完成后该目录无
quota-blocked 单元。`rank129..140` 的 empty remote 主要来自上市前日期或 provider
空返回。所有批次使用 `symbol-date` raw layout、`zstd` level 3 parquet、`--resume`、
`--continue-on-error` 和 quota guard。

追加使用剩余额度到 99% guard 时，`rank141..165` 均完整完成，无 failed 或
quota-blocked 单元。`rank166` 在 99% guard 下从 `2026-04-20` 起正常截停，共 17 个
symbol-date 单元未请求 provider，后续可用 `--resume` 补齐。

## 质量与聚合

| 数据集 | health report | daily aggregate rows | 备注 |
| --- | --- | ---: | --- |
| Core128 increment refetch | `artifacts/reports/tick_health_core128_increment_20260513_refetch_20260514.json` | 128 | 无 warning |
| Core200 rank128 | `artifacts/reports/tick_health_core200_rank128_20250401_20260513.json` | 271 | 无 warning |
| Core200 rank129..140 | `artifacts/reports/tick_health_core200_rank129_140_20250401_20260513.json` | 3,041 | warning 类型：timestamp 非单调、累计成交量回落、累计成交额回落 |
| Core200 rank141..160 | `artifacts/reports/tick_health_core200_rank141_160_20250401_20260513.json` | 5,057 | warning 类型：timestamp 非单调、最优价交叉、档位顺序异常、累计成交量回落、累计成交额回落 |
| Core200 rank161..165 | `artifacts/reports/tick_health_core200_rank161_165_20250401_20260513.json` | 1,365 | warning 类型：timestamp 非单调、累计成交量回落、累计成交额回落 |
| Core200 rank166 partial | `artifacts/reports/tick_health_core200_rank166_20250401_20260513_partial.json` | 256 | 无 warning |

日频聚合产物位于：

- `artifacts/cache/rqdata/hk_tick_depth_daily/core128_increment_20260513_refetch_20260514/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank128_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank129_140_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank141_160_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank161_165_20250401_20260513/`
- `artifacts/cache/rqdata/hk_tick_depth_daily/core200_rank166_20250401_20260513_partial/`

## Quota

本轮最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 12 |
| bytes used | 1011.53MB |
| bytes remaining | 12.47MB |
| used pct | 98.78% |

本轮在 `rank166` 触发 99% quota guard。截停时 used pct 为 98.78%，下一单估算
3.53MB，已超过到 99% 阈值的剩余安全空间，因此未继续强行请求。

## 覆盖状态

正式 Core200 完整历史覆盖从 `rank127` 推进到 `rank165`。`rank128` 目录已从 partial
状态补齐到 `2026-05-13`。`rank166` 已部分覆盖到 `2026-04-17`；`2026-04-20` 到
`2026-05-13` 等待 quota 重置后 `--resume` 补齐。由于 `2026-05-13` 已确认可取，
后续可继续下载 Core200 `rank166` resume，再推进 `rank167..170`。
