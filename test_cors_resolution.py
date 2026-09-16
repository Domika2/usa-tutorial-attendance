import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_cors():
    print("Testing CORS and Cross-Port Connection from Port 5500 (Live Server) to Port 5000...")

    # 1. Test OPTIONS preflight request with Origin: http://127.0.0.1:5500
    req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", method="OPTIONS")
    req.add_header("Origin", "http://127.0.0.1:5500")
    req.add_header("Access-Control-Request-Method", "POST")
    req.add_header("Access-Control-Request-Headers", "Content-Type")

    with urllib.request.urlopen(req) as resp:
        status = resp.getcode()
        allow_origin = resp.headers.get("Access-Control-Allow-Origin")
        allow_methods = resp.headers.get("Access-Control-Allow-Methods")
        print(f"[PASS] OPTIONS /api/attendance/clock-in -> Status: {status}, Origin: {allow_origin}, Methods: {allow_methods}")
        assert status == 200 or status == 204
        assert allow_origin == "*"

    import time
    ts = int(time.time())
    test_user = f"Admin_{ts}"
    # 2. Test POST /api/admin/create-password with Origin: http://127.0.0.1:5500 (Live Server)
    payload = json.dumps({
        "full_name": "Ogbein Dominion",
        "username": test_user,
        "password": "Password123!",
        "role": "Administrator"
    }).encode("utf-8")

    req2 = urllib.request.Request(f"{BASE_URL}/api/admin/create-password", data=payload, method="POST")
    req2.add_header("Origin", "http://127.0.0.1:5500")
    req2.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req2) as resp:
        status = resp.getcode()
        allow_origin = resp.headers.get("Access-Control-Allow-Origin")
        data = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] POST /api/admin/create-password from Live Server -> Status: {status}, Origin: {allow_origin}, Result: {data.get('success')}")
        assert status == 200 or status == 201
        assert data.get("success") is True
        token = data.get("token")

    # 3. Test POST /api/attendance/clock-in with Origin: http://127.0.0.1:5500 (Live Server)
    clock_payload = json.dumps({
        "name": "Ogbein Dominion",
        "email": f"student_{ts}@gmail.com",
        "branch": "Popoola Branch",
        "session_type": "Morning Session",
        "call_number": "+2349067749039",
        "whatsapp_number": "+2349067749039",
        "parent_phone": "+2348012345678"
    }).encode("utf-8")

    req3 = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", data=clock_payload, method="POST")
    req3.add_header("Origin", "http://127.0.0.1:5500")
    req3.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req3) as resp:
        status = resp.getcode()
        allow_origin = resp.headers.get("Access-Control-Allow-Origin")
        data = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] POST /api/attendance/clock-in from Live Server -> Status: {status}, Origin: {allow_origin}, Result: {data.get('success')}")
        assert status == 200
        assert data.get("success") is True

    # 3b. Test repeat clock-in (verifying no sqlite3.Row AttributeError occurs)
    req3b = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", data=clock_payload, method="POST")
    req3b.add_header("Origin", "http://127.0.0.1:5500")
    req3b.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req3b) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[PASS] Repeat Clock-in handled -> Status: 200, message: {data.get('message')}")
    except urllib.error.HTTPError as err:
        assert err.code == 400
        data = json.loads(err.read().decode("utf-8"))
        print(f"[PASS] Repeat Clock-in handled gracefully -> Status: {err.code}, already_clocked_in: {data.get('already_clocked_in')}, message: {data.get('message')}")
        assert data.get("already_clocked_in") is True

    # 4. Test POST /api/admin/login with Origin: http://127.0.0.1:5500 (Live Server)
    login_payload = json.dumps({
        "username": test_user,
        "password": "Password123!"
    }).encode("utf-8")

    req4 = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=login_payload, method="POST")
    req4.add_header("Origin", "http://127.0.0.1:5500")
    req4.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req4) as resp:
        status = resp.getcode()
        allow_origin = resp.headers.get("Access-Control-Allow-Origin")
        data = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] POST /api/admin/login from Live Server -> Status: {status}, Origin: {allow_origin}, Staff: {data.get('staff_name')}")
    # 5. Test POST /api/attendance/clock-out with Origin: http://127.0.0.1:5500 (Live Server)
    out_payload = json.dumps({
        "name": "Ogbein Dominion",
        "email": f"student_{ts}@gmail.com",
        "branch": "Popoola Branch",
        "session_type": "Morning Session"
    }).encode("utf-8")

    req5 = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-out", data=out_payload, method="POST")
    req5.add_header("Origin", "http://127.0.0.1:5500")
    req5.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req5) as resp:
        status = resp.getcode()
        allow_origin = resp.headers.get("Access-Control-Allow-Origin")
        data = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] POST /api/attendance/clock-out from Live Server -> Status: {status}, Origin: {allow_origin}, Message: {data.get('message')}")
        assert status == 200
        assert data.get("success") is True

    print("\n=======================================================")
    print("ALL LIVE SERVER (PORT 5500) TO PORT 5000 TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    test_cors()
