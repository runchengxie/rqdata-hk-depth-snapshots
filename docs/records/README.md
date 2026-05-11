# 执行记录

本目录保存会随账号、quota、provider 行为或下载覆盖变化的 dated record。稳定规则放在
`docs/workflow.md`、`docs/data-contracts.md`、`docs/quality-gates.md`、
`docs/providers-rqdata.md` 和 `docs/development.md`。

| 记录 | 内容 |
| --- | --- |
| [2026-05-06 RQData provider baseline](2026-05-06-hk-rqdata-provider-baseline.md) | 权限窗口、quota、样本估算和下载策略 |
| [2026-05-11 universe and coverage](2026-05-11-hk-tick-universe-and-coverage.md) | Core universe、配置文件组织和覆盖状态 |
| [2026-05-11 download summary](2026-05-11-hk-tick-download-summary.md) | 2026-05-06 到 2026-05-11 的下载、质量和聚合摘要 |

旧逐日流水已压缩成上面三份摘要。需要逐 run 审计时，以对应 raw cache 下的
`meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json` 为准。

不要在记录中写入 secrets、token、私有账号凭据或完整本地 credential 路径。
