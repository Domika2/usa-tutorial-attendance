import http.server
import socketserver
import os
import json
import urllib.parse
import mimetypes
import socket
import io
import csv
import sys
import time
from datetime import datetime
import database

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PORT = int(os.environ.get("PORT", 5000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

DATA_VERSION = 1
LAST_DATA_UPDATE = time.time()

def notify_data_change():
    global DATA_VERSION, LAST_DATA_UPDATE
    DATA_VERSION += 1
    LAST_DATA_UPDATE = time.time()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

class AttendanceHandler(http.server.BaseHTTPRequestHandler):

    def get_base_url(self):
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        if render_url:
            return render_url.rstrip("/")
        host_header = self.headers.get("Host")
        proto = self.headers.get("X-Forwarded-Proto", "http")
        if host_header and not host_header.startswith("localhost") and not host_header.startswith("127.0.0.1"):
            return f"{proto}://{host_header}".rstrip("/")
        ip = get_local_ip()
        return f"http://{ip}:{PORT}".rstrip("/")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def send_json(self, data, status_code=200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def parse_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        except Exception:
            return {}

    def get_auth_staff(self, query_params=None):
        auth_header = self.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1].strip()
        elif query_params and "token" in query_params:
            token = query_params["token"][0]

        return database.verify_staff_session(token)

    def serve_static(self, path):
        clean_path = path.lstrip("/").replace("/", os.sep)
        if not clean_path or clean_path == "index":
            clean_path = "index.html"
        elif clean_path in ["clock-in", "clockin"]:
            clean_path = "clock-in.html"
        elif clean_path in ["clock-out", "clockout"]:
            clean_path = "clock-out.html"
        elif clean_path == "admin":
            clean_path = "admin.html"
        elif clean_path in ["posters", "qr-posters"]:
            clean_path = "qr-posters.html"

        file_path = os.path.normpath(os.path.join(PUBLIC_DIR, clean_path))
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_json({"error": "File not found"}, 404)
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            if file_path.endswith(".css"):
                mime_type = "text/css"
            elif file_path.endswith(".js"):
                mime_type = "application/javascript"
            else:
                mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type or "json" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_GET(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # API Endpoints
            if path.startswith("/api/"):
                if path == "/api/server-info":
                    base_url = self.get_base_url()
                    ip = get_local_ip()
                    centre_name = database.get_config("centre_name", "USA Tutorial Centre")
                    qr_info = database.get_qr_info()
                    self.send_json({
                        "ip": ip,
                        "port": PORT,
                        "host": base_url,
                        "local_host": f"http://localhost:{PORT}",
                        "main_portal_url": f"{base_url}/index.html",
                        "clock_in_url": f"{base_url}/clock-in.html",
                        "clock_out_url": f"{base_url}/clock-out.html",
                        "centre_name": centre_name,
                        "branches": ["Popoola Branch", "Kilimanjaro Branch"],
                        "default_branch": "Popoola Branch",
                        "sessions": ["Morning Session (9am-2:30pm)", "Evening Session (3pm-7pm)", "Both Sessions"],
                        "qr_info": qr_info
                    })
                    return

                elif path == "/api/admin/auth-status":
                    has_admin = database.admin_exists()
                    centre_name = database.get_config("centre_name", "USA Tutorial Centre")
                    self.send_json({
                        "has_admin": has_admin,
                        "centre_name": centre_name
                    })
                    return

                elif path == "/api/attendance/status":
                    email = query_params.get("email", [""])[0]
                    status_record = database.get_student_status(email)
                    self.send_json({"record": status_record})
                    return

                elif path == "/api/admin/dashboard":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access. Please login as staff."}, 401)
                        return
                    branch = query_params.get("branch", ["ALL"])[0]
                    stats = database.get_dashboard_stats(branch)
                    today_records = database.get_today_records(branch)
                    absentee_alerts = database.get_absentee_alerts(branch)
                    qr_info = database.get_qr_info()
                    self.send_json({
                        "staff": staff,
                        "stats": stats,
                        "today_records": today_records,
                        "absentee_alerts": absentee_alerts,
                        "qr_info": qr_info,
                        "branches": ["Popoola Branch", "Kilimanjaro Branch"]
                    })
                    return

                elif path == "/api/admin/absentee-alerts":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access"}, 401)
                        return
                    branch = query_params.get("branch", ["ALL"])[0]
                    alerts = database.get_absentee_alerts(branch)
                    self.send_json({"alerts": alerts, "count": len(alerts)})
                    return

                elif path == "/api/admin/qr-info":
                    qr_info = database.get_qr_info()
                    base_url = self.get_base_url()
                    qr_info["base_url"] = base_url
                    qr_info["popoola_url"] = f"{base_url}/index.html?branch=Popoola+Branch&token={qr_info['token']}"
                    qr_info["kilimanjaro_url"] = f"{base_url}/index.html?branch=Kilimanjaro+Branch&token={qr_info['token']}"
                    self.send_json(qr_info)
                    return

                elif path == "/api/admin/students":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access"}, 401)
                        return
                    branch = query_params.get("branch", ["ALL"])[0]
                    students = database.get_all_students(branch)
                    self.send_json({"students": students, "count": len(students)})
                    return

                elif path == "/api/admin/check-updates":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access"}, 401)
                        return
                    try:
                        client_version = int(query_params.get("version", [0])[0])
                    except (ValueError, TypeError):
                        client_version = 0
                    
                    self.send_json({
                        "updated": client_version < DATA_VERSION,
                        "version": DATA_VERSION,
                        "timestamp": LAST_DATA_UPDATE
                    })
                    return

                elif path == "/api/admin/records":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access"}, 401)
                        return
                    search = query_params.get("search", [""])[0]
                    date_filter = query_params.get("date", [""])[0]
                    status_filter = query_params.get("status", ["ALL"])[0]
                    branch_filter = query_params.get("branch", ["ALL"])[0]
                    records = database.get_all_records(search, date_filter, status_filter, branch_filter)
                    self.send_json({"records": records, "count": len(records)})
                    return

                elif path == "/api/admin/export":
                    staff = self.get_auth_staff(query_params)
                    if not staff:
                        self.send_json({"error": "Unauthorized access"}, 401)
                        return
                    
                    search = query_params.get("search", [""])[0]
                    date_filter = query_params.get("date", [""])[0]
                    status_filter = query_params.get("status", ["ALL"])[0]
                    branch_filter = query_params.get("branch", ["ALL"])[0]
                    records = database.get_all_records(search, date_filter, status_filter, branch_filter)
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        "ID", "Student Name", "Email", "Tutorial Branch", "Session",
                        "Call Number", "WhatsApp Number", "Parent Phone",
                        "Date", "Time In", "Time Out", "Duration", "Status", "Notes", "Recorded At"
                    ])
                    for r in records:
                        writer.writerow([
                            r["id"],
                            r["student_name"],
                            r["student_email"],
                            r.get("branch", "Popoola Branch"),
                            r.get("session_type", "Morning Session"),
                            r.get("call_number", ""),
                            r.get("whatsapp_number", ""),
                            r.get("parent_phone", ""),
                            r["date"],
                            r["time_in"],
                            r["time_out"] or "N/A",
                            r["duration_formatted"] or "N/A",
                            r["status"],
                            r["notes"] or "",
                            r["created_at"]
                        ])
                    
                    csv_bytes = output.getvalue().encode("utf-8-sig")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", f'attachment; filename="attendance_report_{today_str}.csv"')
                    self.send_header("Content-Length", str(len(csv_bytes)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(csv_bytes)
                    return

                else:
                    self.send_json({"error": "Endpoint not found"}, 404)
                    return

            # Serve static files
            self.serve_static(path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)

            if path == "/api/attendance/clock-in":
                data = self.parse_json_body()
                name = data.get("name", "").strip()
                email = data.get("email", "").strip()
                branch = data.get("branch", "Popoola Branch").strip()
                call_number = data.get("call_number", "").strip()
                whatsapp_number = data.get("whatsapp_number", "").strip() or call_number
                parent_phone = data.get("parent_phone", "").strip()
                session_type = data.get("session_type", "Morning Session").strip()
                notes = data.get("notes", "").strip()

                if not name or not email:
                    self.send_json({"success": False, "message": "Full Name and Email address are required."}, 400)
                    return

                if not branch:
                    self.send_json({"success": False, "message": "Tutorial Branch is required."}, 400)
                    return

                if branch not in ["Popoola Branch", "Kilimanjaro Branch"]:
                    branch = "Popoola Branch"

                if "@" not in email or "." not in email:
                    self.send_json({"success": False, "message": "Please enter a valid email address."}, 400)
                    return

                if not call_number:
                    self.send_json({"success": False, "message": "Student's Call Number is required."}, 400)
                    return

                if not whatsapp_number:
                    self.send_json({"success": False, "message": "Student's WhatsApp Number is required."}, 400)
                    return

                if not parent_phone:
                    self.send_json({"success": False, "message": "Parent's Phone Number is required."}, 400)
                    return

                if session_type not in ["Morning Session", "Evening Session", "Both Sessions"]:
                    session_type = "Morning Session"

                result = database.clock_in_student(name, email, branch, notes, call_number, whatsapp_number, parent_phone, session_type)
                if result.get("success"):
                    notify_data_change()
                self.send_json(result, 200 if result["success"] else 400)
                return

            elif path == "/api/attendance/clock-out":
                data = self.parse_json_body()
                name = data.get("name", "").strip()
                email = data.get("email", "").strip()
                branch = data.get("branch", "Popoola Branch").strip()
                session_type = data.get("session_type", "").strip()

                if not email:
                    self.send_json({"success": False, "message": "Email address is required."}, 400)
                    return

                result = database.clock_out_student(name, email, branch, session_type)
                if result.get("success"):
                    notify_data_change()
                self.send_json(result, 200 if result["success"] else 400)
                return

            elif path == "/api/staff/login":
                data = self.parse_json_body()
                name = data.get("name", "").strip()
                role = data.get("role", "").strip()
                password = data.get("password", "").strip()
                username = data.get("username", "").strip()

                centre_name = database.get_config("centre_name", "USA Tutorial Centre")

                if password:
                    user_to_auth = username or name
                    auth_res = database.authenticate_admin(user_to_auth, password)
                    if auth_res["success"]:
                        auth_res["centre_name"] = centre_name
                        self.send_json(auth_res, 200)
                    else:
                        self.send_json(auth_res, 401)
                    return

                if not name:
                    self.send_json({"success": False, "message": "Please enter your Name."}, 400)
                    return

                if role not in ["Secretary", "Director", "Admin"]:
                    self.send_json({"success": False, "message": "Role must be 'Secretary', 'Director', or 'Admin'."}, 400)
                    return

                session = database.create_staff_session(name, role)
                self.send_json({
                    "success": True,
                    "token": session["token"],
                    "staff_name": session["staff_name"],
                    "staff_role": session["staff_role"],
                    "centre_name": centre_name,
                    "message": f"Welcome, {session['staff_name']} ({session['staff_role']})"
                })
                return

            elif path == "/api/admin/create-password":
                data = self.parse_json_body()
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()
                full_name = data.get("full_name", "").strip()
                role = data.get("role", "Director").strip()

                if not username or not password or not full_name:
                    self.send_json({"success": False, "message": "Username, password, and full name are required."}, 400)
                    return

                if len(username) < 3:
                    self.send_json({"success": False, "message": "Username must be at least 3 characters long."}, 400)
                    return

                if len(password) < 6:
                    self.send_json({"success": False, "message": "Password must be at least 6 characters long."}, 400)
                    return

                result = database.create_admin(username, password, full_name, role)
                if result["success"]:
                    auth_res = database.authenticate_admin(username, password)
                    auth_res["centre_name"] = database.get_config("centre_name", "USA Tutorial Centre")
                    auth_res["message"] = "Admin account and password created successfully!"
                    self.send_json(auth_res, 201)
                else:
                    self.send_json(result, 400)
                return

            elif path == "/api/admin/login":
                data = self.parse_json_body()
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()
                pin = str(data.get("pin", "")).strip()
                centre_name = database.get_config("centre_name", "USA Tutorial Centre")

                if username and password:
                    result = database.authenticate_admin(username, password)
                    if result["success"]:
                        result["centre_name"] = centre_name
                        self.send_json(result, 200)
                    else:
                        self.send_json(result, 401)
                    return

                if password and not username:
                    conn = database.get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM admins ORDER BY id ASC LIMIT 1")
                    first_admin = cursor.fetchone()
                    conn.close()
                    if first_admin:
                        result = database.authenticate_admin(first_admin["username"], password)
                        if result["success"]:
                            result["centre_name"] = centre_name
                            self.send_json(result, 200)
                            return
                        else:
                            self.send_json({"success": False, "message": "Incorrect admin password."}, 401)
                            return

                stored_pin = database.get_config("admin_pin", "1234")
                if pin and pin == stored_pin:
                    token = database.get_config("session_token", "admin_secret_token_2026")
                    self.send_json({
                        "success": True,
                        "token": token,
                        "staff_name": "Administrator",
                        "staff_role": "Director",
                        "centre_name": centre_name,
                        "message": "Login successful"
                    })
                    return

                self.send_json({
                    "success": False,
                    "message": "Invalid credentials. Please provide your username and password."
                }, 401)
                return

            elif path == "/api/admin/change-password":
                staff = self.get_auth_staff()
                if not staff:
                    self.send_json({"error": "Unauthorized access. Please login first."}, 401)
                    return

                data = self.parse_json_body()
                username = data.get("username", "").strip()
                old_password = data.get("old_password", "").strip()
                new_password = data.get("new_password", "").strip()

                if not old_password or not new_password:
                    self.send_json({"success": False, "message": "Current and new passwords are required."}, 400)
                    return

                if len(new_password) < 6:
                    self.send_json({"success": False, "message": "New password must be at least 6 characters long."}, 400)
                    return

                if not username:
                    conn = database.get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT username FROM admins WHERE full_name = ? LIMIT 1", (staff["staff_name"],))
                    row = cursor.fetchone()
                    if row:
                        username = row["username"]
                    else:
                        cursor.execute("SELECT username FROM admins ORDER BY id ASC LIMIT 1")
                        row2 = cursor.fetchone()
                        if row2:
                            username = row2["username"]
                    conn.close()

                if not username:
                    self.send_json({"success": False, "message": "No admin user found to update."}, 404)
                    return

                result = database.change_admin_password(username, old_password, new_password)
                self.send_json(result, 200 if result["success"] else 400)
                return

            elif path == "/api/admin/manual-record":
                staff = self.get_auth_staff()
                if not staff:
                    self.send_json({"error": "Unauthorized"}, 401)
                    return
                data = self.parse_json_body()
                name = data.get("name", "").strip()
                email = data.get("email", "").strip()
                branch = data.get("branch", "Popoola Branch").strip()
                date_str = data.get("date", "").strip()
                time_in = data.get("time_in", "").strip()
                time_out = data.get("time_out", "").strip()
                notes = data.get("notes", "").strip()
                call_number = data.get("call_number", "").strip()
                whatsapp_number = data.get("whatsapp_number", "").strip() or call_number
                parent_phone = data.get("parent_phone", "").strip()
                session_type = data.get("session_type", "Morning Session").strip()

                if not name or not email or not date_str or not time_in:
                    self.send_json({"success": False, "message": "Name, email, date, and time in are required."}, 400)
                    return

                record = database.manual_add_record(name, email, branch, date_str, time_in, time_out, notes, call_number, whatsapp_number, parent_phone, session_type)
                self.send_json({"success": True, "record": record, "message": "Record created successfully."})
                return

            elif path == "/api/admin/acknowledge-alert":
                staff = self.get_auth_staff()
                if not staff:
                    self.send_json({"error": "Unauthorized access"}, 401)
                    return
                data = self.parse_json_body()
                email = data.get("email", "").strip().lower()
                session_type = data.get("session_type", "Morning Session").strip()
                date_str = data.get("date", "").strip()

                if not email:
                    self.send_json({"success": False, "message": "Student email is required to acknowledge alert."}, 400)
                    return

                res = database.acknowledge_absentee_alert(email, session_type, date_str, staff.get("staff_name", "Admin"))
                self.send_json(res, 200)
                return

            elif path == "/api/admin/refresh-qr":
                staff = self.get_auth_staff()
                if not staff:
                    self.send_json({"error": "Unauthorized access"}, 401)
                    return
                qr_info = database.refresh_qr_token()
                base_url = self.get_base_url()
                qr_info["base_url"] = base_url
                qr_info["popoola_url"] = f"{base_url}/index.html?branch=Popoola+Branch&token={qr_info['token']}"
                qr_info["kilimanjaro_url"] = f"{base_url}/index.html?branch=Kilimanjaro+Branch&token={qr_info['token']}"
                self.send_json({
                    "success": True,
                    "message": "Daily QR codes refreshed successfully.",
                    "qr_info": qr_info
                }, 200)
                return

            elif path == "/api/admin/settings":
                staff = self.get_auth_staff(query_params)
                if not staff:
                    self.send_json({"error": "Unauthorized"}, 401)
                    return
                data = self.parse_json_body()
                if "centre_name" in data and data["centre_name"].strip():
                    database.set_config("centre_name", data["centre_name"].strip())
                self.send_json({"success": True, "message": "Settings updated successfully."})
                return

            elif path in ("/api/admin/clear-records", "/api/admin/records/clear"):
                staff = self.get_auth_staff(query_params)
                if not staff:
                    self.send_json({"error": "Unauthorized"}, 401)
                    return
                branch = query_params.get("branch", ["ALL"])[0]
                database.clear_all_attendance(branch)
                self.send_json({"success": True, "message": "Attendance records cleared from database."})
                return

            else:
                self.send_json({"error": "Endpoint not found"}, 404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": str(e)}, 500)

    def do_DELETE(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)

            if path.startswith("/api/admin/record/"):
                staff = self.get_auth_staff(query_params)
                if not staff:
                    self.send_json({"error": "Unauthorized"}, 401)
                    return
                try:
                    record_id = int(path.split("/")[-1])
                    deleted = database.delete_record(record_id)
                    if deleted:
                        notify_data_change()
                        self.send_json({"success": True, "message": "Record permanently deleted from database."})
                    else:
                        self.send_json({"success": False, "message": "Record not found."}, 404)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, 400)
                return

            elif path in ("/api/admin/records", "/api/admin/clear-records"):
                staff = self.get_auth_staff(query_params)
                if not staff:
                    self.send_json({"error": "Unauthorized"}, 401)
                    return
                branch = query_params.get("branch", ["ALL"])[0]
                database.clear_all_attendance(branch)
                notify_data_change()
                self.send_json({"success": True, "message": "All attendance records permanently cleared from database."})
                return
            
            self.send_json({"error": "Endpoint not found"}, 404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": str(e)}, 500)

def run_server():
    global PORT
    PORT = int(os.environ.get("PORT", 5000))
    database.init_db()
    ip = get_local_ip()
    print("=" * 60)
    print("USA TUTORIAL CENTRE ATTENDANCE SYSTEM RUNNING")
    print("=" * 60)
    print(f"Host Binding:      0.0.0.0:{PORT}")
    print(f"Local Access:      http://localhost:{PORT}")
    print(f"Network / QR URL:  http://{ip}:{PORT}")
    print(f"Role Select / Hub: http://{ip}:{PORT}/index.html")
    print(f"Clock-In Portal:   http://{ip}:{PORT}/clock-in.html")
    print(f"Clock-Out Portal:  http://{ip}:{PORT}/clock-out.html")
    print(f"Admin Dashboard:   http://{ip}:{PORT}/admin.html")
    print(f"Printable Posters: http://{ip}:{PORT}/qr-posters.html")
    print("=" * 60)

    class ReusableTCPServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("0.0.0.0", PORT), AttendanceHandler) as httpd:
        print(f"Server successfully listening on 0.0.0.0:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
