#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV 直播源聚合 + 智能检测
功能：
  1. 从多个源抓取直播列表
  2. 自动检测每个频道的可用性
  3. 剔除卡顿/无效源
  4. 生成干净的 M3U/TXT
"""

import requests
from datetime import datetime
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

print("🚀 开始生成直播源...")

# ================== 配置区 ==================

# 上游源地址（替换成你自己的）
ONLINE_URLS = [
    "https://zb.7778.uk/",
    "https://fty.xxooo.cf/tv",
    # 在这里添加更多源...
]

# 输出文件名
OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"

# ================== 智能检测配置 ==================

CHECK_CONFIG = {
    'enabled': True,           # 是否启用智能检测（False则跳过检测）
    'timeout': 5,              # 单个源检测超时（秒）
    'max_workers': 20,         # 并发检测数
    'min_speed': 0.3,          # 最低速度 MB/s，低于此值视为卡顿
    'max_urls_per_channel': 3, # 每个频道最多保留几条线路
    'test_size': 512 * 1024,   # 下载多少字节测速（512KB）
}

# ================== 白名单配置 ==================

WHITELIST_KEYWORDS = [
    "CCTV", "央视",
    "北京卫视", "东方卫视", "天津卫视", "重庆卫视",
    "河北卫视", "山西卫视", "内蒙古卫视", "辽宁卫视", "吉林卫视",
    "黑龙江卫视", "江苏卫视", "浙江卫视", "安徽卫视", "福建卫视",
    "江西卫视", "山东卫视", "河南卫视", "湖北卫视", "湖南卫视",
    "广东卫视", "广西卫视", "海南卫视", "四川卫视", "贵州卫视",
    "云南卫视", "西藏卫视", "陕西卫视", "甘肃卫视", "青海卫视",
    "宁夏卫视", "新疆卫视",
    "深圳卫视", "厦门卫视", "青岛卫视", "大连卫视", "宁波卫视",
    "凤凰卫视", "凤凰资讯", "凤凰中文",
    "4K", "经典4K", "CCTV4K", "CHC", "重温经典",
]

# ==================================================

# 全局计数器（用于显示进度）
check_counter = 0
check_lock = threading.Lock()


def is_valid_channel(line):
    """检查是否为有效的频道行（白名单模式）"""
    if ',' not in line:
        return False

    parts = line.split(',', 1)
    if len(parts) != 2:
        return False

    title, url = parts[0].strip(), parts[1].strip()

    if WHITELIST_KEYWORDS:
        matched = False
        for keyword in WHITELIST_KEYWORDS:
            if keyword in title:
                matched = True
                break
        if not matched:
            return False

    if not (url.startswith('http://') or url.startswith('https://')):
        return False

    if len(title) > 50 or len(url) > 200:
        return False

    return True


def fetch_online_sources():
    """抓取多个在线源"""
    all_channels = []
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]

            for line in lines:
                if ',' in line and not line.startswith('#'):
                    if is_valid_channel(line):
                        all_channels.append(line)

            print(f"   ✅ 从 {url} 获取了有效频道")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_channels


# ================== 智能检测核心 ==================

def check_single_url(url, timeout=5):
    """
    检测单个URL是否可用，返回速度
    返回: (is_valid, speed_mb, response_time_ms)
    """
    try:
        start_time = time.time()
        response = requests.get(
            url,
            timeout=timeout,
            stream=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        if response.status_code != 200:
            return False, 0, 0

        # 下载测试数据测速
        downloaded = 0
        test_size = CHECK_CONFIG['test_size']
        chunk_size = 64 * 1024  # 64KB

        for chunk in response.iter_content(chunk_size=chunk_size):
            downloaded += len(chunk)
            if downloaded >= test_size:
                break

        elapsed = time.time() - start_time
        if elapsed > 0:
            speed_mb = downloaded / (1024 * 1024) / elapsed
        else:
            speed_mb = 0

        return True, speed_mb, elapsed * 1000

    except Exception:
        return False, 0, 0


def batch_check_urls(urls, channel_name=""):
    """
    批量检测一个频道的所有线路
    返回: 有效的线路列表（按速度排序）
    """
    if not urls:
        return []

    global check_counter
    valid_urls = []

    with ThreadPoolExecutor(max_workers=CHECK_CONFIG['max_workers']) as executor:
        future_to_url = {
            executor.submit(check_single_url, url, CHECK_CONFIG['timeout']): url
            for url in urls
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                is_valid, speed, response_time = future.result()

                with check_lock:
                    check_counter += 1
                    current = check_counter

                if is_valid and speed >= CHECK_CONFIG['min_speed']:
                    valid_urls.append({
                        'url': url,
                        'speed': speed,
                        'response_time': response_time
                    })
                    # 只显示部分信息，避免刷屏
                    if current % 10 == 0:
                        print(f"     ✅ 已检测 {current} 个线路，有效 {len(valid_urls)} 个")
                else:
                    if current % 20 == 0:
                        print(f"     ⏳ 已检测 {current} 个线路...")

            except Exception:
                pass

    # 按速度排序（从快到慢）
    valid_urls.sort(key=lambda x: x['speed'], reverse=True)

    return valid_urls


def smart_filter_channels(channels):
    """
    智能过滤频道列表，移除卡顿源
    channels: list of dict [{'name': 'CCTV1', 'urls': ['url1', 'url2']}]
    返回: 过滤后的列表
    """
    if not CHECK_CONFIG['enabled']:
        print("   ⏭️ 智能检测已禁用，跳过")
        return channels

    if not channels:
        return []

    print(f"\n🧪 开始智能检测 {len(channels)} 个频道...")
    print(f"   ⏱️ 超时: {CHECK_CONFIG['timeout']}秒 | 最低速度: {CHECK_CONFIG['min_speed']} MB/s")
    print(f"   🔄 并发数: {CHECK_CONFIG['max_workers']}\n")

    global check_counter
    check_counter = 0

    filtered = []
    total = len(channels)

    for idx, channel in enumerate(channels, 1):
        name = channel.get('name', '未知')
        urls = channel.get('urls', [])

        # 显示进度
        print(f"  [{idx}/{total}] 检测: {name} ({len(urls)}条线路)")

        if not urls:
            print(f"     ⚠️ 无线路，跳过")
            continue

        # 检测该频道的所有线路
        valid_urls = batch_check_urls(urls, name)

        if valid_urls:
            # 保留最快的 N 条线路
            max_urls = CHECK_CONFIG['max_urls_per_channel']
            best_urls = valid_urls[:max_urls]

            channel['urls'] = [item['url'] for item in best_urls]
            channel['speed'] = best_urls[0]['speed']  # 记录最快速度
            channel['speed_mb'] = f"{best_urls[0]['speed']:.2f}MB/s"
            filtered.append(channel)

            speed_info = ', '.join([f"{item['speed']:.2f}MB/s" for item in best_urls[:3]])
            print(f"     ✅ 保留 {len(best_urls)}/{len(urls)} 条线路 (最快: {best_urls[0]['speed']:.2f} MB/s)")
        else:
            print(f"     ❌ 所有线路均无效/卡顿，已剔除")

    print(f"\n📊 智能检测完成：保留 {len(filtered)}/{total} 个频道")
    return filtered


def parse_channels_from_lines(lines):
    """
    从原始行解析频道列表
    输入: ['CCTV1,http://xxx', 'CCTV2,http://yyy']
    输出: [{'name': 'CCTV1', 'urls': ['http://xxx']}, ...]
    """
    channel_dict = {}

    for line in lines:
        if ',' not in line:
            continue
        parts = line.split(',', 1)
        if len(parts) != 2:
            continue

        name, url = parts[0].strip(), parts[1].strip()
        if not url.startswith('http'):
            continue

        # 按频道名分组
        if name not in channel_dict:
            channel_dict[name] = {
                'name': name,
                'urls': []
            }
        channel_dict[name]['urls'].append(url)

    return list(channel_dict.values())


def channels_to_lines(channels):
    """
    将频道列表转回原始行格式
    """
    lines = []
    for ch in channels:
        for url in ch['urls']:
            lines.append(f"{ch['name']},{url}")
    return lines


# ================== 生成输出 ==================

def generate_txt(channels):
    """生成 TXT 文件"""
    # 按分类整理
    cctv = []
    satellite = []
    other = []

    for ch in channels:
        name = ch['name']
        for url in ch['urls']:
            line = f"{name},{url}"
            if "CCTV" in name or "央视" in name:
                cctv.append(line)
            elif "卫视" in name:
                satellite.append(line)
            else:
                other.append(line)

    result = []
    if cctv:
        result.append("央视频道,#genre#")
        result.extend(cctv)
    if satellite:
        result.append("卫视频道,#genre#")
        result.extend(satellite)
    if other:
        result.append("其他频道,#genre#")
        result.extend(other)

    return '\n'.join(result)


def generate_m3u(channels):
    """生成 M3U 文件"""
    cctv = []
    satellite = []
    other = []

    for ch in channels:
        name = ch['name']
        for url in ch['urls']:
            if "CCTV" in name or "央视" in name:
                cctv.append((name, url))
            elif "卫视" in name:
                satellite.append((name, url))
            else:
                other.append((name, url))

    m3u_lines = [
        "#EXTM3U",
        f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ]

    if cctv:
        m3u_lines.append('#EXTINF:-1 group-title="央视频道",央视频道')
        for name, url in cctv:
            m3u_lines.append(f'#EXTINF:-1 group-title="央视频道",{name}')
            m3u_lines.append(url)

    if satellite:
        m3u_lines.append('#EXTINF:-1 group-title="卫视频道",卫视频道')
        for name, url in satellite:
            m3u_lines.append(f'#EXTINF:-1 group-title="卫视频道",{name}')
            m3u_lines.append(url)

    if other:
        m3u_lines.append('#EXTINF:-1 group-title="其他频道",其他频道')
        for name, url in other:
            m3u_lines.append(f'#EXTINF:-1 group-title="其他频道",{name}')
            m3u_lines.append(url)

    return '\n'.join(m3u_lines)


# ================== 主程序 ==================

def main():
    print("\n📡 抓取在线源...")
    raw_channels = fetch_online_sources()

    if not raw_channels:
        print("❌ 未抓取到任何频道，请检查源地址")
        return

    print(f"\n📋 原始频道数: {len(raw_channels)}")

    # 去重
    seen = set()
    unique_lines = []
    for line in raw_channels:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    print(f"📋 去重后: {len(unique_lines)}")

    # 解析为字典格式
    channel_dicts = parse_channels_from_lines(unique_lines)
    print(f"📋 解析为 {len(channel_dicts)} 个频道")

    # ========== 智能检测 ==========
    if CHECK_CONFIG['enabled']:
        print("\n" + "="*50)
        print("🧪 启动智能检测（自动过滤卡顿源）")
        print("="*50)
        channel_dicts = smart_filter_channels(channel_dicts)
    else:
        print("\n⏭️ 跳过智能检测")

    # 转回行格式
    final_lines = channels_to_lines(channel_dicts)
    print(f"\n📋 最终频道数: {len(final_lines)}")

    # 生成 TXT
    txt_content = generate_txt(channel_dicts)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")

    # 生成 M3U
    m3u_content = generate_m3u(channel_dicts)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 TXT: {OUTPUT_TXT} ({len(final_lines)} 个频道)")
    print(f"   📄 M3U: {OUTPUT_M3U}")

    # 统计信息
    total_urls = sum(len(ch['urls']) for ch in channel_dicts)
    print(f"   📊 共 {len(channel_dicts)} 个频道，{total_urls} 条有效线路")


if __name__ == "__main__":
    main()
