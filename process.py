import requests
import sys
import time
from datetime import datetime

# ================== 配置区 ==================
URLS = [
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://iptv-org.github.io/iptv/countries/cn.m3u",           # 中国大陆
    "https://iptv-org.github.io/iptv/countries/hk.m3u",           # 香港
    "https://iptv-org.github.io/iptv/countries/tw.m3u",           # 台湾
    "https://raw.githubusercontent.com/Ftindy/IPTV-URL/main/IPTV.m3u",
]

# 保留的关键词（可继续添加）
KEEP_KEYWORDS = [
    "CCTV", "央视", "卫视", "湖南", "江苏", "浙江", "北京", "上海",
    "东方", "凤凰", "凤凰资讯", "凤凰香港", "TVB", "有线", "Now", 
    "台湾", "中天", "东森", "民视", "台视", "华视", "新闻"
]

OUTPUT_FILE = "iptv_playlist.m3u"
# ===========================================

def fetch_playlist(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for attempt in range(4):
        try:
            resp = requests.get(url, headers=headers, timeout=25)
            if resp.status_code == 200 and len(resp.text) > 800:
                print(f"✅ 成功 {url}")
                return resp.text
        except Exception as e:
            print(f"⚠️ 失败 {url}: {e}")
        time.sleep(2)
    return None

def filter_channels(lines):
    """只保留包含关键词的频道"""
    filtered = []
    for line in lines:
        if any(kw in line for kw in KEEP_KEYWORDS):
            filtered.append(line)
    return filtered

def main():
    all_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", 
                 "# 中国大陆 + 港台新闻频道"]

    total = 0
    for url in URLS:
        content = fetch_playlist(url)
        if content:
            lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#EXTM3U")]
            filtered = filter_channels(lines)
            all_lines.extend(filtered)
            total += len(filtered)
            print(f"   从 {url} 保留 {len(filtered)} 个频道")
            # 为了避免文件过大，成功获取主要源后可提前退出
            if "cn.m3u" in url or "IPTV.m3u" in url:
                break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"\n🎉 完成！共保留 {total} 个频道 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
