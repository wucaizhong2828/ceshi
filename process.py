#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from datetime import datetime

# ==============================================
# 配置：在这里添加你的直播源地址，一行一个
# ==============================================
SOURCE_URLS = [
    "https://0701.tv1288.xyz",
]

# 过滤关键词：频道名包含这些词会被删除
SPAM_KEYWORDS = ["加群", "TG", "t.me", "关注", "广告", "备用", "防失联", "微信", "QQ", "最新"]

# ==============================================
# 抓取所有源（增强伪装）
# ==============================================
def fetch_all_sources():
    all_lines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://0701.tv1288.xyz/",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="120", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    for url in SOURCE_URLS:
        try:
            print(f"  正在抓取: {url}")
            resp = requests.get(url, timeout=15, headers=headers)
            resp.encoding = 'utf-8'
            content = resp.text

            # 检查是否返回了 HTML 页面（被拦截）
            if '<!DOCTYPE html>' in content or '<html' in content.lower():
                print(f"  ⚠️ 警告: {url} 返回了 HTML 页面，可能被拦截")
                # 尝试从 HTML 中提取真实内容（如果被包装的话）
                # 这里不跳过，继续尝试解析

            lines = content.split('\n')
            all_lines.extend(lines)
            all_lines.append("")
        except Exception as e:
            print(f"  ❌ 抓取失败: {url} - {e}")

    return '\n'.join(all_lines)


# ==============================================
# 检测格式并处理
# ==============================================
def process_content(text):
    lines = text.split('\n')
    
    # 检测格式
    is_txt = any(',#genre#' in line for line in lines)
    is_m3u = any('#EXTINF' in line for line in lines)
    
    print(f"  📋 检测到格式: {'TXT' if is_txt else 'M3U' if is_m3u else '未知'}")
    
    if is_txt:
        return process_txt(text)
    elif is_m3u:
        return convert_m3u_to_txt(text)
    else:
        print("  ⚠️ 未知格式，尝试按 TXT 处理")
        return process_txt(text)


# ==============================================
# 处理 TXT 格式（频道名,地址）
# ==============================================
def process_txt(text):
    lines = text.split('\n')
    result = []
    total = 0
    filtered = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 保留分类行
        if ',#genre#' in line:
            result.append(line)
            continue
        
        # 处理频道行
        if ',' in line and not line.startswith('#'):
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                # 检查是否包含过滤关键词
                is_spam = any(kw in title for kw in SPAM_KEYWORDS)
                if not is_spam:
                    result.append(line)
                    total += 1
                else:
                    filtered += 1
                    print(f"  🚫 已过滤: {title}")
        else:
            # 保留其他行（如注释）
            result.append(line)
    
    print(f"  📊 共 {total} 个频道，过滤了 {filtered} 个，保留 {total} 个")
    return '\n'.join(result)


# ==============================================
# M3U → TXT 转换（备用）
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
        
        if line.startswith('#EXTINF'):
            # 提取频道名（最后一个逗号后面的内容）
            title_match = re.search(r',([^,]+)$', line)
            title = title_match.group(1).strip() if title_match else "未知频道"
            
            is_spam = any(kw in title for kw in SPAM_KEYWORDS)
            
            i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                # 检查是否是 URL（http/https 开头）
                if re.match(r'^https?://', url_line):
                    total += 1
                    if not is_spam:
                        txt_lines.append(f"{title},{url_line}")
                    else:
                        filtered += 1
                        print(f"  🚫 已过滤: {title}")
                # 如果是 javascript: 或其他，跳过
            i += 1
            continue
        
        i += 1
    
    print(f"  📊 共 {total} 个频道，过滤了 {filtered} 个，保留 {total - filtered} 个")
    return '\n'.join(txt_lines)


# ==============================================
# 生成 M3U 格式
# ==============================================
def generate_m3u(txt_content):
    lines = txt_content.split('\n')
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
                if re.match(r'^https?://', url):
                    m3u_lines.append(f'#EXTINF:-1 group-title="{current_group}",{title}')
                    m3u_lines.append(url)
    
    return '\n'.join(m3u_lines)


# ==============================================
# 主流程
# ==============================================
def main():
    print(f"[{datetime.now()}] 开始抓取 {len(SOURCE_URLS)} 个直播源...")

    raw = fetch_all_sources()
    print(f"抓取完成，合并后大小: {len(raw)} 字符")

    # 打印前 200 个字符，帮助调试
    if len(raw) > 200:
        print(f"内容预览: {raw[:200]}...")

    # 处理内容（自动识别格式）
    txt_content = process_content(raw)
    print(f"处理完成，TXT 大小: {len(txt_content)} 字符")

    # 保存 TXT 格式
    with open('tv.txt', 'w', encoding='utf-8') as f:
        f.write(txt_content)

    # 生成并保存 M3U 格式
    m3u_content = generate_m3u(txt_content)
    with open('tv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"[{datetime.now()}] ✅ 完成！已更新 tv.txt 和 tv.m3u")


if __name__ == "__main__":
    main()
