import datetime
import json
import threading
import time
import requests

from mitmproxy.http import HTTPFlow
from mitmproxy import ctx

import global_config


class Hook:
    def __init__(self):
        self.score_fetch = False
        self.zipped_scores = []


    def exit_later(self):
        print("数据已成功上传。程序将在3秒后执行自动清理动作。")
        time.sleep(3)
        ctx.master.shutdown()


    def parse_scores(self):
        """
        将嵌套列表转换为键值对的 JSON 格式
        """
        keys = [
            "song_no", "level", "high_score", "best_score_rank",
            "good_cnt", "ok_cnt", "ng_cnt", "pound_cnt", "combo_cnt",
            "stage_cnt", "clear_cnt", "full_combo_cnt",
            "dondaful_combo_cnt", "update_datetime"
        ]
        self.parsed_scores = [
            dict(zip(keys, score)) for score in self.zipped_scores
        ]


    def upload_scores(self):
        """
        上传成绩到目标服务器
        """
        upload_url = "http://47.243.115.221:573/api/score/upload"  # 服务器地址
        headers = {"Content-Type": "application/json",
                   "Authorization": global_config.user_token}        # 设置请求头
        try:
            print(f'当前用户token为:{global_config.user_token}')
            response = requests.post(upload_url, json=self.parsed_scores, headers=headers)
            if response.status_code == 200:
                print("成绩数据已成功上传到远程服务器！")
            else:
                print(f"上传失败，服务器返回状态码: {response.status_code}")

            threading.Thread(target=self.exit_later).start()
            return
        except Exception as e:
            print(f"上传失败，发生异常: {e}")
            threading.Thread(target=self.exit_later).start()
            return


    def response(self, flow: HTTPFlow):
        # 第一部分：拦截特定成绩上传请求
        if ("https://wl-taiko.wahlap.net/api/user/profile/songscore" in flow.request.url
                and flow.request.headers.get('Authorization')):
            resp_dict = flow.response.json()
            if resp_dict.get("status") != 0:
                print(f"错误: {resp_dict.get('message')}")
                return
            zipped_scores = []
            # 保存原始嵌套列表
            score_items = resp_dict.get("data", {}).get("scoreInfo", [])
            for score_item in score_items:
                zipped_scores.append((
                    score_item['song_no'],
                    score_item['level'],
                    score_item['high_score'],
                    score_item['best_score_rank'],
                    score_item['good_cnt'],
                    score_item['ok_cnt'],
                    score_item['ng_cnt'],
                    score_item['pound_cnt'],
                    score_item['combo_cnt'],
                    score_item['stage_cnt'],
                    score_item['clear_cnt'],
                    score_item['full_combo_cnt'],
                    score_item['dondaful_combo_cnt'],
                    score_item['update_datetime'],
                ))
            self.score_fetch = True
            self.zipped_scores = zipped_scores
             # 转换为键值对格式
            self.parse_scores()

            with open("zipped_scores.json", "w", encoding="utf-8") as file:
                json.dump(self.parsed_scores, file, ensure_ascii=False, indent=4)

            print("成绩数据 已获取。准备上传至 叽奇...")
            threading.Thread(target=self.upload_scores).start()  # 启动上传线程
        



addons = [Hook()]
