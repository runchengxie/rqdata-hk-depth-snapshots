# 术语表

| 术语 | 含义 |
| --- | --- |
| CLI | 命令行入口 `rqdata-tick` |
| tick-depth | RQData 港股历史十档 tick 快照 |
| tick-depth snapshot | 某标的某时间戳的十档盘口状态，带快照时点行情和累计成交字段 |
| raw tick | provider 返回后写入 raw cache 的原始 tick 数据 |
| raw cache | `download` 写出的 parquet 数据集 |
| raw layout | raw cache 的目录布局 |
| symbol-date | 默认 raw layout，一个标的、一个交易日、一个 parquet |
| legacy batch | 历史批处理 raw layout，保留读取兼容 |
| metadata | 每次运行生成的元数据 JSON |
| audit | 下载单元级审计 CSV |
| provider | 数据源适配器，当前包括 RQDataClient 和 FakeProvider |
| FakeProvider | 离线测试 provider，生成确定性样本数据 |
| quota | RQData 账号数据调用额度或用量 |
| resume | 断点续传，按本地文件校验结果跳过已有单元 |
| health | raw tick 自身质量检查 |
| daily aggregate | 从 tick 聚合出的日频研究特征 |
| reconcile-daily | tick 聚合 OHLCV 与外部日频 reference asset 的对账命令 |
| reference asset | 对账使用的外部日频资产 |
| raw-daily | 与 raw tick 使用同一报价口径的日频 reference |
| cross-clean | cross 项目的研究清洗口径 reference |
| quality flag | 聚合产物中的质量标记 |
| asset | 可发布或交付的目录，包含 manifest、meta、symbols、fields 和数据文件 |
| order event | 逐笔委托新增、撤单、改单或成交回报事件；本项目不处理 |
| trade print | 逐笔成交明细；本项目不下载或建模 |
| record | 带日期的执行记录，保存账号、quota、provider 行为或下载覆盖等当日事实 |
| vendor snapshot | 外部 provider API 文档快照，用作离线参考 |
