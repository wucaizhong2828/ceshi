#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ==============================================
# 配置
# ==============================================
SOURCE_URLS = [
    "https://raw.giteeusercontent.com/yunkaixx/tv/raw/master/live.txt",
]

# 过滤关键词
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
# 从 #EXTINF 行提取频道名
# ==============================================
def extract_title_from_extinf(line):
    """
    从 #EXTINF 行中提取频道名
    支持格式：
    1. #EXTINF:-1 tvg-id="CCTV1" group-title="央视",CCTV1综合
    2. #EXTINF:-1,CCTV1综合
    3. #EXTINF:-1 tvg-id="CCTV1",CCTV1综合
    """
    # 方法1：查找最后一个逗号后面的内容（最可靠）
    if ',' in line:
        # 找到最后一个逗号的位置
        last_comma = line.rfind(',')
        title = line[last_comma + 1:].strip()
        if title:
            return title
    
    # 方法2：尝试从 tvg-name 或 tvg-id 提取（备用）
    name_match = re.search(r'tvg-name="([^"]+)"', line)
    if name_match:
        return name_match.group(1)
    
    id_match = re.search(r'tvg-id="([^"]+)"', line)
    if id_match:
        return id_match.group(1)
    
    return "未知频道"


# ==============================================
# M3U → TXT 转换 + 过滤
# ==============================================
def convert_m3u_to_txt(text):
    lines = text.split('\n')
    txt_lines = []
    i = 0
    total = 0
    filtered = 0
    
    # 调试：打印前 10 行
    print("  📋 原始数据前 10 行预览：")
    for idx, line in enumerate(lines[:10]):
        if line.strip():
            print(f"    {idx+1}: {line[:100]}...")
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 处理 #EXTINF 行
        if line.startswith('#EXTINF'):
            # 提取频道名
            title = extract_title_from_extinf(line)
            
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
                        txt_lines.append(f"{title},{url_line}")
                        if total <= 3:  # 只打印前3个成功解析的频道
                            print(f"  ✅ 解析成功: {title} -> {url_line[:50]}...")
                    else:
                        filtered += 1
                        print(f"  🚫 已过滤: {title}")
            i += 1
            continue
        
        # 跳过其他行
        i += 1
    
    print(f"  📊 共 {total} 个频道，过滤了 {filtered} 个，保留 {total - filtered} 个")
    return '\n'.join(txt_lines)


# ==============================================
# 主流程
# ==============================================
def main():
    print(f"[{datetime.now()}] 开始抓取 {len(SOURCE_URLS)} 个直播源...")

    raw = fetch_all_sources()
    print(f"抓取完成，合并后大小: {len(raw)} 字符")

    txt_content = convert_m3u_to_txt(raw)
    print(f"转换完成，TXT 大小: {len(txt_content)} 字符")

    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(txt_content)

    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(raw)

    print(f"[{datetime.now()}] ✅ 完成！已更新 tv.txt 和 tv.m3u")

if __name__ == "__main__":
    main()
