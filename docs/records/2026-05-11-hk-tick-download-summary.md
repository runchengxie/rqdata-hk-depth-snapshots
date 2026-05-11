# 港股 Tick 下载摘要：2026-05-11

状态：压缩记录。

记录日期：2026-05-11。

本记录合并 2026-05-06 到 2026-05-11 的逐日下载流水。详细 run 级事实以 raw cache 下的
`meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json` 为准。

## 完整覆盖池

| 数据集 | 目标窗口 | planned | non-empty | empty remote | raw rows | health |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Round1 20 | `2025-04-01` 到 `2026-05-06` | 5,360 | 4,375 | 985 | 44,763,273 | pass / warning |
| active15 add-on | `2025-04-01` 到 `2026-05-06` | 4,020 | 3,990 | 30 | 37,705,425 | pass / warning |
| active10 add-on2 | `2025-04-01` 到 `2026-05-06` | 2,680 | 2,088 | 592 | 11,003,989 | pass / warning |
| active15 add-on3 | `2025-04-01` 到 `2026-05-06` | 4,020 | 3,827 | 193 | 25,935,030 | pass / warning |
| Core200 rank050..064 | `2025-04-01` 到 `2026-05-06` | 4,020 | 3,807 | 213 | 17,261,481 | pass / warning |
| Core200 rank065..074 | `2025-04-01` 到 `2026-05-06` | 2,680 | 2,320 | 360 | 11,437,561 | pass / warning |
| Core200 rank075..090 | `2025-04-01` 到 `2026-05-06` | 4,020 | 3,919 | 101 | 16,238,623 | pass / warning |
| Core200 rank091..100 | `2025-04-01` 到 `2026-05-06` | 2,680 | 2,318 | 362 | 7,656,332 | pass / warning |
| Core200 rank101 | `2025-04-01` 到 `2026-05-08` | 270 | 270 | 0 | 1,624,038 | pass |

`empty_remote` 主要来自退市、上市前日期或 provider 空返回。所有数据集均无 failed 单元；
warning 主要是少量 timestamp 非单调、累计成交量回落或累计成交额回落。

## 增量与 probe

| 数据集 | 窗口 | planned | non-empty | empty remote | raw rows | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Core100 increment | `2026-05-07` 到 `2026-05-08` | 200 | 200 | 0 | 1,618,557 | Core100 已接到最新两日 |
| Core200 rank102..110 increment | `2026-05-07` 到 `2026-05-08` | 18 | 18 | 0 | 92,309 | 只有最新两日 |
| micro tail25 probe | `2026-03-02` 到 `2026-05-08` | 1,150 | 184 | 966 | 111,992 | 覆盖稀疏，少数标的贡献 rows |
| low-turnover nonzero25 probe | `2026-03-02` 到 `2026-05-08` | 1,150 | 797 | 353 | 5,837 | 覆盖更均匀，单元 tick rows 很少 |

## 质量结论

| 检查 | 结论 |
| --- | --- |
| health status | 所有记录数据集均为 pass |
| structural failures | 未记录 duplicate key、quote ladder invalid、negative depth volume 或 outside session rows |
| warning 类型 | 少量 timestamp、volume、turnover 单元级 warning |
| aggregate-daily | 已为记录数据集生成 daily aggregate |
| research usability | 已聚合的非空行基本可用于 research；cost model 可用性由 quality flag 控制 |

## 产物索引

| 产物 | 位置约定 |
| --- | --- |
| raw cache | `artifacts/cache/rqdata/hk_tick_depth/<run-name>/` |
| download metadata | raw cache 下的 `meta/download_*.json` |
| download audit | raw cache 下的 `audit/download_*.csv` |
| health report | `artifacts/reports/tick_health_<run-name>.json` |
| health unit diagnostics | `artifacts/reports/tick_health_<run-name>_units.csv` |
| daily aggregate | `artifacts/cache/rqdata/hk_tick_depth_daily/<run-name>/data.parquet` |

## 后续动作

1. 继续补 Core200 `rank102..110` 的完整历史窗口。
2. 每轮继续按 quota guard、`--resume` 和 audit 作为进度事实来源。
3. 低成交 probe 结果可用于 sizing，不应直接替代 Core universe。
