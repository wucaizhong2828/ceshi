import requests
import sys
import time
from datetime import datetime

# ================== 配置区 ==================
URLS = [
    "https://0701.tv1288.xyz",
    "https://tv1288.xyz",           # 备用主域名
    # 可继续添加其他稳定源
]

FILTER_KEYWORDS = []   # 如需过滤填 ["CCTV", "卫视"]

OUTPUT_FILE = "iptv_playlist.m3u"
MAX_RETRIES = 5
# ===========================================

def fetch_playlist(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            print(f"✅ 成功获取 {url}")
            return resp.text
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次尝试失败 {url}: {e}")
            time.sleep(2 ** attempt)   # 指数退避
    print(f"❌ 最终失败: {url}")
    return None

def main():
    all_lines = [f"#EXTM3U",
                 f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]

    success = False
    for url in URLS:
        content = fetch_playlist(url)
        if content:
            lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#EXTM3U")]
            if FILTER_KEYWORDS:
                lines = [line for line in lines if any(k.lower() in line.lower() for k in FILTER_KEYWORDS)]
            all_lines.extend(lines)
            success = True
            print(f"获取到 {len(lines)} 行数据")
            break

    if not success:
        print("❌ 所有源均失败，使用上一次缓存")
        # 可选：保留旧文件
        if not all_lines:
            sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"🎉 更新完成 → {OUTPUT_FILE} ({len(all_lines)} 行)")

if __name__ == "__main__":
    main()
