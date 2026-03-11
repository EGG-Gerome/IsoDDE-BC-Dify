import pandas as pd 
import os 
import logging

# ===== 配置 ===== 
# 数据目录相对于当前脚本的路径 
DATA_REL_PATH = '../data'   # 请根据您的实际目录结构调整 

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# =================== 

def get_data_dir():
    """返回数据目录的绝对路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, DATA_REL_PATH))
    return data_dir

def annotate_maf_file(input_maf, output_maf):
    """批量注释 MAF 文件"""
    if not os.path.exists(input_maf):
        logger.error(f"文件不存在：{input_maf}")
        return

    data_dir = get_data_dir()
    
    # 读取CIViC数据文件
    variant_file = os.path.join(data_dir, 'nightly-VariantSummaries.tsv')
    assertion_file = os.path.join(data_dir, 'nightly-AcceptedAssertionSummaries.tsv')
    
    if not os.path.exists(variant_file) or not os.path.exists(assertion_file):
        logger.error("CIViC数据文件不存在，请先下载nightly-VariantSummaries.tsv和nightly-AcceptedAssertionSummaries.tsv文件")
        return
    
    try:
        # 读取CIViC数据文件（使用更直接的方式）
        logger.info("读取CIViC数据文件...")
        
        # 读取Variants文件
        variants = []
        try:
            with open(variant_file, 'r') as f:
                header = f.readline().strip().split('\t')
                for line in f:
                    fields = line.strip().split('\t')
                    # 即使字段数量不足，也尝试创建字典
                    variant_dict = {}
                    for i, field in enumerate(fields):
                        if i < len(header):
                            variant_dict[header[i]] = field
                    # 只有当至少有基本字段时才添加
                    if 'feature_name' in variant_dict and 'variant' in variant_dict:
                        variants.append(variant_dict)
        except Exception as e:
            logger.error(f"读取Variants文件失败: {e}")
        
        # 读取Assertions文件
        assertions = []
        with open(assertion_file, 'r') as f:
            header = f.readline().strip().split('\t')
            for line in f:
                fields = line.strip().split('\t')
                if len(fields) >= len(header):
                    assertions.append(dict(zip(header, fields)))
        
        logger.info(f"Variants文件行数: {len(variants)}")
        logger.info(f"Assertions文件行数: {len(assertions)}")
        
        # 读取MAF文件
        logger.info("读取MAF文件...")
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

        evidence = []
        clinical = []
        drug = []

        # 先在Variants文件中查找匹配的基因和变体
        variant_match = None
        found = False
        
        # 直接遍历variants列表
        for var in variants:
            # 检查feature_name列（可能包含基因符号）
            if 'feature_name' in var:
                feature_name = var['feature_name']
                if feature_name.lower() == gene.lower():
                    # 检查变体是否匹配
                    if 'variant' in var:
                        var_variant = var['variant']
                        if (var_variant == variant or 
                            var_variant.lower() == variant.lower() or 
                            variant.lower() in var_variant.lower()):
                            variant_match = var
                            logger.info(f"找到匹配的变体：{feature_name} {var_variant}")
                            found = True
                            break
                        # 检查别名是否匹配
                        if 'variant_aliases' in var and var['variant_aliases']:
                            if variant.lower() in var['variant_aliases'].lower():
                                variant_match = var
                                logger.info(f"在别名中找到匹配：{feature_name} {var_variant} (别名: {var['variant_aliases']})")
                                found = True
                                break
        
        if not found:
            logger.info(f"无结果：{gene} {variant}")
        
        if variant_match is not None:
            # 在Assertions文件中查找相关的断言
            for assertion in assertions:
                if 'molecular_profile' in assertion:
                    molecular_profile = assertion['molecular_profile']
                    # 检查molecular_profile是否包含基因信息
                    if gene.lower() in molecular_profile.lower():
                        # 提取证据等级（从amp_category字段）
                        if 'amp_category' in assertion and assertion['amp_category']:
                            evidence.append(assertion['amp_category'])
                        # 提取临床意义
                        if 'significance' in assertion and assertion['significance']:
                            clinical.append(assertion['significance'])
                        # 提取药物关联
                        if 'therapies' in assertion and assertion['therapies']:
                            drug.extend([t.strip() for t in assertion['therapies'].split(',')])
        
        # 去重并保存结果
        maf_df.at[idx, 'CIViC_Evidence_Level'] = '; '.join(set(evidence))
        maf_df.at[idx, 'CIViC_Clinical_Significance'] = '; '.join(set(clinical))
        maf_df.at[idx, 'CIViC_Drug_Associations'] = '; '.join(set(drug))

        logger.info(f"已注释 {idx+1}/{total_rows}: {gene} {hgvsp}")

        # 每 10 条保存一次进度
        if (idx + 1) % 10 == 0:
            maf_df.to_csv(output_maf, sep='\t', index=False)
            logger.info(f'已保存进度：{idx+1}/{total_rows}')

    maf_df.to_csv(output_maf, sep='\t', index=False)
    logger.info(f"完成，结果保存至 {output_maf}")

if __name__ == "__main__":
    data_dir = get_data_dir()
    # 确保数据目录存在（如果不存在，os.makedirs 会创建）
    os.makedirs(data_dir, exist_ok=True)
    
    input_file = os.path.join(data_dir, 'tcga_brca_maf.txt')
    output_file = os.path.join(data_dir, 'annotated_brca_maf.txt')
    
    annotate_maf_file(input_file, output_file)