# 开发与维护

## 安装

离线开发依赖：

```bash
uv sync --group dev
```

真实 RQData provider 依赖：

```bash
uv sync --extra rqdata --group dev
```

live extras 只在需要访问 provider 时安装。

## 检查运行时机

当前仓库没有 CI workflow 或 commit hook。本地修改和提交不会自动执行离线检查；
合并、发布或交付前应显式运行本页列出的测试、lint 和类型检查命令。

## 测试

离线测试：

```bash
uv run pytest
```

lint：

```bash
uv run ruff check .
```

类型检查：

```bash
uv run pyright
```

当前 Ruff 门禁启用 `E`、`F`、`I`、`UP`、`B`、`C4`、`RET`、`PT` 和 `RUF100`。
其中 `C4`、`RET` 和 `PT` 提供低噪音的集合构造、返回路径与 pytest 规则检查；
`RUF100` 防止无效 `noqa` 长期累积。`SIM` 与 `ARG` 仍需结合现有 provider stub、
测试 doubles 和数据处理代码逐步处理后接入。

Pyright 以 `basic` 模式检查下载控制面、存储、归档和发布相关 runtime 模块。
直接将 include 扩至整个 `src/rqdata_tick_data` 会暴露 pandas 聚合、对账、
provider/schema 和测试夹具边界的待收敛类型问题。这些模块的分阶段纳入计划记录在
[维护债清单](internal/maintenance-debt-inventory.md) 中。

离线测试使用 `FakeProvider`，不需要 RQData 账号。

## Live Tests

live smoke 需要显式开启：

```bash
uv sync --extra rqdata --group dev
RQDATA_TICK_LIVE_TESTS=1 uv run pytest -m rqdata_live
```

live smoke 只做最小 quota 或 provider 检查。

## 环境变量

真实 RQData 认证可以使用本地 `rqdatac` 配置，也可以把变量放在本机 shell 环境或未提交
版本控制的 `.env` 中。`RQDataClient` 通过 `python-dotenv` 读取 `.env`。支持变量：

- `RQDATA_USERNAME`
- `RQDATA_USER`
- `RQDATA_PASSWORD`
- `RQDATA_URI`

本项目没有维护默认 `.envrc.example`。如需 direnv，可自行让 `.envrc` 只加载 `.env` 或 `.env.local`，依赖安装仍使用显式 `uv sync` 命令。

## 文档契约测试

`tests/test_cli_docs_contracts.py` 负责约束：

- CLI help 可打开。
- README 风格离线命令可用。
- markdown 内链存在。
- `docs/cli.md` 覆盖 parser 暴露的命令和参数。
- `RQDataClient` 环境变量已写入稳定文档，项目不依赖环境变量样例文件。
- records 索引收录全部 dated records。
- 稳定文档没有本地绝对路径或账号日期事实。
- universe manifest 引用的文件存在，TXT 标的数与 manifest 一致。
- records 带有日期和记录语境。
- 项目文档避开绕弯对比句式。

CLI 参数、输出布局、metadata、audit 字段或质量检查发生变化时，同步更新文档和测试。

## 维护工具

`project_tools/` 是维护工具目录，不属于 runtime 行为。当前维护债清单见
[internal/maintenance-debt-inventory.md](internal/maintenance-debt-inventory.md)。

大型原始快照缓存不应通过临时脚本整目录读入内存。需要健康检查、聚合、对账和交付目录输出时，优先使用 CLI 入口。
