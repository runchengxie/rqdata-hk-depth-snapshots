# 文档索引

本目录按读者任务和 tick-depth 工作流组织文档。根目录 `README.md` 只保留项目入口信息；这里放完整操作说明、数据契约、质量规则和维护约束。

| 任务 | 页面 |
| --- | --- |
| 快速查命令和参数 | [CLI 参考](cli.md) |
| 跑完整流程 | [工作流](workflow.md) |
| 理解 raw cache、metadata、audit、asset 输出 | [数据契约](data-contracts.md) |
| 判断数据质量和对账结果 | [质量门禁](quality-gates.md) |
| 配置 FakeProvider 或真实 RQData | [RQData Provider](providers-rqdata.md) |
| 运行测试、lint、维护脚本 | [开发与维护](development.md) |
| 统一术语 | [术语表](terminology.md) |
| 查看带日期的 quota、下载、覆盖记录 | [执行记录](records/) |
| 查看 RQData API 离线快照 | [Vendor 参考](vendor/) |

稳定文档描述长期规则；`records/` 目录保存某一日期的账号、quota、provider 行为和执行结果。
