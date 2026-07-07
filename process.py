from datetime import datetime

print("测试脚本开始运行...")

with open("iptv_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write(f"# 测试生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    f.write("# CCTV1,http://example.com/test.m3u8\n")

print("测试文件已生成！")
print("iptv_playlist.m3u 创建成功")
