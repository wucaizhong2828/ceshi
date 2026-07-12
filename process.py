import requests
from datetime import datetime

print("开始生成直播源...")

# ================== 配置区 ==================
# 手动维护的精选源（只需要这一个文件）
LOCAL_SOURCES = [
    "tv1.txt",      # 格式：频道名,地址
]

# 自动抓取的在线源（支持 TXT 和 M3U 两种格式）
ONLINE_URLS = [
    "https://zb.7778.uk/",  # TXT 格式
    "https://raw.githubusercontent.com/wucaizhong2828/ceshi/refs/heads/main/tv1.txt",  # TXT 格式
]

# 保留关键词（频道名包含这些才保留，留空则全部保留）
KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻", "北京", "东方", "江苏", "浙江", "湖南", "湖北", "广东", "广西", "黑龙江", "海南", "重庆", "深圳"]

OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"
# ===========================================

def extract_title(line):
    """从 #EXTINF 行中提取频道名"""
    if ',' in line:
        title = line.split(',')[-1].strip()
        return title
    return "未知频道"

def parse_txt_content(content):
    """解析 TXT 格式（频道名,地址）"""
    lines = content.splitlines()
    result = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ',' in line:
            result.append(line)
    return result

def load_local_sources():
    """加载本地手动维护的源"""
    all_channels = []
    for filename in LOCAL_SOURCES:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                channels = parse_txt_content(content)
                print(f"   📂 从 {filename} 加载了 {len(channels)} 个频道")
                all_channels.extend(channels)
        except FileNotFoundError:
            print(f"   ⚠️ 文件 {filename} 不存在，跳过")
        except Exception as e:
            print(f"   ❌ 读取 {filename} 失败: {e}")
    return all_channels

def fetch_online_sources():
    """抓取在线源，返回解析后的频道列表（支持 TXT 和 M3U 两种格式）"""
    all_channels = []
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            
            # 检测格式：是否包含 #EXTM3U 或 #EXTINF
            is_m3u = any(line.startswith('#EXTM3U') for line in lines)
            has_extinf = any(line.startswith('#EXTINF') for line in lines)
            
            if is_m3u or has_extinf:
                # ===== M3U 格式解析 =====
                print(f"   📋 检测到 M3U 格式")
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if not line:
                        i += 1
                        continue
                    if line.startswith('#EXTINF'):
                        title = extract_title(line)
                        # 检查保留关键词
                        if KEEP_KEYWORDS and not any(k in title for k in KEEP_KEYWORDS):
                            i += 1
                            if i < len(lines) and (lines[i].startswith('http://') or lines[i].startswith('https://')):
                                i += 1
                            continue
                        i += 1
                        if i < len(lines):
                            url_line = lines[i]
                            if url_line.startswith('http://') or url_line.startswith('https://'):
                                all_channels.append(f"{title},{url_line}")
                    i += 1
            else:
                # ===== TXT 格式解析（频道名,地址） =====
                print(f"   📋 检测到 TXT 格式")
                for line in lines:
                    if ',' in line and not line.startswith('#'):
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            title, url_addr = parts[0].strip(), parts[1].strip()
                            if url_addr.startswith('http://') or url_addr.startswith('https://'):
                                # 检查保留关键词
                                if KEEP_KEYWORDS:
                                    if any(k in title for k in KEEP_KEYWORDS):
                                        all_channels.append(f"{title},{url_addr}")
                                else:
                                    all_channels.append(f"{title},{url_addr}")
            
            print(f"   ✅ 从 {url} 获取了频道（累计 {len(all_channels)} 个）")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_channels

def merge_channels(local_channels, online_channels):
    """合并频道：本地优先，去重"""
    channel_map = {}
    
    # 先添加本地频道
    for ch in local_channels:
        if ',' in ch:
            name = ch.split(',')[0].strip()
            channel_map[name] = ch
            print(f"   📌 本地: {name}")
    
    # 再添加在线频道（不重复的）
    added = 0
    for ch in online_channels:
        if ',' in ch:
            name = ch.split(',')[0].strip()
            if name not in channel_map:
                channel_map[name] = ch
                added += 1
    
    print(f"   🔄 从在线源补充了 {added} 个新频道")
    return list(channel_map.values())

def generate_m3u(txt_content):
    """从 TXT 格式生成 M3U 格式"""
    lines = txt_content.splitlines()
    m3u_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
    current_group = "默认频道"
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if url.startswith('http://') or url.startswith('https://'):
                    m3u_lines.append(f'#EXTINF:-1 group-title="{current_group}",{title}')
                    m3u_lines.append(url)
    
    return '\n'.join(m3u_lines)

def main():
    print("🚀 开始生成直播源...")
    
    # 1. 加载本地精选源
    print("\n📂 加载精选源...")
    local_channels = load_local_sources()
    
    # 2. 抓取在线源
    print("\n📡 抓取在线源...")
    online_channels = fetch_online_sources()
    
    # 3. 合并（本地优先，去重）
    print("\n🔄 合并频道...")
    merged = merge_channels(local_channels, online_channels)
    
    # 4. 保存 TXT 格式
    txt_content = "\n".join(merged)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")
    
    # 5. 生成并保存 M3U 格式
    m3u_content = generate_m3u(txt_content)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")
    
    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(merged)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
