# HK RQData Provider Baseline：2026-05-06

状态：压缩记录。

记录日期：2026-05-06。

本记录合并原 provider status、下载规模估算和首轮路线图。适用范围是记录日期下的当前
RQData 账号、quota 和 provider 行为；账号权限或 provider 返回策略变化后需要重新估算。

## Provider 状态

| 项 | 记录值 |
| --- | --- |
| account class | `TRIAL` |
| daily quota | 约 `1GB/day` |
| 历史 tick 最早有效日 | `2025-04-01` |
| 目标估算窗口 | `2025-04-01` 到 `2026-05-06` |
| HK trading days | 268 |
| live calendar | RQData `get_trading_dates(..., market="hk")` |
| raw layout | `symbol-date` |
| quota guard | 默认 0.95 stop ratio，必要时用小 batch 补尾部 |

`2025-03-03` probe 返回 0 行并提示早于账号允许的最早 tick 日期，因此正式下载起点设为
`2025-04-01`。

## 样本估算

估算来自 20 个标的在 `2025-04-01` 的真实下载样本：

| 项 | 数值 |
| --- | ---: |
| quota_delta_bytes | 6,935,980 |
| rows | 204,482 |
| symbols | 20 |
| empty_symbols | 5 |
| rows_per_symbol_mean | 10,224 |
| rows_per_symbol_median | 1,705 |
| rows_per_symbol_p90 | 22,042 |
| rows_per_symbol_max | 119,412 |
| parquet_total_bytes | 10,035,438 |

线性外推到 `2025-04-01` 到 `2026-05-06`：

| 下载范围 | 标的数 | quota 粗估 | parquet 粗估 | 决策 |
| --- | ---: | ---: | ---: | --- |
| 小样本 | 20 | 约 1.9 GB | 约 2.7 GB | 可用来验证链路 |
| 核心池 | 100 | 约 9.3 GB | 约 13.5 GB | 分批推进 |
| 港股通研究池 | 930 | 约 86 GB | 约 125 GB | 长期分批 |
| 全市场 | 3195 | 约 297 GB | 约 430 GB | 当前 quota 下暂停 |

tick 数据有活跃度尾部；单日行情、停牌和新上市标的会改变真实成本。后续估算以
download metadata 和 audit 中的 quota、rows、status 为准。

## 执行规则

| 规则 | 记录 |
| --- | --- |
| 下载单位 | 按 symbol-date 分片，便于 resume、health 和低内存扫描 |
| chunk 尺寸 | 预估 quota 控制在约 300MB 到 700MB |
| 失败处理 | 保留 raw cache，用同一命令加 `--resume` 续跑 |
| 质量门禁 | 每个 chunk 后跑 `health`，再跑 `aggregate-daily` |
| 研究入口 | 低频研究优先消费 daily aggregate |
| 对账 | raw-daily 用作 gate；cross-clean 只记录研究口径差异 |

首轮先跑 Round1 20 标的，再扩展到 active add-on 和 Core200。全市场 tick-depth 只在
quota、磁盘和研究收益都重新评估后启动。
