# 维护债清单

状态日期：2026-05-25。

本清单记录当前仍影响团队维护和全量运行可靠性的拆分目标。兼容性标识和历史数据布局
保留到迁移方案完成。

| 范围 | 当前问题 | 后续处理 | 验证 |
| --- | --- | --- | --- |
| `src/rqdata_tick_data/downloader.py` | 模块较大；全量计划、audit 和 metadata 在长任务中累积内存。 | 先流式写 audit 和周期 checkpoint，再抽取 planning、quota 和 legacy batch 执行模块。 | `tests/test_downloader_storage_cli.py`；全量恢复演练。 |
| `_download_symbol_date_tick_depth` | 同时负责 resume、quota、retry、写入、audit 和 metadata。 | 引入运行状态对象与批次提交函数。 | 下载器和 audit metadata 测试。 |
| `_download_batch_tick_depth` | 历史布局写入路径与主路径重复。 | 保留读取兼容；数据迁移确认后停止新 batch 写入。 | legacy layout 兼容与 deprecation 测试。 |
| `src/rqdata_tick_data/reconcile.py` | 对账函数混合原始检查、日频加载、合并检查和 verdict。 | 拆分输入准备、比较和报告生成。 | 对账与质量门禁测试。 |
| `src/rqdata_tick_data/cli.py` | parser 注册与 handler 已按命令域拆开；新增命令时仍需同步稳定文档。 | 以文档契约测试守住参数覆盖和入口名称。 | CLI help 和离线 smoke 测试。 |
| `src/rqdata_tick_data/health.py` | JSON 和 CSV 的全量 diagnostics 驻留已消除；兼容 `.parquet` 明细输出仍集中缓冲。 | 如需以 parquet 保存超大池全明细，引入稳定 schema 的流式 ParquetWriter。 | health 诊断测试；大池 parquet 输出峰值内存检查。 |
| `src/rqdata_tick_data/coverage.py` | `inspect_raw_part` 同时负责 identity、schema、字段覆盖和路径一致性校验。 | 校验范围扩展前拆分规则函数。 | coverage 和 resume 测试。 |
| `src/rqdata_tick_data/release_assets.py` | 打包、manifest、归档容器和 GitHub 上传集中在一个模块。 | 继续使用共享安全去重规则，后续分离 archive 与 GitHub 发布适配器。 | `tests/test_release_assets.py`。 |
| `project_tools/export_repo_source.py` | 维护导出工具排除在运行时 lint 与测试范围外。 | 确认团队用途后删除或纳入独立工具测试。 | 文档契约和工具测试。 |
| `project_tools/package.sh` | 源码维护打包脚本与数据发布流程容易混淆。 | 明确只用于源码快照；无使用方时移除。 | 文档契约或 shell 检查。 |
| `SchemaError` | 已删除的无用异常类。 | 保持删除状态。 | `rg SchemaError` 无运行时引用。 |
| `cache_dataset_root` | 已删除的无用存储 helper。 | 保持删除状态。 | `rg cache_dataset_root` 无运行时引用。 |

`tests/test_maintainability_contracts.py` 目前只保证大函数进入清单。函数和模块复杂度门禁、
类型检查与全量运行内存测试仍需分阶段补入。
