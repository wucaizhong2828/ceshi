import requests
import sys
import time
from datetime import datetime

# ================== 配置区 ==================
URLS = [
    "https://0701.tv1288.xyz",
    # "https://tv1288.xyz",   # 备用域名，确认存在后再启用
    # 可以继续添加其他稳定源
]

# 过滤关键词：包含这些词的频道会被删除（留空则不过滤）
FILTER_KEYWORDS = ["加群", "TG", "t.me", "关注", "广告", "备用", "防失联", "微信", "QQ", "最新"]

OUTPUT_FILE = "iptv_playlist.m3u"
MAX_RETRIES = 5
# ===========================================

def fetch_playlist(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://0701.tv1288.xyz/",
    }
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            content = resp.text
            
            # 检查是否返回了 HTML（被拦截）
            if '<!DOCTYPE html>' in content or '<html' in content.lower():
                print(f"⚠️ 第 {attempt+1} 次尝试 {url}: 返回 HTML，可能被拦截")
                time.sleep(2 ** attempt)
                continue
            
            print(f"✅ 成功获取 {url} ({len(content)} 字符)")
            return content
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次尝试失败 {url}: {e}")
            time.sleep(2 ** attempt)
    
    print(f"❌ 最终失败: {url}")
    return None

def main():
    print(f"[{datetime.now()}] 🚀 开始更新直播源...")
    
    all_lines = [
        "#EXTM3U",
        f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ]
    
    success = False
    for url in URLS:
        content = fetch_playlist(url)
        if content:
            lines = [
                line.strip() for line in content.splitlines() 
                if line.strip() and not line.strip().startswith("#EXTM3U")
            ]
            
            # 过滤关键词
            if FILTER_KEYWORDS:
                original_count = len(lines)
                lines = [
                    line for line in lines 
                    if not any(kw.lower() in line.lower() for kw in FILTER_KEYWORDS)
                ]
                filtered_count = original_count - len(lines)
                if filtered_count > 0:
                    print(f"   🚫 过滤了 {filtered_count} 个频道")
            
            all_lines.extend(lines)
            success = True
            print(f"   📺 获取到 {len(lines)} 个频道")
            break
    
    if not success:
        print("❌ 所有源均失败")
        sys.exit(1)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")
    
    print(f"🎉 更新完成 → {OUTPUT_FILE} ({len(all_lines)} 行)")

if __name__ == "__main__":
    main()
