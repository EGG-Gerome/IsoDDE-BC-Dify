# CIViC 批量注释脚本

## 功能

本脚本用于使用 CIViC API 批量注释 MAF 文件，添加以下注释列：
- `CIViC_Evidence_Level`：证据等级
- `CIViC_Clinical_Significance`：临床意义
- `CIViC_Drug_Associations`：药物关联

## 依赖

- Python 3.12+
- requests
- pandas

## 安装依赖

```bash
pip install requests pandas
```

## 使用方法

1. 确保 `data` 目录存在于脚本所在目录的上级目录
2. 将 MAF 文件命名为 `tcga_brca_maf.txt` 并放入 `data` 目录
3. 运行脚本：

```bash
python civic_annotator.py
```

4. 注释结果将保存为 `data/annotated_brca_maf.txt`

## 配置

- `DATA_REL_PATH`：数据目录相对于当前脚本的路径，默认为 `../data`
- 脚本会自动创建数据目录（如果不存在）

## 注意事项

1. 脚本使用 CIViC API，可能存在速率限制，因此每查询一次会休眠 1 秒
2. 脚本会每 10 条记录保存一次进度，以防止意外中断导致数据丢失
3. 请确保 MAF 文件包含 `Hugo_Symbol` 和 `HGVSp_Short` 列
4. 对于无效的基因名或突变信息，脚本会跳过并记录警告

## 输入文件格式

输入文件应为标准 MAF 格式，使用制表符分隔，包含以下列：
- `Hugo_Symbol`：基因符号
- `HGVSp_Short`：蛋白质改变的简短表示（如 p.V600E）

## 输出文件

输出文件在输入文件的基础上添加了三列注释信息：
- `CIViC_Evidence_Level`：来自 CIViC 的证据等级
- `CIViC_Clinical_Significance`：来自 CIViC 的临床意义
- `CIViC_Drug_Associations`：来自 CIViC 的药物关联
