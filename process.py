#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ==============================================
# 配置
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
# M3U → TXT 转换 + 过滤
# ==============================================
def convert_m3u_to_txt(text):
    lines = text.split('\n')
    txt_lines = []
    i = 0
    total = 0
    filtered = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 处理 #EXTINF 行
        if line.startswith('#EXTINF'):
            # 提取频道名（最后一个逗号后面的内容）
            title_match = re.search(r',([^,]+)$', line)
            title = title_match.group(1).strip() if title_match else ""
            
            # 检查是否包含过滤关键词
            is_spam = any(kw in title for kw in SPAM_KEYWORDS)
            
            # 下一行应该是 URL
            i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                # 如果是 http/https 开头的 URL
                if re.match(r'^https?://', url_line):
                    total += 1
                    if not is_spam:
                        # 输出 TXT 格式：频道名,地址
                        txt_lines.append(f"{title},{url_line}")
                    else:
                        filtered += 1
                        print(f"  🚫 已过滤: {title}")
            i += 1
            continue
        
        # 跳过其他行（如 #EXTM3U, # 注释等）
        i += 1
    
    print(f"  共 {total} 个频道，过滤了 {filtered} 个，保留 {total - filtered} 个")
    return '\n'.join(txt_lines)


# ==============================================
# 主流程
# ==============================================
def main():
    print(f"[{datetime.now()}] 开始抓取 {len(SOURCE_URLS)} 个直播源...")

    raw = fetch_all_sources()
    print(f"抓取完成，合并后大小: {len(raw)} 字符")

    # 转换为 TXT 格式
    txt_content = convert_m3u_to_txt(raw)
    print(f"转换完成，TXT 大小: {len(txt_content)} 字符")

    # 保存 TXT 格式（频道名,地址）
    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(txt_content)

    # 保存 M3U 格式（保留原始结构，供播放器使用）
    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(raw)

    print(f"[{datetime.now()}] ✅ 完成！已更新 tv.txt 和 tv.m3u")

if __name__ == "__main__":
    main()
