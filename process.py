import requests
from datetime import datetime

print("开始生成直播源...")

# ================== 配置区 ==================
ONLINE_URLS = [
    "https://zb.7778.uk/",
    "https://fty.xxooo.cf/tv",
]
OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"

# 黑名单：包含这些关键词的行将被过滤掉
BLACKLIST_KEYWORDS = [
    "影视仓", "接口大全", "panurl",
    "柳河", "综合",
]
# ===========================================

def is_valid_channel(line):
    """检查是否为有效的频道行"""
    if ',' not in line:
        return False
    
    parts = line.split(',', 1)
    if len(parts) != 2:
        return False
    
    title, url = parts[0].strip(), parts[1].strip()
    
    # 检查黑名单关键词
    for keyword in BLACKLIST_KEYWORDS:
        if keyword in line:
            return False
    
    # 检查 URL 是否有效
    if not (url.startswith('http://') or url.startswith('https://') or url == '#genre#'):
        return False
    
    # 检查是否包含乱码（包含特殊符号或过长）
    if len(title) > 50 or len(url) > 200:
        return False
    
    # 检查是否包含乱码字符（非中文、英文、数字、常用符号）
    import re
    # 如果标题包含大量特殊符号，视为乱码
    if re.search(r'[^\u4e00-\u9fa5a-zA-Z0-9\-_\s\+\#\.\:]', title):
        # 如果特殊符号占比过高，过滤掉
        special_chars = re.findall(r'[^\u4e00-\u9fa5a-zA-Z0-9\-_\s\+\#\.\:]', title)
        if len(special_chars) > len(title) * 0.3:  # 特殊符号超过30%
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

def generate_m3u(txt_content):
    """从 TXT 格式生成 M3U 格式"""
    lines = txt_content.splitlines()
    m3u_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
    current_group = "默认频道"

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url == '#genre#':
                    current_group = title
                    continue
                if url.startswith('http://') or url.startswith('https://'):
                    m3u_lines.append(f'#EXTINF:-1 group-title="{current_group}",{title}')
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

    # 保存 TXT
    txt_content = "\n".join(unique_channels)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")

    # 生成 M3U
    m3u_content = generate_m3u(txt_content)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(unique_channels)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
