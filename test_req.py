import urllib.request
import traceback

try:
    req = urllib.request.Request("http://127.0.0.1:5000/index.html")
    with urllib.request.urlopen(req) as resp:
        print("Status:", resp.status)
        print("Length:", len(resp.read()))
except Exception as e:
    traceback.print_exc()
