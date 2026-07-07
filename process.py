import requests
from datetime import datetime

URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻"]

print("开始更新...")

all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]

for url in URLS:
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            filtered = [line for line in lines if any(k in line for k in KEEP_KEYWORDS)]
            all_lines.extend(filtered)
            print(f"从 {url} 保留 {len(filtered)} 个频道")
    except Exception as e:
        print(f"获取 {url} 失败: {e}")

with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines) + "\n")

print(f"完成！共 {len(all_lines)} 行")
