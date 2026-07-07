import requests
from datetime import datetime

URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

KEEP_KEYWORDS = [
    "CCTV", "央视", "卫视", "湖南", "江苏", "浙江", "北京", "上海", "东方",
    "凤凰", "TVB", "Now", "中天", "东森", "民视", "台视", "新闻"
]

print("开始抓取并过滤频道...")

all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
all_lines.append("# 中国大陆 + 香港台湾新闻频道")

count = 0
for url in URLS:
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = [line.strip() for line in resp.text.splitlines() if line.strip() and not line.startswith("#EXT")]
            filtered = [line for line in lines if any(k in line for k in KEEP_KEYWORDS)]
            all_lines.extend(filtered)
            count += len(filtered)
            print(f"从 {url} 保留 {len(filtered)} 个频道")
    except Exception as e:
        print(f"获取失败 {url}: {e}")

with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines) + "\n")

print(f"完成！共保留 {count} 个频道")
