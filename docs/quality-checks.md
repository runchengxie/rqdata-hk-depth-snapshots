# Quality Checks

`health` 检查 raw tick 数据自身质量。输出包含数据集级 summary 和 symbol-date 级 `unit_diagnostics`。
raw parquet 会按分片增量扫描，报告中只为触发 warning 的 symbol-date 保留样例行。

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

`aggregate-daily` 会输出质量标记：

- `quote_quality_flag`
- `vwap_quality_flag`
- `coverage_quality_flag`
- `tick_count_quality_flag`
- `is_usable_for_research`
- `is_usable_for_cost_model`

这些字段只描述数据可用性，不代表交易建议。

`aggregate-daily` 和 `reconcile-daily` 对 raw tick 输入使用分片级增量读取。内存中主要保留
单个 parquet 分片、symbol-date 诊断、日频聚合行和最终对账表，适合全周期小样本或核心池
续跑后直接做质量门禁。
