import requests
from datetime import datetime
import re

print("开始生成直播源...")

# ================== 配置区 ==================
ONLINE_URLS = [
    "https://zb.7778.uk/",
    "https://fty.xxooo.cf/tv",
]
OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"

# 白名单：只保留包含这些关键词的频道
WHITELIST_KEYWORDS = [
    # 央视
    "CCTV",
    "央视",
    # 省级卫视
    "北京卫视", "东方卫视", "天津卫视", "重庆卫视",
    "河北卫视", "山西卫视", "内蒙古卫视", "辽宁卫视", "吉林卫视",
    "黑龙江卫视", "江苏卫视", "浙江卫视", "安徽卫视", "福建卫视",
    "江西卫视", "山东卫视", "河南卫视", "湖北卫视", "湖南卫视",
    "广东卫视", "广西卫视", "海南卫视", "四川卫视", "贵州卫视",
    "云南卫视", "西藏卫视", "陕西卫视", "甘肃卫视", "青海卫视",
    "宁夏卫视", "新疆卫视",
    # 计划单列市/特区
    "深圳卫视", "厦门卫视", "青岛卫视", "大连卫视", "宁波卫视",
    # 凤凰
    "凤凰卫视", "凤凰资讯", "凤凰中文",
    # 4K 频道
    "4K",
    "经典4K",
    "CCTV4K",
    "CHC",
    "重温经典",
]
# ===========================================

def is_valid_channel(line):
    """检查是否为有效的频道行（白名单模式）"""
    if ',' not in line:
        return False

    parts = line.split(',', 1)
    if len(parts) != 2:
        return False

    title, url = parts[0].strip(), parts[1].strip()

    # 白名单检查
    if WHITELIST_KEYWORDS:
        matched = False
        for keyword in WHITELIST_KEYWORDS:
            if keyword in title:
                matched = True
                break
        if not matched:
            return False

    # 检查 URL 是否有效
    if not (url.startswith('http://') or url.startswith('https://') or url == '#genre#'):
        return False

    # 检查乱码
    if len(title) > 50 or len(url) > 200:
        return False

    if re.search(r'[^\u4e00-\u9fa5a-zA-Z0-9\-_\s\+\#\.\:]', title):
        special_chars = re.findall(r'[^\u4e00-\u9fa5a-zA-Z0-9\-_\s\+\#\.\:]', title)
        if len(special_chars) > len(title) * 0.3:
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

            print(f"   ✅ 从 {url} 获取了 {len(all_channels)} 个有效频道（累计）")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_channels

def generate_txt(merged_channels):
    """生成 TXT 文件，统一分类名"""
    lines = []
    cctv_channels = []
    satellite_channels = []
    other_channels = []

    for line in merged_channels:
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url == '#genre#':
                    # 统一分类名
                    if "央视" in title:
                        lines.append("央视频道,#genre#")
                    elif "卫视" in title:
                        lines.append("卫视频道,#genre#")
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

    # 去重分类标题
    seen_genre = set()
    result = []
    for line in lines:
        if line.endswith(',#genre#'):
            if line in seen_genre:
                continue
            seen_genre.add(line)
        result.append(line)

    return '\n'.join(result)

def generate_m3u(merged_channels):
    """生成 M3U 文件，央视和省市分成两个板块"""
    cctv_channels = []
    satellite_channels = []
    other_channels = []

    for line in merged_channels:
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url.startswith('http://') or url.startswith('https://'):
                    # 判断属于哪个板块
                    if "CCTV" in title or "央视" in title:
                        cctv_channels.append((title, url))
                    elif "卫视" in title:
                        satellite_channels.append((title, url))
                    else:
                        other_channels.append((title, url))

    # 生成 M3U
    m3u_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]

    # 1. 央视频道
    if cctv_channels:
        for title, url in cctv_channels:
            m3u_lines.append(f'#EXTINF:-1 group-title="央视频道",{title}')
            m3u_lines.append(url)

    # 2. 卫视频道
    if satellite_channels:
        for title, url in satellite_channels:
            m3u_lines.append(f'#EXTINF:-1 group-title="卫视频道",{title}')
            m3u_lines.append(url)

    # 3. 其他频道
    if other_channels:
        for title, url in other_channels:
            m3u_lines.append(f'#EXTINF:-1 group-title="其他频道",{title}')
            m3u_lines.append(url)

    return '\n'.join(m3u_lines)

def main():
    print("🚀 开始生成直播源...")

    print("\n📡 抓取在线源...")
    channels = fetch_online_sources()

    # 去重
    seen = set()
    unique_channels = []
    for ch in channels:
        if ch not in seen:
            seen.add(ch)
            unique_channels.append(ch)

    # 生成 TXT（统一分类名）
    txt_content = generate_txt(unique_channels)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")

    # 生成 M3U（分两个板块）
    m3u_content = generate_m3u(unique_channels)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(unique_channels)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
