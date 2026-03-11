# 项目结构规范

本文档定义了 IsoDDE-BC-Dify 的推荐目录结构、各目录职责与命名规范，遵循 Python 社区商业级项目惯例。

---

## 推荐目录树

```
IsoDDE-BC-Dify/
│
├── src/                              # 源代码根目录（可安装 Python 包）
│   └── isodde_bc_dify/               #   顶层包
│       ├── __init__.py
│       ├── __main__.py               #   python -m isodde_bc_dify 入口
│       ├── cli.py                    #   命令行接口（argparse）
│       └── civic/                    #   CIViC 注释子模块
│           ├── __init__.py
│           ├── annotate.py           #     注释编排器（读 MAF → 调后端 → 写结果）
│           ├── io.py                 #     MAF 读写 + schema 校验
│           ├── schemas.py            #     数据结构定义（CIViCAnnotation 等）
│           └── backends/             #     可插拔后端
│               ├── __init__.py
│               ├── tsv.py            #       离线 TSV dump 后端
│               └── graphql.py        #       在线 GraphQL API 后端
│
├── scripts/                          # 便捷脚本（薄 wrapper）
│   ├── civic_annotator.py            #   CIViC 注释快捷入口
│   └── README.md                     #   脚本使用说明
│
├── tests/                            # 测试目录
│   ├── __init__.py
│   ├── conftest.py                   #   pytest fixtures
│   ├── fixtures/                     #   测试用小样例数据（可提交到 git）
│   │   ├── tiny_variants.tsv
│   │   ├── tiny_assertions.tsv
│   │   └── tiny_maf.tsv
│   ├── test_tsv_backend.py           #   TSV 后端测试
│   ├── test_io.py                    #   I/O + schema 校验测试
│   └── test_annotate.py              #   端到端注释测试
│
├── data/                             # 数据目录（.gitignore 忽略内容）
│   ├── README.md                     #   数据说明（不被 ignore）
│   ├── nightly-VariantSummaries.tsv  #   CIViC 变体 dump
│   ├── nightly-AcceptedAssertionSummaries.tsv  # CIViC 断言 dump
│   ├── cohortMAF.2026-03-10.maf      #   TCGA-BRCA MAF
│   ├── cache/                        #   GraphQL 查询缓存（自动生成）
│   └── Archives/                     #   历史数据归档
│
├── notes/                            # 项目笔记（版本迭代记录）
│   ├── 20260309-04-V1.0...md
│   ├── ...
│   └── 20260311-04-V5.0...md
│
├── docs/                             # 项目文档
│   └── structure.md                  #   本文件
│
├── pyproject.toml                    # 项目配置（构建、依赖、工具）
├── requirements.txt                  # 传统依赖清单（兼容 pip install -r）
├── README.md                         # 项目入口文档
├── .gitignore                        # Git 忽略规则
└── LICENSE                           # 开源许可证（可选）
```

---

## 各目录职责

### `src/isodde_bc_dify/` — 核心库

遵循 [src-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) 惯例：

- 所有可 import 的 Python 代码放在这里
- 通过 `pyproject.toml` 配置 `[tool.setuptools.packages.find] where = ["src"]`
- 好处：`import isodde_bc_dify` 始终引用已安装的版本，不会意外引用工作目录下的同名文件夹

### `scripts/` — 便捷脚本

- 只做 CLI wrapper，不包含核心逻辑
- 方便不想 `pip install` 的用户直接 `python scripts/xxx.py` 运行
- 如果脚本超过 ~50 行，说明核心逻辑应该移入 `src/`

### `tests/` — 测试

- 使用 `pytest` 框架
- `fixtures/` 存放可提交到 git 的小样例数据（不超过几 KB）
- 测试文件以 `test_` 前缀命名

### `data/` — 数据

- 通过 `.gitignore` 忽略所有内容（除 `README.md`）
- `README.md` 记录所需文件名、来源、关键列说明
- 大文件不入库，由使用者手动下载或通过脚本获取

### `notes/` — 项目笔记

- 按 `日期-版本号-标题.md` 命名
- 记录项目迭代过程、设计决策、踩坑记录
- 仅做参考，不作为代码依赖

### `docs/` — 正式文档

- 面向外部用户/协作者的文档
- 如需要可扩展为 Sphinx / MkDocs 站点

---

## 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| Python 包名 | 小写 + 下划线 | `isodde_bc_dify` |
| Python 模块 | 小写 + 下划线 | `civic_annotator.py` |
| Python 类 | PascalCase | `TSVBackend`, `CIViCAnnotation` |
| Python 函数/变量 | snake_case | `annotate_maf`, `variant_index` |
| CLI 命令 | kebab-case | `civic-annotate` |
| 输出列名 | PascalCase 带前缀 | `CIViC_AMP_Category` |
| 测试文件 | `test_` 前缀 | `test_tsv_backend.py` |
| Fixture 数据 | 描述性名称 | `tiny_variants.tsv` |
| 配置文件 | 标准名称 | `pyproject.toml`, `.gitignore` |
| 笔记文件 | `日期-序号-版本-标题.md` | `20260311-04-V5.0-...md` |

---

## 现有文件归类迁移记录

| 原位置 | 现位置 | 说明 |
|--------|--------|------|
| `scripts/civic_annotator.py`（174行核心逻辑） | `src/isodde_bc_dify/civic/`（包） + `scripts/civic_annotator.py`（薄 wrapper） | 核心逻辑迁入包，脚本保留为便捷入口 |
| `src/fetch/`（空目录） | 已删除 | 未使用的占位目录 |
| `scripts/data/`（空目录） | 已删除 | 未使用的占位目录 |
| `requirements.txt` | 保留 + 新增 `pyproject.toml` | `pyproject.toml` 为主，`requirements.txt` 兼容旧工作流 |
| 无 | `tests/` | 新增 pytest 测试套件 |
| 无 | `docs/structure.md` | 新增本文件 |
| 无 | `data/README.md` | 新增数据说明 |
