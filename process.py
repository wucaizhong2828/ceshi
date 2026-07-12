def fetch_online_sources():
    """抓取在线源，返回解析后的频道列表"""
    all_channels = []
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            
            # 判断是 M3U 还是 TXT（更全面的检测）
            is_m3u = any(line.startswith('#EXTM3U') for line in lines) or \
                     any(line.startswith('#EXTINF') for line in lines)
            
            if is_m3u:
                # M3U 解析
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if not line:
                        i += 1
                        continue
                    
                    if line.startswith('#EXTINF'):
                        title = extract_title(line)
                        # 检查保留关键词
                        should_keep = True
                        if KEEP_KEYWORDS:
                            should_keep = any(k in title for k in KEEP_KEYWORDS)
                        
                        i += 1  # 移动到下一行（应该是 URL）
                        if i < len(lines):
                            url_line = lines[i]
                            if url_line.startswith('http://') or url_line.startswith('https://'):
                                if should_keep:
                                    all_channels.append(f"{title},{url_line}")
                            # 注意：这里不再额外 i += 1，因为循环末尾会 +1
                    # 如果不是 #EXTINF 行，直接跳过
                    i += 1
            else:
                # TXT 格式解析
                for line in lines:
                    if ',' in line and not line.startswith('#'):
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            title, url = parts[0].strip(), parts[1].strip()
                            if url.startswith('http://') or url.startswith('https://'):
                                should_keep = True
                                if KEEP_KEYWORDS:
                                    should_keep = any(k in title for k in KEEP_KEYWORDS)
                                if should_keep:
                                    all_channels.append(f"{title},{url}")  # 统一格式
            
            print(f"   ✅ 从 {url} 获取到频道（累计 {len(all_channels)} 个）")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_channels
