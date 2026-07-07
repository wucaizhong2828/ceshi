import requests
from datetime import datetime

print("开始生成直播源...")

# ================== 配置区 ==================
# 手动维护的精品源（本地文件）
LOCAL_SOURCES = [
    "tv1.txt",      # 格式：频道名,地址
    # "tv1.m3u",    # 也可以加 M3U 格式的文件
]

# 自动抓取的在线源
ONLINE_URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

# 保留关键词（频道名包含这些才保留，留空则全部保留）
KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻"]

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

def parse_m3u_content(content):
    """解析 M3U 格式，提取频道名和地址"""
    lines = content.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('#EXTINF'):
            title = extract_title(line)
            i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                if url_line.startswith('http://') or url_line.startswith('https://'):
                    result.append(f"{title},{url_line}")
        i += 1
    return result

def load_local_sources():
    """加载本地手动维护的源"""
    all_channels = []
    for filename in LOCAL_SOURCES:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if filename.endswith('.m3u'):
                    channels = parse_m3u_content(content)
                else:
                    channels = parse_txt_content(content)
                print(f"   📂 从 {filename} 加载了 {len(channels)} 个频道")
                all_channels.extend(channels)
        except FileNotFoundError:
            print(f"   ⚠️ 文件 {filename} 不存在，跳过")
        except Exception as e:
            print(f"   ❌ 读取 {filename} 失败: {e}")
    return all_channels

def fetch_online_sources():
    """抓取在线源"""
    all_lines = []
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            all_lines.extend(lines)
            print(f"   ✅ 从 {url} 获取到 {len(lines)} 行")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_lines

def merge_channels(txt_channels, m3u_lines):
    """
    txt_channels: 从本地加载的 TXT 格式频道列表 ['频道名,地址', ...]
    m3u_lines: 从在线源抓取的原始行（包含 #EXTINF 和 URL）
    """
    # 收集已存在的频道名（用于去重）
    existing_names = set()
    for ch in txt_channels:
        if ',' in ch:
            name = ch.split(',')[0].strip()
            existing_names.add(name)
    
    # 解析在线源，只添加不重复的频道
    added = 0
    i = 0
    while i < len(m3u_lines):
        line = m3u_lines[i].strip()
        if not line:
            i += 1
            continue
        
        if line.startswith('#EXTINF'):
            title = extract_title(line)
            # 检查是否包含保留关键词
            if KEEP_KEYWORDS and not any(k in line for k in KEEP_KEYWORDS):
                i += 1
                if i < len(m3u_lines) and (m3u_lines[i].strip().startswith('http://') or m3u_lines[i].strip().startswith('https://')):
                    i += 1
                continue
            
            # 检查是否已存在
            if title not in existing_names:
                # 获取 URL
                i += 1
                if i < len(m3u_lines):
                    url_line = m3u_lines[i].strip()
                    if url_line.startswith('http://') or url_line.startswith('https://'):
                        txt_channels.append(f"{title},{url_line}")
                        existing_names.add(title)
                        added += 1
            else:
                # 跳过已存在的
                i += 1
                if i < len(m3u_lines) and (m3u_lines[i].strip().startswith('http://') or m3u_lines[i].strip().startswith('https://')):
                    i += 1
        else:
            i += 1
    
    print(f"   🔄 从在线源补充了 {added} 个新频道")
    return txt_channels

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
    
    # 1. 加载本地手动源
    print("\n📂 加载手动维护的源...")
    txt_channels = load_local_sources()
    
    # 2. 抓取在线源
    print("\n📡 抓取在线源...")
    online_m3u_lines = fetch_online_sources()
    
    # 3. 合并（去重）
    print("\n🔄 合并频道（本地优先，去重）...")
    merged = merge_channels(txt_channels, online_m3u_lines)
    
    # 4. 保存 TXT
    txt_content = "\n".join(merged)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content + "\n")
    
    # 5. 生成并保存 M3U
    m3u_content = generate_m3u(txt_content)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content + "\n")
    
    print(f"\n🎉 完成！")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(merged)} 个频道)")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(m3u_content.splitlines())} 行)")

if __name__ == "__main__":
    main()
