#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ==============================================
# 配置：在这里添加你的直播源地址，一行一个
# ==============================================
SOURCE_URLS = [
    "https://gitee.com/mytv-android/mymigu/raw/main/migu.m3u",
]

# 过滤关键词：频道名包含这些词会被删除
SPAM_KEYWORDS = ["加群", "TG", "t.me", "关注", "广告", "备用", "防失联", "微信", "QQ", "最新"]

# ==============================================
# 抓取所有源
# ==============================================
def fetch_all_sources():
    all_lines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    for url in SOURCE_URLS:
        try:
            print(f"  正在抓取: {url}")
            resp = requests.get(url, timeout=10, headers=headers)
            resp.encoding = 'utf-8'
            content = resp.text

            if '<!DOCTYPE html>' in content or '<html' in content.lower():
                print(f"  ⚠️ 警告: {url} 返回了 HTML 页面，跳过")
                continue

            lines = content.split('\n')
            all_lines.extend(lines)
            all_lines.append("")
        except Exception as e:
            print(f"  ❌ 抓取失败: {url} - {e}")

    return '\n'.join(all_lines)


# ==============================================
# 解析并过滤频道（支持 TXT 和 M3U 两种格式）
# ==============================================
def parse_and_filter(text):
    lines = text.split('\n')
    result = []
    current_group = "默认频道"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ===== 处理 TXT 格式 =====
        if ',#genre#' in line:
            current_group = line.split(',')[0].strip()
            result.append(line)
            continue

        if ',' in line and not line.startswith('#'):
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if not any(kw in title for kw in SPAM_KEYWORDS):
                    result.append(line)
            continue

        # ===== 处理 M3U 格式 =====
        # 保留所有 #EXTINF 行
        if line.startswith('#EXTINF'):
            result.append(line)
            continue

        # 保留 URL 行（非 # 开头，且看起来像 URL）
        if not line.startswith('#') and ('http://' in line or 'https://' in line):
            result.append(line)
            continue

        # 保留其他 # 开头的行（如 #EXTM3U）
        if line.startswith('#'):
            result.append(line)
            continue

    return '\n'.join(result)


# ==============================================
# 生成 M3U 格式（保留原始 M3U 结构）
# ==============================================
def generate_m3u(cleaned_text):
    lines = cleaned_text.split('\n')
    m3u_lines = ["#EXTM3U"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 保留所有 #EXTINF 行
        if line.startswith('#EXTINF'):
            m3u_lines.append(line)
            continue

        # 保留 URL 行
        if not line.startswith('#') and ('http://' in line or 'https://' in line):
            m3u_lines.append(line)
            continue

        # 保留其他 # 开头的重要行
        if line.startswith('#') and not line.startswith('#EXTM3U'):
            m3u_lines.append(line)
            continue

    return '\n'.join(m3u_lines)


# ==============================================
# 主流程
# ==============================================
def main():
    print(f"[{datetime.now()}] 开始抓取 {len(SOURCE_URLS)} 个直播源...")

    raw = fetch_all_sources()
    print(f"抓取完成，合并后大小: {len(raw)} 字符")

    cleaned = parse_and_filter(raw)
    print(f"过滤完成，清洗后大小: {len(cleaned)} 字符")

    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned)

    m3u_content = generate_m3u(cleaned)
    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"[{datetime.now()}] ✅ 完成！已更新 tv.txt 和 tv.m3u")


if __name__ == "__main__":
    main()
