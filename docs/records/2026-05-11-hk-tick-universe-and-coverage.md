# 港股 Tick Universe 与覆盖状态：2026-05-11

状态：压缩记录。

记录日期：2026-05-11。

本记录合并原 Round1 标的说明、Core universe 生成记录和 2026-05-11 前的覆盖结论。

## 配置入口

当前配置集中在 `configs/universe/hk_tick_depth/`：

| 目录 | 用途 |
| --- | --- |
| `current/` | Core100、Core200、Core300 和 selection CSV |
| `slices/` | Core200 下载分片 |
| `probes/` | 低成交或尾部 sizing probe |
| `archive/` | Round1 与早期 active add-on 样本 |
| `manifest.yml` | selection date、rank window、用途和状态索引 |

新的下载命令应使用整理后的路径；旧执行记录中的 flat path 只作为当时审计线索。

## Core 选择口径

| 项 | 口径 |
| --- | --- |
| selection date | `2026-05-06` |
| rank window | `2026-04-01` 到 `2026-05-06` |
| instrument filter | `all_instruments("CS", market="hk", date="2026-05-06")` |
| status filter | `Active` |
| connect filter | `stock_connect` 非空 |
| ranking metric | rank window 日频 `total_turnover` 加总 |
| industry source | `get_instrument_industry(..., source="citics_2019", level=1)` |

Core200 和 Core300 是流动性优先清单，不做行业硬配额。行业字段保存在
`current/hk_tick_depth_core300_selection_20260506.csv`，用于解释分布和后续重选。

## 覆盖状态

| 池 | 标的数 | 覆盖状态 |
| --- | ---: | --- |
| Round1 bootstrap | 20 | `2025-04-01` 到 `2026-05-06` 已完成，保留在 archive |
| active add-on 样本 | 40 | 三组早期高成交 add-on 已覆盖到 `2026-05-06`，保留在 archive |
| Core100 | 100 | 历史窗口已覆盖，并已追加 `2026-05-07` 到 `2026-05-08` |
| Core200 | 200 | 截至 `rank101` 的完整历史覆盖已完成，当前为 101/200 |
| Core200 `rank102..110` | 9 | 只有 `2026-05-07` 到 `2026-05-08` 两日增量，完整历史待补 |
| low-turnover probes | 50 | 已完成 `2026-03-02` 到 `2026-05-08` sizing probe |
| Core300 | 300 | selection list 已生成，下载等待 Core200 稳定后推进 |

Round1 中 `01469.XHKG` 和 `06880.XHKG` 是退市/empty remote 边界样本，只保留审计价值。
正式 Core 池以后续 selection CSV 为准。

## 后续优先级

1. 补 Core200 `rank102..110` 的完整历史窗口。
2. 按 10 到 15 个标的一组继续推进 Core200。
3. Core200 稳定后再推进 Core300。
4. 如需行业均衡版，在同一 selection CSV 上增加行业上限或分层抽样。
