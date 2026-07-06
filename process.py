#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ===== 配置 =====
SOURCE_URL = "https://0701.tv1288.xyz"
SPAM_KEYWORDS = ["加群", "TG", "t.me", "关注", "广告", "备用", "防失联", "微信", "QQ", "最新"]

# ===== 抓取原始内容 =====
def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.encoding = 'utf-8'
    return resp.text

# ===== 解析并过滤 =====
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

# ===== 生成 M3U 格式 =====
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

# ===== 主流程 =====
def main():
    print(f"[{datetime.now()}] 开始抓取...")
    raw = fetch_source()
    print(f"抓取完成，原始大小: {len(raw)} 字符")
    
    cleaned = parse_and_filter(raw)
    print(f"过滤完成，清洗后大小: {len(cleaned)} 字符")
    
    # 保存 TXT 格式（覆盖你原来的 tv.txt）
    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    # 保存 M3U 格式（新增）
    m3u_content = generate_m3u(cleaned)
    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"[{datetime.now()}] 完成！已更新 tv.txt 和 tv.m3u")

if __name__ == "__main__":
    main()
