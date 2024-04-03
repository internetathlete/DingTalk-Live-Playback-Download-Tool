import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess
import sys
import re
import tkinter as tk
from tkinter import filedialog

# 将错误信息输出到空文件
null_file = open(os.devnull, 'w')
sys.stderr = null_file

# 全局变量，用于存储浏览器对象
browser = None

# 获取浏览器Cookie的函数，用户手动登录后调用
def get_browser_cookie(url, browser_type='chrome'):
    browser = None  # 初始化浏览器变量
    if browser_type == 'chrome':
        # Chrome WebDriver的选项
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-usb-device-event-log')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-logging')  # 禁用日志记录
        chrome_options.add_argument('--log-level=3')  # 设置日志级别为 WARNING

        # 创建Chrome WebDriver实例
        browser = webdriver.Chrome(options=chrome_options)
    elif browser_type == 'edge':
        # Edge WebDriver的选项
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument('--disable-usb-device-event-log')
        edge_options.add_argument('--ignore-certificate-errors')
        edge_options.add_argument('--disable-logging')  # 禁用 Edge 浏览器的日志输出
        edge_options.add_argument('--log-level=3')  # 设置 Edge 浏览器的日志级别为 ERROR
        edge_options.add_argument('--silent')  # 静默启动，减少输出

        # 设置启动 Edge 浏览器时不显示日志信息
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 创建Edge WebDriver实例
        browser = webdriver.Edge(options=edge_options)
    elif browser_type == 'firefox':
        # Firefox WebDriver的选项
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--disable-usb-device-event-log')
        firefox_options.add_argument('--ignore-certificate-errors')
        firefox_options.add_argument('--disable-logging')  # 禁用 Firefox 浏览器的日志输出
        firefox_options.add_argument('--log-level=3')  # 设置 Firefox 浏览器的日志级别为 ERROR
        firefox_options.add_argument('--silent')  # 静默启动，减少输出

        # 创建 Firefox WebDriver实例
        browser = webdriver.Firefox(options=firefox_options)

    # 打开指定的URL
    browser.get(url)

    # 等待用户手动登录
    input("请在浏览器中登录钉钉账户后，按Enter键继续...")

    # 获取请求头和直播名称
    headers = browser.execute_script("return Object.fromEntries(new Headers(fetch(arguments[0], { method: 'GET' })).entries())", url)
    live_name_element = browser.find_element(By.CLASS_NAME, "RccE3tVv")
    live_name = live_name_element.text
    print(f"直播名称: {live_name}")

    # 获取Cookie
    cookies = browser.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    return browser, cookie_dict, headers, live_name

# 重复获取浏览器Cookie的函数，无需手动确认
def repeat_get_browser_cookie(url):
    global browser
    if browser is None:
        # Edge WebDriver的选项
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument('--disable-usb-device-event-log')
        edge_options.add_argument('--ignore-certificate-errors')
        edge_options.add_argument('--disable-logging')  # 禁用 Edge 浏览器的日志输出
        edge_options.add_argument('--log-level=3')  # 设置 Edge 浏览器的日志级别为 ERROR
        edge_options.add_argument('--silent')  # 静默启动，减少输出

        # 设置启动 Edge 浏览器时不显示日志信息
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 创建Edge WebDriver实例
        browser = webdriver.Edge(options=edge_options)

    # 打开指定的URL
    browser.get(url)

    #  等待页面加载过程中出现包含 m3u8 链接的网络请求
    m3u8_request = WebDriverWait(browser, 30).until(lambda x: any("m3u8" in entry['name'] for entry in browser.execute_script("return window.performance.getEntriesByType('resource')")))

    # 获取请求头和直播名称
    headers = browser.execute_script("return Object.fromEntries(new Headers(fetch(arguments[0], { method: 'GET' })).entries())", url)
    live_name_element = browser.find_element(By.CLASS_NAME, "RccE3tVv")
    live_name = live_name_element.text
    print(f"直播名称: {live_name}")

    # 获取Cookie
    cookies = browser.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    return cookie_dict, headers, live_name

# 下载m3u8文件的函数
def download_m3u8_file(url, filename, headers):
    global browser
    # 执行JavaScript来获取m3u8内容
    m3u8_content = browser.execute_script("return fetch(arguments[0], { method: 'GET', headers: arguments[1] }).then(response => response.text())", url)

    # 将m3u8内容保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(m3u8_content)

    return filename

# 从URL中提取前缀的函数
def extract_prefix(url):
    # 定义正则表达式模式
    pattern = re.compile(r'(https?://[^/]+/live_hp/[0-9a-f-]+)')

    # 在输入链接中查找匹配项
    match = pattern.search(url)

    # 返回提取的内容，如果有匹配项的话
    if match:
        return match.group(1)
    else:
        return url

# 替换m3u8文件中的前缀的函数
def replace_prefix(m3u8_file, prefix):
    updated_lines = []
    with open(m3u8_file, 'r') as file:
        for line in file:
            index = line.find('/')
            if index != -1:
                updated_line = prefix + line[index:]
            else:
                updated_line = line
            updated_lines.append(updated_line)

    # 新文件的路径
    output_file = os.path.join(os.path.dirname(m3u8_file), 'modified_' + os.path.basename(m3u8_file))
    with open(output_file, 'w') as file:
        file.writelines(updated_lines)

    # print(f"修改后的m3u8文件已保存为: {output_file}")

    return output_file

# 使用外部工具下载m3u8文件的函数（手动选择路径模式）
def download_m3u8_with_options(m3u8_file, save_name):
    # 允许用户选择目录
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 请求用户选择目录
    work_dir = filedialog.askdirectory(title="选择保存视频的目录")

    # 如果用户取消选择，返回而不执行命令
    if not work_dir:
        print("用户取消了选择。视频下载已中止。")
        return

    # 构造带有指定 workDir 的命令
    command = [
        ".\\N_m3u8DL-CLI_v3.0.2.exe",
        m3u8_file,
        "--enableDelAfterDone",
        "--saveName",
        save_name,
        "--workDir",
        work_dir
    ]

    # print(" ".join(command))

    # 使用 subprocess 运行命令
    subprocess.run(command)

    print("视频下载成功完成。")

# 使用外部工具下载m3u8文件的函数（自动下载模式）
def auto_download_m3u8_with_options(m3u8_file, save_name):
    # 构造命令
    command = [
        ".\\N_m3u8DL-CLI_v3.0.2.exe",
        m3u8_file,
        "--enableDelAfterDone",
        "--saveName",
        save_name,
    ]

    # print(" ".join(command))

    # 使用 subprocess 运行命令
    subprocess.run(command)

    print("视频下载成功完成。")

# 主程序
if __name__ == "__main__":
    print("===============================================")
    print("     欢迎使用钉钉直播回放下载工具 v1.0")
    print("         构建日期：2024年04月03日")
    print("===============================================")
    print("")

    try:
        # 从用户输入中获取钉钉直播链接
        dingtalk_url = input("请输入钉钉直播回放分享链接: ")
        # 询问用户选择下载模式
        download_mode = input("请选择下载模式（输入1：自动下载模式，输入2：手动选择保存路径模式）: ")
        if download_mode not in ['1', '2']:
            print("无效的下载模式选择。")
            sys.exit(1)
        # 询问用户选择要使用的浏览器类型
        browser_option = input("请选择您使用的浏览器（输入1：Chrome，输入2：Edge，输入3：Firefox）: ")
        if browser_option == '1':
            browser_type = 'chrome'
        elif browser_option == '2':
            browser_type = 'edge'
        elif browser_option == '3':
            browser_type = 'firefox'
        else:
            print("无效的浏览器选择。请重新运行程序并选择有效的选项。")
            sys.exit(1)

        browser, cookies_data, m3u8_headers, live_name = get_browser_cookie(dingtalk_url, browser_type)

        while True:
            # 执行JavaScript以查找页面上的m3u8链接
            m3u8_links = browser.execute_script("""
                var m3u8Links = [];
                var requests = performance.getEntriesByType('resource');
                
                for (var request of requests) {
                    if (request.name.includes("m3u8")) {
                        m3u8Links.push(request.name);
                    }
                }

                return m3u8Links;
            """)

            # 如果找到m3u8链接，则进行处理
            if m3u8_links:
                # print("包含 'm3u8' 字符的请求链接:")
                for link in m3u8_links:
                    # print(link)

                    # 下载m3u8文件并获取其路径
                    m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)

                    # 提取前缀并替换m3u8文件中的前缀
                    prefix = extract_prefix(link)
                    modified_m3u8_file = replace_prefix(m3u8_file, prefix)

                    # 使用直播名称作为保存文件名
                    save_name = live_name

                    # 根据用户选择的模式进行下载
                    if download_mode == '1':
                        auto_download_m3u8_with_options(modified_m3u8_file, save_name)
                    elif download_mode == '2':
                        download_m3u8_with_options(modified_m3u8_file, save_name)

            else:
                print("未找到包含 'm3u8' 字符的请求链接。")

            # 等待用户输入新的直播链接
            print('=' * 50)
            dingtalk_url = input("请继续输入钉钉直播链接，或输入q退出程序: ")
            if dingtalk_url.lower() == 'q':
                browser.quit()
                print("程序已退出。")
                break
            cookies_data, m3u8_headers, live_name = repeat_get_browser_cookie(dingtalk_url)

    except Exception as e:
        print(f"发生错误: {e}")

