import requests 
import pandas as pd 
import time 
import os 
import logging

# ===== 配置 ===== 
# 数据目录相对于当前脚本的路径 
DATA_REL_PATH = '../data'   # 请根据您的实际目录结构调整 

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# =================== 

CIVIC_API_URL = "https://civicdb.org/api/graphql"
QUERY_TEMPLATE = """
query VariantQuery($gene: String!, $variant: String!) {
    variants(gene: $gene, variantName: $variant) {
        edges {
            node {
                id
                name
                variantAliases
                assertions {
                    clinicalSignificance
                    evidenceLevels
                    assertionType
                    therapies {
                        name
                    }
                }
            }
        }
    }
}
"""

def get_data_dir():
    """返回数据目录的绝对路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, DATA_REL_PATH))
    return data_dir

def query_civic_variant(gene, variant):
    """查询 CIViC 数据库"""
    variables = {"gene": gene, "variant": variant}
    try:
        response = requests.post(
            CIVIC_API_URL,
            json={"query": QUERY_TEMPLATE, "variables": variables},
            timeout=30
        )
        if response.status_code != 200:
            logger.error(f"API 返回状态码异常：{response.status_code}")
            return None
        result = response.json()
        if 'errors' in result:
            logger.error(f"API 返回错误：{result['errors']}")
            return None
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败：{e}")
        return None

def annotate_maf_file(input_maf, output_maf):
    """批量注释 MAF 文件"""
    if not os.path.exists(input_maf):
        logger.error(f"文件不存在：{input_maf}")
        return

    try:
        maf_df = pd.read_csv(input_maf, sep='\t')
    except Exception as e:
        logger.error(f"读取文件失败：{e}")
        return

    # 添加注释列
    maf_df['CIViC_Evidence_Level'] = ''
    maf_df['CIViC_Clinical_Significance'] = ''
    maf_df['CIViC_Drug_Associations'] = ''

    total_rows = len(maf_df)
    logger.info(f"开始注释 {total_rows} 条记录")

    for idx, row in maf_df.iterrows():
        gene = row['Hugo_Symbol']
        hgvsp = row['HGVSp_Short']

        # 处理空值
        if pd.isna(hgvsp) or not isinstance(hgvsp, str):
            variant = ""
        else:
            variant = hgvsp[2:] if hgvsp.startswith('p.') else hgvsp

        if not variant or pd.isna(gene):
            logger.warning(f"跳过第 {idx+1} 行：无有效突变或基因名")
            continue

        result = query_civic_variant(gene, variant)
        if not result:
            logger.warning(f"查询失败：{gene} {variant}")
            continue

        variants = result.get('data', {}).get('variants', {}).get('edges', [])
        if not variants:
            logger.info(f"无结果：{gene} {variant}")
            continue

        variant_info = variants[0]['node']
        evidence = []
        clinical = []
        drug = []

        for assertion in variant_info.get('assertions', []):
            # 证据等级
            ev = assertion.get('evidenceLevels')
            if ev:
                if isinstance(ev, list):
                    evidence.extend(ev)
                else:
                    evidence.append(ev)
            # 临床意义
            cs = assertion.get('clinicalSignificance')
            if cs:
                if isinstance(cs, list):
                    clinical.extend(cs)
                else:
                    clinical.append(cs)
            # 药物关联
            therapies = assertion.get('therapies', [])
            for therapy in therapies:
                drug_name = therapy.get('name')
                if drug_name:
                    drug.append(drug_name)

        maf_df.at[idx, 'CIViC_Evidence_Level'] = '; '.join(set(evidence))
        maf_df.at[idx, 'CIViC_Clinical_Significance'] = '; '.join(set(clinical))
        maf_df.at[idx, 'CIViC_Drug_Associations'] = '; '.join(set(drug))

        logger.info(f"已注释 {idx+1}/{total_rows}: {gene} {hgvsp}")

        # 每 10 条保存一次进度
        if (idx + 1) % 10 == 0:
            maf_df.to_csv(output_maf, sep='\t', index=False)
            logger.info(f'已保存进度：{idx+1}/{total_rows}')

        time.sleep(1)  # 避免 API 速率限制

    maf_df.to_csv(output_maf, sep='\t', index=False)
    logger.info(f"完成，结果保存至 {output_maf}")

if __name__ == "__main__":
    data_dir = get_data_dir()
    # 确保数据目录存在（如果不存在，os.makedirs 会创建）
    os.makedirs(data_dir, exist_ok=True)
    
    input_file = os.path.join(data_dir, 'tcga_brca_maf.txt')
    output_file = os.path.join(data_dir, 'annotated_brca_maf.txt')
    
    annotate_maf_file(input_file, output_file)