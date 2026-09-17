import os
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

import urllib.request
import json
import time

urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("Testing USA Tutorial Centre Attendance API...")
    
    # 1. Test Server Info (Name and Logo)
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/server-info")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("1. Server Info OK:", data["centre_name"], "on port", data["port"])
            assert data["centre_name"] == "USA Tutorial Centre", f"Expected 'USA Tutorial Centre', got {data['centre_name']}"
    except Exception as e:
        print("Server info failed:", e)
        return False

    # 2. Test Logo Static Asset
    try:
        req = urllib.request.Request(f"{BASE_URL}/images/logo.png")
        with urllib.request.urlopen(req) as resp:
            status = resp.getcode()
            content_len = len(resp.read())
            print(f"2. Logo Asset OK: Status {status}, Length {content_len} bytes")
            assert status == 200
            assert content_len > 1000
    except Exception as e:
        print("Logo static file failed:", e)
        return False

    # 3. Test Admin Auth Status
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/admin/auth-status")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"3. Admin Auth Status OK: has_admin={data.get('has_admin')}, centre={data.get('centre_name')}")
            assert data["centre_name"] == "USA Tutorial Centre"
    except Exception as e:
        print("Auth status failed:", e)
        return False

    # 4. Test Create Admin Password
    admin_user = f"admin_test_{int(time.time())}"
    admin_pass = "SecurePass123!"
    try:
        payload = json.dumps({
            "full_name": "Test Principal",
            "username": admin_user,
            "password": admin_pass,
            "role": "Director"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/admin/create-password", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            token = data["token"]
            print(f"4. Create Admin Password OK: {data['message']}, Token: {token[:15]}...")
            assert data["success"] is True
    except Exception as e:
        print("Create admin password failed:", e)
        return False

    # 5. Test Login with Wrong Password (expect 401)
    try:
        bad_payload = json.dumps({
            "username": admin_user,
            "password": "WrongPassword!"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=bad_payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                print("5. Expected 401 but got:", resp.getcode())
                return False
        except urllib.error.HTTPError as he:
            assert he.code == 401
            print("5. Invalid Password Prevention OK: 401 Unauthorized returned")
    except Exception as e:
        print("Wrong password test failed:", e)
        return False

    # 6. Test Login with Correct Password
    try:
        login_payload = json.dumps({
            "username": admin_user,
            "password": admin_pass
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=login_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            token = data["token"]
            print(f"6. Admin Password Login OK: Welcome {data['staff_name']} ({data['staff_role']})")
            assert data["success"] is True
    except Exception as e:
        print("Admin login with password failed:", e)
        return False

    # 7. Test Change Admin Password
    new_pass = "BrandNewPass456!"
    try:
        change_payload = json.dumps({
            "username": admin_user,
            "old_password": admin_pass,
            "new_password": new_pass
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/admin/change-password",
            data=change_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"7. Change Password OK: {data['message']}")
            assert data["success"] is True
    except Exception as e:
        print("Change password failed:", e)
        return False

    # 8. Test Login with New Password
    try:
        re_login_payload = json.dumps({
            "username": admin_user,
            "password": new_pass
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=re_login_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            new_token = data["token"]
            print(f"8. New Password Login OK. Token: {new_token[:15]}...")
            assert data["success"] is True
    except Exception as e:
        print("Login with updated password failed:", e)
        return False

    # 9. Test Student Clock-In with USA Tutorial Centre
    try:
        payload = json.dumps({
            "name": "David Miller",
            "email": "david.miller@example.com",
            "branch": "Main Campus",
            "notes": "Physics Class"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"9. Student Clock-In OK: {data['record']['student_name']} at {data['record']['time_in']}")
            assert data["success"] is True
    except Exception as e:
        print("Clock-In failed:", e)
        return False

    # 10. Test Student Clock-Out
    time.sleep(1)
    try:
        payload = json.dumps({
            "name": "David Miller",
            "email": "david.miller@example.com",
            "branch": "Main Campus"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-out", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"10. Student Clock-Out OK: Time Out {data['record']['time_out']}, Duration: {data['record']['duration_formatted']}")
            assert data["success"] is True
    except Exception as e:
        print("Clock-Out failed:", e)
        return False

    # 11. Test Admin Dashboard Stats
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/admin/dashboard?token={new_token}")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"11. Admin Dashboard OK: Today total={data['stats']['total_today']}, Inside={data['stats']['currently_inside']}")
            assert data["stats"]["total_today"] >= 1
    except Exception as e:
        print("Admin dashboard query failed:", e)
        return False

    print("\n>>> ALL USA TUTORIAL CENTRE TESTS PASSED SUCCESSFULLY! <<<")
    return True

if __name__ == "__main__":
    test_api()
