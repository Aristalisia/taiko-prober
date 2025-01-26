import json
import os
import subprocess
import sys
import time
import global_config
from mitmproxy.tools.main import mitmdump
import requests

def get_resource_path(raw_file_name):
    """获取资源文件的路径，适配开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # 如果程序在打包后的环境中运行，获取与程序同目录下的文件路径
        return os.path.join(os.path.dirname(sys.argv[0]), raw_file_name)
    else:
        # 如果程序在开发环境中运行，获取当前脚本所在目录的文件路径
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), raw_file_name)


def post_account_data(account_data):
    """向服务器发送 POST 请求验证账号"""
    url = "http://47.243.115.221:573/api/donder/login"  # 替换为实际的 URL
    try:
        response = requests.post(url, json=account_data)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success") == True:
                global_config.user_token = response_data.get("token")
                print("账号验证成功，继续执行程序。")
                return True
            else:
                print(f"服务器返回失败: {response_data.get('message', '未知错误')}")
        else:
            print(f"HTTP 请求失败，状态码: {response.status_code}")
    except requests.RequestException as e:
        print(f"请求失败: {e}")
    return False

if __name__ == '__main__':
    # 获取 account.txt 文件的路径
    account_file_path = get_resource_path('account.txt')

    # 检查 account.txt 文件是否存在
    if os.path.exists(account_file_path):
        print(f"找到 account.txt 文件，路径为: {account_file_path}")
        # 打开并读取文件
        with open(account_file_path, 'r', encoding='utf-8') as file:
            try:
                account_data = json.load(file)
                # 检查文件内容是否包含 Account 和 Password 字段
                if "donderUsername" in account_data and "donderPassword" in account_data:
                    print("发现 account.txt 文件，正在验证账号...")
                    print(account_data)
                    if not post_account_data(account_data):
                        print("账号验证失败，程序即将退出。")
                        time.sleep(5)
                        exit(1)
                else:
                    print("account.txt 格式错误，缺少 donderUsername 或 donderPassword 字段。")
                    time.sleep(5)
                    exit(1)
            except json.JSONDecodeError:
                print("account.txt 文件格式无效，无法解析为 JSON。")
                time.sleep(5)
                exit(1)
    else:
        print(f"未找到 account.txt 文件，将在当前目录创建新的 account.txt 文件...")
        default_data = {
            "donderUsername": "",
            "donderPassword": ""
        }
        # 创建并写入文件
        with open(account_file_path, 'w', encoding='utf-8') as file:
            json.dump(default_data, file, ensure_ascii=False, indent=4)
        print(f"新文件已创建，路径为: {account_file_path}")
        print('请在account.txt内填写您的账号密码后尝试再次运行程序')
        time.sleep(5)
        exit(0)

    # 在独立进程中启动mitmproxy
    print("正在初始化本地代理与证书")
    pre_config = subprocess.Popen([get_resource_path('pre_config.bat')], shell=True)
    pre_config.wait()
    if pre_config.returncode != 0:
        print("初始化失败，请检查错误信息。")
        time.sleep(5)
        exit(1)

    print("正在监听成绩数据。请使用电脑端微信，打开鼓众广场小程序，点击我的成绩，等待程序自动获取成绩数据。")
    mitmdump(['-s', get_resource_path('mitm_hook.py'), '-q'])

    print("正在清理本地代理配置")
    post_clean = subprocess.Popen([get_resource_path('post_clean.bat')], shell=True)
    post_clean.wait()
