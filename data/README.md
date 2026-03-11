# data/ 目录说明

本目录存放运行所需的数据文件。所有内容已被 `.gitignore` 忽略，不会提交到版本库。

## 必需文件

| 文件名 | 来源 | 下载方式 |
|--------|------|----------|
| `nightly-VariantSummaries.tsv` | [CIViC Nightly Downloads](https://civicdb.org/downloads/nightly/) | 直接下载 TSV |
| `nightly-AcceptedAssertionSummaries.tsv` | [CIViC Nightly Downloads](https://civicdb.org/downloads/nightly/) | 直接下载 TSV |
| `cohortMAF.2026-03-10.maf` | [GDC Portal](https://portal.gdc.cancer.gov/) | Cohort Level MAF (WXS) |

## CIViC TSV 关键列

**VariantSummaries.tsv**:
- `variant_id`, `feature_name` (基因名), `variant` (变体名), `variant_aliases`, `single_variant_molecular_profile_id`

**AcceptedAssertionSummaries.tsv**:
- `molecular_profile_id`, `molecular_profile`, `disease`, `therapies`, `significance`, `amp_category`

两个文件通过 `single_variant_molecular_profile_id` == `molecular_profile_id` 关联，实现 variant-level 精确匹配。

## MAF 文件必需列

- `Hugo_Symbol`: 基因符号 (例: `PIK3CA`)
- `HGVSp_Short`: 蛋白突变简写 (例: `p.H1047R`)

## 输出文件

| 文件名 | 说明 |
|--------|------|
| `annotated_brca_maf.tsv` | CIViC 注释后的 MAF |
| `cache/civic_graphql_cache.jsonl` | GraphQL 查询缓存（自动生成） |

## 自定义文件名

如果你的 CIViC 文件名不同（如 `Variants.tsv`、`Accepted_AID.tsv`），可通过 CLI 参数覆盖：

```bash
isodde civic-annotate \
    --input-maf data/your_maf.txt \
    --output-maf data/annotated.tsv \
    --variant-tsv Variants.tsv \
    --assertion-tsv Accepted_AID.tsv
```
