import os
import warnings
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import sys
import re
import tkinter as tk
from tkinter import filedialog
import logging
import time
import json


logging.disable(logging.CRITICAL)  # 禁用所有日志

# 处理用户输入路径中的多余引号和空格
def clean_file_path(input_path):
    return input_path.strip().replace('"', '').replace("'", "")

# 检查文件格式并读取包含钉钉直播链接的CSV或Excel文件
def read_links_file(file_path):
    try:
        file_path = clean_file_path(file_path)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):  # Excel 文件
            df = pd.read_excel(file_path)
        else:
            raise ValueError("文件格式不支持，请使用CSV或Excel文件。")

        # 查找所有以 "https://n.dingtalk.com" 开头的链接
        links = {}
        for col in df.columns:
            filtered_links = df[col].dropna().astype(str).apply(lambda x: x if x.startswith("https://n.dingtalk.com") else None)
            for i, link in filtered_links.dropna().items():
                links[i] = link

        if not links:
            raise ValueError("未找到有效的钉钉直播链接。")

        return links
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        sys.exit(1)


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

# 获取浏览器Cookie的函数
def get_browser_cookie(url, browser_type='edge'):
    global browser
    try:
        if browser_type == 'edge':
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--disable-usb-device-event-log')
            edge_options.add_argument('--ignore-certificate-errors')
            edge_options.add_argument('--disable-logging')
            # edge_options.add_argument('--disable-cache')
            # edge_options.add_argument('--disk-cache-size=0')
            edge_options.add_argument('--disable_ssl_verification')
            edge_options.add_argument('--log-level=3')
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # 启用浏览器日志，获取网络请求
            edge_options.set_capability("ms:loggingPrefs", {
                'browser': 'ALL',       # 启用浏览器日志
                'performance': 'ALL'    # 启用性能日志
            })
            browser = webdriver.Edge(options=edge_options)
        elif browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--disable-usb-device-event-log')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-logging')
            # chrome_options.add_argument('--disable-cache')
            # chrome_options.add_argument('--disk-cache-size=0')
            chrome_options.add_argument('--log-level=3')
            # 启用浏览器日志，获取网络请求
            chrome_options.set_capability("goog:loggingPrefs", {
                'browser': 'ALL',       # 启用浏览器日志
                'performance': 'ALL'    # 启用性能日志
            })

            browser = webdriver.Chrome(options=chrome_options)
        elif browser_type == 'firefox':
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--disable-usb-device-event-log')
            firefox_options.add_argument('--ignore-certificate-errors')
            firefox_options.add_argument('--disable-logging')
            # firefox_options.add_argument('--disable-cache')
            # firefox_options.add_argument('--disk-cache-size=0')
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
        

        # m3u8_request = WebDriverWait(browser, 30).until(lambda x: any("m3u8" in entry['name'] for entry in browser.execute_script("return window.performance.getEntriesByType('resource')")))
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

# def refresh_page_by_click(browser):
#     try:
#         browser.refresh()
#         # 使用 XPath 定位刷新按钮并模拟点击
#         refresh_button = WebDriverWait(browser, 2).until(
#             EC.element_to_be_clickable((By.XPATH, '//*[@id="J_controls_bar"]/div[2]/button[2]'))
#         )
#         refresh_button.click()
#         print("刷新按钮已点击，页面正在刷新...")
#     except Exception as e:
#         print(f"模拟点击刷新按钮时发生错误: {e}")

# Chrome 和 Edge 逻辑
# def fetch_m3u8_links(browser):
#     m3u8_links = []  # 初始化为空列表
#     for attempt in range(5):
#         try:
#             logs = browser.get_log("performance")

#             # 遍历日志，提取第一个包含 m3u8 的链接
#             for log in logs:
#                 try:
#                     # 使用正则表达式从日志中提取 m3u8 链接
#                     pattern = r'https://[^"]+\.m3u8\?[^"]+'
#                     found_links = re.findall(pattern, log['message'])

#                     if found_links:
#                         # 清理末尾的 "]" 和 "\" 等不必要字符
#                         cleaned_link = re.sub(r'[\]\s\\]+$', '', found_links[0])
#                         m3u8_links.append(cleaned_link)  # 使用 append() 将链接添加到列表
#                         print(f"捕获到第一个 m3u8 链接: {cleaned_link}")
#                         return m3u8_links  # 返回第一个捕获到的链接

#                 except Exception as e:
#                     print(f"处理日志时发生错误: {e}")

#             # 如果没有找到 m3u8 链接，进行重试
#             print(f"第 {attempt + 1} 次尝试未获取到 m3u8 链接，重试中...")
#             refresh_page_by_click(browser)

#         except Exception as e:
#             print(f"获取 m3u8 链接时发生错误: {e}")
#     return None  # 如果尝试多次仍未找到，返回 None


# Firefox逻辑
# def fetch_m3u8_links(browser):
#     m3u8_links = []  # 初始化为空列表
#     for attempt in range(5):
#         try:
#             # 获取浏览器的性能日志
#             logs = browser.execute_script("""
#                 var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
#                 var network = performance.getEntries() || {};
#                 return network;
#             """)

#             # 定义日志输出路径
#             log_file_path = "performance_logs.txt"

#             # 将日志写入到文件
#             with open(log_file_path, "w", encoding="utf-8") as log_file:
#                 # 使用 JSON 格式化输出日志信息
#                 json.dump(logs, log_file, indent=4, ensure_ascii=False)

#             # 遍历日志，提取第一个包含 m3u8 的链接
#             for log in logs:
#                 try:
#                     # 将 log 转为字符串格式
#                     log_str = str(log)

#                     # 修改正则表达式，只匹配 m3u8 链接的部分
#                     pattern = r'https://[^"]+\.m3u8\?[^\'"]+'  # 支持?后有多种字符的情况
#                     found_links = re.findall(pattern, log_str)

#                     if found_links:
#                         # 获取第一个匹配的链接
#                         m3u8_link = found_links[0]
#                         m3u8_links.append(m3u8_link)  # 使用 append() 将链接添加到列表
#                         print(f"捕获到 m3u8 链接: {m3u8_link}")
#                         return m3u8_links  # 返回第一个捕获到的链接
#                 except Exception as e:
#                     print(f"处理日志时发生错误: {e}")

#             # 如果没有找到 m3u8 链接，进行重试
#             print(f"第 {attempt + 1} 次尝试未获取到 m3u8 链接，重试中...")

#             # 你可以在这里加入刷新页面的操作
#             refresh_page_by_click(browser)

#         except Exception as e:
#             print(f"获取 m3u8 链接时发生错误: {e}")
#     return None  # 如果尝试多次仍未找到，返回 None




def fetch_m3u8_links(browser, browser_type):
    m3u8_links = []  # 初始化为空列表
    for attempt in range(5):
        try:
            # 根据浏览器类型获取日志
            if browser_type == 'chrome' or browser_type == 'edge':  # Chrome 和 Edge 使用 get_log
                logs = browser.get_log("performance")
            elif browser_type == 'firefox':  # Firefox 使用 execute_script
                logs = browser.execute_script("""
                    var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                    var network = performance.getEntries() || {};
                    return network;
                """)

            # 遍历日志，提取第一个包含 m3u8 的链接
            for log in logs:
                try:
                    # 根据浏览器的不同处理日志
                    if 'message' in log:  # Chrome 和 Edge 的日志结构
                        log_message = log['message']
                    else:  # Firefox 的日志结构是直接在 log 对象中
                        log_message = str(log)

                    # 使用正则表达式从日志中提取 m3u8 链接
                    pattern = r'https://[^,\'"]+\.m3u8\?[^\'"]+'
                    found_links = re.findall(pattern, log_message)


                    if found_links:
                        # 清理末尾的 "]" 和 "\" 等不必要字符（适用于 Chrome 和 Edge）
                        cleaned_link = re.sub(r'[\]\s\\\'"]+$', '', found_links[0])
                        m3u8_links.append(cleaned_link)  # 使用 append() 将链接添加到列表
                        # print(f"捕获到第一个 m3u8 链接: {cleaned_link}")
                        return m3u8_links  # 返回第一个捕获到的链接

                except Exception as e:
                    print(f"处理日志时发生错误: {e}")

            # 如果没有找到 m3u8 链接，进行重试
            print(f"第 {attempt + 1} 次尝试未获取到 m3u8 链接，重试中...")
            refresh_page_by_click(browser)

        except Exception as e:
            print(f"获取 m3u8 铯链接时发生错误: {e}")
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

# def replace_prefix(m3u8_file, prefix):
#     updated_lines = []
#     with open(m3u8_file, 'r') as file:
#         for line in file:
#             index = line.find('/')
#             updated_line = prefix + line[index:] if index != -1 else line
#             updated_lines.append(updated_line)

#     output_file = os.path.join(os.path.dirname(m3u8_file), 'modified_' + os.path.basename(m3u8_file))
#     with open(output_file, 'w') as file:
#         file.writelines(updated_lines)

#     return output_file

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

def auto_download_m3u8_with_options(m3u8_file, save_name, prefix):
    # 获取程序所在的目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    downloads_dir = os.path.join(base_dir, 'Downloads')
    
    # 确保 Downloads 目录存在
    os.makedirs(downloads_dir, exist_ok=True)

    command = [
        get_executable_name(),
        m3u8_file,
        "--ui-language", "zh-CN",
        "--save-name", save_name,
        "--save-dir", downloads_dir,
        "--base-url", prefix,
    ]

    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {downloads_dir}")

# 主程序入口
if __name__ == "__main__":
    print("===============================================")
    print("     欢迎使用钉钉直播回放下载工具 v1.2")
    print("         构建日期：2024年11月10日")
    print("===============================================")

    try:
        dingtalk_url = input("请输入钉钉直播回放分享链接: ")
        save_mode = validate_input("请选择保存模式（输入1：保存到程序默认路径，输入2：手动选择保存路径模式，直接回车默认选择1）: ", ['1', '2'], default_option='1')
        browser_option = validate_input("请选择您使用的浏览器（输入1：Edge，输入2：Chrome，输入3：Firefox，直接回车默认选择1）: ", ['1', '2', '3'], default_option='1')

        browser_type = {'1': 'edge', '2': 'chrome', '3': 'firefox'}[browser_option]
        browser, cookies_data, m3u8_headers, live_name = get_browser_cookie(dingtalk_url, browser_type)

        while True:
            m3u8_links = fetch_m3u8_links(browser, browser_type)

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
