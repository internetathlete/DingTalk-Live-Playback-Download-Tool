import os
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import sys
import re
import tkinter as tk
from tkinter import filedialog
import logging
import pandas as pd
from urllib.parse import urlparse, parse_qs


logging.disable(logging.CRITICAL)  # 禁用所有日志



# 支持默认选项的输入验证函数
def validate_input(prompt, valid_options, default_option=None):
    while True:
        choice = input(prompt)
        if choice == '' and default_option is not None:
            return default_option
        if choice in valid_options:
            return choice
        print("无效的选择，请重新输入。")

# 根据操作系统选择N_m3u8DL-RE可执行文件
def get_executable_name():
    system = platform.system()
    if system == 'Windows':
        return 'N_m3u8DL-RE.exe'
    elif system == 'Linux' or system == 'Darwin':  # Darwin是macOS的系统名
        return './N_m3u8DL-RE'  # Linux和macOS执行文件
    else:
        raise Exception(f"不支持的操作系统: {system}")

# 处理用户输入路径中的多余引号和空格
def clean_file_path(input_path):
    return input_path.strip().replace('"', '').replace("'", "")


def read_links_file(file_path):
    try:
        # 清理文件路径
        file_path = clean_file_path(file_path)

        # 存储找到的链接
        links = {}

        # 判断文件类型，处理 CSV 文件
        if file_path.endswith('.csv'):
            try:
                # 尝试用 utf-8 编码打开文件
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # 如果 utf-8 编码失败，尝试用 gbk 编码
                try:
                    df = pd.read_csv(file_path, encoding='gbk')
                except UnicodeDecodeError:
                    print(f"文件 {file_path} 使用的编码无法识别，请尝试其他编码格式。")
                    sys.exit(1)

            # 遍历 CSV 中所有列和每列的每一行
            for col in df.columns:
                # 遍历每个单元格，检查链接
                for i, value in df[col].dropna().items():
                    if isinstance(value, str) and value.startswith("https://n.dingtalk.com"):
                        links[i] = value  # 保存符合条件的链接

        # 判断文件类型，处理 Excel 文件
        elif file_path.endswith(('.xlsx', '.xls')):  # Excel 文件
            # 读取整个 Excel 文件
            xls = pd.ExcelFile(file_path)
            # 遍历每个工作表
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # 遍历工作表中的每一列
                for col in df.columns:
                    # 遍历每个单元格，检查链接
                    for i, value in df[col].dropna().items():
                        if isinstance(value, str) and value.startswith("https://n.dingtalk.com"):
                            links[i] = value  # 保存符合条件的链接

        else:
            raise ValueError(f"文件格式不支持: {file_path}. 请使用CSV或Excel文件。")

        if not links:
            raise ValueError("未找到有效的钉钉直播链接。")

        return links

    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        sys.exit(1)


# 获取浏览器Cookie的函数
def get_browser_cookie(url, browser_type='edge'):
    global browser
    try:
        if browser_type == 'edge':
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--disable-usb-device-event-log')
            edge_options.add_argument('--ignore-certificate-errors')
            edge_options.add_argument('--disable-logging')          
            edge_options.add_argument('--disable_ssl_verification')
            edge_options.add_argument('--log-level=3')
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            edge_options.set_capability("ms:loggingPrefs", {"performance": "ALL"})
            # 启用浏览器日志，获取网络请求
            # edge_options.set_capability("ms:loggingPrefs", {
            #     'browser': 'ALL',       # 启用浏览器日志
            #     'performance': 'ALL'    # 启用性能日志
            # })
            browser = webdriver.Edge(options=edge_options)
        elif browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--disable-usb-device-event-log')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            # 启用浏览器日志，获取网络请求
            # chrome_options.set_capability("goog:loggingPrefs", {
            #     'browser': 'ALL',       # 启用浏览器日志
            #     'performance': 'ALL'    # 启用性能日志
            # })
            chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            browser = webdriver.Chrome(options=chrome_options)
        elif browser_type == 'firefox':
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--disable-usb-device-event-log')
            firefox_options.add_argument('--ignore-certificate-errors')
            firefox_options.add_argument('--disable-logging')
            firefox_options.add_argument('--log-level=3')
            # 启用Firefox日志
            firefox_options.set_capability('moz:firefoxOptions', {
                'log': {
                    'level': 'ALL',    # 开启日志级别
                    'browser': 'ALL',  # 启用浏览器日志
                }
            })

            browser = webdriver.Firefox(options=firefox_options)

        browser.get(url)
        input("请在浏览器中登录钉钉账户后，按Enter键继续...")

        headers = browser.execute_script("return Object.fromEntries(new Headers(fetch(arguments[0], { method: 'GET' })).entries())", url)
        live_name_element = browser.find_element(By.CLASS_NAME, "_3TIxkhmY")
        live_name = live_name_element.text
        print(f"直播名称: {live_name}")

        cookies = browser.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

        return browser, cookie_dict, headers, live_name
    except Exception as e:
        print(f"获取Cookie时发生错误: {e}")
        if browser:
            browser.quit()
        sys.exit(1)

def repeat_get_browser_cookie(url):
    global browser
    try:
        if browser is None:
            return get_browser_cookie(url)
        
        browser.get(url)
        WebDriverWait(browser, 2).until(EC.visibility_of_element_located((By.CLASS_NAME, "_3TIxkhmY")))
        headers = browser.execute_script("return Object.fromEntries(new Headers(fetch(arguments[0], { method: 'GET' })).entries())", url)
        live_name_element = browser.find_element(By.CLASS_NAME, "_3TIxkhmY")
        live_name = live_name_element.text
        print(f"直播名称: {live_name}")

        cookies = browser.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

        return cookie_dict, headers, live_name
    except Exception as e:
        print(f"重复获取Cookie时发生错误: {e}")
        if browser:
            browser.quit()
        sys.exit(1)

def repeat_process_links(new_links_dict, browser, browser_type, save_mode):
    """
    继续处理新输入的钉钉直播回放链接，并下载视频。
    """
    total_links = len(new_links_dict)
    print(f"共提取到 {total_links} 个新的钉钉直播回放分享链接。")

    saved_path = None  # 用于保存路径
    for idx, dingtalk_url in new_links_dict.items():
        print(f"正在下载第 {idx + 1} 个视频，共 {total_links} 个视频。")
        cookies_data, m3u8_headers, live_name = repeat_get_browser_cookie(dingtalk_url)
        m3u8_links = fetch_m3u8_links(browser, browser_type, dingtalk_url)

        if m3u8_links:
            for link in m3u8_links:
                m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)
                prefix = extract_prefix(link)
                save_name = live_name

                if save_mode == '1':
                    saved_path = auto_download_m3u8_with_options(m3u8_file, save_name, prefix)  # 默认下载到 Downloads
                elif save_mode == '2':
                    saved_path = download_m3u8_with_reused_path(m3u8_file, save_name, prefix, saved_path)  # 手动选择路径

        print('=' * 100)

    return saved_path


def continue_download(saved_path, browser, browser_type):
    """
    继续下载新的钉钉直播回放链接。
    """
    continue_option = input("是否继续输入钉钉直播回放链接表格路径进行下载？(按Enter继续，按q退出程序): ")
    if continue_option.lower() == 'q':
        print("程序已退出。")
        if browser:
            browser.quit()
        return False
    else:
        file_path = input("请输入新的钉钉直播回放链接表格路径（支持CSV或Excel格式，可直接将文件拖放进窗口）: ")
        new_links_dict = read_links_file(file_path)
        print(f"共提取到 {len(new_links_dict)} 个新的钉钉直播回放分享链接。")
        saved_path = repeat_process_links(new_links_dict, browser, browser_type)
        return True, saved_path
import json
import os
import time

# def save_logs_to_file(logs):
#     # 获取当前时间戳，确保文件名唯一
#     timestamp = time.strftime("%Y%m%d_%H%M%S")
#     file_name = f"logs_{timestamp}.json"
    
#     # 如果 logs.json 已经存在，自动修改文件名
#     count = 1
#     while os.path.exists(file_name):
#         file_name = f"logs_{timestamp}_{count}.json"
#         count += 1
    
#     # 将日志内容写入文件
#     try:
#         with open(file_name, 'w', encoding='utf-8') as f:
#             json.dump(logs, f, ensure_ascii=False, indent=4)
#         print(f"日志已保存为 {file_name}")
#     except Exception as e:
#         print(f"保存日志时发生错误: {e}")

import re
from urllib.parse import urlparse, parse_qs

def fetch_m3u8_links(browser, browser_type, dingtalk_url):
    m3u8_links = []  # 初始化为空列表
    # 从用户输入的URL中提取 liveUuid
    parsed_url = urlparse(dingtalk_url)
    query_params = parse_qs(parsed_url.query)
    live_uuid = query_params.get('liveUuid', [None])[0]

    if not live_uuid:
        print("未能从 URL 提取 liveUuid，程序将退出。")
        return None

    for attempt in range(5):  # 重试次数为 5（你可以根据需要调整）
        try:
            if browser_type == 'chrome' or browser_type == 'edge':  # Chrome 和 Edge 使用 get_log
                logs = browser.get_log("performance")
#                 # 将获取到的 logs 保存为日志文件
#                 save_logs_to_file(logs)
            elif browser_type == 'firefox':  # Firefox 使用 execute_script 和正则表达式
                logs = browser.execute_script("""
                    var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                    var network = performance.getEntries() || {};
                    return network;
                """)
#                 # 将获取到的 logs 保存为日志文件
#                 save_logs_to_file(logs)
            # 遍历日志，提取 m3u8 链接
            for log in logs:
                try:
                    # 根据浏览器的不同处理日志
                    if browser_type == 'firefox':
                        # 使用正则表达式从日志中提取 m3u8 链接
                        log_message = str(log)
                        pattern = r'https://[^,\'"]+\.m3u8\?[^\'"]+'
                        found_links = re.findall(pattern, log_message)

                        if found_links:
                            # 清理末尾的 "]" 和 "\" 等不必要字符
                            cleaned_link = re.sub(r'[\]\s\\\'"]+$', '', found_links[0])
                            m3u8_links.append(cleaned_link)  # 使用 append() 将链接添加到列表
                            print(f"获取到m3u8链接: {cleaned_link}")  # 输出第一条符合条件的链接
                            return m3u8_links  # 返回第一个捕获到的链接

                    else:  # Chrome 和 Edge 的日志结构
                        if 'message' in log:
                            log_message = log['message']
                        else:
                            log_message = str(log)

                        if '.m3u8' in log_message:
                            start_idx = log_message.find("url\":\"") + len("url\":\"")
                            end_idx = log_message.find("\"", start_idx)
                            m3u8_url = log_message[start_idx:end_idx]

                            # 只在链接中包含 liveUuid 时，才加入到列表
                            if live_uuid in m3u8_url:
                                print(f"获取到m3u8链接: {m3u8_url}")  # 输出第一条符合条件的链接
                                m3u8_links.append(m3u8_url)
                                return m3u8_links  # 找到后直接返回并退出函数

                except Exception as e:
                    print(f"处理日志时发生错误: {e}")

            # 如果没有找到 m3u8 链接，进行重试
            print(f"第 {attempt + 1} 次尝试未获取到 m3u8 链接，重试中...")
            refresh_page_by_click(browser)

        except Exception as e:
            print(f"获取 m3u8 链接时发生错误: {e}")
    
    return None  # 如果尝试多次仍未找到，返回 None

def refresh_page_by_click(browser):
    # 模拟点击刷新按钮的操作
    try:
        # 例如使用 JavaScript 模拟刷新
        browser.execute_script("location.reload();")
        print("页面已刷新")
    except Exception as e:
        print(f"刷新页面时发生错误: {e}")


def download_m3u8_file(url, filename, headers):
    global browser
    m3u8_content = browser.execute_script("return fetch(arguments[0], { method: 'GET', headers: arguments[1] }).then(response => response.text())", url)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(m3u8_content)

    return filename

def extract_prefix(url):
    pattern = re.compile(r'(https?://[^/]+/live_hp/[0-9a-f-]+)')
    match = pattern.search(url)
    return match.group(1) if match else url

def download_m3u8_with_options(m3u8_file, save_name, prefix):
    root = tk.Tk()
    root.withdraw()
    save_dir = filedialog.askdirectory(title="选择保存视频的目录")

    if not save_dir:
        print("用户取消了选择。视频下载已中止。")
        return
    

    command = [
        get_executable_name(),
        m3u8_file,
        "--ui-language", "zh-CN",
        "--save-name", save_name,
        "--save-dir", save_dir,
        "--base-url", prefix,
    ]

    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {save_dir}")

# 用于批量下载时，复用保存路径
def download_m3u8_with_reused_path(m3u8_file, save_name, prefix, saved_path=None):
    # 如果没有提供已保存的路径，则弹出文件选择框
    if saved_path is None:
        root = tk.Tk()
        root.withdraw()
        saved_path = filedialog.askdirectory(title="选择保存视频的目录")
        
        if not saved_path:
            print("用户取消了选择。视频下载已中止。")
            return

    # 构建下载命令
    command = [
        get_executable_name(),
        m3u8_file,
        "--ui-language", "zh-CN",
        "--save-name", save_name,
        "--save-dir", saved_path,
        "--base-url", prefix,
    ]

    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {saved_path}")
    return saved_path  # 返回已选择的路径，以便后续使用



def auto_download_m3u8_with_options(m3u8_file, save_name, prefix):
    # 获取当前工作目录
    base_dir = os.getcwd()
    
    # 确定 Downloads 文件夹的路径
    downloads_dir = os.path.join(base_dir, 'Downloads')
    
    # 确保 Downloads 文件夹存在
    os.makedirs(downloads_dir, exist_ok=True)
    
    # 构建命令
    command = [
        get_executable_name(),
        m3u8_file,
        "--ui-language", "zh-CN",
        "--save-name", save_name,
        "--save-dir", downloads_dir,  # 设置保存目录为 Downloads 文件夹
        "--base-url", prefix,
    ]
    
    # 执行命令
    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {downloads_dir}")
    
# 单个下载模式
def single_mode():
    try:
        dingtalk_url = input("请输入钉钉直播回放分享链接: ")
        save_mode = validate_input("请选择保存模式（输入1：保存到程序默认路径，输入2：手动选择保存路径模式，直接回车默认选择1）: ", ['1', '2'], default_option='1')
        browser_option = validate_input("请选择您使用的浏览器（输入1：Edge，输入2：Chrome，输入3：Firefox，直接回车默认选择1）: ", ['1', '2', '3'], default_option='1')

        browser_type = {'1': 'edge', '2': 'chrome', '3': 'firefox'}[browser_option]
        browser, cookies_data, m3u8_headers, live_name = get_browser_cookie(dingtalk_url, browser_type)

        while True:
            m3u8_links = fetch_m3u8_links(browser, browser_type, dingtalk_url)

            # print(m3u8_links)

            if m3u8_links:
                for link in m3u8_links:
                    # print(f"当前输入的 m3u8 链接: {link}")
                    m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)
                    prefix = extract_prefix(link)
                    # modified_m3u8_file = replace_prefix(m3u8_file, prefix)
                    save_name = live_name

                    if save_mode == '1':
                        auto_download_m3u8_with_options(m3u8_file, save_name, prefix)
                    elif save_mode == '2':
                        download_m3u8_with_options(m3u8_file, save_name, prefix)
            else:
                print("未找到包含 'm3u8' 字符的请求链接。")

            print('=' * 100)
            dingtalk_url = input("请继续输入钉钉直播分享链接，或输入q退出程序: ")
            if dingtalk_url.lower() == 'q':
                if browser:
                    browser.quit()
                print("程序已退出。")
                break
            cookies_data, m3u8_headers, live_name = repeat_get_browser_cookie(dingtalk_url)

    except KeyboardInterrupt:
        print("\n程序已被用户终止。")
        if browser:
            browser.quit()
        sys.exit(0)

    except Exception as e:
        print(f"发生错误: {e}")
        if browser:
            browser.quit()

# 批量下载模式
def batch_mode():
    try:
        # 获取链接文件并读取内容
        file_path = input("请输入钉钉直播回放链接表格路径（支持CSV或Excel格式，可直接将文件拖放进窗口）: ")
        links_dict = read_links_file(file_path)
        save_mode = validate_input("请选择保存模式（输入1：保存到程序默认路径，输入2：手动选择保存路径模式，直接回车默认选择1）: ", ['1', '2'], default_option='1')
        browser_option = validate_input("请选择您使用的浏览器（输入1：Edge，输入2：Chrome，输入3：Firefox，直接回车默认选择1）: ", ['1', '2', '3'], default_option='1')

        browser_type = {'1': 'edge', '2': 'chrome', '3': 'firefox'}[browser_option]
        total_links = len(links_dict)
        print(f"共提取到 {total_links} 个钉钉直播回放分享链接。")
        # 使用第一个链接获取Cookie和直播信息
        first_link = next(iter(links_dict.values()))
        browser, cookies_data, m3u8_headers, live_name = get_browser_cookie(first_link, browser_type)
        print(f"正在下载第 1 个视频，共 {total_links} 个视频。")
        m3u8_links = fetch_m3u8_links(browser, browser_type, first_link)

        saved_path = None  # 用于保存第一次选择的路径

        if m3u8_links:
            for link in m3u8_links:
                m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)
                prefix = extract_prefix(link)
                save_name = live_name

                if save_mode == '1':
                    saved_path = auto_download_m3u8_with_options(m3u8_file, save_name, prefix)  # 默认下载到 Downloads
                elif save_mode == '2':
                    saved_path = download_m3u8_with_reused_path(m3u8_file, save_name, prefix, saved_path)  # 手动选择路径

        print('=' * 100)
        for idx, dingtalk_url in list(links_dict.items())[1:]:
            print(f"正在下载第 {idx + 1} 个视频，共 {total_links} 个视频。")
            cookies_data, m3u8_headers, live_name = repeat_get_browser_cookie(dingtalk_url)
            m3u8_links = fetch_m3u8_links(browser, browser_type, dingtalk_url)

            if m3u8_links:
                for link in m3u8_links:
                    m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)
                    prefix = extract_prefix(link)
                    save_name = live_name

                    if save_mode == '1':
                        saved_path = auto_download_m3u8_with_options(m3u8_file, save_name, prefix)  # 默认下载到 Downloads
                    elif save_mode == '2':
                        saved_path = download_m3u8_with_reused_path(m3u8_file, save_name, prefix, saved_path)  # 手动选择路径
            print('=' * 100)

        # 继续下载
        while True:
            continue_option = input("是否继续输入钉钉直播回放链接表格路径进行下载？(按Enter继续，按q退出程序): ")
            if continue_option.lower() == 'q':
                print("程序已退出。")
                if browser:
                    browser.quit()
                break
            else:
                file_path = input("请输入新的钉钉直播回放链接表格路径（支持CSV或Excel格式，可直接将文件拖放进窗口）: ")
                new_links_dict = read_links_file(file_path)
                # print(f"共提取到 {len(new_links_dict)} 个新的钉钉直播回放分享链接。")
                saved_path = repeat_process_links(new_links_dict, browser, browser_type, save_mode)

    except KeyboardInterrupt:
        print("\n程序已被用户终止。")
        if browser:
            browser.quit()
        sys.exit(0)

    except Exception as e:
        print(f"发生错误: {e}")
        if browser:
            browser.quit()


# 主程序入口
if __name__ == "__main__":
    print("===============================================")
    print("     欢迎使用钉钉直播回放下载工具 v1.2")
    print("         构建日期：2024年12月8日")
    print("===============================================")

    try:
        download_mode = validate_input("请选择下载模式（输入1：单个视频下载模式，输入2：批量下载模式，直接回车默认选择1）: ", ['1', '2'], default_option='1')
        if download_mode == '1':
            single_mode()
        elif download_mode == '2':
            batch_mode()

    except KeyboardInterrupt:
        print("\n程序已被用户终止。")
        if browser:
            browser.quit()
        sys.exit(0)

    except Exception as e:
        print(f"发生错误: {e}")
        if browser:
            browser.quit()  