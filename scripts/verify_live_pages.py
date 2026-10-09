import urllib.request
import re

for pid in [41, 42, 43, 44, 39, 40]:
    url = f"http://127.0.0.1:8000/product/{pid}/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            c_links = re.findall(r'res\.cloudinary\.com/[^\s"\'<>]+', html)
            title = re.search(r'<title>(.*?)</title>', html)
            t = title.group(1).strip() if title else 'No title'
            print(f"Product {pid:<2} -> HTTP {resp.status} | Title: {t:<40} | Cloudinary links: {len(c_links)}")
    except Exception as e:
        print(f"Product {pid:<2} -> Error: {e}")
