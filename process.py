import requests
from datetime import datetime

print("开始更新直播源...")

URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻"]

all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
all_lines.append("# 中国大陆 + 香港台湾新闻频道")

total = 0
for url in URLS:
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            lines = [line.strip() for line in resp.text.splitlines() if line.strip() and not line.startswith("#EXTM3U")]
            filtered = [line for line in lines if any(k in line for k in KEEP_KEYWORDS)]
            all_lines.extend(filtered)
            total += len(filtered)
            print(f"从 {url} 保留 {len(filtered)} 个频道")
    except Exception as e:
        print(f"获取失败: {e}")

# 保存 m3u
with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines) + "\n")

# 同时保存 txt 版本（纯链接列表）
with open("iptv_playlist.txt", "w", encoding="utf-8") as f:
    for line in all_lines:
        if line.startswith("http") or "," in line:
            f.write(line + "\n")

print(f"完成！共保留 {total} 个频道")
print("已生成 iptv_playlist.m3u 和 iptv_playlist.txt")
