import requests
from datetime import datetime
import re

print("开始生成直播源...")

# ================== 配置区 ==================
ONLINE_URLS = [
    "https://zb.7778.uk/",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    # "https://raw.githubusercontent.com/Ftindy/IPTV-URL/main/IPTV.m3u",  # 已失效，暂时注释
    "https://raw.githubusercontent.com/vamoschuck/TV/main/M3U",
    "https://testingcf.jsdelivr.net/gh/YueChan/Live@main/IPTV.m3u",
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
    """检查是否为有效的频道行（白名单模式），用于 TXT 格式"""
    if ',' not in line:
        return False

    parts = line.split(',', 1)
    if len(parts) != 2:
        return False

    title, url = parts[0].strip(), parts[1].strip()

    # 白名单检查
    if WHITELIST_KEYWORDS:
        matched = False
        for keyword in WHILIST_KEYWORDS:
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

def parse_m3u_content(content):
    """解析标准的 M3U 格式内容，返回频道列表（频道名,URL）"""
    channels = []
    lines = content.splitlines()
    current_title = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#EXTINF'):
            # 提取频道名，通常在逗号之后
            if ',' in line:
                # 处理可能包含 group-title 等参数的情况
                parts = line.split(',', 1)
                if len(parts) == 2:
                    current_title = parts[1].strip()
                else:
                    current_title = None
            else:
                current_title = None
        elif line and not line.startswith('#') and current_title:
            # 这是一个媒体URL，与之前提取的标题配对
            if line.startswith('http://') or line.startswith('https://'):
                # 检查标题是否在白名单中
                test_line = f"{current_title},{line}"
                if is_valid_channel(test_line):
                    channels.append(test_line)
                current_title = None
    
    return channels

def parse_txt_content(content):
    """解析 TXT 格式内容（频道名,URL）"""
    channels = []
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    for line in lines:
        if ',' in line and not line.startswith('#'):
            if is_valid_channel(line):
                channels.append(line)
    
    return channels

def fetch_online_sources():
    """抓取多个在线源，自动识别格式"""
    all_channels = []
    # 模拟浏览器请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30, headers=headers)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            
            content = resp.text
            channels = []
            
            # 判断格式：检查是否包含 M3U 特征
            if '#EXTM3U' in content or '#EXTINF' in content:
                print(f"   🔍 检测到 M3U 格式，使用 M3U 解析器")
                channels = parse_m3u_content(content)
            else:
                print(f"   🔍 检测到 TXT 格式，使用 TXT 解析器")
                channels = parse_txt_content(content)
            
            all_channels.extend(channels)
            print(f"   ✅ 从 {url} 获取了 {len(channels)} 个有效频道（累计 {len(all_channels)} 个）")
            
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    
    return all_channels

def generate_txt(merged_channels):
    """生成 TXT 文件"""
    cctv = []
    satellite = []
    other = []

    for line in merged_channels:
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url.startswith('http://') or url.startswith('https://'):
                    if "CCTV" in title or "央视" in title:
                        cctv.append(line)
                    elif "卫视" in title:
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

def generate_m3u(merged_channels):
    """生成 M3U 文件"""
    cctv = []
    satellite = []
    other = []

    for line in merged_channels:
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url.startswith('http://') or url.startswith('https://'):
                    if "CCTV" in title or "央视" in title:
                        cctv.append((title, url))
                    elif "卫视" in title:
                        satellite.append((title, url))
                    else:
                        other.append((title, url))

    m3u_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]

    if cctv:
        m3u_lines.append('#EXTINF:-1 group-title="央视频道",央视频道')
        for title, url in cctv:
            m3u_lines.append(f'#EXTINF:-1 group-title="央视频道",{title}')
            m3u_lines.append(url)

    if satellite:
        m3u_lines.append('#EXTINF:-1 group-title="卫视频道",卫视频道')
        for title, url in satellite:
            m3u_lines.append(f'#EXTINF:-1 group-title="卫视频道",{title}')
            m3u_lines.append(url)

    if other:
        m3u_lines.append('#EXTINF:-1 group-title="其他频道",其他频道')
        for title, url in other:
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

    print(f"📊 去重后共 {len(unique_channels)} 个频道")

    if not unique_channels:
        print("⚠️ 警告：没有抓取到任何频道！")
        return

    # 生成 TXT
    txt_content = generate_txt(unique_channels)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")

    # 生成 M3U
    m3u_content = generate_m3u(unique_channels)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(unique_channels)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
