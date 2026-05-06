# Terminology

| Term | Meaning |
| --- | --- |
| tick | RQData 港股历史 Tick 快照数据 |
| raw tick | 未复权、未清洗成研究口径的原始 tick |
| daily aggregate | 从 tick 聚合出的日频特征 |
| quota | RQData 账号数据调用额度或用量 |
| provider | 数据源适配器，当前主要是 RQData 或 FakeProvider |
| resume | 断点续传，按本地文件校验结果跳过已有单元 |
| metadata | 每次运行生成的元数据 JSON |
| audit | 下载单元级审计 CSV |
| health | raw tick 自身质量检查 |
| reconcile | tick 与外部日频 reference 对账 |
| raw-daily | 与 raw tick 同报价口径的日频 reference |
| cross-clean | cross 项目的研究清洗口径 |
| symbol-date | 默认 raw layout，一个标的一个交易日一个 parquet |
| legacy batch | 历史批处理 raw layout，保留读取兼容 |
