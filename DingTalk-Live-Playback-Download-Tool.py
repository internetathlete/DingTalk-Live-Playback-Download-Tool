import os
import warnings
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import subprocess
import sys
import re
import tkinter as tk
from tkinter import filedialog
import logging

logging.disable(logging.CRITICAL)  # 禁用所有日志

# 全局变量，用于存储浏览器对象
browser = None

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
            edge_options.add_argument('--log-level=3')
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            browser = webdriver.Edge(options=edge_options)
        elif browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--disable-usb-device-event-log')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')

            browser = webdriver.Chrome(options=chrome_options)
        elif browser_type == 'firefox':
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--disable-usb-device-event-log')
            firefox_options.add_argument('--ignore-certificate-errors')
            firefox_options.add_argument('--disable-logging')
            firefox_options.add_argument('--log-level=3')

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

        m3u8_request = WebDriverWait(browser, 30).until(lambda x: any("m3u8" in entry['name'] for entry in browser.execute_script("return window.performance.getEntriesByType('resource')")))

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

def replace_prefix(m3u8_file, prefix):
    updated_lines = []
    with open(m3u8_file, 'r') as file:
        for line in file:
            index = line.find('/')
            updated_line = prefix + line[index:] if index != -1 else line
            updated_lines.append(updated_line)

    output_file = os.path.join(os.path.dirname(m3u8_file), 'modified_' + os.path.basename(m3u8_file))
    with open(output_file, 'w') as file:
        file.writelines(updated_lines)

    return output_file

def download_m3u8_with_options(m3u8_file, save_name):
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
        "--save-dir", save_dir
    ]

    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {save_dir}")

def auto_download_m3u8_with_options(m3u8_file, save_name):
    command = [
        get_executable_name(),
        m3u8_file,
        "--ui-language", "zh-CN",
        "--save-name", save_name,
    ]

    subprocess.run(command)
    print(f"视频下载成功完成。文件保存路径: {os.getcwd()}")

# 支持默认选项的输入验证函数
def validate_input(prompt, valid_options, default_option=None):
    while True:
        choice = input(prompt)
        if choice == '' and default_option is not None:
            return default_option
        if choice in valid_options:
            return choice
        print("无效的选择，请重新输入。")

if __name__ == "__main__":
    print("===============================================")
    print("     欢迎使用钉钉直播回放下载工具 v1.1")
    print("         构建日期：2024年10月01日")
    print("===============================================")

    try:
        dingtalk_url = input("请输入钉钉直播回放分享链接: ")
        download_mode = validate_input("请选择下载模式（输入1：自动下载模式，输入2：手动选择保存路径模式，默认选择1）: ", ['1', '2'], default_option='1')
        browser_option = validate_input("请选择您使用的浏览器（输入1：Edge，输入2：Chrome，输入3：Firefox，默认选择1）: ", ['1', '2', '3'], default_option='1')

        browser_type = {'1': 'edge', '2': 'chrome', '3': 'firefox'}[browser_option]
        browser, cookies_data, m3u8_headers, live_name = get_browser_cookie(dingtalk_url, browser_type)

        while True:
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

            if m3u8_links:
                for link in m3u8_links:
                    m3u8_file = download_m3u8_file(link, 'output.m3u8', m3u8_headers)
                    prefix = extract_prefix(link)
                    modified_m3u8_file = replace_prefix(m3u8_file, prefix)
                    save_name = live_name

                    if download_mode == '1':
                        auto_download_m3u8_with_options(modified_m3u8_file, save_name)
                    elif download_mode == '2':
                        download_m3u8_with_options(modified_m3u8_file, save_name)
            else:
                print("未找到包含 'm3u8' 字符的请求链接。")

            print('=' * 50)
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
