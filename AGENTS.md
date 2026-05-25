# AGENTS.md

## 项目范围

本项目用于探查、下载、校验、对账、聚合和打包 RQData 港股历史十档盘口快照数据。
数据来自 RQData 港股 `frequency="tick"` 接口，包含十档买卖盘、快照时点行情和
累计成交字段。

支持范围：

- 历史十档盘口快照。
- 原始快照缓存质量检查。
- 原始快照到日频研究特征的聚合。
- 与外部日频基准数据的对账。
- 原始快照 / 日频交付目录输出和本地归档分包。

数据范围不含逐笔成交、逐笔委托事件、订单优先级和严格订单簿重建所需事件流。
队列位置模拟和实盘交易执行需要其他系统。

## 标准命令

安装离线开发依赖：

```bash
uv sync --group dev
```

运行离线测试：

```bash
uv run pytest
```

运行 lint：

```bash
uv run ruff check .
```

需要访问真实 RQData provider 时安装 live extras：

```bash
uv sync --extra rqdata --group dev
```

## 数据布局

默认原始快照布局是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

历史 `batch` 原始快照布局继续保持读取兼容。新下载使用 `symbol-date`；新
`raw_layout=batch` 下载已废弃，并会记录到 metadata。

## 质量边界

- `health` 检查原始快照数据质量。
- `reconcile-daily` 将原始快照聚合结果与外部日频基准数据对账。
- `raw-daily` 用于同报价口径下载门禁。
- `cross-clean` 用于研究清洗底座覆盖检查；价格、成交量或成交额口径差异记录为 `info`。
- `aggregate-daily` 生成日频研究特征和质量标记。

## 大数据和 OOM 规则

- 全周期快照下载、health 扫描、聚合、对账和交付目录输出都按长 I/O 任务处理。
- 新下载保持 `symbol-date` 原始快照布局；它是 resume、健康诊断、聚合和低内存扫描的操作单元。
- live RQData 运行优先把单批 estimated quota 控制在 `300MB-700MB` 附近。
- 运行时使用 `--resume`、`--continue-on-error`、quota guard 和 audit 输出作为进度记录；非 `dry-run` 下载会按完成批次追加写出 audit。
- 任务无 traceback 消失后，重启前先检查目标输出：
  - `meta/download_*.json`
  - `audit/download_*.csv`
  - `artifacts/reports/*.json`
  - `free -h`
  - `dmesg -T | tail`
  - `ps -eo pid,ppid,stat,etime,pcpu,pmem,args`
- 无声退出或 Codex session 消失先按可能 OOM 处理，直到日志或 kernel message 排除该原因。
- 避免在 agent 或临时脚本中整目录读入原始快照 parquet 缓存。健康检查、聚合、对账和输出优先使用 CLI/reporting 入口。
- `health`、`aggregate-daily`、`reconcile-daily` 和原始快照 `emit-asset` 的峰值内存应接近一个 parquet part 加紧凑诊断或日频行。
- 超大池报告写到 `artifacts/reports/`，完成后检查 JSON/CSV 输出。
- health、聚合、对账或交付目录输出失败时，先按日期或标的缩小任务，并保留已有原始快照缓存供 resume 使用。

## 文档同步规则

- CLI 参数、输出布局、metadata、audit 字段或质量检查变化时，同步 README、docs 和文档契约测试。
- README 保持项目入口职责，详细说明放在 `docs/`。
- 账号 quota、provider 行为、下载覆盖和样本估算等带日期事实放在 `docs/records/`。
- 稳定文档围绕 `docs/workflow.md`、`docs/data-contracts.md`、`docs/quality-gates.md`、`docs/providers-rqdata.md` 和 `docs/development.md` 维护。
- 外部 provider API 快照放在 `docs/vendor/`，项目支持范围以本项目 CLI、代码和稳定文档为准。
- 文档、测试、metadata 示例和代码中禁止写入 secrets、本地凭据或私有 token。
