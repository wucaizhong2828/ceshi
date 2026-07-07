import requests
from datetime import datetime

print("开始生成直播源...")

URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻"]

all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
all_lines.append("# 中国大陆 + 香港台湾新闻频道")

txt_lines = []

for url in URLS:
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            for line in lines:
                if any(k in line for k in KEEP_KEYWORDS):
                    all_lines.append(line)
                    # 提取链接保存到txt
                    if "," in line:
                        name, link = line.split(",", 1)
                        txt_lines.append(link.strip())
    except Exception as e:
        print(f"获取失败: {e}")

# 保存 m3u
with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines) + "\n")

# 保存 txt（纯链接列表）
with open("iptv_playlist.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines) + "\n")

print(f"完成！m3u 共 {len(all_lines)} 行，txt 共 {len(txt_lines)} 个链接")
