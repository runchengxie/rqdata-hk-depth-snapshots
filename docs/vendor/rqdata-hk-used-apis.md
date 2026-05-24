# RQData 港股 API 使用摘要

本页记录项目实际依赖的 RQData 港股接口语义。完整外部文档见
[原始快照](snapshots/rqdata-hk-api-20260319.md)。

## 项目依赖

| 用途 | RQData 能力 | 项目约定 |
| --- | --- | --- |
| 十档盘口快照下载 | `rqdatac.get_price(..., frequency="tick", market="hk", expect_df=True)` | 用 `symbol-date` 原始快照布局保存，数据范围不含订单簿重建事件流 |
| 交易日历 | `rqdatac.get_trading_dates(..., market="hk")` | provider calendar 是 live 下载默认日历 |
| Quota | `rqdatac.user.get_quota()` 或兼容 quota getter | 下载前记录 quota，下载中用 quota guard |
| 合约池生成 | `all_instruments("CS", market="hk", date=...)` | 只把 `Active` 且 `stock_connect` 非空的普通股纳入 Core universe |
| 合约核对 | `instruments(..., market="hk")` | 核对 `round_lot`、上市日、退市日、港股通状态和代码复用 |
| 行业解释 | `get_instrument_industry(..., source="citics_2019", level=1)` | 仅作为 universe 分布解释字段 |
| 日频基准数据 | `get_price(..., frequency="1d", market="hk")` | 只用于 raw-daily gate 或 cross-clean 对照 |

## Tick 字段

默认下载保留十档盘口和累计成交字段：

```text
open high low last prev_close volume total_turnover num_trades limit_up limit_down change_rate
a1-a10 a1_v-a10_v b1-b10 b1_v-b10_v
```

`volume` 和 `total_turnover` 按累计字段处理；日频特征由 `aggregate-daily` 从原始快照
重新聚合。少量 symbol-day 可能出现时间戳非单调或累计字段回落，项目将其记录为
quality warning。

## 边界

API 快照只用于字段和接口语义核对。账号权限窗口、quota、provider 空返回比例和下载覆盖以
`docs/records/` 中的 dated record 与本地 metadata/audit 为准。
