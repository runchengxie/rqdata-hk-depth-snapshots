# 港股 Tick 下载进展：2026-05-15

状态：按 95% quota guard 补齐 Core200 后段，并推进 Core300 `rank201..230` 到
quota guard 截停点；追加按 99.5% quota guard 补 `2026-05-14` Core200 增量。

记录日期：2026-05-15。

本轮开始前查询 quota，TRIAL 账号日额度已重置为 1GB，remaining days 为 11，
bytes used 为 0。下载顺序为先收口前一日 partial，再按流动性 rank 连续推进：
Core200 `rank166` resume、Core200 `rank167..180`、Core200 `rank181..200`、
Core300 `rank201..230`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | raw size |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Core200 rank166 resume | 1 | `2025-04-01` 到 `2026-05-13` | 17 | 0 | 256 | 0 | 44,024 new rows | 39MB total |
| Core200 rank167..180 | 14 | `2025-04-01` 到 `2026-05-13` | 3,414 | 408 | 0 | 0 | 6,844,109 | 403MB |
| Core200 rank181..200 | 20 | `2025-04-01` 到 `2026-05-13` | 5,010 | 450 | 0 | 0 | 13,012,988 | 699MB |
| Core300 rank201..230 partial | 30 | `2025-04-01` 到 `2026-05-13` | 2,902 | 447 | 0 | 4,841 | 7,117,570 | 406MB |

所有批次使用 `symbol-date` raw layout、`zstd` level 3 parquet、`--resume`、
`--continue-on-error`、provider 交易日历和 `--quota-stop-ratio 0.95`。

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core200 rank166 resume | `artifacts/cache/rqdata/hk_tick_depth/core200_rank166_20250401_20260513/meta/download_20260515_041701.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank166_20250401_20260513/audit/download_20260515_041659_99642a8c.csv` |
| Core200 rank167..180 | `artifacts/cache/rqdata/hk_tick_depth/core200_rank167_180_20250401_20260513/meta/download_20260515_041742.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank167_180_20250401_20260513/audit/download_20260515_041742_ee2916cb.csv` |
| Core200 rank181..200 | `artifacts/cache/rqdata/hk_tick_depth/core200_rank181_200_20250401_20260513/meta/download_20260515_042943.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_rank181_200_20250401_20260513/audit/download_20260515_042943_872113c3.csv` |
| Core300 rank201..230 partial | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_20250401_20260513/meta/download_20260515_044505.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_rank201_230_20250401_20260513/audit/download_20260515_044505_64e7d529.csv` |

## Quota

本轮最终查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 11 |
| bytes used | 970.89MB |
| bytes remaining | 53.11MB |
| used pct | 94.81% |

`rank201..230` 在 95% guard 下正常截停。截停时 metadata 记录
`quota_blocked=4,841`，后续可在 quota 重置后对同一目录使用 `--resume` 补齐。

## 覆盖状态

按既有 dated records 的覆盖连续性，正式 Core200 完整历史覆盖已推进到 `rank200`。
Core300 `rank201..230` 已部分覆盖到 guard 截停点，目录保留可 resume 的缺口。

本轮只执行 live 下载和下载层审计汇总；尚未对新增目录运行 `health` 或
`aggregate-daily`。

## 追加下载：99.5% guard

追加目标是按推荐顺序先补最新交易日增量，再考虑 resume Core300。本轮先下载
Core200 `2026-05-14` 单日增量，使用同一输出目录分两次执行：

1. `batch_size=5`，`--quota-stop-ratio 0.995`，写入 145 个标的后 guard 截停。
2. `batch_size=1`，同一目录 `--resume`，再写入 49 个标的后 guard 截停。

未继续切换到 Core300，因为第二轮结束后距离 99.5% 只剩约 0.84MiB 安全空间；
下一只 Core200 标的估算请求量高于剩余 guard 空间。

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | raw size | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core200 `2026-05-14` increment partial, pass 1 | 200 | `2026-05-14` | 145 | 0 | 0 | 55 | 1,021,367 | 51MB total | not run at pass boundary | - |
| Core200 `2026-05-14` increment partial, pass 2 | 200 | `2026-05-14` | 49 | 0 | 145 | 6 | 148,436 new rows | 51MB total | pass / warning | 194 |

Run records:

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core200 `2026-05-14` increment pass 1 | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/meta/download_20260515_144704.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/audit/download_20260515_144704_9cdb1cca.csv` |
| Core200 `2026-05-14` increment pass 2 | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/meta/download_20260515_144806.json` | `artifacts/cache/rqdata/hk_tick_depth/core200_increment_20260514_20260515/audit/download_20260515_144805_85debada.csv` |

质量与聚合输出：

- health report: `artifacts/reports/tick_health_core200_increment_20260514_20260515_partial.json`
- health units: `artifacts/reports/tick_health_core200_increment_20260514_20260515_partial_units.csv`
- daily aggregate: `artifacts/cache/rqdata/hk_tick_depth_daily/core200_increment_20260514_20260515_partial/data.parquet`
- daily aggregate meta: `artifacts/cache/rqdata/hk_tick_depth_daily/core200_increment_20260514_20260515_partial/meta.json`

health 结果为 `status=pass`，扫描 194 个 symbol-date 分片、1,169,803 行；
warning 类型为 timestamp 非单调、累计成交量回落、累计成交额回落，无 failure。

追加后最终 quota 查询结果：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 11 |
| bytes used | 1018.04MB |
| bytes remaining | 5.96MB |
| used pct | 99.42% |

剩余待 resume 的 Core200 `2026-05-14` 标的为：

- `01918.XHKG`
- `01258.XHKG`
- `03200.XHKG`
- `01877.XHKG`
- `00853.XHKG`
- `00189.XHKG`
