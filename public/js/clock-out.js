// Clock-Out Page Logic
document.addEventListener("DOMContentLoaded", () => {
    const timeEl = document.getElementById("liveTime");
    const dateEl = document.getElementById("liveDate");
    const form = document.getElementById("clockOutForm");
    const nameInput = document.getElementById("studentName");
    const emailInput = document.getElementById("studentEmail");
    const branchInput = document.getElementById("studentBranch");
    const sessionInput = document.getElementById("classSession");
    const submitBtn = document.getElementById("clockOutBtn");
    const alertBox = document.getElementById("alertBox");
    const successCard = document.getElementById("successCard");
    const formCard = document.getElementById("formCard");
    const resetBtn = document.getElementById("resetBtn");
    const centreNameEl = document.getElementById("centreNameDisplay");

    // Update digital clock
    function updateClock() {
        const now = new Date();
        const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
        const dateOptions = { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' };
        
        if (timeEl) timeEl.textContent = now.toLocaleTimeString('en-US', timeOptions);
        if (dateEl) dateEl.textContent = now.toLocaleDateString('en-US', dateOptions);
    }
    updateClock();
    setInterval(updateClock, 1000);

    function getApiUrl(endpoint) {
        if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
        if (window.location.port === "5000") return endpoint;
        const host = window.location.hostname && window.location.hostname !== "" ? window.location.hostname : "127.0.0.1";
        return `http://${host}:5000${endpoint}`;
    }

    // Fetch server info
    fetch(getApiUrl("/api/server-info"))
        .then(res => res.json())
        .then(data => {
            if (data.centre_name && centreNameEl) {
                centreNameEl.textContent = data.centre_name;
            }
        })
        .catch(console.error);

    // UI Elements for Quick Clock Out
    const quickCard = document.getElementById("quickClockOutCard");
    const quickNameEl = document.getElementById("quickStudentName");
    const quickEmailEl = document.getElementById("quickStudentEmail");
    const quickBranchEl = document.getElementById("quickBranch");
    const quickSessionEl = document.getElementById("quickSession");
    const quickTimeInEl = document.getElementById("quickTimeIn");
    const quickAvatarEl = document.getElementById("quickAvatar");
    const quickClockOutBtn = document.getElementById("quickClockOutBtn");
    const quickAlertBox = document.getElementById("quickAlertBox");
    const editDetailsLink = document.getElementById("editDetailsLink");
    const cancelEditContainer = document.getElementById("cancelEditContainer");
    const cancelEditBtn = document.getElementById("cancelEditBtn");

    function getInitials(name) {
        if (!name) return "ST";
        const parts = name.trim().split(/\s+/);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return parts[0].substring(0, 2).toUpperCase();
    }

    // Check if this device has already clocked out for today
    const todayISO = new Date().toISOString().split("T")[0];
    let activeSession = null;
    try {
        const savedSessionJson = localStorage.getItem("tutorial_active_clockin");
        if (savedSessionJson) {
            const parsed = JSON.parse(savedSessionJson);
            if (parsed.date === todayISO) {
                activeSession = parsed;
                if (parsed.is_clocked_out) {
                    showSuccess(parsed, "Departure Already Recorded for Today");
                    return;
                }
            }
        }
    } catch (e) {
        console.error(e);
    }

    // Read branch from URL params if arrived via QR code
    const urlParams = new URLSearchParams(window.location.search);
    const paramBranch = urlParams.get("branch");

    // Load saved student identity
    let savedProfile = null;
    try {
        const pJson = localStorage.getItem("tutorial_student_profile");
        if (pJson) savedProfile = JSON.parse(pJson);
    } catch (e) {}

    const studentName = (activeSession && activeSession.student_name) || (savedProfile && savedProfile.name) || localStorage.getItem("tutorial_student_name") || "";
    const studentEmail = (activeSession && activeSession.student_email) || (savedProfile && savedProfile.email) || localStorage.getItem("tutorial_student_email") || "";
    const studentBranch = paramBranch || (activeSession && activeSession.branch) || (savedProfile && savedProfile.branch) || localStorage.getItem("tutorial_student_branch") || "Popoola Branch";
    const studentSession = (activeSession && activeSession.session_type) || (savedProfile && savedProfile.session_type) || localStorage.getItem("tutorial_student_session") || "Morning Session";
    const studentTimeIn = (activeSession && activeSession.time_in) || "Clocked In Today";

    function setupViews() {
        if (studentName && studentEmail) {
            // Student identity known: Show 1-Tap Quick Clock-Out!
            if (formCard) formCard.style.display = "none";
            if (quickCard) quickCard.style.display = "block";

            if (quickNameEl) quickNameEl.textContent = studentName;
            if (quickEmailEl) quickEmailEl.textContent = studentEmail;
            if (quickBranchEl) quickBranchEl.textContent = studentBranch;
            if (quickSessionEl) quickSessionEl.textContent = studentSession;
            if (quickTimeInEl) quickTimeInEl.textContent = studentTimeIn;
            if (quickAvatarEl) quickAvatarEl.textContent = getInitials(studentName);
        } else {
            // Fallback to manual entry form
            if (quickCard) quickCard.style.display = "none";
            if (formCard) formCard.style.display = "block";
            if (nameInput) nameInput.value = studentName;
            if (emailInput) emailInput.value = studentEmail;
            if (branchInput) branchInput.value = studentBranch;
            if (sessionInput) sessionInput.value = studentSession;
        }
    }

    setupViews();

    // 1-Tap Quick Clock-Out Button Handler
    if (quickClockOutBtn) {
        quickClockOutBtn.addEventListener("click", () => {
            performClockOut({
                name: studentName,
                email: studentEmail,
                branch: studentBranch,
                session_type: studentSession
            }, quickClockOutBtn, quickAlertBox);
        });
    }

    // Edit / manual entry link
    if (editDetailsLink) {
        editDetailsLink.addEventListener("click", (e) => {
            e.preventDefault();
            if (quickCard) quickCard.style.display = "none";
            if (formCard) formCard.style.display = "block";
            if (cancelEditContainer) cancelEditContainer.style.display = "block";

            if (nameInput) nameInput.value = studentName;
            if (emailInput) emailInput.value = studentEmail;
            if (branchInput) branchInput.value = studentBranch;
            if (sessionInput) sessionInput.value = studentSession;
        });
    }

    // Cancel edit button
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener("click", () => {
            if (formCard) formCard.style.display = "none";
            if (cancelEditContainer) cancelEditContainer.style.display = "none";
            if (quickCard) quickCard.style.display = "block";
        });
    }

    // Handle Manual Clock Out Form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();

        const name = nameInput ? nameInput.value.trim() : "";
        const email = emailInput.value.trim().toLowerCase();
        const branch = branchInput ? branchInput.value.trim() : "Popoola Branch";
        const session_type = sessionInput ? sessionInput.value.trim() : "Morning Session";

        if (!name || !email || !branch) {
            showAlert("Please enter your Full Name, Email address, and Tutorial Branch.", "danger");
            return;
        }

        await performClockOut({ name, email, branch, session_type }, submitBtn, alertBox);
    });

    async function performClockOut(payload, triggerBtn, alertEl) {
        if (triggerBtn) {
            triggerBtn.disabled = true;
            triggerBtn.innerHTML = `<span>Clocking out...</span>`;
        }
        if (alertEl) alertEl.style.display = "none";

        try {
            const res = await fetch(getApiUrl("/api/attendance/clock-out"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok && data.success) {
                persistClockOut(data.record, payload);
                showSuccess(data.record, "Great job today! You are clocked out.");
            } else if (data.already_clocked_out) {
                persistClockOut(data.record || payload, payload);
                showSuccess(data.record, "You have already clocked out for today.");
            } else {
                const msg = data.message || "Could not clock out. Please check your email and try again.";
                if (alertEl) {
                    alertEl.className = "alert alert-danger";
                    alertEl.textContent = msg;
                    alertEl.style.display = "flex";
                } else {
                    showAlert(msg, "danger");
                }
            }
        } catch (err) {
            console.error("Clock-out error:", err);
            const msg = "Could not connect to backend server. Please ensure 'py server.py' is running on port 5000.";
            if (alertEl) {
                alertEl.className = "alert alert-danger";
                alertEl.textContent = msg;
                alertEl.style.display = "flex";
            } else {
                showAlert(msg, "danger");
            }
        } finally {
            if (triggerBtn) {
                triggerBtn.disabled = false;
                if (triggerBtn === quickClockOutBtn) {
                    triggerBtn.innerHTML = `<span>🚪 Click to Clock Out</span>`;
                } else {
                    triggerBtn.innerHTML = `<span>Clock Out</span> <span>➔</span>`;
                }
            }
        }
    }

    function persistClockOut(record, fallbackPayload = {}) {
        try {
            let sessionData = activeSession || {};
            sessionData.date = todayISO;
            sessionData.student_name = record.student_name || fallbackPayload.name || sessionData.student_name || "";
            sessionData.student_email = record.student_email || fallbackPayload.email || sessionData.student_email || "";
            sessionData.branch = record.branch || fallbackPayload.branch || sessionData.branch || "Popoola Branch";
            sessionData.session_type = record.session_type || fallbackPayload.session_type || sessionData.session_type || "Morning Session";
            sessionData.time_in = record.time_in || sessionData.time_in || "N/A";
            sessionData.time_out = record.time_out || new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
            sessionData.duration_formatted = record.duration_formatted || "< 1 min";
            sessionData.is_clocked_out = true;
            localStorage.setItem("tutorial_active_clockin", JSON.stringify(sessionData));
        } catch (e) {
            console.error("Failed to persist clock out state:", e);
        }
    }

    function showSuccess(record, titleMessage) {
        if (formCard) formCard.style.display = "none";
        if (quickCard) quickCard.style.display = "none";
        if (successCard) successCard.style.display = "block";

        document.getElementById("resTitle").textContent = titleMessage;
        document.getElementById("resName").textContent = record.student_name || "Student";
        document.getElementById("resEmail").textContent = record.student_email;
        document.getElementById("resBranch").textContent = record.branch || "Popoola Branch";
        const sessionEl = document.getElementById("resSession");
        if (sessionEl) sessionEl.textContent = record.session_type || "Morning Session";
        document.getElementById("resTimeIn").textContent = record.time_in || "N/A";
        document.getElementById("resTimeOut").textContent = record.time_out || "Recorded";
        document.getElementById("resDuration").textContent = record.duration_formatted || "< 1 min";
    }

    function showAlert(msg, type = "danger") {
        alertBox.className = `alert alert-${type}`;
        alertBox.textContent = msg;
        alertBox.style.display = "flex";
    }

    function hideAlert() {
        alertBox.style.display = "none";
    }
});
