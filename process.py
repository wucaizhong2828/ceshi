import requests
from datetime import datetime

print("开始生成直播源...")

# ================== 配置区 ==================
ONLINE_URL = "https://zb.7778.uk/"
OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"

# 黑名单：包含这些关键词的行将被过滤掉
BLACKLIST_KEYWORDS = ["影视仓官网", "接口大全", "panurl"]
# ===========================================

def fetch_online_sources():
    """抓取在线源，过滤掉黑名单内容"""
    all_channels = []
    try:
        print(f"   📡 正在抓取: {ONLINE_URL}")
        resp = requests.get(ONLINE_URL, timeout=30)
        resp.encoding = 'utf-8'
        resp.raise_for_status()
        lines = [line.strip() for line in resp.text.splitlines() if line.strip()]

        for line in lines:
            if ',' in line and not line.startswith('#'):
                # 检查黑名单
                if any(k in line for k in BLACKLIST_KEYWORDS):
                    continue
                all_channels.append(line)

        print(f"   ✅ 从 {ONLINE_URL} 获取了 {len(all_channels)} 个频道")
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

    # 保存 TXT
    txt_content = "\n".join(channels)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")

    # 生成 M3U
    m3u_content = generate_m3u(txt_content)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(channels)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
