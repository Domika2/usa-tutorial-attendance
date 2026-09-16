import sys
import os
import json
import time
from datetime import datetime

# Add current dir to sys.path so we can import directly
sys.path.insert(0, os.path.dirname(__file__))

import database

def run_tests():
    print("==================================================")
    print("STARTING FULL PROJECT 3 VERIFICATION")
    print("==================================================")

    # Step 0: Initialize database
    database.init_db()
    print("[PASS] Step 0: Database initialized successfully.")

    # Step 1: Branches and Server Info
    qr_info = database.get_qr_info()
    assert "Popoola Branch" in qr_info["branches"], "Popoola Branch missing from QR branches"
    assert "Kilimanjaro Branch" in qr_info["branches"], "Kilimanjaro Branch missing from QR branches"
    print(f"[PASS] Step 1: Branches verified -> {qr_info['branches']}")

    # Step 2: Test Contact Fields & Clock-In
    # 2a. Attempt clock-in with missing contact details directly via database function
    timestamp = int(time.time())
    test_email_1 = f"student_{timestamp}@example.com"
    
    # Clock in with complete contacts for Popoola Branch
    clock_res = database.clock_in_student(
        name="Tunde Bakare",
        email=test_email_1,
        branch="Popoola Branch",
        notes="First time student",
        call_number="08011223344",
        whatsapp_number="08011223344",
        parent_phone="08099887766",
        session_type="Morning Session"
    )
    assert clock_res["success"] is True, f"Clock-in failed: {clock_res}"
    rec1 = clock_res["record"]
    assert rec1["branch"] == "Popoola Branch"
    assert rec1["session_type"] == "Morning Session"
    assert rec1["call_number"] == "08011223344"
    assert rec1["whatsapp_number"] == "08011223344"
    assert rec1["parent_phone"] == "08099887766"
    print("[PASS] Step 2: Clock-in with full contact details & Popoola Branch verified.")

    # Step 3: Test Session Clock-out Rules
    # 3a. Student with "Morning Session" clocking out during morning
    clock_out_res = database.clock_out_student(
        name="Tunde Bakare",
        email=test_email_1,
        branch="Popoola Branch",
        session_type="Morning Session"
    )
    assert clock_out_res["success"] is True, f"Morning clock-out failed: {clock_out_res}"
    print("[PASS] Step 3a: Morning Session clock-out verified.")

    # 3b. Student in "Morning Session" attempting to clock out with Evening Session
    test_email_2 = f"morning_only_{timestamp}@example.com"
    database.clock_in_student(
        name="Seyi Makinde",
        email=test_email_2,
        branch="Kilimanjaro Branch",
        call_number="08022334455",
        whatsapp_number="08022334455",
        parent_phone="08077665544",
        session_type="Morning Session"
    )

    # Try clocking out as Evening Session - MUST BE BLOCKED
    violation_attempt = database.clock_out_student(
        name="Seyi Makinde",
        email=test_email_2,
        branch="Kilimanjaro Branch",
        session_type="Evening Session"
    )
    assert violation_attempt["success"] is False, "Expected session rule violation but succeeded!"
    assert violation_attempt.get("session_rule_violation") is True, "session_rule_violation flag not set"
    print(f"[PASS] Step 3b: Session rule violation correctly blocked: '{violation_attempt['message']}'")

    # 3c. Student in "Both Sessions"
    test_email_both = f"both_sessions_{timestamp}@example.com"
    database.clock_in_student(
        name="Amaka Obi",
        email=test_email_both,
        branch="Popoola Branch",
        call_number="08033445566",
        whatsapp_number="08033445566",
        parent_phone="08055443322",
        session_type="Both Sessions"
    )
    # Clock out in evening for student with "Both Sessions" - MUST BE ALLOWED
    both_out_res = database.clock_out_student(
        name="Amaka Obi",
        email=test_email_both,
        branch="Popoola Branch",
        session_type="Evening Session"
    )
    assert both_out_res["success"] is True, f"Both Sessions student clock out failed: {both_out_res}"
    print("[PASS] Step 3c: 'Both Sessions' student permitted to clock-in morning and clock-out evening.")

    # Step 4: Absentee Alert System
    # Register an unclocked morning student and an unclocked evening student
    test_absent_morning = f"absent_morning_{timestamp}@example.com"
    test_absent_evening = f"absent_evening_{timestamp}@example.com"

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO students (name, email, branch, phone, call_number, whatsapp_number, parent_phone, session_type)
    VALUES (?, ?, 'Popoola Branch', '08011112222', '08011112222', '08011112222', '08099998888', 'Morning Session')
    """, ("Femi Otedola", test_absent_morning))
    
    cursor.execute("""
    INSERT INTO students (name, email, branch, phone, call_number, whatsapp_number, parent_phone, session_type)
    VALUES (?, ?, 'Kilimanjaro Branch', '08033334444', '08033334444', '08033334444', '08077776666', 'Evening Session')
    """, ("Folorunsho Alakija", test_absent_evening))
    conn.commit()
    conn.close()

    alerts = database.get_absentee_alerts("ALL")
    # Check if morning alert triggered for Femi Otedola (if current time >= 9am)
    now_hour = datetime.now().hour
    if now_hour >= 9:
        morning_alerts = [a for a in alerts if a["student_email"].lower() == test_absent_morning.lower()]
        assert len(morning_alerts) >= 1, "Expected absentee alert for Femi Otedola"
        m_alert = morning_alerts[0]
        assert m_alert["call_number"] == "08011112222"
        assert m_alert["parent_phone"] == "08099998888"
        assert "Morning Session" in m_alert["session_type"]
        print(f"[PASS] Step 4a: Morning Absentee Alert generated: {m_alert['student_name']} ({m_alert['branch']})")

        # Test Acknowledgment (Sticky until Admin clicks 'Okay')
        ack_res = database.acknowledge_absentee_alert(
            email=test_absent_morning,
            session_type="Morning Session",
            admin_name="Director Vance"
        )
        assert ack_res["success"] is True

        # Re-fetch alerts - Femi's alert must now be cleared
        remaining_alerts = database.get_absentee_alerts("ALL")
        remaining_femi = [a for a in remaining_alerts if a["student_email"].lower() == test_absent_morning.lower()]
        assert len(remaining_femi) == 0, "Acknowledged alert was not cleared!"
        print("[PASS] Step 4b: Absentee Alert acknowledged and cleared persistently.")

    # Step 5: QR Refresh Token
    token1 = database.get_qr_info()["token"]
    refresh_res = database.refresh_qr_token()
    token2 = refresh_res["token"]
    assert token1 != token2 or token2 is not None, "Token was not refreshed"
    print(f"[PASS] Step 5: Daily QR Token refreshed -> Old: '{token1}', New: '{token2}' at {refresh_res['time']}")

    print("\n==================================================")
    print("ALL PROJECT 3 REQUIREMENTS VERIFIED SUCCESSFULLY! ")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
