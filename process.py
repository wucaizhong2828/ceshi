#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime

# ==============================================
# 配置
# ==============================================
SOURCE_URLS = [
    "https://gitee.com/mytv-android/mymigu/raw/main/migu.m3u",
]

# ==============================================
# 抓取所有源
# ==============================================
def fetch_all_sources():
    all_lines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    for url in SOURCE_URLS:
        try:
            print(f"  正在抓取: {url}")
            resp = requests.get(url, timeout=10, headers=headers)
            resp.encoding = 'utf-8'
            content = resp.text
            lines = content.split('\n')
            all_lines.extend(lines)
            all_lines.append("")
        except Exception as e:
            print(f"  ❌ 抓取失败: {url} - {e}")
    return '\n'.join(all_lines)

# ==============================================
# 主流程（跳过所有解析和过滤，直接保存原始数据）
# ==============================================
def main():
    print(f"[{datetime.now()}] 开始抓取 {len(SOURCE_URLS)} 个直播源...")

    raw = fetch_all_sources()
    print(f"抓取完成，合并后大小: {len(raw)} 字符")
    print(f"前 200 个字符预览: {raw[:200]}")

    # 直接保存原始内容
    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(raw)

    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(raw)

    print(f"[{datetime.now()}] ✅ 完成！已更新 tv.txt 和 tv.m3u")

if __name__ == "__main__":
    main()
