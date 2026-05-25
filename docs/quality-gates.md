# 质量门禁

质量门禁由三层组成：

1. `health` 检查原始快照自身质量。
2. `aggregate-daily` 输出研究特征和质量标记。
3. `reconcile-daily` 将原始快照聚合 OHLCV 与外部日频基准数据对账。

## Severity 和退出码

`health` 与 `reconcile-daily` 支持 `--fail-on-severity`：

| 值 | 行为 |
| --- | --- |
| `none` | 只写报告，退出码保持 0 |
| `info` | 出现 info、warning 或 error 时返回非零 |
| `warning` | 出现 warning 或 error 时返回非零 |
| `error` | 出现 error 时返回非零 |

默认值是 `error`。下载验收通常使用 `warning`，探索性检查可使用 `none`。

## 原始快照 Health

`health` 会按 parquet 分片增量扫描。JSON summary 的 `unit_diagnostics` 默认只保留最多
`20` 个异常 symbol-date 样例，并通过 `unit_count`、`anomalous_unit_count` 和
`unit_diagnostics_truncated` 说明采样范围。需要完整 symbol-date 诊断时传入
`--out-units <path>.csv`，CSV 会随分片扫描流式写出。

当前检查包括：

- 空数据集和缺少必要字段。
- timestamp 解析失败。
- `order_book_id + datetime` 重复。
- 同 timestamp 下字段冲突。
- timestamp 在同一 symbol-date 内回退。
- best bid/ask 缺失、最优盘口交叉、零价差。
- 十档 ask/bid 阶梯异常。
- 十档深度量为负。
- 累计 `volume` 和 `total_turnover` 为负、回落、大幅 reset、缺失后恢复。
- HK 交易阶段分布和 session 外记录。

示例：

```bash
rqdata-hk-depth health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-json artifacts/reports/tick_health_demo.json \
  --out-units artifacts/reports/tick_health_demo_units.csv \
  --unit-sample-limit 20 \
  --fail-on-severity warning
```

## Aggregate Quality Flags

`aggregate-daily` 输出研究可用性标记：

- `quote_quality_flag`
- `vwap_quality_flag`
- `coverage_quality_flag`
- `tick_count_quality_flag`
- `is_usable_for_research`
- `is_usable_for_cost_model`

这些字段描述数据可用性和特征质量。研究使用时应按策略选择 `is_usable_for_research` 或更细质量标记。

## Daily Reconciliation

`reconcile-daily` 将原始快照聚合出的 OHLCV 与外部日频基准数据对账。

检查范围：

- 原始快照是否为空。
- timestamp 解析失败和 session 外记录。
- quote ladder 异常。
- 快照聚合 OHLC 边界异常。
- daily reference OHLC 边界异常。
- 日频有成交但缺原始快照。
- 快照聚合 close、volume、turnover 与日频基准数据超出容忍度。
- 快照标的无法匹配日频基准数据。

聚合 metadata 会记录 close、volume、turnover 的来源，例如 `last_valid_tick`、`final`、`max_fallback` 和 `missing`。

## Reference Policy

| Policy | 用途 | 数值差异处理 |
| --- | --- | --- |
| `raw-daily` | 下载质量门禁，要求日频基准数据与原始快照使用同一报价口径 | 价格、成交量、成交额超容忍度按门禁 severity 处理 |
| `cross-clean` | 与研究清洗底座做覆盖检查 | 价格、成交量、成交额口径差异记录为 `info` |

`raw-daily` 是下载验收首选基准数据。`cross-clean` 用于确认研究底座覆盖和标的映射，覆盖缺口仍按 warning 进入门禁。

## 容忍度和 Session

`reconcile-daily` 支持：

- `--price-rtol` / `--price-atol`
- `--volume-rtol` / `--volume-atol`
- `--turnover-rtol` / `--turnover-atol`
- `--session-start`
- `--session-end`
- `--sample-limit`

默认 session 窗口为 `09:00` 到 `16:30`。该窗口用于识别明显时间异常，不替代交易所完整 session 规则。

## 低内存扫描

`health`、`aggregate-daily` 和 `reconcile-daily` 对原始快照输入使用分片级增量读取。
`health` 的 JSON 仅保留有界异常样例，完整 CSV 诊断按分片写出；全量运行不应把全部
symbol-date 诊断放入 JSON。内存中主要保留单个 parquet 分片、有限诊断样例、日频聚合
行和最终对账表。
