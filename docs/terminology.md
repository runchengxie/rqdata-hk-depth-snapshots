# 术语表

| 术语 | 含义 |
| --- | --- |
| CLI | 主命令行入口 `rqdata-hk-depth`；`rqdata-tick` 为兼容入口 |
| 十档盘口快照 | 某标的某时间戳的十档买卖盘状态，带快照时点行情和累计成交字段 |
| RQData tick 频率 | 本项目取数使用的 provider 接口频率；数据语义以十档盘口快照为准 |
| 原始快照缓存 | `download` 将 provider 返回快照写出的 parquet 数据集 |
| 原始快照布局 | 原始快照缓存的目录布局 |
| symbol-date | 默认原始快照布局，一个标的、一个交易日、一个 parquet |
| legacy batch | 历史批处理原始快照布局，保留读取兼容 |
| compact 派生物 | 按标的和时间段合并的冷归档 parquet 派生物 |
| row-group-days | compact 输出中一个 parquet row group 合并的源交易日 part 上限 |
| duplicate policy | compact 输入出现重复日期-标的时使用的显式、可审计选择规则 |
| metadata | 每次运行生成的元数据 JSON |
| audit | 下载单元级审计 CSV |
| provider | 数据源适配器，当前包括 RQDataClient 和 FakeProvider |
| FakeProvider | 离线测试 provider，生成确定性样本数据 |
| quota | RQData 账号数据调用额度或用量 |
| resume | 断点续传，按本地文件校验结果跳过已有单元 |
| health | 原始快照自身质量检查 |
| 日频聚合数据 | 从原始快照聚合出的日频研究特征 |
| reconcile-daily | 原始快照聚合 OHLCV 与外部日频基准数据的对账命令 |
| 日频基准数据 | 对账使用的外部日频数据 |
| raw-daily | 与原始快照使用同一报价口径的日频基准数据 |
| cross-clean | cross 项目的研究清洗口径基准数据 |
| quality flag | 聚合产物中的质量标记 |
| 交付目录 | 可发布或交付的数据目录，包含 manifest、meta、symbols、fields 和数据文件 |
| 逐笔委托事件 | 委托新增、撤单、改单或成交回报事件；超出本项目数据范围 |
| 逐笔成交明细 | 每笔成交记录；超出本项目数据范围 |
| record | 带日期的执行记录，保存账号、quota、provider 行为或下载覆盖等当日事实 |
| vendor snapshot | 外部 provider API 文档快照，用作离线参考 |
