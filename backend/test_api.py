import urllib.request
import urllib.parse
import json

# Login
data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8000/api/token", data=data)
try:
    response = urllib.request.urlopen(req)
    token = json.loads(response.read().decode('utf-8'))["access_token"]
    print("Token:", token)
except urllib.error.HTTPError as e:
    print("Login Failed:", e.code)
    print(e.read().decode('utf-8'))
    exit()

# Get species
req2 = urllib.request.Request("http://127.0.0.1:8000/api/species")
req2.add_header("Authorization", f"Bearer {token}")
try:
    res2 = urllib.request.urlopen(req2)
    print(res2.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Species Failed:", e.code)
    print(e.read().decode('utf-8'))