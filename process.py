import requests
import sys
import time
from datetime import datetime
import random

URLS = ["https://0701.tv1288.xyz", "https://tv1288.xyz"]
OUTPUT_FILE = "iptv_playlist.m3u"

# 免费代理示例（可自行替换更稳定的）
PROXIES = [
    {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},  # 本地可不填
    # 更多免费代理可自行搜索
]

def fetch_playlist(url):
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.baidu.com/",
    }

    for attempt in range(6):
        try:
            proxy = random.choice(PROXIES) if PROXIES else None
            resp = requests.get(url, headers=headers, timeout=25, proxies=proxy)
            if resp.status_code == 200 and len(resp.text) > 500:
                print(f"✅ 成功 {url}")
                return resp.text
            print(f"⚠️ 状态码 {resp.status_code} {url}")
        except Exception as e:
            print(f"⚠️ 异常 {url}: {e}")
        time.sleep(4)
    return None

def main():
    all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"]

    for url in URLS:
        content = fetch_playlist(url)
        if content:
            all_lines.extend([line.strip() for line in content.splitlines() if line.strip()])
            print(f"获取成功，共 {len(all_lines)} 行")
            break
    else:
        print("❌ 全部失败，保留旧文件")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"🎉 完成 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
