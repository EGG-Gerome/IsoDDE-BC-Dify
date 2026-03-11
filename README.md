# IsoDDE-BC-Dify

**基于乳腺癌的 IsoDDE 药物结合力预测 MVP**（Dify 实践版本）

本项目实现从基因突变数据出发，经 CIViC 临床证据注释、蛋白序列构建、IsoDDE 药物亲和力预测，到临床加权排序的完整流程。

---

## 快速开始

### 1. 安装依赖

```bash
# 推荐使用虚拟环境
python -m venv venv && source venv/bin/activate

# 安装项目（开发模式）
pip install -e ".[dev]"
```

### 2. 准备数据

将以下文件放入 `data/` 目录（该目录已被 `.gitignore` 忽略）：

| 文件 | 来源 | 说明 |
|------|------|------|
| `cohortMAF.2026-03-10.maf` | [GDC Portal](https://portal.gdc.cancer.gov/) | TCGA-BRCA 队列 MAF |
| `nightly-VariantSummaries.tsv` | [CIViC Nightly](https://civicdb.org/downloads/nightly/) | CIViC 变体汇总 |
| `nightly-AcceptedAssertionSummaries.tsv` | [CIViC Nightly](https://civicdb.org/downloads/nightly/) | CIViC 已接受断言汇总 |

详细数据说明见 [`data/README.md`](data/README.md)。

### 3. 运行 CIViC 注释

```bash
# 方式 1：使用 CLI（推荐）
isodde civic-annotate \
    --input-maf data/cohortMAF.2026-03-10.maf \
    --output-maf data/annotated_brca_maf.tsv

# 方式 2：直接运行脚本
python scripts/civic_annotator.py

# 方式 3：作为 Python 模块
python -m isodde_bc_dify civic-annotate \
    --input-maf data/cohortMAF.2026-03-10.maf \
    --output-maf data/annotated_brca_maf.tsv
```

### 4. 选择注释后端

**TSV 后端**（默认）—— 使用本地 CIViC nightly dump 文件，无需网络，速度快：

```bash
isodde civic-annotate \
    --input-maf data/cohortMAF.2026-03-10.maf \
    --output-maf data/annotated_brca_maf.tsv \
    --backend tsv
```

**GraphQL 后端** —— 实时查询 CIViC API，数据最新但较慢：

```bash
isodde civic-annotate \
    --input-maf data/cohortMAF.2026-03-10.maf \
    --output-maf data/annotated_brca_maf.tsv \
    --backend graphql \
    --sleep-seconds 1.5
```

可通过 `--variant-tsv` / `--assertion-tsv` 覆盖默认文件名，或通过环境变量 `ISO_DDE_DATA_DIR` 指定数据目录。

---

## 输出字段说明

注释后的 TSV 在原始 MAF 列基础上追加以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| `CIViC_Variant_ID` | CIViC 变体 ID | `306` |
| `CIViC_Variant_Name` | CIViC 中的变体名称 | `Amplification` |
| `CIViC_AMP_Category` | AMP/ASCO/CAP 分级 | `Tier I - Level A` |
| `CIViC_Clinical_Significance` | 临床意义 | `Sensitivity/Response` |
| `CIViC_Drug_Associations` | 关联药物 | `Trastuzumab` |
| `CIViC_Disease` | 关联疾病 | `Her2-receptor Positive Breast Cancer` |
| `CIViC_Assertion_Types` | 断言类型 | `Predictive` |
| `CIViC_Match_Type` | 匹配方式 | `exact` / `alias` / `none` |
| `CIViC_Evidence_Level` | (向后兼容) 同 AMP_Category | `Tier I - Level A` |

---

## 项目结构

```
IsoDDE-BC-Dify/
├── src/isodde_bc_dify/       # Python 包（核心逻辑）
│   ├── civic/                #   CIViC 注释模块
│   │   ├── backends/         #     TSV / GraphQL 后端
│   │   ├── annotate.py       #     注释编排器
│   │   ├── io.py             #     MAF 读写 + schema 校验
│   │   └── schemas.py        #     数据结构定义
│   └── cli.py                #   命令行入口
├── scripts/                  # 便捷脚本（薄 wrapper）
├── data/                     # 数据目录（.gitignore）
├── tests/                    # 单元测试
│   └── fixtures/             #   测试用小样例数据
├── notes/                    # 项目笔记（保留）
├── docs/                     # 项目文档
├── pyproject.toml            # 项目配置 + 依赖
└── README.md                 # 本文件
```

---

## 开发

```bash
# 运行测试
pytest

# 代码检查
ruff check src/ tests/

# 格式化
ruff format src/ tests/
```

---

## 许可证

MIT
