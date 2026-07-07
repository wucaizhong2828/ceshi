import requests
import traceback
from datetime import datetime

print("=== 开始执行 ===")

try:
    URLS = [
        "https://iptv-org.github.io/iptv/countries/cn.m3u",
    ]

    KEEP_KEYWORDS = ["CCTV", "央视", "卫视"]

    all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]

    for url in URLS:
        print(f"正在获取: {url}")
        resp = requests.get(url, timeout=30)
        print(f"状态码: {resp.status_code}")
        if resp.status_code == 200:
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            filtered = [line for line in lines if any(k in line for k in KEEP_KEYWORDS)]
            all_lines.extend(filtered)
            print(f"保留 {len(filtered)} 个频道")

    with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    print("文件写入成功！")
    print(f"总行数: {len(all_lines)}")

except Exception as e:
    print("发生错误:")
    print(traceback.format_exc())
    raise
