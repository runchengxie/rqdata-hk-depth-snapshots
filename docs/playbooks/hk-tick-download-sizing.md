# 港股 Tick 深度下载规模估算

本页解决什么：记录 RQData 港股十档 tick 数据下载前的权限、quota、磁盘和分批策略判断。
本页不解决什么：不承诺全市场真实最终成本；tick 数据高度依赖标的活跃度、日期和账号权限。
适合谁：准备决定是否下载核心池、港股通池或全市场 tick 深度历史的人。
记录日期：2026-05-06。

## 当前结论

按当前 `TRIAL` 账号约 `1GB/day` quota，从 `2025-04-01` 下载到 `2026-05-06`：

| 下载范围 | 标的数 | quota 粗估 | 本地 snappy parquet 粗估 | 判断 |
| --- | ---: | ---: | ---: | --- |
| 小样本 | 20 | 约 1.9 GB | 约 2.7 GB | 需要拆 2 天左右 |
| 核心池 | 100 | 约 9.3 GB | 约 13.5 GB | 可以做，但要分批 |
| 港股通研究池 | 930 | 约 86 GB | 约 125 GB | 需要长期分批和严格 resume |
| 全市场 | 3195 | 约 297 GB | 约 430 GB | 当前 trial quota 不适合一次性做 |

这些数字来自 20 个标的、单日真实下载样本外推。样本刻意混入了活跃大票和普通标的，仍然会受单日行情、活跃股尾部和停牌/无数据比例影响。全市场真实成本可能低于线性外推，也可能在热门行情日显著抬高。

## 权限窗口

真实 probe 发现，当前账号的历史 tick 最早允许日期是 `2025-04-01`。

`2025-03-03` 的 probe 可以完成 provider 调用，但 RQData 返回 0 行并给出 warning：请求日期早于账号允许的最早 tick 日期。因此当前全周期下载起点应设为 `2025-04-01`，不要从更早日期开始消耗空请求。

从 `2025-04-01` 到 `2026-05-06`，RQData 港股交易日历返回 `268` 个交易日。

## 真实样本

### 单标的 probe

命令：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250401 \
  --out /tmp/rqdata_tick_live_probe_00001_20250401
```

结果：

| 项 | 数值 |
| --- | ---: |
| rows | 2398 |
| first_timestamp | 2025-04-01 09:20:31.262 |
| last_timestamp | 2025-04-01 16:08:07.008 |
| raw parquet | 约 156 KB |
| health | pass |
| daily aggregate rows | 1 |

### 20 标的一日样本

样本日期：`2025-04-01`。

样本标的：

```text
00001.HK,00005.HK,00388.HK,00700.HK,00941.HK,
01299.HK,01810.HK,02318.HK,03690.HK,09988.HK,
00008.HK,00373.HK,00312.HK,00377.HK,00356.HK,
00515.HK,06880.HK,01469.HK,02772.HK,02499.HK
```

结果摘要：

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

重点观察：tick 数据有很强的活跃度尾部。样本里 `01810.XHKG` 单日有 `119,412` 行，明显高于普通标的；而部分标的当天为 0 行。

## 外推方法

当前粗估使用：

```text
period_quota = sample_quota_delta / sample_symbols * trading_days * target_symbols
period_disk = sample_parquet_bytes / sample_symbols * trading_days * target_symbols
```

其中：

```text
sample_quota_delta = 6,935,980 bytes
sample_parquet_bytes = 10,035,438 bytes
sample_symbols = 20
trading_days = 268
```

换算后约为：

```text
quota_per_symbol_period ~= 92.9 MB
disk_per_symbol_period ~= 134.5 MB
```

这是下载前规划用的粗估，不是账单承诺。真实执行应以每个 chunk 的 `metadata.json` 里的 `quota_before` / `quota_after` 为准，并持续更新估算。

## 推荐下载策略

1. 先下载核心流动性标的，不先跑全市场。
2. 每个 chunk 控制在 `300MB-700MB` 预估 quota 内，给失败重试和 provider 波动留余量。
3. 使用默认 `symbol-date` raw layout 和 `--resume`，保证按“标的-日期”安全续跑。
4. 每个 chunk 后立即跑 `health --fail-on-severity warning`，再做 daily aggregate。
5. 保留 raw tick 作为审计/校准底座；低频研究默认消费 daily aggregate。

建议的第一阶段：

```text
标的数：20-100
日期：2025-04-01 到 2026-05-06
目标：跑通完整 download -> health -> aggregate -> asset emission
```

建议的第二阶段：

```text
标的池：港股通或 cross 项目的研究池
节奏：按月份或按 50-100 标的一组拆分
门禁：每组保留 metadata、health report、aggregate metadata
```

全市场只有在 quota 明显提升后再考虑。以当前 `1GB/day` 试用 quota，按样本线性外推，全市场可能需要数百天的 quota 周期，不适合现在直接启动。

## 现场命令参考

查看 quota：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick quota --pretty
```

核心池下载示例：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra rqdata rqdata-tick download \
  --symbols-file symbols_core.txt \
  --start-date 20250401 \
  --end-date 20260506 \
  --out artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --batch-size 10 \
  --resume \
  --continue-on-error
```

健康检查：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --fail-on-severity warning
```

聚合：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/data.parquet
```

## 后续需要更新的现场数字

每次扩大下载后，更新这些字段：

| 字段 | 说明 |
| --- | --- |
| quota_before / quota_after | 从下载 metadata 读取 |
| rows | 下载 metadata 的总行数 |
| empty_units | 区分停牌、未上市、无权限或无数据 |
| parquet_total_bytes | raw parts 总大小 |
| health status | 是否有重复 timestamp、盘口交叉、累计成交回落 |
| aggregate rows | 最终可用于低频研究的 symbol-date 行数 |

