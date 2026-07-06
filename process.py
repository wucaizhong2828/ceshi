#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ============================================================
#  👇 只需要在这里添加你的网址，一行一个
# ============================================================
SOURCE_URLS = [
    "https://0701.tv1288.xyz",          
    # "https://gongdian.top/tv/iptv", 
    # "https://gitee.com/mytv-android/mymigu/raw/main/migu.m3u",    
]

SPAM_KEYWORDS = ["加群", "TG", "t.me", "关注", "广告", "备用", "防失联", "微信", "QQ", "最新"]
# ============================================================

def fetch_all_sources():
    all_lines = []
    for url in SOURCE_URLS:
        try:
            print(f"  正在抓取: {url}")
            resp = requests.get(url, timeout=10)
            resp.encoding = 'utf-8'
            lines = resp.text.split('\n')
            all_lines.extend(lines)
            all_lines.append("")
        except Exception as e:
            print(f"  ❌ 抓取失败: {url} - {e}")
    return '\n'.join(all_lines)

def parse_and_filter(text):
    lines = text.split('\n')
    result = []
    current_group = "默认频道"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
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
        else:
            result.append(line)
    
    return '\n'.join(result)

def generate_m3u(cleaned_text):
    lines = cleaned_text.split('\n')
    m3u_lines = ["#EXTM3U"]
    current_group = "默认频道"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if ',#genre#' in line:
            current_group = line.split(',')[0].strip()
            continue
        
        if ',' in line and not line.startswith('#'):
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                m3u_lines.append(f'#EXTINF:-1 group-title="{current_group}",{title}')
                m3u_lines.append(url)
    
    return '\n'.join(m3u_lines)

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
