import sqlite3
import os
import time
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance.db"))

def get_db():
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create Attendance table with branch, contacts, and session
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        student_email TEXT NOT NULL,
        branch TEXT NOT NULL DEFAULT 'Popoola Branch',
        date TEXT NOT NULL,
        time_in TEXT NOT NULL,
        time_in_raw INTEGER NOT NULL,
        time_out TEXT,
        time_out_raw INTEGER,
        duration_minutes INTEGER DEFAULT 0,
        duration_formatted TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'CLOCKED_IN',
        notes TEXT DEFAULT '',
        call_number TEXT DEFAULT '',
        whatsapp_number TEXT DEFAULT '',
        parent_phone TEXT DEFAULT '',
        session_type TEXT NOT NULL DEFAULT 'Morning Session',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migrate columns if they don't exist in attendance
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [row["name"] for row in cursor.fetchall()]
    attendance_cols_to_add = [
        ("branch", "TEXT NOT NULL DEFAULT 'Popoola Branch'"),
        ("call_number", "TEXT DEFAULT ''"),
        ("whatsapp_number", "TEXT DEFAULT ''"),
        ("parent_phone", "TEXT DEFAULT ''"),
        ("session_type", "TEXT NOT NULL DEFAULT 'Morning Session'")
    ]
    for col_name, col_type in attendance_cols_to_add:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE attendance ADD COLUMN {col_name} {col_type}")

    # Create Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        branch TEXT DEFAULT 'Popoola Branch',
        phone TEXT DEFAULT '',
        call_number TEXT DEFAULT '',
        whatsapp_number TEXT DEFAULT '',
        parent_phone TEXT DEFAULT '',
        session_type TEXT DEFAULT 'Morning Session',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("PRAGMA table_info(students)")
    student_columns = [row["name"] for row in cursor.fetchall()]
    student_cols_to_add = [
        ("branch", "TEXT DEFAULT 'Popoola Branch'"),
        ("call_number", "TEXT DEFAULT ''"),
        ("whatsapp_number", "TEXT DEFAULT ''"),
        ("parent_phone", "TEXT DEFAULT ''"),
        ("session_type", "TEXT DEFAULT 'Morning Session'")
    ]
    for col_name, col_type in student_cols_to_add:
        if col_name not in student_columns:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")

    # Create Absentee Acknowledgements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS absentee_acknowledgements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        session_type TEXT NOT NULL,
        student_email TEXT NOT NULL,
        acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        acknowledged_by TEXT DEFAULT 'Admin',
        UNIQUE(date, session_type, student_email)
    )
    """)

    # Migrate legacy branch names to official Popoola Branch
    cursor.execute("""
    UPDATE attendance SET branch = 'Popoola Branch'
    WHERE branch IN ('Main Campus', 'Downtown Branch', 'North Campus', 'City Center Branch')
    """)
    cursor.execute("""
    UPDATE students SET branch = 'Popoola Branch'
    WHERE branch IN ('Main Campus', 'Downtown Branch', 'North Campus', 'City Center Branch')
    """)

    # Create Staff Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_name TEXT NOT NULL,
        staff_role TEXT NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Admins table with password hashing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Director',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Admin Config table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Set default values
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('admin_pin', '1234')")
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('centre_name', 'USA Tutorial Centre')")
    cursor.execute("UPDATE admin_config SET value = 'USA Tutorial Centre' WHERE key = 'centre_name'")
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('session_token', 'admin_secret_token_2026')")
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('qr_refresh_token', 'daily_qr_token_default')")
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('qr_refresh_date', '')")
    cursor.execute("INSERT OR IGNORE INTO admin_config (key, value) VALUES ('qr_refresh_time', '')")

    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pwd_hash, salt

def verify_password(password, salt, stored_hash):
    pwd_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(pwd_hash, stored_hash)

def admin_exists():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM admins")
    cnt = cursor.fetchone()["cnt"]
    conn.close()
    return cnt > 0

def get_admin_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_admin(username, password, full_name, role="Director"):
    username = username.strip()
    full_name = full_name.strip()
    role = role.strip() or "Director"
    password = password.strip()

    if len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters long."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters long."}
    if not full_name:
        return {"success": False, "message": "Full Name is required."}

    pwd_hash, salt = hash_password(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO admins (username, password_hash, salt, full_name, role)
        VALUES (?, ?, ?, ?, ?)
        """, (username, pwd_hash, salt, full_name, role))
        conn.commit()
        admin_id = cursor.lastrowid
        conn.close()
        return {
            "success": True,
            "message": "Admin account and password created successfully!",
            "admin": {
                "id": admin_id,
                "username": username,
                "full_name": full_name,
                "role": role
            }
        }
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": f"Username '{username}' already exists. Please choose another username."}
    except Exception as e:
        conn.close()
        return {"success": False, "message": f"Failed to create admin: {str(e)}"}

def authenticate_admin(username, password):
    username = username.strip()
    password = password.strip()

    if not username or not password:
        return {"success": False, "message": "Username and password are required."}

    admin = get_admin_by_username(username)
    if not admin:
        return {"success": False, "message": "Invalid username or password."}

    if not verify_password(password, admin["salt"], admin["password_hash"]):
        return {"success": False, "message": "Invalid username or password."}

    session = create_staff_session(admin["full_name"], admin["role"])
    return {
        "success": True,
        "token": session["token"],
        "staff_name": admin["full_name"],
        "staff_role": admin["role"],
        "username": admin["username"],
        "message": f"Welcome back, {admin['full_name']}!"
    }

def change_admin_password(username, old_password, new_password):
    username = username.strip()
    old_password = old_password.strip()
    new_password = new_password.strip()

    if len(new_password) < 6:
        return {"success": False, "message": "New password must be at least 6 characters long."}

    admin = get_admin_by_username(username)
    if not admin:
        return {"success": False, "message": "Admin user not found."}

    if not verify_password(old_password, admin["salt"], admin["password_hash"]):
        return {"success": False, "message": "Current password is incorrect."}

    new_hash, new_salt = hash_password(new_password)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE admins
    SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (new_hash, new_salt, admin["id"]))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Password updated successfully!"}

def format_time_12h(epoch_secs):
    return datetime.fromtimestamp(epoch_secs).strftime("%I:%M:%S %p")

def format_date_str(epoch_secs):
    return datetime.fromtimestamp(epoch_secs).strftime("%Y-%m-%d")

def format_duration(total_minutes):
    if total_minutes < 1:
        return "< 1 min"
    hours = total_minutes // 60
    mins = total_minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins} mins"

def create_staff_session(name, role):
    name = name.strip()
    role = role.strip()
    session_token = f"staff_{int(time.time())}_{secrets.token_hex(16)}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO staff_sessions (staff_name, staff_role, session_token)
    VALUES (?, ?, ?)
    """, (name, role, session_token))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "token": session_token,
        "staff_name": name,
        "staff_role": role
    }

def verify_staff_session(token):
    if not token:
        return None
    # Check default secret token as fallback
    if token == "admin_secret_token_2026":
        return {"staff_name": "Administrator", "staff_role": "Director"}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM staff_sessions WHERE session_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def clock_in_student(name, email, branch="Popoola Branch", notes="", call_number="", whatsapp_number="", parent_phone="", session_type="Morning Session"):
    name = name.strip()
    email = email.strip().lower()
    branch = (branch or "Popoola Branch").strip()
    if branch not in ("Popoola Branch", "Kilimanjaro Branch"):
        branch = "Popoola Branch"

    if session_type not in ("Morning Session", "Evening Session", "Both Sessions"):
        session_type = "Morning Session"

    call_number = call_number.strip()
    whatsapp_number = whatsapp_number.strip() or call_number
    parent_phone = parent_phone.strip()

    now_epoch = int(time.time())
    today_str = format_date_str(now_epoch)
    time_str = format_time_12h(now_epoch)

    conn = get_db()
    cursor = conn.cursor()

    # Save or update student in students directory
    cursor.execute("""
    INSERT INTO students (name, email, branch, phone, call_number, whatsapp_number, parent_phone, session_type, last_seen)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(email) DO UPDATE SET
        name = excluded.name,
        branch = excluded.branch,
        phone = CASE WHEN excluded.call_number != '' THEN excluded.call_number ELSE students.phone END,
        call_number = CASE WHEN excluded.call_number != '' THEN excluded.call_number ELSE students.call_number END,
        whatsapp_number = CASE WHEN excluded.whatsapp_number != '' THEN excluded.whatsapp_number ELSE students.whatsapp_number END,
        parent_phone = CASE WHEN excluded.parent_phone != '' THEN excluded.parent_phone ELSE students.parent_phone END,
        session_type = excluded.session_type,
        last_seen = CURRENT_TIMESTAMP
    """, (name, email, branch, call_number, call_number, whatsapp_number, parent_phone, session_type))

    # Check if student already has an active clock-in today without clock-out
    cursor.execute("""
    SELECT * FROM attendance
    WHERE student_email = ? AND date = ? AND status = 'CLOCKED_IN'
    ORDER BY id DESC LIMIT 1
    """, (email, today_str))
    
    existing = cursor.fetchone()
    if existing:
        conn.close()
        existing_data = dict(existing)
        return {
            "success": False,
            "already_clocked_in": True,
            "record": existing_data,
            "message": f"Student is already clocked in at {existing_data['time_in']} today ({existing_data.get('session_type', 'Morning Session')})."
        }

    # Insert new attendance record
    cursor.execute("""
    INSERT INTO attendance (student_name, student_email, branch, date, time_in, time_in_raw, status, notes, call_number, whatsapp_number, parent_phone, session_type)
    VALUES (?, ?, ?, ?, ?, ?, 'CLOCKED_IN', ?, ?, ?, ?, ?)
    """, (name, email, branch, today_str, time_str, now_epoch, notes, call_number, whatsapp_number, parent_phone, session_type))
    
    record_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM attendance WHERE id = ?", (record_id,))
    new_record = cursor.fetchone()
    conn.close()

    return {
        "success": True,
        "already_clocked_in": False,
        "record": dict(new_record),
        "message": f"Successfully clocked in at {time_str} for {session_type} ({branch})"
    }

def clock_out_student(name, email, branch="Popoola Branch", session_type=None):
    email = email.strip().lower()
    now_epoch = int(time.time())
    today_str = format_date_str(now_epoch)
    time_out_str = format_time_12h(now_epoch)
    now_dt = datetime.fromtimestamp(now_epoch)
    current_hour = now_dt.hour

    conn = get_db()
    cursor = conn.cursor()

    # Find the most recent active clock-in record for today
    cursor.execute("""
    SELECT * FROM attendance
    WHERE student_email = ? AND date = ? AND status = 'CLOCKED_IN'
    ORDER BY id DESC LIMIT 1
    """, (email, today_str))

    active_record = cursor.fetchone()

    if not active_record:
        # Check if they already completed clock out today
        cursor.execute("""
        SELECT * FROM attendance
        WHERE student_email = ? AND date = ? AND status = 'COMPLETED'
        ORDER BY id DESC LIMIT 1
        """, (email, today_str))
        completed_record = cursor.fetchone()
        
        if completed_record:
            conn.close()
            return {
                "success": False,
                "already_clocked_out": True,
                "record": dict(completed_record),
                "message": f"You already clocked out at {completed_record['time_out']} today."
            }

        # If no clock-in found at all today, create a completed record
        used_branch = branch or "Popoola Branch"
        chosen_session = session_type or "Morning Session"
        cursor.execute("""
        INSERT INTO attendance (student_name, student_email, branch, date, time_in, time_in_raw, time_out, time_out_raw, duration_minutes, duration_formatted, status, notes, session_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'Direct Clock-Out', 'COMPLETED', 'No clock-in recorded', ?)
        """, (name or "Student", email, used_branch, today_str, time_out_str, now_epoch, time_out_str, now_epoch, chosen_session))
        record_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT * FROM attendance WHERE id = ?", (record_id,))
        created = cursor.fetchone()
        conn.close()
        return {
            "success": True,
            "no_previous_clock_in": True,
            "record": dict(created),
            "message": f"Clocked out at {time_out_str} ({chosen_session})."
        }

    active_data = dict(active_record)
    rec_session = active_data.get("session_type") or "Morning Session"

    # Business Rule Enforcement:
    # "Some students do attend both morning and evening session so ONLY such students
    # should be allowed to clock-in in the morning session and clock-out at the end of the evening session."
    if rec_session == "Morning Session":
        if (session_type == "Evening Session") or (current_hour >= 15):
            conn.close()
            return {
                "success": False,
                "session_rule_violation": True,
                "message": "Morning Session ended at 2:30 PM. Only students enrolled in 'Both Sessions' are allowed to clock-in in the morning and clock-out at the end of the evening session. Please contact the administrator."
            }

    # Calculate duration
    time_in_raw = active_record["time_in_raw"]
    duration_secs = max(0, now_epoch - time_in_raw)
    duration_mins = int(duration_secs / 60)
    duration_fmt = format_duration(duration_mins)

    # Update active record
    cursor.execute("""
    UPDATE attendance
    SET time_out = ?,
        time_out_raw = ?,
        duration_minutes = ?,
        duration_formatted = ?,
        status = 'COMPLETED',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (time_out_str, now_epoch, duration_mins, duration_fmt, active_record["id"]))

    conn.commit()
    cursor.execute("SELECT * FROM attendance WHERE id = ?", (active_record["id"],))
    updated_record = cursor.fetchone()
    conn.close()

    return {
        "success": True,
        "record": dict(updated_record),
        "message": f"Successfully clocked out at {time_out_str}. Total time: {duration_fmt}"
    }

def get_student_status(email):
    email = email.strip().lower()
    today_str = format_date_str(int(time.time()))
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM attendance
    WHERE student_email = ? AND date = ?
    ORDER BY id DESC LIMIT 1
    """, (email, today_str))

    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_today_records(branch_filter="ALL"):
    today_str = format_date_str(int(time.time()))
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM attendance WHERE date = ?"
    params = [today_str]
    if branch_filter and branch_filter != "ALL":
        query += " AND branch = ?"
        params.append(branch_filter)
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_records(search="", date_filter="", status_filter="", branch_filter="ALL"):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM attendance WHERE 1=1"
    params = []

    if search:
        query += " AND (student_name LIKE ? OR student_email LIKE ? OR branch LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if date_filter:
        query += " AND date = ?"
        params.append(date_filter)

    if status_filter and status_filter != "ALL":
        query += " AND status = ?"
        params.append(status_filter)

    if branch_filter and branch_filter != "ALL":
        query += " AND branch = ?"
        params.append(branch_filter)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_dashboard_stats(branch_filter="ALL"):
    today_str = format_date_str(int(time.time()))
    conn = get_db()
    cursor = conn.cursor()

    b_clause = ""
    params_today = [today_str]
    if branch_filter and branch_filter != "ALL":
        b_clause = " AND branch = ?"
        params_today.append(branch_filter)

    # Total today
    cursor.execute(f"SELECT COUNT(*) as count FROM attendance WHERE date = ?{b_clause}", params_today)
    total_today = cursor.fetchone()["count"]

    # Currently inside
    cursor.execute(f"SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = 'CLOCKED_IN'{b_clause}", params_today)
    currently_inside = cursor.fetchone()["count"]

    # Clocked out completed today
    cursor.execute(f"SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = 'COMPLETED'{b_clause}", params_today)
    clocked_out_today = cursor.fetchone()["count"]

    # Total all-time records
    if branch_filter and branch_filter != "ALL":
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE branch = ?", (branch_filter,))
    else:
        cursor.execute("SELECT COUNT(*) as count FROM attendance")
    total_all_time = cursor.fetchone()["count"]

    # Total unique registered students
    if branch_filter and branch_filter != "ALL":
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE branch = ?", (branch_filter,))
    else:
        cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()["count"]

    # Average duration today
    cursor.execute(f"SELECT AVG(duration_minutes) as avg_dur FROM attendance WHERE date = ? AND status = 'COMPLETED' AND duration_minutes > 0{b_clause}", params_today)
    avg_row = cursor.fetchone()
    avg_minutes = int(avg_row["avg_dur"]) if avg_row["avg_dur"] is not None else 0
    avg_duration_str = format_duration(avg_minutes)

    conn.close()

    return {
        "today_date": today_str,
        "total_today": total_today,
        "currently_inside": currently_inside,
        "clocked_out_today": clocked_out_today,
        "total_all_time": total_all_time,
        "total_students": total_students,
        "avg_duration_today": avg_duration_str,
        "avg_minutes_today": avg_minutes
    }

def manual_add_record(name, email, branch="Popoola Branch", date_str="", time_in_str="", time_out_str="", notes="", call_number="", whatsapp_number="", parent_phone="", session_type="Morning Session"):
    conn = get_db()
    cursor = conn.cursor()
    now_epoch = int(time.time())

    status = "COMPLETED" if time_out_str else "CLOCKED_IN"
    duration_mins = 0
    duration_fmt = ""
    branch = (branch or "Popoola Branch").strip()
    if branch not in ("Popoola Branch", "Kilimanjaro Branch"):
        branch = "Popoola Branch"

    if session_type not in ("Morning Session", "Evening Session", "Both Sessions"):
        session_type = "Morning Session"

    # Parse duration if both times provided
    if time_in_str and time_out_str:
        try:
            t1 = datetime.strptime(f"{date_str} {time_in_str}", "%Y-%m-%d %I:%M:%S %p")
            t2 = datetime.strptime(f"{date_str} {time_out_str}", "%Y-%m-%d %I:%M:%S %p")
            diff = int((t2 - t1).total_seconds() / 60)
            if diff >= 0:
                duration_mins = diff
                duration_fmt = format_duration(duration_mins)
        except Exception:
            pass

    # Update or insert student
    cursor.execute("""
    INSERT INTO students (name, email, branch, phone, call_number, whatsapp_number, parent_phone, session_type, last_seen)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(email) DO UPDATE SET
        name = excluded.name,
        branch = excluded.branch,
        phone = CASE WHEN excluded.call_number != '' THEN excluded.call_number ELSE students.phone END,
        call_number = CASE WHEN excluded.call_number != '' THEN excluded.call_number ELSE students.call_number END,
        whatsapp_number = CASE WHEN excluded.whatsapp_number != '' THEN excluded.whatsapp_number ELSE students.whatsapp_number END,
        parent_phone = CASE WHEN excluded.parent_phone != '' THEN excluded.parent_phone ELSE students.parent_phone END,
        session_type = excluded.session_type,
        last_seen = CURRENT_TIMESTAMP
    """, (name, email, branch, call_number, call_number, whatsapp_number, parent_phone, session_type))

    cursor.execute("""
    INSERT INTO attendance (student_name, student_email, branch, date, time_in, time_in_raw, time_out, time_out_raw, duration_minutes, duration_formatted, status, notes, call_number, whatsapp_number, parent_phone, session_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, email, branch, date_str, time_in_str, now_epoch, time_out_str, now_epoch if time_out_str else None, duration_mins, duration_fmt, status, notes, call_number, whatsapp_number, parent_phone, session_type))

    record_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM attendance WHERE id = ?", (record_id,))
    record = cursor.fetchone()
    conn.close()
    return dict(record)

def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_config(key, default=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM admin_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_config(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO admin_config (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_absentee_alerts(branch="ALL"):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    
    # Morning alert window: active from 9:00 AM onwards (e.g. 9 to 12pm and remaining daytime)
    morning_active = (current_hour >= 9)
    # Evening alert window: active from 3:00 PM (15:00) onwards (e.g. 3 to 5pm and remaining evening)
    evening_active = (current_hour >= 15)

    if not morning_active and not evening_active:
        return []

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if branch and branch != "ALL":
        query += " AND branch = ?"
        params.append(branch)
    cursor.execute(query, params)
    registered_students = [dict(r) for r in cursor.fetchall()]

    # Fetch all records for today
    cursor.execute("SELECT student_email, session_type, status FROM attendance WHERE date = ?", (today_str,))
    today_records = cursor.fetchall()
    clocked_map = {}
    for r in today_records:
        em = r["student_email"].strip().lower()
        if em not in clocked_map:
            clocked_map[em] = []
        clocked_map[em].append(r["session_type"])

    # Fetch acknowledgements for today
    cursor.execute("SELECT session_type, student_email FROM absentee_acknowledgements WHERE date = ?", (today_str,))
    acks = set((r["session_type"], r["student_email"].strip().lower()) for r in cursor.fetchall())

    conn.close()

    alerts = []
    for st in registered_students:
        email = st["email"].strip().lower()
        student_session = st.get("session_type") or "Morning Session"
        student_branch = st.get("branch") or "Popoola Branch"
        call_no = st.get("call_number") or st.get("phone") or ""
        wa_no = st.get("whatsapp_number") or call_no
        parent_no = st.get("parent_phone") or ""

        # Morning Session Alert check (for students in Morning Session or Both Sessions)
        if morning_active and student_session in ("Morning Session", "Both Sessions"):
            has_clocked = (email in clocked_map)
            is_acked = ("Morning Session", email) in acks
            if not has_clocked and not is_acked:
                alerts.append({
                    "alert_id": f"morning_{email}_{today_str}",
                    "date": today_str,
                    "session_type": "Morning Session",
                    "session_label": "Morning Session (9:00 AM – 12:00 PM)",
                    "student_name": st["name"],
                    "student_email": st["email"],
                    "branch": student_branch,
                    "call_number": call_no,
                    "whatsapp_number": wa_no,
                    "parent_phone": parent_no,
                    "message": f"{st['name']} has not clocked in for Morning Session (expected 9:00 AM – 12:00 PM)."
                })

        # Evening Session Alert check (for students in Evening Session or Both Sessions)
        if evening_active and student_session in ("Evening Session", "Both Sessions"):
            has_evening_attendance = False
            if email in clocked_map:
                sessions_clocked = clocked_map[email]
                if "Evening Session" in sessions_clocked or "Both Sessions" in sessions_clocked:
                    has_evening_attendance = True

            is_acked_eve = ("Evening Session", email) in acks
            if not has_evening_attendance and not is_acked_eve:
                alerts.append({
                    "alert_id": f"evening_{email}_{today_str}",
                    "date": today_str,
                    "session_type": "Evening Session",
                    "session_label": "Evening Session (3:00 PM – 5:00 PM)",
                    "student_name": st["name"],
                    "student_email": st["email"],
                    "branch": student_branch,
                    "call_number": call_no,
                    "whatsapp_number": wa_no,
                    "parent_phone": parent_no,
                    "message": f"{st['name']} has not clocked in for Evening Session (expected 3:00 PM – 5:00 PM)."
                })

    return alerts

def acknowledge_absentee_alert(email, session_type="Morning Session", date_str=None, admin_name="Admin"):
    if not date_str:
        date_str = format_date_str(int(time.time()))
    email = email.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO absentee_acknowledgements (date, session_type, student_email, acknowledged_by)
    VALUES (?, ?, ?, ?)
    """, (date_str, session_type, email, admin_name))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Alert acknowledged and cleared from dashboard."}

def refresh_qr_token():
    now_epoch = int(time.time())
    today_str = format_date_str(now_epoch)
    now_time_str = format_time_12h(now_epoch)
    token = secrets.token_urlsafe(8)
    set_config("qr_refresh_token", token)
    set_config("qr_refresh_date", today_str)
    set_config("qr_refresh_time", now_time_str)
    return {
        "token": token,
        "date": today_str,
        "time": now_time_str,
        "branches": ["Popoola Branch", "Kilimanjaro Branch"]
    }

def get_qr_info():
    token = get_config("qr_refresh_token", "daily_qr_token_default")
    date_str = get_config("qr_refresh_date", format_date_str(int(time.time())))
    time_str = get_config("qr_refresh_time", format_time_12h(int(time.time())))
    return {
        "token": token,
        "date": date_str,
        "time": time_str,
        "branches": ["Popoola Branch", "Kilimanjaro Branch"]
    }

def get_all_students(branch_filter="ALL"):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if branch_filter and branch_filter != "ALL":
        query += " AND branch = ?"
        params.append(branch_filter)
    query += " ORDER BY name ASC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def delete_record(record_id):
    """Deletes an attendance record from the database. Also clears associated student if they have no other records."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, student_email FROM attendance WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    email = row["student_email"]
    cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
    
    # Check if student has remaining attendance records
    cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE student_email = ?", (email,))
    remaining = cursor.fetchone()["cnt"]
    if remaining == 0:
        cursor.execute("DELETE FROM students WHERE email = ?", (email,))
        cursor.execute("DELETE FROM absentee_acknowledgements WHERE student_email = ?", (email,))
        
    conn.commit()
    conn.close()
    return True

def clear_all_attendance(branch_filter="ALL"):
    """Clears attendance records and associated registered students."""
    conn = get_db()
    cursor = conn.cursor()
    if branch_filter and branch_filter != "ALL":
        cursor.execute("DELETE FROM attendance WHERE branch = ?", (branch_filter,))
        cursor.execute("""
            DELETE FROM students 
            WHERE branch = ? 
            AND email NOT IN (SELECT DISTINCT student_email FROM attendance)
        """, (branch_filter,))
    else:
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM students")
        cursor.execute("DELETE FROM absentee_acknowledgements")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('attendance', 'students', 'absentee_acknowledgements')")
        except Exception:
            pass
    conn.commit()
    conn.close()
    return True

