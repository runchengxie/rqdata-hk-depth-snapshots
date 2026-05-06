# Reconciliation

`reconcile-daily` 将 raw tick 聚合出的 OHLCV 与外部日频 reference asset 对账。

两种 reference policy：

| Policy | 用途 |
| --- | --- |
| `raw-daily` | 下载质量门禁，要求日频 reference 与 raw tick 使用同一报价口径 |
| `cross-clean` | 与研究清洗底座做覆盖检查；价格、成交量、成交额口径差异记录为 `info` |

对账检查包括：

- raw tick 是否为空。
- timestamp 解析失败和 session 外记录。
- quote ladder 异常。
- tick-derived OHLC 边界异常。
- daily reference OHLC 边界异常。
- 日频有成交但缺 tick。
- tick close、volume、turnover 与日频 reference 超出容忍度。
- tick 标的无法匹配 daily reference。

聚合 metadata 会记录 close、volume、turnover 的来源，例如 `last_valid_tick`、`final`、`max_fallback` 和 `missing`。
