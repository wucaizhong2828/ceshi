import requests
from datetime import datetime

print("开始生成直播源...")

# ================== 配置区 ==================
URLS = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
]

# 只保留包含这些关键词的频道（留空则全部保留）
KEEP_KEYWORDS = ["CCTV", "央视", "卫视", "凤凰", "TVB", "中天", "东森", "新闻"]

# ==========================================
# 🆕 画质过滤：只保留高清（1080P/HD/FHD），去除低画质（720P/SD等）
# 如果想保留所有画质，请将 ENABLE_QUALITY_FILTER 改为 False
# ==========================================
ENABLE_QUALITY_FILTER = True  # True=开启高清过滤，False=关闭

# 高清画质关键词（包含这些的保留）
HD_KEYWORDS = ["1080p", "1080P", "HD", "FHD", "高清"]

# 低画质关键词（包含这些的剔除）
LOW_QUALITY_KEYWORDS = ["720p", "720P", "SD", "标清", "低清"]

OUTPUT_M3U = "tv.m3u"
OUTPUT_TXT = "tv.txt"
# ===========================================

# ==========================================
# 从 #EXTINF 行提取频道名
# ==========================================
def extract_title(line):
    """从 #EXTINF 行中提取频道名"""
    if ',' in line:
        title = line.split(',')[-1].strip()
        return title
    return "未知频道"

# ==========================================
# 🆕 检查频道是否为高清（过滤低画质）
# ==========================================
def is_hd_quality(line):
    """检查 #EXTINF 行是否为高清画质"""
    # 如果关闭过滤，全部保留
    if not ENABLE_QUALITY_FILTER:
        return True
    
    # 检查是否包含低画质关键词（包含则剔除）
    for kw in LOW_QUALITY_KEYWORDS:
        if kw in line:
            return False
    
    # 检查是否包含高清关键词（包含则保留）
    for kw in HD_KEYWORDS:
        if kw in line:
            return True
    
    # 默认：如果既没有高清也没有低清标识，默认保留（不误杀）
    return True

# ==========================================
# 主流程
# ==========================================
def main():
    all_m3u_lines = ["#EXTM3U", f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
    txt_lines = ["# IPTV 直播源 - 生成时间: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')]
    
    total_matched = 0
    total_hd = 0
    total_filtered = 0
    
    for url in URLS:
        try:
            print(f"📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            
            matched = 0
            hd_count = 0
            filtered_count = 0
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # 跳过原有的 #EXTM3U 头
                if line.startswith("#EXTM3U"):
                    i += 1
                    continue
                
                # 处理 #EXTINF 行
                if line.startswith('#EXTINF'):
                    # 检查是否包含保留关键词
                    if not KEEP_KEYWORDS or any(k in line for k in KEEP_KEYWORDS):
                        # 🆕 检查画质（去除低画质）
                        if is_hd_quality(line):
                            # 添加到 M3U
                            all_m3u_lines.append(line)
                            matched += 1
                            hd_count += 1
                            
                            # 提取频道名
                            title = extract_title(line)
                            
                            # 下一行应该是 URL
                            i += 1
                            if i < len(lines):
                                url_line = lines[i]
                                if url_line.startswith('http://') or url_line.startswith('https://'):
                                    all_m3u_lines.append(url_line)
                                    # 添加到 TXT（频道名,地址）
                                    txt_lines.append(f"{title},{url_line}")
                                else:
                                    # 如果下一行不是 URL，单独处理
                                    all_m3u_lines.append(url_line)
                            i += 1
                        else:
                            # 🆕 低画质，跳过
                            filtered_count += 1
                            i += 1
                            if i < len(lines) and (lines[i].startswith('http://') or lines[i].startswith('https://')):
                                i += 1
                    else:
                        # 不保留此频道，但仍需跳过 URL 行
                        i += 1
                        if i < len(lines) and (lines[i].startswith('http://') or lines[i].startswith('https://')):
                            i += 1
                    continue
                
                # 其他行（如注释）直接保留
                if not line.startswith('#'):
                    all_m3u_lines.append(line)
                i += 1
            
            print(f"   ✅ 匹配到 {matched} 个频道，其中高清 {hd_count} 个，过滤低画质 {filtered_count} 个")
            total_matched += matched
            total_hd += hd_count
            total_filtered += filtered_count
            
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")

    # 保存 M3U
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("\n".join(all_m3u_lines) + "\n")

    # 保存 TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")

    print(f"\n🎉 完成！")
    print(f"   📄 m3u 文件: {OUTPUT_M3U} ({len(all_m3u_lines)} 行)")
    print(f"   📄 txt 文件: {OUTPUT_TXT} ({len(txt_lines)-1} 个高清频道)")
    print(f"   📊 总计: 匹配 {total_matched} 个频道，保留高清 {total_hd} 个，过滤低画质 {total_filtered} 个")

if __name__ == "__main__":
    main()
