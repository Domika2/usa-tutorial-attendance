// Clock-In Page Logic
document.addEventListener("DOMContentLoaded", () => {
    const timeEl = document.getElementById("liveTime");
    const dateEl = document.getElementById("liveDate");
    const form = document.getElementById("clockInForm");
    const nameInput = document.getElementById("studentName");
    const emailInput = document.getElementById("studentEmail");
    const branchInput = document.getElementById("studentBranch");
    const sessionInput = document.getElementById("classSession");
    const callInput = document.getElementById("studentCallNumber");
    const whatsappInput = document.getElementById("studentWhatsapp");
    const sameAsCallCheck = document.getElementById("sameAsCallCheck");
    const parentPhoneInput = document.getElementById("parentPhone");
    const rememberCheckbox = document.getElementById("rememberMe");
    const submitBtn = document.getElementById("clockInBtn");
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

    // Same as Call Number helper
    if (sameAsCallCheck && whatsappInput && callInput) {
        sameAsCallCheck.addEventListener("change", () => {
            if (sameAsCallCheck.checked) {
                whatsappInput.value = callInput.value.trim();
            }
        });
        callInput.addEventListener("input", () => {
            if (sameAsCallCheck.checked) {
                whatsappInput.value = callInput.value.trim();
            }
        });
    }

    function getApiUrl(endpoint) {
        if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
        return endpoint;
    }

    // Unified fetch with automatic 5-second retry for cold starts
    async function fetchWithRetry(url, options = {}, retries = 1, onStatus = null) {
        try {
            const res = await fetch(url, options);
            if (!res.ok && [502, 503, 504].includes(res.status) && retries > 0) {
                throw new Error(`Server status ${res.status}`);
            }
            return res;
        } catch (err) {
            if (retries > 0) {
                const wakeupMsg = "Connecting to server (waking up free tier)...";
                if (typeof onStatus === "function") {
                    onStatus(wakeupMsg);
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
                return fetchWithRetry(url, options, retries - 1, onStatus);
            }
            throw err;
        }
    }

    // Fetch server info
    fetchWithRetry(getApiUrl("/api/server-info"), {}, 1)
        .then(res => res.json())
        .then(data => {
            if (data.centre_name && centreNameEl) {
                centreNameEl.textContent = data.centre_name;
            }
        })
        .catch(console.error);

    // UI Elements
    const quickCard = document.getElementById("quickClockInCard");
    const quickNameEl = document.getElementById("quickStudentName");
    const quickEmailEl = document.getElementById("quickStudentEmail");
    const quickBranchEl = document.getElementById("quickBranch");
    const quickSessionEl = document.getElementById("quickSession");
    const quickPhoneEl = document.getElementById("quickPhone");
    const quickAvatarEl = document.getElementById("quickAvatar");
    const quickClockInBtn = document.getElementById("quickClockInBtn");
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

    function getSavedProfile() {
        try {
            const json = localStorage.getItem("tutorial_student_profile");
            if (json) {
                const p = JSON.parse(json);
                if (p && p.name && p.email) return p;
            }
        } catch (e) {}

        const name = localStorage.getItem("tutorial_student_name");
        const email = localStorage.getItem("tutorial_student_email");
        if (name && email) {
            return {
                name,
                email,
                branch: localStorage.getItem("tutorial_student_branch") || "Popoola Branch",
                session_type: localStorage.getItem("tutorial_student_session") || "Morning Session",
                call_number: localStorage.getItem("tutorial_student_call") || "",
                whatsapp_number: localStorage.getItem("tutorial_student_whatsapp") || "",
                parent_phone: localStorage.getItem("tutorial_student_parent_phone") || ""
            };
        }
        return null;
    }

    function saveProfile(profile) {
        localStorage.setItem("tutorial_student_profile", JSON.stringify(profile));
        localStorage.setItem("tutorial_student_name", profile.name);
        localStorage.setItem("tutorial_student_email", profile.email);
        localStorage.setItem("tutorial_student_branch", profile.branch);
        localStorage.setItem("tutorial_student_session", profile.session_type);
        localStorage.setItem("tutorial_student_call", profile.call_number);
        localStorage.setItem("tutorial_student_whatsapp", profile.whatsapp_number);
        localStorage.setItem("tutorial_student_parent_phone", profile.parent_phone);
    }

    // Check if this device has already clocked in for today
    const todayISO = new Date().toISOString().split("T")[0];
    const savedActiveClockinJson = localStorage.getItem("tutorial_active_clockin");
    if (savedActiveClockinJson) {
        try {
            const activeData = JSON.parse(savedActiveClockinJson);
            if (activeData.date === todayISO) {
                // Device is locked into today's active session
                showSuccess(activeData, "Attendance Recorded for Today");
                return;
            } else {
                localStorage.removeItem("tutorial_active_clockin");
            }
        } catch (e) {
            localStorage.removeItem("tutorial_active_clockin");
        }
    }

    // Read branch and attendance token from URL params if arrived via QR code
    const urlParams = new URLSearchParams(window.location.search);
    const paramBranch = urlParams.get("branch");
    const paramToken = urlParams.get("attendance_token") || urlParams.get("token");

    if (paramToken) {
        localStorage.setItem("tutorial_attendance_token", paramToken);
    }

    let studentProfile = getSavedProfile();

    // If QR code specified branch, update profile's branch for today
    if (paramBranch && studentProfile) {
        studentProfile.branch = paramBranch;
        saveProfile(studentProfile);
    }

    function setupViews() {
        if (studentProfile && studentProfile.name && studentProfile.email) {
            // Returning Student: Show 1-Tap Quick Clock-In Card!
            if (formCard) formCard.style.display = "none";
            if (quickCard) quickCard.style.display = "block";

            if (quickNameEl) quickNameEl.textContent = studentProfile.name;
            if (quickEmailEl) quickEmailEl.textContent = studentProfile.email;
            if (quickBranchEl) quickBranchEl.textContent = studentProfile.branch || "Popoola Branch";
            if (quickSessionEl) quickSessionEl.textContent = studentProfile.session_type || "Morning Session";
            if (quickPhoneEl) quickPhoneEl.textContent = studentProfile.call_number || "--";
            if (quickAvatarEl) quickAvatarEl.textContent = getInitials(studentProfile.name);
        } else {
            // First time: Show full registration form so student fills details once
            if (quickCard) quickCard.style.display = "none";
            if (formCard) formCard.style.display = "block";
            if (branchInput && paramBranch) branchInput.value = paramBranch;
        }
    }

    setupViews();

    // 1-Tap Quick Clock-In Button Handler
    if (quickClockInBtn) {
        quickClockInBtn.addEventListener("click", () => {
            if (!studentProfile) return;
            performClockIn(studentProfile, quickClockInBtn, quickAlertBox);
        });
    }

    // Edit details link
    if (editDetailsLink) {
        editDetailsLink.addEventListener("click", (e) => {
            e.preventDefault();
            if (quickCard) quickCard.style.display = "none";
            if (formCard) formCard.style.display = "block";
            if (cancelEditContainer) cancelEditContainer.style.display = "block";

            if (studentProfile) {
                if (nameInput) nameInput.value = studentProfile.name || "";
                if (emailInput) emailInput.value = studentProfile.email || "";
                if (branchInput) branchInput.value = studentProfile.branch || "Popoola Branch";
                if (sessionInput) sessionInput.value = studentProfile.session_type || "Morning Session";
                if (callInput) callInput.value = studentProfile.call_number || "";
                if (whatsappInput) whatsappInput.value = studentProfile.whatsapp_number || "";
                if (parentPhoneInput) parentPhoneInput.value = studentProfile.parent_phone || "";
            }
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

    // Handle Clock In Form submission (First-time or edit)
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();

        const name = nameInput.value.trim();
        const email = emailInput.value.trim().toLowerCase();
        const branch = branchInput.value.trim();
        const session_type = sessionInput ? sessionInput.value.trim() : "Morning Session";
        const call_number = callInput ? callInput.value.trim() : "";
        const whatsapp_number = whatsappInput ? whatsappInput.value.trim() : call_number;
        const parent_phone = parentPhoneInput ? parentPhoneInput.value.trim() : "";

        if (!name || !email || !branch) {
            showAlert("Please fill in your Name, Email, and Tutorial Branch.", "danger");
            return;
        }

        if (!call_number) {
            showAlert("Student's Call Number is required.", "danger");
            return;
        }

        if (!whatsapp_number) {
            showAlert("Student's WhatsApp Number is required.", "danger");
            return;
        }

        if (!parent_phone) {
            showAlert("Parent's Phone Number is required.", "danger");
            return;
        }

        const profileData = {
            name,
            email,
            branch,
            session_type,
            call_number,
            whatsapp_number,
            parent_phone
        };

        // Save profile permanently so student never has to fill details again!
        saveProfile(profileData);
        studentProfile = profileData;

        // Perform Clock In
        await performClockIn(profileData, submitBtn, alertBox);
    });

    async function performClockIn(profile, triggerBtn, alertEl) {
        if (triggerBtn) {
            triggerBtn.disabled = true;
            triggerBtn.innerHTML = `<span>Clocking in...</span>`;
        }
        if (alertEl) alertEl.style.display = "none";

        const attendanceToken = urlParams.get("attendance_token") ||
                               urlParams.get("token") ||
                               localStorage.getItem("tutorial_attendance_token") ||
                               "PERMANENT_SESSION_KEY";

        const clockInPayload = {
            ...profile,
            attendance_token: attendanceToken,
            token: attendanceToken
        };

        try {
            const res = await fetchWithRetry(getApiUrl("/api/attendance/clock-in"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(clockInPayload)
            }, 1, (statusMsg) => {
                if (triggerBtn) triggerBtn.innerHTML = `<span>⏳ ${statusMsg}</span>`;
                if (alertEl) {
                    alertEl.className = "alert alert-info";
                    alertEl.textContent = statusMsg;
                    alertEl.style.display = "flex";
                }
            });

            const data = await res.json();

            if (res.ok && data.success) {
                const rec = data.record || {};
                persistActiveClockIn(rec, profile);
                showSuccess(rec, "Welcome! Clock-In Successfully Recorded.");
            } else if (data.already_clocked_in) {
                const rec = data.record || {};
                persistActiveClockIn(rec, profile);
                showSuccess(rec, "You are already clocked in for today's session.");
            } else {
                const msg = data.message || "Could not clock in. Please try again.";
                if (alertEl) {
                    alertEl.className = "alert alert-danger";
                    alertEl.textContent = msg;
                    alertEl.style.display = "flex";
                } else {
                    showAlert(msg, "danger");
                }
            }
        } catch (err) {
            console.error("Clock-in error:", err);
            const msg = "Could not connect to backend server. Please check your network connection and try again.";
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
                if (triggerBtn === quickClockInBtn) {
                    triggerBtn.innerHTML = `<span>⚡ Click to Clock In</span>`;
                } else {
                    triggerBtn.innerHTML = `<span>Clock In</span> <span>➔</span>`;
                }
            }
        }
    }

    function persistActiveClockIn(record, profile = {}) {
        try {
            const activeData = {
                date: record.date || todayISO,
                student_name: record.student_name || profile.name || "",
                student_email: record.student_email || profile.email || "",
                branch: record.branch || profile.branch || "Popoola Branch",
                session_type: record.session_type || profile.session_type || "Morning Session",
                call_number: record.call_number || profile.call_number || "",
                parent_phone: record.parent_phone || profile.parent_phone || "",
                time_in: record.time_in || new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
            };
            localStorage.setItem("tutorial_active_clockin", JSON.stringify(activeData));
        } catch (e) {
            console.error("Storage error:", e);
        }
    }

    function showSuccess(record, titleMessage) {
        if (formCard) formCard.style.display = "none";
        if (quickCard) quickCard.style.display = "none";
        if (successCard) successCard.style.display = "block";

        const resTitle = document.getElementById("resTitle");
        const resName = document.getElementById("resName");
        const resEmail = document.getElementById("resEmail");
        const resBranch = document.getElementById("resBranch");
        const sessionEl = document.getElementById("resSession");
        const phoneEl = document.getElementById("resPhone");
        const parentPhoneEl = document.getElementById("resParentPhone");
        const resTimeIn = document.getElementById("resTimeIn");
        const resDate = document.getElementById("resDate");

        if (resTitle) resTitle.textContent = titleMessage;
        if (resName) resName.textContent = record.student_name || "Student";
        if (resEmail) resEmail.textContent = record.student_email || "";
        if (resBranch) resBranch.textContent = record.branch || "Popoola Branch";
        if (sessionEl) sessionEl.textContent = record.session_type || "Morning Session";
        if (phoneEl) phoneEl.textContent = record.call_number || "--";
        if (parentPhoneEl) parentPhoneEl.textContent = record.parent_phone || "--";
        if (resTimeIn) resTimeIn.textContent = record.time_in || "--";
        if (resDate) resDate.textContent = record.date || todayISO;
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

