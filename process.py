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
# 解析并过滤（自动识别 M3U 或 TXT 格式）
# ==============================================
def parse_and_filter(text):
    lines = text.split('\n')
    result = []
    
    # 检测是否为 M3U 格式
    is_m3u = any('#EXTM3U' in line or '#EXTINF' in line for line in lines if line.strip())
    
    if is_m3u:
        # ===== M3U 格式处理 =====
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 保留所有 #EXTINF 行（同时检查是否包含过滤关键词）
            if line.startswith('#EXTINF'):
                # 检查频道名是否包含过滤词
                if not any(kw in line for kw in SPAM_KEYWORDS):
                    result.append(line)
                continue
            
            # 保留 URL 行（必须是 http/https 开头）
            if re.match(r'^https?://', line):
                result.append(line)
                continue
            
            # 保留其他 # 开头的行（如 #EXTM3U）
            if line.startswith('#'):
                result.append(line)
                continue
            
            # 跳过其他未知行（如 javascript: 等）
    else:
        # ===== TXT 格式处理 =====
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


# ==============================================
# 生成 M3U 格式（直接输出原始 M3U 结构）
# ==============================================
def generate_m3u(cleaned_text):
    lines = cleaned_text.split('\n')
    m3u_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 确保 #EXTM3U 在第一行
        if line.startswith('#EXTM3U'):
            if '#EXTM3U' not in m3u_lines:
                m3u_lines.insert(0, line)
            continue
        
        # 保留所有 #EXTINF 行
        if line.startswith('#EXTINF'):
            m3u_lines.append(line)
            continue
        
        # 保留 URL 行（http/https 开头）
        if re.match(r'^https?://', line):
            m3u_lines.append(line)
            continue
        
        # 保留其他 # 开头的行
        if line.startswith('#'):
            m3u_lines.append(line)
            continue
    
    # 如果第一行不是 #EXTM3U，手动添加
    if not m3u_lines or not m3u_lines[0].startswith('#EXTM3U'):
        m3u_lines.insert(0, '#EXTM3U')
    
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
