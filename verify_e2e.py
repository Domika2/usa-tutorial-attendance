import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def verify_all():
    print("=== Running Updated End-to-End Verification ===")
    
    # 1. Verify HTML pages
    pages = [
        "/",
        "/index.html",
        "/clock-in.html",
        "/clock-out.html",
        "/admin.html",
        "/qr-posters.html",
        "/css/style.css",
        "/js/clock-in.js",
        "/js/clock-out.js",
        "/js/admin.js",
        "/js/qrcode.min.js",
        "/js/qr-posters.js"
    ]
    
    for p in pages:
        req = urllib.request.Request(f"{BASE_URL}{p}")
        with urllib.request.urlopen(req) as resp:
            status = resp.getcode()
            print(f"  [GET {p}] -> Status: {status}")
            assert status == 200

    # 2. Test Staff Login (Director)
    staff_payload = json.dumps({
        "name": "Eleanor Vance",
        "role": "Director"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/staff/login", data=staff_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        staff_data = json.loads(resp.read().decode())
        director_token = staff_data["token"]
        print(f"  [Staff Login - Director] -> OK: {staff_data['staff_name']} ({staff_data['staff_role']}), Token: {director_token}")
        assert staff_data["staff_role"] == "Director"

    # 3. Test Staff Login (Secretary)
    staff_payload_2 = json.dumps({
        "name": "Arthur Dent",
        "role": "Secretary"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/staff/login", data=staff_payload_2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        staff_data_2 = json.loads(resp.read().decode())
        secretary_token = staff_data_2["token"]
        print(f"  [Staff Login - Secretary] -> OK: {staff_data_2['staff_name']} ({staff_data_2['staff_role']})")
        assert staff_data_2["staff_role"] == "Secretary"

    # 4. Student Clock-In with Name, Email, and Branch
    clock_in_1 = json.dumps({
        "name": "Marcus Kane",
        "email": "marcus.kane@example.com",
        "branch": "Main Campus"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", data=clock_in_1, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res1 = json.loads(resp.read().decode())
        assert res1["success"] is True
        print(f"  [Clock-In Student 1] -> OK: {res1['record']['student_name']}, Branch: {res1['record']['branch']}, Time In: {res1['record']['time_in']}")
        assert res1["record"]["branch"] == "Main Campus"

    clock_in_2 = json.dumps({
        "name": "Chloe Decker",
        "email": "chloe.decker@example.com",
        "branch": "Downtown Branch"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-in", data=clock_in_2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res2 = json.loads(resp.read().decode())
        assert res2["success"] is True
        print(f"  [Clock-In Student 2] -> OK: {res2['record']['student_name']}, Branch: {res2['record']['branch']}, Time In: {res2['record']['time_in']}")
        assert res2["record"]["branch"] == "Downtown Branch"

    # 5. Student Clock-Out
    time.sleep(1)
    clock_out_1 = json.dumps({
        "name": "Marcus Kane",
        "email": "marcus.kane@example.com",
        "branch": "Main Campus"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/attendance/clock-out", data=clock_out_1, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res_out = json.loads(resp.read().decode())
        assert res_out["success"] is True
        print(f"  [Clock-Out Student 1] -> OK: {res_out['record']['student_name']}, Time Out: {res_out['record']['time_out']}, Duration: {res_out['record']['duration_formatted']}")

    # 6. Admin Dashboard query with Branch filter
    req = urllib.request.Request(f"{BASE_URL}/api/admin/dashboard?token={director_token}&branch=Downtown+Branch")
    with urllib.request.urlopen(req) as resp:
        dash_data = json.loads(resp.read().decode())
        stats = dash_data["stats"]
        print(f"  [Admin Dashboard (Downtown Branch Filter)] -> Inside: {stats['currently_inside']}, Total Today: {stats['total_today']}")
        assert stats["currently_inside"] >= 1  # Chloe is inside

    # 7. CSV Export Verification with Branch
    req = urllib.request.Request(f"{BASE_URL}/api/admin/export?token={secretary_token}")
    with urllib.request.urlopen(req) as resp:
        csv_text = resp.read().decode("utf-8-sig")
        print(f"  [Admin CSV Export] -> CSV Header row contains: {csv_text.splitlines()[0]}")
        assert "Tutorial Branch" in csv_text
        assert "Downtown Branch" in csv_text
        assert "Main Campus" in csv_text

    print("\n==========================================")
    print(">>> ALL UPDATED REQUIREMENTS VERIFIED! <<<")
    print("==========================================")

if __name__ == "__main__":
    verify_all()
