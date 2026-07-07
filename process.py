import requests
import sys
import time
from datetime import datetime

# ================== 配置区 ==================
URLS = [
    "https://0701.tv1288.xyz",
    "https://tv1288.xyz",
]

OUTPUT_FILE = "iptv_playlist.m3u"
MAX_RETRIES = 5
# ===========================================

def fetch_playlist(url):
    # 更强的浏览器伪装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.google.com/",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                print(f"✅ 成功获取 {url}")
                return resp.text
            elif resp.status_code == 403:
                print(f"⚠️ 第 {attempt+1} 次 403 拒绝 {url}")
            else:
                print(f"⚠️ 第 {attempt+1} 次失败 {url} 状态码: {resp.status_code}")
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次异常 {url}: {e}")
        
        time.sleep(3 * (attempt + 1))  # 更长等待
    
    print(f"❌ 最终失败: {url}")
    return None

def main():
    all_lines = [f"#EXTM3U",
                 f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                 f"# Source: {URLS[0]}"]

    success = False
    for url in URLS:
        content = fetch_playlist(url)
        if content and len(content.strip()) > 100:   # 确保内容有效
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            all_lines.extend(lines)
            success = True
            print(f"✅ 获取有效数据 {len(lines)} 行")
            break

    if not success:
        print("❌ 所有源均失败，保留上一次缓存")
        # 如果想强制退出可取消注释下面一行
        # sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"🎉 更新完成 → {OUTPUT_FILE} ({len(all_lines)} 行)")

if __name__ == "__main__":
    main()
