import os
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

import urllib.request
import urllib.parse
import urllib.error
import json
import time

# Install opener to completely bypass Windows system proxy for localhost tests
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

BASE_URL = "http://127.0.0.1:5000"

def test_static_qr_system():
    print("==================================================")
    print("Testing Permanent 24/7 QR Code & Static Validation")
    print("==================================================")

    # 1. Test /api/admin/qr-info
    req = urllib.request.Request(f"{BASE_URL}/api/admin/qr-info")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("1. /api/admin/qr-info returned:")
        print("   - Token:", data.get("token"))
        print("   - Is Permanent:", data.get("is_permanent"))
        print("   - Validity:", data.get("validity"))
        print("   - Direct Clock-In URL:", data.get("direct_clock_in_url"))
        print("   - Popoola URL:", data.get("popoola_url"))
        assert data.get("token") == "PERMANENT_SESSION_KEY"
        assert data.get("is_permanent") is True
        assert "attendance_token=PERMANENT_SESSION_KEY" in data.get("direct_clock_in_url")
        print("[PASS] Permanent QR info verified.")

    # 2. Test Clock-In with Permanent Static Token
    clock_in_email = f"student_static_{int(time.time())}@example.com"
    payload = {
        "name": "Static QR Student",
        "email": clock_in_email,
        "branch": "Popoola Branch",
        "call_number": "08012345678",
        "whatsapp_number": "08012345678",
        "parent_phone": "08098765432",
        "session_type": "Morning Session",
        "attendance_token": "PERMANENT_SESSION_KEY"
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/attendance/clock-in",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2) as resp2:
        res2 = json.loads(resp2.read().decode())
        assert res2["success"] is True
        print(f"[PASS] Clock-in with permanent static token succeeded for: {res2['record']['student_name']}")

    # 3. Test Clock-Out with Permanent Static Token
    payload_out = {
        "name": "Static QR Student",
        "email": clock_in_email,
        "branch": "Popoola Branch",
        "session_type": "Morning Session",
        "attendance_token": "PERMANENT_SESSION_KEY"
    }
    req3 = urllib.request.Request(
        f"{BASE_URL}/api/attendance/clock-out",
        data=json.dumps(payload_out).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as resp3:
        res3 = json.loads(resp3.read().decode())
        assert res3["success"] is True
        print(f"[PASS] Clock-out with permanent static token succeeded for: {res3['record']['student_name']}")

    # 4. Test Clock-In with Invalid/Fake Token (Should be rejected with 400)
    bad_payload = {
        "name": "Intruder",
        "email": "intruder@example.com",
        "branch": "Popoola Branch",
        "call_number": "08011112222",
        "parent_phone": "08033334444",
        "attendance_token": "INVALID_TEMPORARY_EXPIRED_KEY"
    }
    req4 = urllib.request.Request(
        f"{BASE_URL}/api/attendance/clock-in",
        data=json.dumps(bad_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req4)
        raise AssertionError("Expected 400 for invalid attendance_token")
    except urllib.error.HTTPError as err:
        assert err.code == 400
        body = json.loads(err.read().decode())
        print(f"[PASS] Invalid token properly rejected with 400: {body.get('message')}")

    # 5. Test Backward Compatibility: Clock-In without token
    compat_email = f"student_compat_{int(time.time())}@example.com"
    compat_payload = {
        "name": "Direct Portal Student",
        "email": compat_email,
        "branch": "Kilimanjaro Branch",
        "call_number": "08055556666",
        "whatsapp_number": "08055556666",
        "parent_phone": "08077778888",
        "session_type": "Evening Session"
    }
    req5 = urllib.request.Request(
        f"{BASE_URL}/api/attendance/clock-in",
        data=json.dumps(compat_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req5) as resp5:
        res5 = json.loads(resp5.read().decode())
        assert res5["success"] is True
        print("[PASS] Backwards-compatible clock-in without token succeeded.")

    print("\n==================================================")
    print("ALL STATIC 24/7 QR TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_static_qr_system()
