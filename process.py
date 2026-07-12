def fetch_online_sources():
    """抓取在线源，返回解析后的频道列表"""
    all_channels = []
    for url in ONLINE_URLS:
        try:
            print(f"   📡 正在抓取: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
            
            # 判断是 M3U 还是 TXT
            is_m3u = any(line.startswith('#EXTM3U') for line in lines)
            
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
                        
                        i += 1  # 移到 URL 行
                        if i < len(lines):
                            url_line = lines[i]
                            if url_line.startswith('http://') or url_line.startswith('https://'):
                                if should_keep:
                                    all_channels.append(f"{title},{url_line}")
                    i += 1
            else:
                # TXT 格式解析
                for line in lines:
                    if ',' in line and not line.startswith('#'):
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            title, url = parts[0].strip(), parts[1].strip()
                            if url.startswith('http://') or url.startswith('https://'):
                                if KEEP_KEYWORDS:
                                    if any(k in title for k in KEEP_KEYWORDS):
                                        all_channels.append(line)
                                else:
                                    all_channels.append(line)
            
            print(f"   ✅ 从 {url} 获取到频道（累计 {len(all_channels)} 个）")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
    return all_channels
