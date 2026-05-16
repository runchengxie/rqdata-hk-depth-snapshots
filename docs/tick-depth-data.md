# Tick-depth 数据说明

本页说明本项目下载的 RQData 港股历史 tick-depth 数据定位、覆盖边界和适合派生的研究
特征。文件布局、metadata、audit 和 asset 契约见
[数据契约](data-contracts.md)；质量门禁见 [质量门禁](quality-gates.md)。

## 数据定位

本项目处理的是历史十档盘口快照：

```text
某标的、某交易日、某时间戳的一次盘口状态
```

它可以理解为“带累计成交字段的十档 quote snapshot”。逐笔订单流、逐笔成交流和订单簿
重建需要其他数据源。

| 类别 | 本项目是否覆盖 | 说明 |
| --- | --- | --- |
| 十档买卖盘价格和数量 | 是 | `a1-a10`、`a1_v-a10_v`、`b1-b10`、`b1_v-b10_v` |
| 快照时点行情 | 是 | `last`、`open`、`high`、`low`、`prev_close` |
| 累计成交字段 | 是 | `volume`、`total_turnover`、可能包括 `num_trades` |
| 逐笔成交明细 | 否 | 没有每笔成交价格、数量、方向和成交编号 |
| 逐笔委托事件 | 否 | 没有新增、撤单、改单、成交回报等 order event |
| 订单簿重建 | 否 | 快照之间缺少完整事件流，不能严格重建 book path |
| 队列位置模拟 | 否 | 缺少订单优先级、排队位置和事件级撮合信息 |

## Raw 字段语义

raw parquet 默认字段来自 `DEFAULT_TICK_DEPTH_FIELDS`：

| 字段组 | 字段 | 语义 |
| --- | --- | --- |
| 标识 | `order_book_id`、`trading_date`、`datetime` | 标的、交易日、快照时间戳 |
| 价格状态 | `open`、`high`、`low`、`last`、`prev_close` | 快照时点可见的当日行情状态 |
| 累计成交 | `volume`、`total_turnover`、`num_trades` | 截至快照时点的累计成交量、成交额和成交笔数信息 |
| 涨跌停/涨跌幅 | `limit_up`、`limit_down`、`change_rate` | provider 返回的参考状态字段 |
| 卖盘十档 | `a1-a10`、`a1_v-a10_v` | 最优到第十档卖价及对应挂单量 |
| 买盘十档 | `b1-b10`、`b1_v-b10_v` | 最优到第十档买价及对应挂单量 |

注意：`volume` 和 `total_turnover` 是累计量。项目在计算 VWAP 时使用相邻快照差分来
近似增量成交；该近似不能提供逐笔成交明细。

## 已落地的日频特征

`aggregate-daily` 会把 symbol-date 级 raw snapshot 聚合成日频研究特征。当前稳定输出
包括：

| 特征组 | 字段示例 | 含义 |
| --- | --- | --- |
| 覆盖度 | `tick_count`、`quote_coverage_ratio`、`bad_quote_ratio` | 快照数量、有效 quote 覆盖、坏 quote 比例 |
| 盘口质量 | `best_spread_cross_ratio`、`quote_ladder_invalid_count`、`negative_depth_volume_count` | 交叉盘口、档位顺序异常、负深度量 |
| 价差 | `spread_bps_p50`、`spread_bps_p90` | 半日或全日快照上的 bid-ask spread 分布 |
| 深度 | `depth1_notional_p50`、`depth5_notional_p50`、`depth10_notional_p50` | 1/5/10 档双边名义深度中位数 |
| 不平衡 | `imbalance1_p50`、`imbalance5_p50` | 买卖盘名义深度不平衡中位数 |
| 成交成本代理 | `open_30m_vwap`、`full_day_tick_vwap`、`open_to_tick_vwap_bps` | 开盘前 30 分钟 VWAP、全天 VWAP、开盘段相对全天偏离 |
| 成交增量质量 | `valid_vwap_increment_count`、`vwap_invalid_increment_count` | 可用于 VWAP 差分的有效/无效增量数 |
| 累计字段诊断 | `volume_decrease_count`、`turnover_decrease_count` | 累计成交量或成交额回落次数 |
| 质量标记 | `quote_quality_flag`、`vwap_quality_flag`、`coverage_quality_flag`、`tick_count_quality_flag` | 单日特征质量状态 |
| 可用性 | `is_usable_for_research`、`is_usable_for_cost_model` | 研究和成本模型的默认可用性标记 |

低频研究默认读取日频聚合产物；raw snapshot 主要用于审计、质量门禁、重算和样本校准。

## 可扩展特征方向

在不引入逐笔订单或逐笔成交假设的前提下，tick-depth snapshot 适合扩展这些特征族：

| 方向 | 可做特征 | 典型用途 |
| --- | --- | --- |
| 流动性水平 | spread 分位数、depth 分位数、有效 quote 覆盖 | 横截面流动性筛选、容量约束 |
| 流动性风险 | spread/深度波动、低深度时间占比、坏 quote 占比 | 风险控制、调仓日过滤 |
| 盘口压力 | depth imbalance、买卖盘倾斜持续性 | 短周期反转/动量候选信号 |
| 交易成本 | open VWAP、full-day VWAP、spread cost proxy | 成本模型、执行回测折扣 |
| 日内结构 | 分时段 spread/depth/VWAP、开盘/收盘段特征 | 执行时间选择、事件窗口分析 |
| 覆盖与活跃度 | tick_count、empty remote、有效交易日覆盖 | universe 过滤、停牌和低活跃识别 |

这些特征都应明确使用时点。如果用日频聚合结果做回测，通常应在 `T+1` 以后使用，或把
原始 snapshot 切到决策时点之前再计算。

## 策略研究思路

这些数据更适合做“流动性、交易成本和短周期盘口状态”研究；订单流重建需要逐笔事件数据。

可考虑的方向：

- 流动性约束组合：用 spread、depth、tick_count 和 coverage 控制可交易性、容量和换手。
- 流动性风险因子：研究低 depth、高 spread 或 quote 质量恶化后的收益、波动和回撤。
- 成本感知调仓：把 `is_usable_for_cost_model`、spread 和 VWAP 偏离作为交易成本输入。
- 开盘执行质量：比较 open 30m VWAP 与 full-day VWAP，校准开盘交易或延迟交易策略。
- 盘口不平衡信号：用 imbalance 的方向、强度和持续性做短周期候选特征，必须做严格
  out-of-sample 和时点控制。
- 事件过滤器：财报、指数调整或南向资金活跃日中，用 depth 和 spread 判断是否放大或
  收缩交易。

## 需其他数据源的研究

以下研究需要逐笔成交或 order event 数据，本项目 raw snapshot 不足以严谨支持：

- 主动买卖方向识别和 trade sign 分类。
- 每笔成交冲击、逐笔冲击曲线或订单流不平衡。
- 撤单率、挂单补单率、订单生命周期。
- 严格订单簿重建和 queue position 模拟。
- 基于订单编号、成交编号或撮合优先级的微观结构研究。

可以用 snapshot 做近似代理，但文档、报告和策略命名中应明确标注为 proxy，避免命名为
order-flow 或 trade-print 指标。

## 回测注意事项

使用这些特征做量化研究时，至少需要控制：

- Point-in-time：同日全日聚合特征不能用于同日盘前决策；需要 lag 或按决策时间切片。
- Universe 偏差：按某一执行日期选出的 universe 需要标注选择日期和排名窗口；历史
  point-in-time universe 需要额外维护成分和生效时间。
- 覆盖范围：账号权限窗口、provider 空返回比例和下载覆盖属于 dated facts，以
  [执行记录](records/) 和本地 metadata / audit 为准。
- Empty remote：`empty_remote` 可能来自未上市、停牌、provider 无返回或权限行为，需要结合
  instrument 和 daily reference 解释。
- 质量标记：研究默认先筛 `is_usable_for_research=true`；成本模型应更严格筛
  `is_usable_for_cost_model=true`。
- 口径差异：raw tick 聚合结果和外部 clean daily reference 可能存在价格、成交量或成交额口径差异。

## 文档维护

当新增 raw 字段、daily aggregate 字段、质量标记或策略可用性口径时，应同步更新本页、
[数据契约](data-contracts.md) 和 [质量门禁](quality-gates.md)。带日期的 provider 行为、
quota、选股依据和执行结果继续记录在 [执行记录](records/)。
