# riskbird
风鸟企业分支信息查询

# 用法
```
usage: riskbird.py [-h] [--output_file OUTPUT_FILE] [--funder_ratio FUNDER_RATIO] input

查询公司投资分支信息并筛选

positional arguments:
  input                 单一公司名称或包含公司名称列表的输入文件路径

options:
  -h, --help            show this help message and exit
  --output_file OUTPUT_FILE
                        结果输出文件路径，如果不指定则打印到控制台
  --funder_ratio FUNDER_RATIO
                        最小资金比例，默认为99
```

# 例子
`python riskbird.py "百度公司"  --funder_ratio 95` 

` python riskbird.py "百度公司" --output_file  output.json --funder_ratio 95` 

`python riskbird.py test.txt  --output_file  output.json --funder_ratio 95` 

