# scripts/ 目录说明

本目录包含便捷脚本，它们是对 `src/isodde_bc_dify/` 包的薄 wrapper。

## civic_annotator.py

使用 CIViC 数据对 MAF 文件进行批量注释。

### 快速运行（使用默认参数）

```bash
# 无参数时自动注释 data/cohortMAF.2026-03-10.maf → data/annotated_brca_maf.tsv
python scripts/civic_annotator.py
```

### 自定义参数

```bash
python scripts/civic_annotator.py civic-annotate \
    --input-maf data/cohortMAF.2026-03-10.maf \
    --output-maf data/annotated_brca_maf.tsv \
    --data-dir data \
    --backend tsv
```

### 前置条件

1. `data/` 目录下需要以下文件：
   - `nightly-VariantSummaries.tsv` —— CIViC 变体汇总（从 [CIViC Nightly](https://civicdb.org/downloads/nightly/) 下载）
   - `nightly-AcceptedAssertionSummaries.tsv` —— CIViC 已接受断言汇总（同上）
   - MAF 文件（需包含 `Hugo_Symbol` 和 `HGVSp_Short` 列）

2. 安装依赖：`pip install -e .` 或 `pip install pandas requests`

### 输出

在原始 MAF 列基础上追加 CIViC 注释列，详见根目录 [README.md](../README.md)。

### 注释后端

- **TSV**（默认）：使用本地 CIViC nightly dump 离线注释，无需网络
- **GraphQL**：实时查询 CIViC API，`--backend graphql --sleep-seconds 1.0`

完整参数说明：`python scripts/civic_annotator.py civic-annotate --help`
