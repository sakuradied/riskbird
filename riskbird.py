import configparser
import requests
import re
import json
import argparse
import os


# 全局变量：存储User-Agent和Cookies配置
global cookies, user_agent

# 读取配置文件并获取User-Agent和Cookie信息
def load_config(config_file='config.ini'):
    """
    加载配置文件，读取User-Agent和Cookies
    :param config_file: 配置文件路径，默认为'config.ini'
    :return: user_agent, cookies
    """
    global cookies, user_agent
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(config_file)
        user_agent = config['riskbird']['user_agent']
        cookies = config['riskbird']['riskbird_cookie']
    except Exception as e:
        cookies = None
        user_agent = None
        print(f"[ERR]: 配置文件加载失败 - {e}")

# 获取企业名称，返回搜索结果的第一家公司名称
def get_first_company_name(company_name):
    """
    根据公司名称从Riskbird API获取查询结果，并返回第一家公司名称
    :param company_name: 要查询的公司名称
    :return: 第一家公司名称，如果查询失败返回None
    """
    url = "https://www.riskbird.com/riskbird-api/newSearch"
    headers = {
        'User-Agent': user_agent,
        'Accept': 'application/json',
        'Origin': 'https://www.riskbird.com',
        'Cookie': str(cookies),
        'App-Device': 'WEB'
    }

    post_data = {
        'queryType': '1',
        'searchKey': company_name,
        'pageNo': 1,
        'range': 10,
        'selectConditionData': ''
    }

    try:
        response = requests.post(url=url, headers=headers, json=post_data)
        response_data = json.loads(response.text)
        if response_data["code"] == 20000:
            first_company_name = response_data["data"]["list"][0]["ENTNAME"]
            return first_company_name
        else:
            print("[ERR]: 查询失败")
            return None
    except Exception as e:
        print(f"[ERR]: 获取公司名称失败 - {e}")
        return None

# 获取企业的order_number
def get_order_number(company_name):
    """
    获取公司页面的order_number
    :param company_name: 公司名称
    :return: order_number，如果获取失败返回None
    """
    url = f"https://www.riskbird.com/ent/{company_name}.html"
    headers = {
        'User-Agent': user_agent,
        'Accept': 'application/json',
        'Origin': 'https://www.riskbird.com',
        'Cookie': str(cookies),
        'App-Device': 'WEB'
    }

    try:
        response = requests.get(url=url, headers=headers)
        pattern = r'WEB\d+'  # 匹配WEB后面跟着的数字
        match = re.search(pattern, response.text)
        if match:
            return match[0]
        else:
            return None
    except Exception as e:
        print(f"[ERR]: 获取企业order_number失败 - {e}")
        return None

# 读取公司名称列表（批量处理）
def read_company_list(input_file):
    """
    从输入文件读取公司名称列表
    :param input_file: 输入文件路径
    :return: 公司名称列表
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            companies = [line.strip() for line in file.readlines()]
        return companies
    except Exception as e:
        print(f"[ERR]: 读取公司列表失败 - {e}")
        return []

# 将结果输出到文件
def write_output(output_file, data):
    """
    将结果写入输出文件
    :param output_file: 输出文件路径
    :param data: 需要写入的数据
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            for item in data:
                file.write(json.dumps(item, ensure_ascii=False, indent=4))
                file.write("\n")
    except Exception as e:
        print(f"[ERR]: 写入输出文件失败 - {e}")

# 获取公司投资分支信息，并筛选出资金比例大于等于指定值的公司
def get_investment_branches(order_number, min_funder_ratio):
    """
    获取公司的投资分支信息，并筛选出资金比例大于等于指定值的公司
    :param order_number: 公司order_number
    :param min_funder_ratio: 最小资金比例，过滤条件
    :return: 满足条件的公司列表
    """
    url = "https://www.riskbird.com/riskbird-api/companyInfo/list"
    headers = {
        'User-Agent': user_agent,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Xs-Content-Type': 'application/json',
        'Origin': 'https://www.riskbird.com',
        'Cookie': str(cookies),
        'App-Device': 'WEB'
    }
    
    post_data = {
        "page": 1,
        "size": 2000,
        "orderNo": order_number,
        "extractType": "companyInvest",
        "sortField": ""
    }

    try:
        response = requests.post(url=url, headers=headers, json=post_data)
        response_data = json.loads(response.text)
        investment_branches = []

        # 提取企业投资信息
        for company in response_data["data"]["apiData"]:
            investment_branches.append({
                "entName": company["entName"],
                "funderRatio": company["funderRatio"]
            })

        # 筛选出符合条件的公司
        filtered_branches = [
            branch for branch in investment_branches
            if float(branch['funderRatio'].strip('%')) >= min_funder_ratio
        ]
        return filtered_branches

    except Exception as e:
        print(f"[ERR]: 获取投资分支信息失败 - {e}")
        return []


def print_output(data):
    """
    将结果打印到控制台
    :param data: 需要打印的数据
    """
    for item in data:
        print(json.dumps(item, ensure_ascii=False, indent=4))


# 主程序，获取企业信息并筛选符合条件的投资分支
def main(company_name, min_funder_ratio):
    """
    主程序，获取指定公司名称的投资分支信息并筛选
    :param company_name: 查询的公司名称
    :param min_funder_ratio: 最小资金比例，筛选条件
    :return: 筛选后的公司信息
    """
    # 加载配置文件
    load_config()

    # 获取目标企业名称
    first_company_name = get_first_company_name(company_name)
    if not first_company_name:
        print(f"[ERR]: 未找到公司 {company_name}")
        return []

    # 获取order_number
    order_number = get_order_number(first_company_name)
    if not order_number:
        print(f"[ERR]: 获取order_number失败，无法继续处理")
        return []

    # 获取并筛选投资分支信息
    investment_branches = get_investment_branches(order_number, min_funder_ratio)
    if not investment_branches:
        print("[INFO]: 无符合条件的投资分支")
        return []
    
    return investment_branches

# 执行主程序，示例查询百度公司，筛选资金比例大于等于99%的分支
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="查询公司投资分支信息并筛选")
    parser.add_argument('input', help="单一公司名称或包含公司名称列表的输入文件路径")
    parser.add_argument('--output_file', help="结果输出文件路径，如果不指定则打印到控制台")
    parser.add_argument('--funder_ratio', type=float, default=99, help="最小资金比例，默认为99")
    args = parser.parse_args()

    # 加载配置文件
    load_config()

    # 判断是单一公司名称还是批量文件
    if os.path.isfile(args.input):
        # 处理批量文件
        companies = read_company_list(args.input)
        if not companies:
            print("[ERR]: 未读取到公司列表")
            exit()

        # 处理每个公司并输出结果
        all_results = []
        for company in companies:
            print(f"[INFO]: 正在处理公司: {company}")
            
            # 获取目标企业名称
            first_company_name = get_first_company_name(company)
            if not first_company_name:
                print(f"[ERR]: 未找到公司 {company}")
                continue

            # 获取order_number
            order_number = get_order_number(first_company_name)
            if not order_number:
                print(f"[ERR]: 获取order_number失败，无法继续处理 {company}")
                continue

            # 获取并筛选投资分支信息
            investment_branches = get_investment_branches(order_number, args.funder_ratio)
            if investment_branches:
                all_results.append({
                    "company": company,
                    "investment_branches": investment_branches
                })

        # 输出结果：如果指定了输出文件，则写入文件，否则打印到控制台
        if all_results:
            if args.output_file:
                write_output(args.output_file, all_results)
                print(f"[INFO]: 结果已成功写入 {args.output_file}")
            else:
                print_output(all_results)
        else:
            print("[INFO]: 没有符合条件的公司")

    else:
        # 处理单一公司名称
        print(f"[INFO]: 正在处理单一公司: {args.input}")
        
        # 获取目标企业名称
        first_company_name = get_first_company_name(args.input)
        if not first_company_name:
            print(f"[ERR]: 未找到公司 {args.input}")
            exit()

        # 获取order_number
        order_number = get_order_number(first_company_name)
        if not order_number:
            print(f"[ERR]: 获取order_number失败，无法继续处理 {args.input}")
            exit()

        # 获取并筛选投资分支信息
        investment_branches = get_investment_branches(order_number, args.funder_ratio)
        if investment_branches:
            result = [{
                "company": args.input,
                "investment_branches": investment_branches
            }]
            
            # 输出结果：如果指定了输出文件，则写入文件，否则打印
            if args.output_file:
                write_output(args.output_file, result)
                print(f"[INFO]: 结果已成功写入 {args.output_file}")
            else:
                print_output(result)
        else:
            print("[INFO]: 没有符合条件的公司")