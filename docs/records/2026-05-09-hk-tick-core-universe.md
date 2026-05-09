# 港股 Tick Core Universe：2026-05-09

状态：已生成。

记录日期：2026-05-09。

## 目标

为后续 tick-depth 下载定义稳定的 Core200 和 Core300 universe，避免继续按临时 add-on
池零散扩展。

## 选择口径

| 项 | 口径 |
| --- | --- |
| selection date | `2026-05-06` |
| rank window | `2026-04-01` 到 `2026-05-06` |
| instrument filter | RQData `all_instruments('CS', market='hk', date='2026-05-06')` |
| status filter | `status=Active` |
| connect filter | `stock_connect` 非空 |
| ranking metric | rank window 日频 `total_turnover` 加总 |
| industry source | `get_instrument_industry(..., source='citics_2019', level=1)` |

Core200 和 Core300 当前是流动性优先清单，不做硬行业配额。行业字段保存在 selection CSV
中，后续如需“行业均衡版”可在同一候选池上再加行业上限或分层抽样。

## 输出文件

| 文件 | 内容 |
| --- | --- |
| `configs/universe/hk_tick_depth_core200.txt` | 前 200 个 active 港股通标的 |
| `configs/universe/hk_tick_depth_core300.txt` | 前 300 个 active 港股通标的 |
| `configs/universe/hk_tick_depth_core300_selection_20260506.csv` | 全部 894 个 eligible 候选的 rank、名称、行业、成交额和当前 tick 覆盖标记 |

## 当前覆盖

当前已下载 tick 池来自 Round1、active15、add-on2 和 add-on3，共 60 个 unique symbols。
按本次 Core universe 口径：

| universe | 已在当前 tick 池中 | 覆盖比例 |
| --- | ---: | ---: |
| Core200 | 50 | 25.00% |
| Core300 | 50 | 16.67% |

另外 10 个当前已下载标的未进入 Core300，主要来自早期流程验证和尾部样本，不应强制纳入
正式 Core 池。

## 行业分布

Core200 一级行业分布：

| 行业 | 数量 |
| --- | ---: |
| 医药 | 22 |
| 电子 | 19 |
| 有色金属 | 19 |
| 汽车 | 14 |
| 非银行金融 | 14 |
| 银行 | 11 |
| 计算机 | 11 |
| 交通运输 | 8 |
| 传媒 | 8 |
| 电力设备及新能源 | 7 |
| 房地产 | 7 |
| 消费者服务 | 6 |
| 通信 | 6 |
| 食品饮料 | 5 |
| 电力及公用事业 | 5 |
| 综合金融 | 4 |
| 纺织服装 | 4 |
| 机械 | 4 |
| 石油石化 | 3 |
| 商贸零售 | 3 |
| 煤炭 | 3 |
| 家电 | 3 |
| 建材 | 2 |
| 基础化工 | 2 |
| 农林牧渔 | 1 |
| 轻工制造 | 1 |

Core300 一级行业分布：

| 行业 | 数量 |
| --- | ---: |
| 医药 | 44 |
| 电子 | 21 |
| 有色金属 | 21 |
| 汽车 | 19 |
| 非银行金融 | 19 |
| 交通运输 | 13 |
| 房地产 | 13 |
| 计算机 | 13 |
| 银行 | 12 |
| 电力及公用事业 | 11 |
| 传媒 | 11 |
| 电力设备及新能源 | 10 |
| 机械 | 9 |
| 消费者服务 | 9 |
| 通信 | 8 |
| 商贸零售 | 7 |
| 食品饮料 | 7 |
| 综合金融 | 7 |
| 纺织服装 | 6 |
| 石油石化 | 5 |
| 煤炭 | 5 |
| 家电 | 4 |
| 基础化工 | 4 |
| 建材 | 3 |
| 农林牧渔 | 2 |
| 轻工制造 | 2 |
| 建筑 | 1 |
| 综合 | 1 |

## 后续建议

下载优先级建议：

1. 先补 Core200 中尚未下载的前 50 个缺口，快速把高成交头部样本扩到 100 个。
2. 再按 rank 每 15-20 个标的一组补到 Core200 完整覆盖。
3. Core200 稳定后，再推进 Core300。

更高价值的配套数据包括 daily reference、PIT universe、stock-connect membership
history、行业和市值/流通市值字段；这些数据用于降低 universe bias 和支撑成本模型解释。
