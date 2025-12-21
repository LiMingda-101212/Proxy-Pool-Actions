# -*- coding: utf-8 -*-
#
# ******************************************
# Copyright (c) 2025 李明达. All rights reserved.
#
# project: ProxyPool
# actions_main.py
# V1.1
# written by LiMingda <lmd101212@outlook.com>
# 2025-12-20
#
# This software is for personal, non-commercial use only.
# Unauthorized commercial use is prohibited.
# 本代码仅供个人学习使用，未经许可不得商用。
#*******************************************

# 云端部署精简版
# 格式支持: 类型,代理,分数,是否支持中国,是否支持国际,是否为透明代理,检测到的IP
#          Type,Proxy:Port,Score,China,International,Transparent,DetectedIP

import re
import requests
import concurrent.futures
import time
import os
import csv
import json
import random
import sys

# 获取命令行参数
arguments = sys.argv

# 爬取参数
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0'
}


# 通用网页爬取解析器
def scrape_proxies(url: str, regex_pattern: str, capture_groups: list):
    """
    :param url: 请求地址
    :param regex_pattern: re解析式，用于解析爬取结果
    :param capture_groups: 要返回的re中的值，[IpName, Port]
    :return: [proxy: port]
    """
    extracted_data = []
    encoding = "utf-8"
    try:
        response = requests.get(url=url, headers=HEADERS, timeout=current_config["actions"]["timeout_cn"])
        if response.status_code == 200:  # 判断状态码
            response.encoding = encoding  # 使用utf-8
            regex = re.compile(regex_pattern, re.S)  # 创建一个re对象
            matches = regex.finditer(response.text)  # 对获取的东西进行解析
            for match in matches:
                for group_name in capture_groups:  # 依次输出参数capture_groups中的指定内容
                    extracted_data.append(f"{match.group(group_name)}")
            proxy_list = [f"{extracted_data[i].strip()}:{extracted_data[i + 1].strip()}" for i in
                          range(0, len(extracted_data), 2)]  # 整合列表为[proxy:port]
            response.close()
            return proxy_list
        else:
            get_error = f"\n[failed] 爬取失败,状态码{response.status_code}"  # 前面的\n防止与进度条混在一行
            print(get_error)
            return get_error

    except Exception as e:
        get_error = f"\n[error] 爬取错误: {str(e)}"
        print(get_error)
        return get_error


# 获取自己的公网IP地址
def get_own_ip(max_retries=5, retry_delay=2):
    """
    获取自己的公网IP地址

    :param max_retries: 最大重试次数
    :param retry_delay: 重试延迟(秒)
    :return: IP地址字符串，失败返回None
    """
    # 使用多个IP检测服务提高可靠性
    # "http://api.ipify.org", -> 不能用
    ip_services = current_config["actions"]["test_url_transparent"]
    timeout = current_config["actions"]["timeout_transparent"]

    for attempt in range(max_retries):
        # 随机打乱服务列表，避免总是使用同一个服务
        random.shuffle(ip_services)

        for service in ip_services:
            try:
                print(f"[info] 尝试从 {service} 获取本机IP...")
                response = requests.get(service, timeout=timeout, headers=HEADERS)

                if response.status_code == 200:
                    if service == "http://httpbin.org/ip":
                        # httpbin返回JSON格式
                        ip_data = response.json()
                        ip = ip_data.get('origin')
                    else:
                        # 其他服务返回纯文本IP
                        ip = response.text.strip()

                    # 验证IP格式
                    if ip and is_valid_ip(ip):
                        print(f"[success] 成功获取本机IP: {ip}")
                        return ip
                    else:
                        print(f"[warning] 从 {service} 获取的IP格式无效: {ip}")

            except requests.exceptions.Timeout:
                print(f"[warning] 请求 {service} 超时")
                continue
            except requests.exceptions.ConnectionError:
                print(f"[warning] 无法连接到 {service}")
                continue
            except Exception as e:
                print(f"[warning] 从 {service} 获取IP时出错: {str(e)}")
                continue

        # 所有服务都失败，等待后重试
        if attempt < max_retries - 1:
            print(f"[info] 所有IP服务都失败，{retry_delay}秒后重试... ({attempt + 1}/{max_retries})")
            time.sleep(retry_delay)

    print("[error] 无法获取本机IP地址，透明代理检测将不可用")
    return None


# 验证IP地址格式是否有效
def is_valid_ip(ip):
    """
    验证IP地址格式是否有效

    :param ip: IP地址字符串
    :return: 是否有效
    """
    import socket
    try:
        # 检查IPv4格式
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        try:
            # 检查IPv6格式
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False


# 检测单个代理是否为透明代理
def check_transparent_proxy(proxy, proxy_type="http", own_ip=None):
    """
    检测代理是否为透明代理

    :param proxy: 代理地址
    :param proxy_type: 代理类型
    :param own_ip: 自己的公网IP
    :return: (是否为透明代理, 检测到的IP)
    """
    try:
        # 设置代理
        if proxy_type == "http":
            proxies_config = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
        elif proxy_type == "socks4":
            proxies_config = {
                "http": f"socks4://{proxy}",
                "https": f"socks4://{proxy}"
            }
        elif proxy_type == "socks5":
            proxies_config = {
                "http": f"socks5://{proxy}",
                "https": f"socks5://{proxy}"
            }
        else:
            proxies_config = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }

        # 避免总是使用同一个服务
        url = random.choice(current_config["actions"]["test_url_transparent"])

        # 使用代理访问检测网站
        response = requests.get(
            url,
            proxies=proxies_config,
            timeout=current_config["actions"]["timeout_transparent"]
        )

        if response.status_code == 200:
            if url == "http://httpbin.org/ip":
                # httpbin返回JSON格式
                proxy_ip_data = response.json()
                proxy_ip = proxy_ip_data.get('origin')
            else:
                # 其他服务返回纯文本IP
                proxy_ip = response.text.strip()

            # 判断是否为透明代理：如果返回的IP包含真实IP，则为透明代理
            is_transparent = own_ip in proxy_ip

            return is_transparent, proxy_ip
        else:
            return False, "unknown"

    except:
        return False, "unknown"


# 检查单个代理IP对单个URL的可用性(支持HTTP和SOCKS)
def check_proxy_single(proxy, test_url, timeout, retries=1, proxy_type="auto"):
    """
    检查单个代理IP对单个URL的可用性（支持HTTP和SOCKS）

    :param proxy_type: 代理类型 - "auto"(自动检测), "http", "socks4", "socks5"
    :param proxy: 代理IP地址和端口 (格式: ip:port)
    :param test_url: 用于测试的URL
    :param timeout: 请求超时时间(秒)
    :param retries: 重试次数
    :return: 是否可用, 响应时间, 检测到的类型
    """
    # 根据代理类型设置proxies字典
    if proxy_type == "auto":
        # 自动检测：先尝试HTTP，再尝试SOCKS5，最后SOCKS4
        protocols_to_try = ["http", "socks5", "socks4"]
    else:
        # 指定类型时，只尝试该类型
        protocols_to_try = [proxy_type]

    detected_type = proxy_type if proxy_type != "auto" else "unknown"

    for current_protocol in protocols_to_try:
        if current_protocol == "http":
            proxies_config = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
        elif current_protocol == "socks4":
            proxies_config = {
                "http": f"socks4://{proxy}",
                "https": f"socks4://{proxy}"
            }
        elif current_protocol == "socks5":
            proxies_config = {
                "http": f"socks5://{proxy}",
                "https": f"socks5://{proxy}"
            }
        else:
            proxies_config = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }

        for attempt in range(retries):
            try:
                start_time = time.time()
                response = requests.get(
                    test_url,
                    proxies=proxies_config,
                    timeout=timeout,
                    allow_redirects=False
                )
                end_time = time.time()
                response_time = end_time - start_time

                if response_time > timeout:
                    # 超时，继续下一个协议（如果是自动检测）
                    break

                # if 200 <= response.status_code < 400:   # 接受200-400,较宽松
                if response.status_code == 200:  # 只接受200,严格
                    detected_type = current_protocol  # 类型
                    return True, response_time, detected_type

            except:
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
                # 当前协议失败，如果是自动检测则尝试下一个协议
                break

    # 如果是指定类型验证失败，返回指定类型（即使失败）
    if proxy_type != "auto":
        detected_type = proxy_type

    return False, None, detected_type


# 检查单个代理的综合验证(调用check_proxy_single和check_transparent_proxy),双重验证代理,可选透明代理检测
def check_proxy_dual(proxy, proxy_type="auto", own_ip=None):
    """
    同时验证百度(国内)和Google(国际)，可选透明代理检测

    :param proxy: 被检测的单个代理
    :param proxy_type: 代理类型
    :param own_ip: 本机ip,用于与代理ip对比
    :return: (是否通过国内, 是否通过国际, 最终检测类型, 是否为透明代理, 检测到的IP)
    """
    # 验证国内网站
    cn_success, cn_response_time, detected_type_cn = check_proxy_single(
        proxy, current_config["actions"]["test_url_cn"], current_config["actions"]["timeout_cn"], 1, proxy_type
    )

    # 验证国际网站
    intl_success, intl_response_time, detected_type_intl = check_proxy_single(
        proxy, current_config["actions"]["test_url_intl"], current_config["actions"]["timeout_intl"], 1, proxy_type
    )

    # 使用第一个成功的检测类型，或者第一个检测类型
    final_type = detected_type_cn if detected_type_cn != "unknown" else detected_type_intl
    if final_type == "unknown":
        final_type = proxy_type if proxy_type != "auto" else "http"

    # 透明代理检测（只在代理有效且需要检测时进行）
    is_transparent = False
    detected_ip = "unknown"

    if (current_config["actions"]["check_transparent"].lower() == "true") and (cn_success or intl_success):
        # 判断是否为透明代理：如果返回的IP包含真实IP，则为透明代理
        is_transparent, detected_ip = check_transparent_proxy(proxy, final_type, own_ip)

    return cn_success, intl_success, final_type, is_transparent, detected_ip


# 批量检查代理IP列表(双重验证+透明代理检测)
def check_proxies_batch(proxies, proxy_types, max_workers=50, check_type="new", own_ip=None):
    """
    批量检查代理IP列表
    双重验证,验证百度和谷歌
    透明代理检测

    :param proxies: 代理字典 {proxy: score}
    :param proxy_types: 代理类型字典 {proxy: type}
    :param max_workers: 最大并发量
    :param check_type: "new" 新代理 / "existing" 已有代理
    :param own_ip: 本机ip
    """
    updated_proxies = {}
    updated_types = {}
    updated_china = {}
    updated_international = {}
    updated_transparent = {}
    updated_detected_ips = {}

    # 还没获取到本机ip,再尝试
    if (own_ip is None) and (current_config["actions"]["check_transparent"].lower() == "true"):
        print("再次尝试获取本机ip")
        own_ip = get_own_ip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {}
        for proxy in proxies:
            # 对于已有代理，使用文件中记录的类型；对于新代理，先看是否指定,否则使用自动检测
            if check_type == "existing" and proxy in proxy_types:
                proxy_type = proxy_types[proxy]
            else:
                proxy_type = proxy_types.get(proxy, "auto")  # 从传入的类型字典获取

            future = executor.submit(check_proxy_dual, proxy, proxy_type, own_ip)
            future_to_proxy[future] = proxy

        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                cn_success, intl_success, detected_type, is_transparent, detected_ip = future.result()

                # 计算分数和更新逻辑
                current_score = proxies.get(proxy, 0)

                if check_type == "new":
                    # 新代理：只要通过任一测试就98分
                    if cn_success or intl_success:
                        updated_proxies[proxy] = 98
                        # 透明代理警告
                        transparent_warning = " | [warning] transparent" if is_transparent else ""
                        print(
                            f"✅[success] {proxy} | type:{detected_type} | China:{'pass' if cn_success else 'fail'} | International:{'pass' if intl_success else 'fail'}{transparent_warning}")
                    else:
                        updated_proxies[proxy] = 0
                        print(f"❌[failed] {proxy}")
                else:
                    # 已有代理：根据测试结果调整分数
                    if cn_success and intl_success:
                        # 两次都通过，加2分
                        updated_proxies[proxy] = min(current_score + 2, current_config["actions"]["max_score"])
                        transparent_warning = " | [warning] transparent" if is_transparent else ""
                        print(
                            f"✅[success] {proxy} | type:{detected_type} | China:pass | International:pass | score:{current_score}->{updated_proxies[proxy]}{transparent_warning}")
                    elif cn_success or intl_success:
                        # 只通过一个，加1分
                        updated_proxies[proxy] = min(current_score + 1, current_config["actions"]["max_score"])
                        status = "China:pass | International:fail" if cn_success else "China:fail | International:pass"
                        transparent_warning = " | [warning] transparent" if is_transparent else ""
                        print(
                            f"✅[success] {proxy} | type:{detected_type} | {status} | score: {current_score}->{updated_proxies[proxy]}{transparent_warning}")
                    else:
                        # 两个都不通过，减1分
                        updated_proxies[proxy] = max(0, current_score - 1)
                        print(
                            f"❌[failed] {proxy} | type:{detected_type} | China:fail | International:fail | score:{current_score}->{updated_proxies[proxy]}")

                # 记录类型和支持范围
                updated_types[proxy] = detected_type
                updated_china[proxy] = cn_success
                updated_international[proxy] = intl_success
                updated_transparent[proxy] = is_transparent
                updated_detected_ips[proxy] = detected_ip

            except Exception as e:
                print(f"[error]❌ {proxy} - {str(e)}")

                if check_type == "existing" and proxy in proxies:
                    updated_proxies[proxy] = max(0, proxies[proxy] - 1)
                else:
                    updated_proxies[proxy] = 0

                updated_types[proxy] = proxy_types.get(proxy, "http")
                updated_china[proxy] = False
                updated_international[proxy] = False
                updated_transparent[proxy] = False
                updated_detected_ips[proxy] = "unknown"

    return updated_proxies, updated_types, updated_china, updated_international, updated_transparent, updated_detected_ips


# 从CSV文件加载代理列表、类型、分数、支持范围和透明代理等信息
def load_proxies_from_file(file_path):
    """
    从CSV文件加载代理列表、类型、分数、支持范围和透明代理信息

    返回值:

    proxies: 代理和分数 -> {'180.167.238.98:7302': 100, '123.128.12.93:9050': 81}

    proxy_types: 代理和类型 -> {'180.167.238.98:7302': 'http', '123.128.12.93:9050': 'http'}

    china_support: 代理和是否支持中国 -> {'180.167.238.98:7302': False, '123.128.12.93:9050': False}

    international_support: 代理和是否支持国际 -> {'180.167.238.98:7302': False, '123.128.12.93:9050': False}

    transparent_proxies: 代理和是否为透明代理 -> {'180.167.238.98:7302': False, '123.128.12.93:9050': False}

    detected_ips: 代理和检测到的ip -> {'164.163.42.46:10000': 'unknown', '176.100.216.164:8282': 'unknown'}

    :param file_path: csv代理池文件
    :returns: 代理和分数, 代理和类型, 代理和是否支持中国, 代理和是否支持国际, 代理和是否为透明代理, 代理和检测到的ip


    """
    proxies = {}
    proxy_types = {}
    china_support = {}
    international_support = {}
    transparent_proxies = {}
    detected_ips = {}


    if not os.path.exists(file_path):
        return proxies, proxy_types, china_support, international_support, transparent_proxies, detected_ips

    with open(file_path, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 6:
                # 格式: 类型,proxy:port,分数,China,International,Transparent,DetectedIP
                proxy_type = row[0].strip().lower()
                proxy = row[1].strip()
                try:
                    score = int(row[2])
                    china = row[3].strip().lower() == 'true'
                    international = row[4].strip().lower() == 'true'
                    transparent = row[5].strip().lower() == 'true'
                    detected_ip = row[6].strip() if len(row) > 6 else "unknown"

                    proxies[proxy] = score
                    proxy_types[proxy] = proxy_type
                    china_support[proxy] = china
                    international_support[proxy] = international
                    transparent_proxies[proxy] = transparent
                    detected_ips[proxy] = detected_ip

                except:
                    # 如果解析失败，使用默认值
                    proxies[proxy] = 70
                    proxy_types[proxy] = "http"
                    china_support[proxy] = False
                    international_support[proxy] = False
                    transparent_proxies[proxy] = False
                    detected_ips[proxy] = "unknown"

    return proxies, proxy_types, china_support, international_support, transparent_proxies, detected_ips


# 保存有效代理到CSV文件（带类型、分数、支持范围和透明代理等信息)
def save_valid_proxies(proxies, proxy_types, china_support, international_support, transparent_proxies, detected_ips,
                       file_path):
    """保存有效代理到CSV文件（带类型、分数、支持范围和透明代理信息）"""
    with open(file_path, 'w', encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        for proxy, score in proxies.items():
            if len(proxy) > 7 and score > 0:  # 基本验证
                proxy_type = proxy_types.get(proxy, "http")
                china = china_support.get(proxy, False)
                international = international_support.get(proxy, False)
                transparent = transparent_proxies.get(proxy, False)
                # 单独处理detected_ip
                detected_ip = detected_ips.get(proxy, "unknown")
                # 过滤无效响应
                try:
                    # 如果是字符串但看起来像JSON，unknown
                    if isinstance(detected_ip, str) and detected_ip.startswith('{') and detected_ip.endswith('}'):
                        # 处理
                        detected_ip = "unknown"

                except Exception as e:
                    print(f"[warning] 筛选detected_ip失败: {e}, 保持原样")

                writer.writerow(
                    [proxy_type, proxy, score, china, international, transparent, detected_ip])


# 更新代理分数文件，移除0分代理
def update_proxy_scores(file_path):
    """更新代理分数文件，移除0分代理"""
    proxies, proxy_types, china_support, international_support, transparent_proxies, detected_ips = load_proxies_from_file(
        file_path)
    valid_proxies = {k: v for k, v in proxies.items() if v > 0}
    valid_types = {k: v for k, v in proxy_types.items() if k in valid_proxies}
    valid_china = {k: v for k, v in china_support.items() if k in valid_proxies}
    valid_international = {k: v for k, v in international_support.items() if k in valid_proxies}
    valid_transparent = {k: v for k, v in transparent_proxies.items() if k in valid_proxies}
    valid_detected_ips = {k: v for k, v in detected_ips.items() if k in valid_proxies}


    save_valid_proxies(valid_proxies, valid_types, valid_china, valid_international, valid_transparent,
                       valid_detected_ips, file_path)
    return len(proxies) - len(valid_proxies)


# 从新获取代理中去掉无效的、重复的
def filter_proxies(all_proxies):
    """
    从新获取代理中去掉无效的、重复的

    使用集合进行查找，时间复杂度O(1)

    :param all_proxies: 新代理列表
    :return: 筛选后的代理列表
    """
    if not all_proxies:
        print("[info] 没有代理需要筛选")
        return []

    print(f"[info] 开始筛选 {len(all_proxies)} 个代理...")

    # 加载现有代理池（使用集合提高查找效率）
    existing_proxies_set = set()
    output_file = current_config["actions"]["output_file"]

    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:
                        existing_proxies_set.add(row[1].strip())
        except Exception as e:
            print(f"[warning] 读取现有代理池失败: {e}")

    # 使用集合进行去重和验证
    seen_proxies = set()
    new_proxies_set = set()
    duplicate_count = 0
    invalid_count = 0
    format_error_count = 0

    for proxy in all_proxies:
        if not proxy or not isinstance(proxy, str):
            invalid_count += 1
            continue

        proxy = proxy.strip()

        # 检查是否已经处理过（当前批次去重）
        if proxy in seen_proxies:
            duplicate_count += 1
            continue
        seen_proxies.add(proxy)

        # 验证代理格式
        if not is_valid_proxy_format(proxy):
            format_error_count += 1
            continue

        # 检查是否已在代理池中
        if proxy in existing_proxies_set:
            duplicate_count += 1
            continue

        # 检查是否在当前新代理集合中（避免重复添加）
        if proxy in new_proxies_set:
            duplicate_count += 1
            continue

        new_proxies_set.add(proxy)

    # 转换为列表
    new_proxies = list(new_proxies_set)

    print(f"[success] 筛选完成!")
    print(f"  有效新代理: {len(new_proxies)}")
    print(f"  重复代理: {duplicate_count}")
    print(f"  格式错误: {format_error_count}")
    print(f"  无效代理: {invalid_count}")

    return new_proxies


# 验证代理格式是否有效
def is_valid_proxy_format(proxy):
    """
    验证代理格式是否有效

    :param proxy: 代理字符串 (ip:port)
    :return: 是否有效
    """
    if not proxy or ':' not in proxy:
        return False

    try:
        ip, port = proxy.split(':', 1)

        # 验证IP格式
        if not is_valid_ip(ip):
            return False

        # 验证端口格式
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            return False

        return True

    except (ValueError, AttributeError):
        return False


# 验证新代理（支持国内外和透明代理检测）
def validate_new_proxies(new_proxies, proxy_type="auto"):
    """验证新代理（支持国内外和透明代理检测）"""
    own_ip = None

    if not new_proxies:
        print("[failed] 没有代理需要验证")
        return

    original_count = len(new_proxies)
    print(f"[info] 共加载 {original_count} 个新代理，使用{proxy_type}类型开始国内外双重测试...")

    # PERF: 初始化本机ip,用于透明代理检测(防止每个验证都重新获取,这样一轮一次)
    if current_config["actions"]["check_transparent"].lower() == "true":
        own_ip = get_own_ip()
        print("[info] 启用透明代理检测")

    # 新代理初始分数为0
    new_proxies_dict = {proxy: 0 for proxy in new_proxies}
    new_types_dict = {proxy: proxy_type for proxy in new_proxies}

    updated_proxies, updated_types, updated_china, updated_international, updated_transparent, updated_detected_ips = check_proxies_batch(
        new_proxies_dict, new_types_dict, current_config["actions"]["max_workers"], check_type="new", own_ip=own_ip
    )

    # 合并到现有代理池
    existing_proxies, existing_types, existing_china, existing_international, existing_transparent, existing_detected_ips = load_proxies_from_file(
        current_config["actions"]["output_file"])

    for proxy, score in updated_proxies.items():
        if proxy not in existing_proxies or existing_proxies[proxy] < score:
            existing_proxies[proxy] = score
            existing_types[proxy] = updated_types[proxy]
            existing_china[proxy] = updated_china[proxy]
            existing_international[proxy] = updated_international[proxy]
            existing_transparent[proxy] = updated_transparent[proxy]
            existing_detected_ips[proxy] = updated_detected_ips[proxy]
        # 浏览器验证部分不变,直接传入
    save_valid_proxies(existing_proxies, existing_types, existing_china, existing_international, existing_transparent,
                       existing_detected_ips, current_config["actions"]["output_file"])
    # 统计结果
    success_count = sum(1 for score in updated_proxies.values() if score == 98)
    china_only = sum(1 for proxy in updated_proxies if updated_china[proxy] and not updated_international[proxy])
    intl_only = sum(1 for proxy in updated_proxies if not updated_china[proxy] and updated_international[proxy])
    both_support = sum(1 for proxy in updated_proxies if updated_china[proxy] and updated_international[proxy])
    transparent_count = sum(1 for proxy in updated_proxies if updated_transparent[proxy])

    print(f"\n[success] 验证完成!")
    print(f"成功代理: {success_count}/{original_count}")
    print(f"仅支持国内: {china_only} | 仅支持国际: {intl_only} | 双支持: {both_support}")
    print(f"透明代理: {transparent_count} 个")
    print(f"代理池已更新至: {current_config['actions']['output_file']}")


# 验证已有代理池中的代理（支持国内外和透明代理检测）
def validate_existing_proxies():
    """验证已有代理池中的代理（支持国内外和透明代理检测）"""
    own_ip = None

    print(f"[info] 开始验证已有代理池，文件：{current_config['actions']['output_file']}...")

    # PERF: 初始化本机ip,用于透明代理检测(防止每个验证都重新获取,这样一轮一次)
    if current_config["actions"]["check_transparent"].lower() == "true":
        own_ip = get_own_ip()
        print("[info] 启用透明代理检测")

    # 加载代理池
    all_proxies, proxy_types, china_support, international_support, transparent_proxies, detected_ips = load_proxies_from_file(
        current_config["actions"]["output_file"])

    if not all_proxies:
        print("[failed] 没有代理需要验证")
        return

    print(f"[start] 共加载 {len(all_proxies)} 个代理，开始测试...")

    # 验证后的
    updated_proxies, updated_types, updated_china, updated_international, updated_transparent, updated_detected_ips = check_proxies_batch(
        all_proxies, proxy_types, current_config["actions"]["max_workers"], "existing", own_ip
    )

    # 更新所有代理分数和支持范围
    for proxy, score in updated_proxies.items():
        all_proxies[proxy] = score
        proxy_types[proxy] = updated_types[proxy]
        china_support[proxy] = updated_china[proxy]
        international_support[proxy] = updated_international[proxy]
        if updated_china[proxy] or updated_international[proxy]:  # 只有通过了才更改,要不然全是unknown
            transparent_proxies[proxy] = updated_transparent[proxy]
            detected_ips[proxy] = updated_detected_ips[proxy]

    # 保存更新后的代理池
    save_valid_proxies(all_proxies, proxy_types, china_support, international_support, transparent_proxies,
                       detected_ips, current_config["actions"]["output_file"])

    # 清理0分代理
    update_proxy_scores(current_config["actions"]["output_file"])

    # 最终统计
    final_proxies, _, final_china, final_international, final_transparent, _ = load_proxies_from_file(
        current_config["actions"]["output_file"])
    final_count = len(final_proxies)

    china_only = sum(1 for proxy in final_proxies if final_china[proxy] and not final_international[proxy])
    intl_only = sum(1 for proxy in final_proxies if not final_china[proxy] and final_international[proxy])
    both_support = sum(1 for proxy in final_proxies if final_china[proxy] and final_international[proxy])
    transparent_count = sum(1 for proxy in final_proxies if final_transparent[proxy])

    print(f"\n[success] 验证完成! 剩余有效代理: {final_count}/{len(all_proxies)}")
    print(f"仅支持国内: {china_only} | 仅支持国际: {intl_only} | 双支持: {both_support}")
    print(f"[warning] 透明代理: {transparent_count} 个")
    print(f"已移除 {len(all_proxies) - final_count} 个无效代理")


# 爬取网页代理
def crawl_proxies(scraper_choice):
    all_proxies = []  # 存储所有爬取的代理
    by_type = ''  # 通过指定类型验证,默认为否

    if scraper_choice == "1":
        try:
            by_type = 'http'  # 默认用http
            count = 1000

            print(f"[start] 开始爬取 {count} 个代理...")
            try:
                # 适合用协程
                import aiohttp
                import asyncio

                async def fetch_proxy(session, url, semaphore):
                    async with semaphore:
                        try:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    proxy = await response.text()
                                    print(proxy)
                                    return proxy.strip()
                        except:
                            return None

                async def fetch_proxies_main():
                    semaphore = asyncio.Semaphore(20)  # 最大并发
                    timeout = aiohttp.ClientTimeout(total=50)  # 超时(给服务器足够响应时间)

                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        tasks = []
                        for _ in range(count):
                            url = 'https://proxypool.scrape.center/random'
                            task = fetch_proxy(session, url, semaphore)
                            tasks.append(task)

                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        return [r for r in results if r and isinstance(r, str) and ':' in r]

                proxies = asyncio.run(fetch_proxies_main())
                if proxies:
                    all_proxies.extend(proxies)

            except ImportError:
                print("[failed] aiohttp 未安装，使用同步请求...")
                # 同步备选方案
                for _ in range(count):
                    try:
                        proxy = requests.get('https://proxypool.scrape.center/random', timeout=30).text.strip()
                        if proxy and ':' in proxy:
                            all_proxies.append(proxy)
                    except:
                        continue

            print(f"[success] 爬取完成！")
        except ValueError:
            print("[error] 错误")
            return None, None

    # https://github.com/databay-labs/free-proxy-list/raw/refs/heads/master/http.txt -> https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt
    # https://github.com/databay-labs/free-proxy-list/raw/refs/heads/master/socks5.txt -> https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt
    # https://github.com/databay-labs/free-proxy-list/raw/refs/heads/master/https.txt -> https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/https.txt
    elif scraper_choice == '2':
        by_type = 'http'  # 默认用http
        print(
            '[start] 开始爬取:https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = response.text.split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    elif scraper_choice == '3':
        by_type = 'socks5'  # 默认用socks5
        print(
            '[start] 开始爬取:https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt'
        try:
            response = requests.get(url, headers=HEADERS)
            result = response.text.split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    elif scraper_choice == '4':
        by_type = 'http'  # 默认用http
        print(
            '[start] 开始爬取:https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/https.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/https.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = response.text.split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    # https://github.com/zloi-user/hideip.me/raw/refs/heads/master/http.txt -> https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/http.txt
    # https://github.com/zloi-user/hideip.me/raw/refs/heads/master/https.txt -> https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/https.txt
    # https://github.com/zloi-user/hideip.me/raw/refs/heads/master/socks4.txt -> https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks4.txt
    # https://github.com/zloi-user/hideip.me/raw/refs/heads/master/socks5.txt -> https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks5.txt
    elif scraper_choice == '5':
        by_type = 'http'  # 默认用http
        print('[start] 开始爬取:https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/http.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/http.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = re.sub(r':\D.*?\n', '\n', response.text).split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    elif scraper_choice == '6':
        by_type = 'http'  # 默认用http
        print('[start] 开始爬取:https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/https.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/https.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = re.sub(r':\D.*?\n', '\n', response.text).split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    elif scraper_choice == '7':
        by_type = 'socks4'
        print('[start] 开始爬取:https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks4.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks4.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = re.sub(r':\D.*?\n', '\n', response.text).split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    elif scraper_choice == '8':
        by_type = 'socks5'
        print('[start] 开始爬取:https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks5.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks5.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = re.sub(r':\D.*?\n', '\n', response.text).split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    # https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt

    elif scraper_choice == '9':
        by_type = 'socks5'
        print('[start] 开始爬取:https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt')
        error_count = 0
        url = 'https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt'

        try:
            response = requests.get(url, headers=HEADERS)
            result = response.text.split("\n")
            proxy_list = []
            for proxy in result:
                if len(result) == 0:
                    print('[failed] 没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'[end] 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'[error] 爬取失败: {str(e)}')

    return filter_proxies(all_proxies), by_type


# 加载设置
def load_settings():
    """加载设置"""
    # 默认配置
    config = {
        "actions": {
            "output_file": "proxies.csv",
            "test_url_cn": "http://www.baidu.com",
            "test_url_intl": "http://www.google.com",
            "test_url_transparent": [
                "http://httpbin.org/ip",
                "http://ipinfo.io/ip"
            ],
            "test_urls_safety": {
                "html": "http://httpbin.org/html",
                "json": "http://httpbin.org/json",
                "https": "https://httpbin.org/get",
                "headers": "http://httpbin.org/headers",
                "delay": "http://httpbin.org/delay/1",
                "base64": "http://httpbin.org/base64/SGVsbG8gV29ybGQ=",
                "ip_test": "http://httpbin.org/ip"
            },
            "test_url_browser": "https://httpbin.org/ip",
            "check_transparent": "True",
            "high_score_agency_scope": 98,
            "timeout_cn": 6,
            "timeout_intl": 10,
            "timeout_transparent": 8,
            "timeout_safety": 10,
            "timeout_browser": 30,
            "max_workers": 100,
            "max_score": 100
        }
    }
    try:
        with open("data/config.json", "r", encoding="utf-8") as f:
            config = json.loads(f.read())
        print("[success] 已从配置文件加载设置")
        return config
    except FileNotFoundError:
        print("[error] 配置文件不存在: data/config.json")
        return config
    except json.JSONDecodeError:
        print("[error] 配置文件格式错误")
        return config
    except Exception as e:
        print(f"[error] 加载配置时出错: {e}")
        return config


if __name__ == '__main__':
    parameter = arguments[1:2]
    print("参数:", parameter)
    # 1 加载设置
    current_config = load_settings()

    if parameter[0] == "update_existing_proxies":
        print("[info] === 开始重新验证已有代理 ===")
        # 验证已有代理
        validate_existing_proxies()

    elif parameter[0] == "crawl_and_verify_new_proxies":
        print("[info] === 开始爬取并验证新代理 ===")
        for i in range(2, 9 + 1):
            # 爬取新代理
            new_proxies, by_type = crawl_proxies(scraper_choice=str(i))

            # 验证新代理
            if new_proxies:
                if by_type:
                    validate_new_proxies(new_proxies, by_type)
                else:
                    validate_new_proxies(new_proxies, "auto")

    else:
        print("[error] 非合法参数")
