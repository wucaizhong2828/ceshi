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
# 解析并过滤：输出 TXT 格式（频道名,地址）
# ==============================================
def parse_and_filter(text):
    lines = text.split('\n')
    result = []
    current_group = "默认频道"
    
    # 检测是否为 M3U 格式
    is_m3u = any('#EXTM3U' in line or '#EXTINF' in line for line in lines if line.strip())
    
    if is_m3u:
        # ===== M3U → TXT 转换 =====
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # 提取分类（从 #EXTINF 中解析 group-title）
            if line.startswith('#EXTINF'):
                # 解析 group-title
                group_match = re.search(r'group-title="([^"]+)"', line)
                if group_match:
                    current_group = group_match.group(1)
                
                # 解析频道名（#EXTINF 行最后一个逗号后面的部分）
                title_match = re.search(r',([^,]+)$', line)
                title = title_match.group(1).strip() if title_match else "未知频道"
                
                # 检查是否包含过滤关键词
                if any(kw in title for kw in SPAM_KEYWORDS):
                    i += 1
                    continue
                
                # 下一行应该是 URL
                i += 1
                if i < len(lines):
                    url_line = lines[i].strip()
                    # 如果是 http/https 开头的 URL
                    if re.match(r'^https?://', url_line):
                        # 输出 TXT 格式：频道名,地址
                        result.append(f"{title},{url_line}")
                    # 如果是 javascript: 或其他，跳过
                i += 1
                continue
            
            # 跳过其他行（如 #EXTM3U, # 注释等）
            i += 1
        
        # 如果转换后没有结果，说明解析可能失败，尝试备用方法
        if not result:
            print("  ⚠️ M3U 解析可能失败，尝试备用解析...")
            # 备用：直接搜索所有 http/https 开头的 URL 行
            for i, line in enumerate(lines):
                line = line.strip()
                if re.match(r'^https?://', line):
                    # 尝试从上一行找频道名
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line.startswith('#EXTINF'):
                            title_match = re.search(r',([^,]+)$', prev_line)
                            title = title_match.group(1).strip() if title_match else "未知频道"
                            if not any(kw in title for kw in SPAM_KEYWORDS):
                                result.append(f"{title},{line}")
    else:
        # ===== TXT 格式处理 =====
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
# 生成 M3U 格式（保留原始 M3U 结构）
# ==============================================
def generate_m3u(cleaned_text):
    # 如果输入是 TXT 格式（包含 ,#genre#），先解析再转换
    lines = cleaned_text.split('\n')
    
    # 检测输入是否为 TXT 格式（包含 ,#genre# 或 频道名,地址 格式）
    is_txt = any(',#genre#' in line for line in lines) or any(',' in line and not line.startswith('#') and not line.startswith('http') for line in lines)
    
    m3u_lines = ["#EXTM3U"]
    current_group = "默认频道"
    
    if is_txt:
        # TXT → M3U 转换
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
                    # 确保 URL 是 http/https 开头
                    if re.match(r'^https?://', url):
                        m3u_lines.append(f'#EXTINF:-1 group-title="{current_group}",{title}')
                        m3u_lines.append(url)
    else:
        # 已经是 M3U 格式，直接保留
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#EXTM3U'):
                continue
            m3u_lines.append(line)
    
    # 确保第一行是 #EXTM3U
    if not m3u_lines[0].startswith('#EXTM3U'):
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
