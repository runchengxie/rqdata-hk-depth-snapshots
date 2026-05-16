# 港股 Tick 下载进展：2026-05-16

状态：补齐 Core200 最新增量，收口 Core300 `rank201..230` partial，并推进
Core300 `rank231..260` 到 95% quota guard 截停点。

记录日期：2026-05-16。

本轮开始前已确认 `2026-05-15` tick-depth 可取：`00700.XHKG` probe 返回
30,604 行。随后按优先级执行：

1. 补齐 Core200 `2026-05-14` 剩余 6 个标的。
2. 下载 Core200 `2026-05-15` 单日增量。
3. Resume Core300 `rank201..230` 历史 partial。
4. 下载 Core300 `rank201..230` 的 `2026-05-14` 到 `2026-05-15` 增量。
5. 推进 Core300 `rank231..260`，并在 95% quota guard 正常截停。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | raw size | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core200 `2026-05-14` tail resume | 200 | `2026-05-14` | 6 | 0 | 194 | 0 | 18,847 new rows | 52MB total | pass / warning | 200 |
| Core200 `2026-05-15` increment | 200 | `2026-05-15` | 200 | 0 | 0 | 0 | 1,153,058 | 51MB | pass / warning | 200 |
| Core300 `rank201..230` resume | 30 | `2025-04-01` 到 `2026-05-13` | 4,597 | 691 | 2,902 | 0 | 8,668,210 new rows | 935MB total | pass / warning | 7,499 |
| Core300 `rank201..230` increment | 30 | `2026-05-14` 到 `2026-05-15` | 60 | 0 | 0 | 0 | 121,558 | 7.2MB | pass | 60 |
| Core300 `rank231..260` partial | 30 | `2025-04-01` 到 `2026-05-15` | 7,355 | 437 | 0 | 458 | 15,082,955 | 878MB | pass | 7,355 |

所有 live 下载均使用 `symbol-date` raw layout、`zstd` level 3 parquet、
provider 交易日历、`--resume`、`--continue-on-error` 和 95% quota guard。

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core200 `2026-05-14` tail resume | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/meta/download_20260516_135345.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/audit/download_20260516_135343_be6340a9.csv` |
| Core200 `2026-05-15` increment | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260515/meta/download_20260516_135407.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260515/audit/download_20260516_135407_7f09df91.csv` |
| Core300 `rank201..230` resume | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_20250401_20260513/meta/download_20260516_135606.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_20250401_20260513/audit/download_20260516_135536_0e7136d0.csv` |
| Core300 `rank201..230` increment | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_increment_20260514_20260515/meta/download_20260516_141510.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_increment_20260514_20260515/audit/download_20260516_141509_ca5ee0df.csv` |
| Core300 `rank231..260` partial | `artifacts/cache/rqdata/hk_tick_depth/core300_rank231_260_20250401_20260515/meta/download_20260516_141543.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_rank231_260_20250401_20260515/audit/download_20260516_141543_6c0682ee.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core200 `2026-05-14` full increment | `artifacts/reports/tick_health_core200_increment_20260514_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_increment_20260514_20260515_full/data.parquet` |
| Core200 `2026-05-15` increment | `artifacts/reports/tick_health_core200_increment_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core200_increment_20260515/data.parquet` |
| Core300 `rank201..230` history | `artifacts/reports/tick_health_core300_rank201_230_20250401_20260513.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_rank201_230_20250401_20260513/data.parquet` |
| Core300 `rank201..230` increment | `artifacts/reports/tick_health_core300_rank201_230_increment_20260514_20260515.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_rank201_230_increment_20260514_20260515/data.parquet` |
| Core300 `rank231..260` partial | `artifacts/reports/tick_health_core300_rank231_260_20250401_20260515_partial.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_rank231_260_20250401_20260515_partial/data.parquet` |

Core200 两个单日增量和 Core300 `rank201..230` 历史目录存在 warning 级质量标记，
主要为 timestamp 非单调、累计成交量回落或累计成交额回落。Core300
`rank201..230` 两日增量与 `rank231..260` partial health 无 warning。所有本轮
health 检查均无 failure。

## Quota

本轮最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 10 |
| bytes used | 970.53MB |
| bytes remaining | 53.47MB |
| used pct | 94.78% |

`rank231..260` 在 95% guard 下正常截停。截停时 metadata 记录
`quota_blocked=458`，无 failed 单元。blocked 单元集中在：

- `2026-04-23` 到 `2026-05-15`：8 个标的各 16 个交易日。
- `2026-04-24` 到 `2026-05-15`：22 个标的各 15 个交易日。

后续可在 quota 重置后对同一目录使用 `--resume` 补齐。

## 覆盖状态

Core200 已补齐到 `2026-05-15`。Core300 `rank201..230` 已覆盖到
`2026-05-15`。Core300 `rank231..260` 已覆盖到 `2026-04-22`，部分标的额外覆盖
到 `2026-04-23`；`2026-04-23/24` 到 `2026-05-15` 的 458 个 symbol-date 单元
等待下一次 quota 重置后 resume。
