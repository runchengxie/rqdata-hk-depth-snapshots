# 文档索引

本目录按读者任务和十档盘口快照工作流组织文档。根目录 `README.md` 保留项目入口信息；
这里放完整操作说明、数据契约、质量规则和维护约束。当前 Python 业务实现由
`market_data_platform.hk_depth` 承载，本目录继续保存兼容入口文档、历史记录和运行约定。

## 推荐阅读路径

| 场景 | 阅读顺序 |
| --- | --- |
| 首次了解项目 | [工作流](workflow.md) -> [十档盘口快照数据说明](depth-snapshot-data.md) -> [术语表](terminology.md) |
| 日常运行下载 | [RQData Provider](providers-rqdata.md) -> [工作流](workflow.md) -> [CLI 参考](cli.md) |
| 验收数据质量 | [质量门禁](quality-gates.md) -> [数据契约](data-contracts.md) -> [执行记录](records/) |
| 发布或归档资产 | [数据契约](data-contracts.md) -> [CLI 参考](cli.md) -> [工作流](workflow.md) |
| 发布到共享 HK 数据根 | [工作流](workflow.md) -> [数据契约](data-contracts.md) |
| 维护代码和文档 | [开发与维护](development.md) -> [维护债清单](internal/maintenance-debt-inventory.md) |

## 页面分工

| 页面 | 内容 |
| --- | --- |
| [CLI 参考](cli.md) | 命令、参数和可复制示例 |
| [工作流](workflow.md) | probe、download、health、aggregate、reconcile、emit 和 package 的主流程 |
| [十档盘口快照数据说明](depth-snapshot-data.md) | 数据语义、可派生特征、研究边界和回测注意事项 |
| [数据契约](data-contracts.md) | 原始快照缓存、metadata、audit、交付目录、tarball 和低内存约束 |
| [质量门禁](quality-gates.md) | health、aggregate quality flags、reconcile policy 和 severity |
| [RQData Provider](providers-rqdata.md) | FakeProvider、RQDataClient、认证、quota 和 live smoke |
| [开发与维护](development.md) | 测试、lint、环境变量、文档契约测试和维护工具 |
| [术语表](terminology.md) | 项目内固定术语 |
| [执行记录](records/) | 带日期的账号、quota、provider 行为、下载覆盖和执行结果 |
| [Vendor 参考](vendor/) | RQData API 使用摘要和外部快照 |

稳定文档描述长期规则；`records/` 保存某一日期的账号、quota、provider 行为和执行结果。
