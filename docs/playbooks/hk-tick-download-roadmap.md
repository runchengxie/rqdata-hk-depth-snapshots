# 港股 Tick 深度下载路线图：2026-05-06

状态：执行参考。

记录日期：2026-05-06。

适用范围：当前 RQData `TRIAL` 账号、约 `1GB/day` quota、历史 tick 最早可用日
`2025-04-01`。

相关依据：[下载规模估算快照](hk-tick-download-sizing.md)。

## 决策原则

tick-depth 数据不作为全市场基础行情底座，而作为微观结构、交易成本、流动性和
执行质量研究资产。低频研究默认消费 `aggregate-daily` 产物，raw tick 主要用于
审计、质量门禁、特征重算和样本校准。

当前阶段不下载全市场 tick-depth。优先把小而稳定的核心资产跑通，再按研究收益
逐层扩展。

## 分层下载范围

| 层级 | 标的范围 | 规模判断 | 用途 | 当前动作 |
| --- | ---: | --- | --- | --- |
| Round 1 | 20 标的小样本 | 约 1.9GB quota / 2.7GB parquet 全周期 | 验证下载、resume、health、aggregate、reconcile | 先跑首月试下载 |
| Core | 100 核心流动性标的 | 约 9.3GB quota / 13.5GB parquet 全周期 | 正式微观结构研究资产 | Round 1 稳定后分批下载 |
| Connect practical | 约 338 港股通/南向实用池 | 约 31GB quota / 45GB parquet 全周期 | 可交易股票池覆盖、组合执行成本 | Core 通过后按月或按标的批次扩展 |
| Broad research | 约 930 广义研究池 | 约 86GB quota / 125GB parquet 全周期 | 更广覆盖实验 | 只有确认收益后慢慢补 |
| Full market | 约 3195 全市场 | 约 297GB quota / 430GB parquet 全周期 | 不适合当前 trial quota | 暂不下载 |

## 字段策略

Round 1 和 Core 使用默认全字段十档：

```text
open high low last prev_close volume total_turnover num_trades limit_up limit_down change_rate
a1-a10 a1_v-a10_v b1-b10 b1_v-b10_v
```

这样可以保留 `spread`、`depth1/5/10`、`imbalance1/5`、VWAP 和报价质量检查能力。
如果后续扩展到 338 或 930 池时发现 quota 与字段数高度相关，再单独做五档或一档
字段敏感性 probe。

## 第一轮试下载

第一轮不直接下载 20 标的全周期，而先跑首月：

```text
标的文件：configs/universe/hk_tick_depth_round1_20.txt
日期范围：2025-04-01 到 2025-04-30
输出目录：artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20250430
raw layout：symbol-date
字段：默认全字段十档
```

这个范围预计只占全周期 20 标的小样本的一小部分，足以观察活跃度尾部、empty
symbol-day、quota audit、health warning 和聚合产物形态。

下载命令：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick download \
  --symbols-file configs/universe/hk_tick_depth_round1_20.txt \
  --start-date 20250401 \
  --end-date 20250430 \
  --out artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20250430 \
  --batch-size 5 \
  --retry-max-attempts 3 \
  --retry-backoff-seconds 2 \
  --quota-stop-ratio 0.95 \
  --quota-safety-multiplier 1.2 \
  --resume \
  --continue-on-error
```

健康检查：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20250430 \
  --out-json artifacts/reports/tick_health_round1_20_20250401_20250430.json \
  --out-units artifacts/reports/tick_health_round1_20_20250401_20250430_units.csv \
  --fail-on-severity warning
```

日频聚合：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20250430 \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/round1_20_20250401_20250430/data.parquet
```

## 第一轮执行结果

执行时间：2026-05-06。

结果摘要：

| 项 | 结果 |
| --- | ---: |
| 交易日 | 19 |
| raw rows | 4,532,612 |
| raw parquet 分片 | 380 |
| written symbol-days | 318 |
| empty remote symbol-days | 62 |
| failed | 0 |
| quota blocked | 0 |
| raw cache 大小 | 约 215M |
| daily aggregate rows | 318 |
| daily aggregate 大小 | 约 64K |

quota 记录：

| 项 | bytes_used | bytes_remaining | used_pct |
| --- | ---: | ---: | ---: |
| 下载前 | 27,015,570 | 1,046,726,254 | 2.52% |
| 下载后 | 162,877,904 | 910,863,920 | 15.17% |

本次下载消耗约 `135.9MB` quota。首月 20 标的实际消耗低于全周期线性估算中的
月度均摊值，但这不应直接外推到所有月份，因为 tick 行数受行情波动和活跃度尾部
影响很大。

health 结果：

| 项 | 结果 |
| --- | --- |
| dataset status | pass |
| warning checks | `timestamp_non_monotonic`、`volume_decrease_count`、`turnover_decrease_count` |
| affected units | `01810.XHKG` 在 `2025-04-11`、`2025-04-23` |
| duplicate key | 0 |
| quote ladder invalid | 0 |
| negative depth volume | 0 |
| outside session rows | 0 |

结论：第一轮下载和聚合链路可用。两个 `01810.XHKG` symbol-day 出现一次 timestamp
回退及累计成交量/成交额回落，扩展下载前应作为复核样本；但没有结构性失败、
quota 阻断或 parquet/resume 问题。

## 验收标准

第一轮完成后同时检查命令退出状态和这些字段：

| 项 | 期望 |
| --- | --- |
| `audit_status_counts.failed` | 为 0，或失败项可解释且可 resume |
| `audit_status_counts.quota_blocked` | 为 0；若不为 0，保留目录并第二天续跑 |
| `audit_status_counts.written` | 与交易日和非空标的数量大体一致 |
| `empty_remote` | 可以存在，但需要确认是否停牌、未上市或 provider 无数据 |
| `health` | 首轮以 warning gate 观察问题；严重结构问题必须先修 |
| `aggregate-daily` | 输出行数应接近非空 symbol-day 数 |
| parquet 总大小 | 用于更新后续 Core/Connect 估算 |

## 扩展规则

Round 1 首月稳定后，再下载同一 20 标的全周期：

```text
2025-04-01 到 2026-05-06
```

20 标的全周期稳定后，进入 100 核心池。100 核心池按标的分组或按月份拆分，每个
chunk 控制在约 `300MB-700MB` 预估 quota。所有正式下载都使用 `symbol-date`、
`--resume` 和 audit 表作为进度事实来源。

全市场只有在 quota 明显提升，并且 Core/Connect 层的聚合特征证明有稳定研究价值
后再重新评估。
