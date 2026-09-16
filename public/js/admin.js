// Admin Dashboard Logic
document.addEventListener("DOMContentLoaded", () => {
    function getApiUrl(endpoint) {
        if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
        if (window.location.port === "5000") return endpoint;
        const host = window.location.hostname && window.location.hostname !== "" ? window.location.hostname : "127.0.0.1";
        return `http://${host}:5000${endpoint}`;
    }

    const authModal = document.getElementById("authModal");
    const staffLoginForm = document.getElementById("staffLoginForm");
    const staffLoginName = document.getElementById("staffLoginName");
    const staffLoginPassword = document.getElementById("staffLoginPassword");
    const pinSubmitBtn = document.getElementById("pinSubmitBtn");
    const pinError = document.getElementById("pinError");
    const pinSuccess = document.getElementById("pinSuccess");

    // Create Password Form Elements
    const createPasswordForm = document.getElementById("createPasswordForm");
    const createFullName = document.getElementById("createFullName");
    const createUsername = document.getElementById("createUsername");
    const createPassword = document.getElementById("createPassword");
    const createRole = document.getElementById("createRole");
    const createSubmitBtn = document.getElementById("createSubmitBtn");
    const setupBanner = document.getElementById("setupBanner");
    const tabSignIn = document.getElementById("tabSignIn");
    const tabCreatePassword = document.getElementById("tabCreatePassword");

    // Password Toggles
    const toggleLoginPass = document.getElementById("toggleLoginPass");
    const toggleCreatePass = document.getElementById("toggleCreatePass");

    // Change Password Modal Elements
    const changePassModal = document.getElementById("changePassModal");
    const openChangePassBtn = document.getElementById("openChangePassBtn");
    const closeChangePassBtn = document.getElementById("closeChangePassBtn");
    const changePassForm = document.getElementById("changePassForm");
    const changePassAlert = document.getElementById("changePassAlert");
    const currPassInput = document.getElementById("currPass");
    const newPassInput = document.getElementById("newPass");
    const confirmPassInput = document.getElementById("confirmPass");
    const toggleCurrPass = document.getElementById("toggleCurrPass");
    const toggleNewPass = document.getElementById("toggleNewPass");
    const toggleConfirmPass = document.getElementById("toggleConfirmPass");
    const savePassBtn = document.getElementById("savePassBtn");

    const adminLogoutBtn = document.getElementById("adminLogoutBtn");
    const adminDashboardView = document.getElementById("adminDashboardView");
    const centreTitleEl = document.getElementById("centreTitle");
    const badgeStaffName = document.getElementById("badgeStaffName");
    const badgeStaffRole = document.getElementById("badgeStaffRole");
    
    // Stats elements
    const statInside = document.getElementById("statInside");
    const statToday = document.getElementById("statToday");
    const statCompleted = document.getElementById("statCompleted");
    const statAvgDuration = document.getElementById("statAvgDuration");

    // Table elements
    const recordsTableBody = document.getElementById("recordsTableBody");
    const tableEmptyState = document.getElementById("tableEmptyState");
    const searchInput = document.getElementById("searchInput");
    const branchFilter = document.getElementById("branchFilter");
    const sessionFilter = document.getElementById("sessionFilter");
    const dateFilter = document.getElementById("dateFilter");
    const statusFilter = document.getElementById("statusFilter");
    const refreshBtn = document.getElementById("refreshBtn");
    const exportBtn = document.getElementById("exportBtn");
    const recordCountEl = document.getElementById("recordCount");

    // Absentee alerts elements
    const absenteeSection = document.getElementById("absenteeAlertsSection");
    const absenteeList = document.getElementById("absenteeAlertsList");
    const absenteeBadge = document.getElementById("absenteeBadgeCount");
    const adminQrRefreshBtn = document.getElementById("adminQrRefreshBtn");

    // Manual Entry Modal elements
    const manualModal = document.getElementById("manualModal");
    const openManualBtn = document.getElementById("openManualBtn");
    const closeManualBtn = document.getElementById("closeManualBtn");
    const manualForm = document.getElementById("manualForm");
    const manualAlert = document.getElementById("manualAlert");

    let authToken = sessionStorage.getItem("admin_auth_token");
    let currentStaffName = sessionStorage.getItem("staff_name") || "Staff";
    let currentStaffRole = sessionStorage.getItem("staff_role") || "Director";
    let currentUsername = sessionStorage.getItem("admin_username") || "admin";
    let autoRefreshTimer = null;
    let realtimeSyncTimer = null;
    let currentDataVersion = 0;
    let isRealtimeUpdating = false;

    // Password Toggle Helper
    function wirePasswordToggle(btn, input) {
        if (!btn || !input) return;
        btn.addEventListener("click", () => {
            if (input.type === "password") {
                input.type = "text";
                btn.textContent = "🙈";
            } else {
                input.type = "password";
                btn.textContent = "👁️";
            }
        });
    }

    wirePasswordToggle(toggleLoginPass, staffLoginPassword);
    wirePasswordToggle(toggleCreatePass, createPassword);
    wirePasswordToggle(toggleCurrPass, currPassInput);
    wirePasswordToggle(toggleNewPass, newPassInput);
    wirePasswordToggle(toggleConfirmPass, confirmPassInput);

    // Tab Switching in Modal
    function switchModalTab(tab) {
        clearAuthAlerts();
        if (tab === "signin") {
            if (tabSignIn) tabSignIn.classList.add("active");
            if (tabCreatePassword) tabCreatePassword.classList.remove("active");
            if (staffLoginForm) staffLoginForm.style.display = "block";
            if (createPasswordForm) createPasswordForm.style.display = "none";
            if (staffLoginName) staffLoginName.focus();
        } else {
            if (tabCreatePassword) tabCreatePassword.classList.add("active");
            if (tabSignIn) tabSignIn.classList.remove("active");
            if (createPasswordForm) createPasswordForm.style.display = "block";
            if (staffLoginForm) staffLoginForm.style.display = "none";
            if (createFullName) createFullName.focus();
        }
    }

    if (tabSignIn) tabSignIn.addEventListener("click", () => switchModalTab("signin"));
    if (tabCreatePassword) tabCreatePassword.addEventListener("click", () => switchModalTab("create"));

    // Check Auth Status from server
    async function checkAuthStatus() {
        try {
            const res = await fetch(getApiUrl("/api/admin/auth-status"));
            const data = await res.json();
            if (data.centre_name && centreTitleEl) centreTitleEl.textContent = data.centre_name;
            if (!data.has_admin) {
                if (setupBanner) setupBanner.style.display = "flex";
                switchModalTab("create");
            } else {
                if (setupBanner) setupBanner.style.display = "none";
                switchModalTab("signin");
            }
        } catch (e) {
            console.error("Auth status check failed:", e);
        }
    }

    // Set today's date in date filter by default
    const todayISO = new Date().toISOString().split("T")[0];
    if (dateFilter) dateFilter.value = todayISO;

    // Real-time synchronization check on every clock-in & clock-out
    async function checkForRealtimeUpdates() {
        if (!authToken || isRealtimeUpdating) return;
        try {
            const res = await fetch(getApiUrl(`/api/admin/check-updates?token=${encodeURIComponent(authToken)}&version=${currentDataVersion}`));
            if (res.status === 401) return;
            if (!res.ok) return;
            const data = await res.json();
            if (data.updated) {
                isRealtimeUpdating = true;
                currentDataVersion = data.version;
                await Promise.all([
                    loadDashboardData(true),
                    loadRecords(true)
                ]);
                flashLiveSyncIndicator();
                isRealtimeUpdating = false;
            } else if (currentDataVersion === 0 && data.version) {
                currentDataVersion = data.version;
            }
        } catch (e) {
            isRealtimeUpdating = false;
        }
    }

    function flashLiveSyncIndicator() {
        const badge = document.getElementById("liveSyncBadge");
        if (badge) {
            badge.style.transform = "scale(1.15)";
            badge.style.background = "#86efac";
            badge.style.borderColor = "#22c55e";
            setTimeout(() => {
                badge.style.transform = "scale(1)";
                badge.style.background = "#dcfce7";
                badge.style.borderColor = "#bbf7d0";
            }, 600);
        }
    }

    // Check Authentication
    function checkAuth() {
        if (!authToken) {
            authModal.classList.add("open");
            adminDashboardView.style.display = "none";
            if (autoRefreshTimer) clearInterval(autoRefreshTimer);
            if (realtimeSyncTimer) clearInterval(realtimeSyncTimer);
            checkAuthStatus();
        } else {
            authModal.classList.remove("open");
            adminDashboardView.style.display = "block";
            
            if (badgeStaffName) badgeStaffName.textContent = currentStaffName;
            if (badgeStaffRole) badgeStaffRole.textContent = currentStaffRole;

            loadDashboardData();
            loadRecords();

            // Instant updates at every clock-in and clock-out (1.5s live polling)
            if (!realtimeSyncTimer) {
                realtimeSyncTimer = setInterval(checkForRealtimeUpdates, 1500);
            }

            if (!autoRefreshTimer) {
                autoRefreshTimer = setInterval(() => {
                    loadDashboardData(true);
                    loadRecords(true);
                }, 30000);
            }
        }
    }

    // Handle Staff / Admin Login Form
    if (staffLoginForm) {
        staffLoginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAuthAlerts();
            const username = staffLoginName.value.trim();
            const password = staffLoginPassword.value.trim();

            if (!username || !password) {
                showPinError("Please enter your username and password.");
                return;
            }

            pinSubmitBtn.disabled = true;
            pinSubmitBtn.textContent = "Verifying Password...";

            try {
                const res = await fetch(getApiUrl("/api/admin/login"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    authToken = data.token;
                    currentStaffName = data.staff_name;
                    currentStaffRole = data.staff_role;
                    currentUsername = data.username || username;
                    sessionStorage.setItem("admin_auth_token", authToken);
                    sessionStorage.setItem("staff_name", currentStaffName);
                    sessionStorage.setItem("staff_role", currentStaffRole);
                    sessionStorage.setItem("admin_username", currentUsername);
                    if (data.centre_name && centreTitleEl) centreTitleEl.textContent = data.centre_name;
                    checkAuth();
                } else {
                    showPinError(data.message || "Invalid username or password.");
                }
            } catch (err) {
                console.error("Login error:", err);
                showPinError("Could not connect to backend server. Ensure 'py server.py' is running on port 5000.");
            } finally {
                pinSubmitBtn.disabled = false;
                pinSubmitBtn.textContent = "Sign In to Dashboard ➔";
            }
        });
    }

    // Handle Create Admin Password Form
    if (createPasswordForm) {
        createPasswordForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAuthAlerts();
            const full_name = createFullName.value.trim();
            const username = createUsername.value.trim();
            const password = createPassword.value.trim();
            const role = createRole.value.trim();

            if (!full_name || !username || !password) {
                showPinError("Please fill out all fields.");
                return;
            }

            if (password.length < 6) {
                showPinError("Password must be at least 6 characters long.");
                return;
            }

            createSubmitBtn.disabled = true;
            createSubmitBtn.textContent = "Creating Password...";

            try {
                const res = await fetch(getApiUrl("/api/admin/create-password"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ full_name, username, password, role })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    showPinSuccess("Admin password created successfully! Entering dashboard...");
                    authToken = data.token;
                    currentStaffName = data.staff_name;
                    currentStaffRole = data.staff_role;
                    currentUsername = data.username || username;
                    sessionStorage.setItem("admin_auth_token", authToken);
                    sessionStorage.setItem("staff_name", currentStaffName);
                    sessionStorage.setItem("staff_role", currentStaffRole);
                    sessionStorage.setItem("admin_username", currentUsername);
                    setTimeout(() => {
                        checkAuth();
                    }, 800);
                } else {
                    showPinError(data.message || "Failed to create admin password.");
                    createSubmitBtn.disabled = false;
                    createSubmitBtn.textContent = "Create Password & Enter Dashboard ➔";
                }
            } catch (err) {
                console.error("Create password error:", err);
                showPinError("Could not connect to backend server. Ensure 'py server.py' is running on port 5000.");
                createSubmitBtn.disabled = false;
                createSubmitBtn.textContent = "Create Password & Enter Dashboard ➔";
            }
        });
    }

    // Change Password Modal Handlers
    if (openChangePassBtn) {
        openChangePassBtn.addEventListener("click", () => {
            changePassModal.classList.add("open");
            changePassForm.reset();
            changePassAlert.style.display = "none";
            currPassInput.focus();
        });
    }

    if (closeChangePassBtn) {
        closeChangePassBtn.addEventListener("click", () => {
            changePassModal.classList.remove("open");
        });
    }

    if (changePassForm) {
        changePassForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const old_password = currPassInput.value.trim();
            const new_password = newPassInput.value.trim();
            const confirm_password = confirmPassInput.value.trim();

            if (!old_password || !new_password) {
                showChangePassAlert("Current and new passwords are required.", "danger");
                return;
            }

            if (new_password.length < 6) {
                showChangePassAlert("New password must be at least 6 characters long.", "danger");
                return;
            }

            if (new_password !== confirm_password) {
                showChangePassAlert("New password and confirmation do not match.", "danger");
                return;
            }

            savePassBtn.disabled = true;
            savePassBtn.textContent = "Updating...";

            try {
                const res = await fetch(getApiUrl("/api/admin/change-password"), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        username: currentUsername,
                        old_password,
                        new_password
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    showChangePassAlert("Password updated successfully!", "success");
                    setTimeout(() => {
                        changePassModal.classList.remove("open");
                    }, 1200);
                } else {
                    showChangePassAlert(data.message || "Failed to update password.", "danger");
                }
            } catch (err) {
                console.error("Change password error:", err);
                showChangePassAlert("Could not connect to backend server. Ensure 'py server.py' is running on port 5000.", "danger");
            } finally {
                savePassBtn.disabled = false;
                savePassBtn.textContent = "Update Password";
            }
        });
    }

    function showChangePassAlert(msg, type = "danger") {
        changePassAlert.className = `alert alert-${type}`;
        changePassAlert.textContent = msg;
        changePassAlert.style.display = "flex";
    }

    function clearAuthAlerts() {
        if (pinError) pinError.style.display = "none";
        if (pinSuccess) pinSuccess.style.display = "none";
    }

    function showPinError(msg) {
        if (pinError) {
            pinError.textContent = msg;
            pinError.style.display = "flex";
        }
        if (pinSuccess) pinSuccess.style.display = "none";
    }

    function showPinSuccess(msg) {
        if (pinSuccess) {
            pinSuccess.textContent = msg;
            pinSuccess.style.display = "flex";
        }
        if (pinError) pinError.style.display = "none";
    }

    // Logout
    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            sessionStorage.removeItem("admin_auth_token");
            sessionStorage.removeItem("staff_name");
            sessionStorage.removeItem("staff_role");
            sessionStorage.removeItem("admin_username");
            authToken = null;
            checkAuth();
        });
    }

    // Load Dashboard Stats
    async function loadDashboardData(silent = false) {
        if (!authToken) return;
        const branch = branchFilter ? branchFilter.value : "ALL";

        try {
            const res = await fetch(getApiUrl(`/api/admin/dashboard?token=${encodeURIComponent(authToken)}&branch=${encodeURIComponent(branch)}`));
            if (res.status === 401) {
                sessionStorage.removeItem("admin_auth_token");
                authToken = null;
                checkAuth();
                return;
            }

            const data = await res.json();
            if (data.stats) {
                const s = data.stats;
                if (statInside) statInside.textContent = s.currently_inside;
                if (statToday) statToday.textContent = s.total_today;
                if (statCompleted) statCompleted.textContent = s.clocked_out_today;
                if (statAvgDuration) statAvgDuration.textContent = s.avg_duration_today;
            }
            if (data.staff) {
                currentStaffName = data.staff.staff_name;
                currentStaffRole = data.staff.staff_role;
                if (badgeStaffName) badgeStaffName.textContent = currentStaffName;
                if (badgeStaffRole) badgeStaffRole.textContent = currentStaffRole;
            }
            // Render Absentee Alerts
            renderAbsenteeAlerts(data.absentee_alerts || []);
        } catch (err) {
            if (!silent) console.error("Error loading stats:", err);
        }
    }

    // Render Absentee Alerts
    function renderAbsenteeAlerts(alerts) {
        if (!absenteeSection || !absenteeList) return;

        if (!alerts || alerts.length === 0) {
            absenteeSection.style.display = "none";
            return;
        }

        absenteeSection.style.display = "block";
        if (absenteeBadge) absenteeBadge.textContent = alerts.length;

        absenteeList.innerHTML = alerts.map(a => {
            const studentCallHref = a.call_number ? `tel:${encodeURIComponent(a.call_number)}` : '#';
            const rawPhone = (a.whatsapp_number || a.call_number || '').replace(/[^0-9]/g, '');
            const waHref = rawPhone ? `https://wa.me/${rawPhone}` : '#';
            const parentCallHref = a.parent_phone ? `tel:${encodeURIComponent(a.parent_phone)}` : '#';

            return `
                <div class="alert-item-card" style="background: white; border: 1px solid #fecaca; border-radius: 8px; padding: 0.85rem 1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                            <span style="font-weight: 700; color: #111827; font-size: 0.95rem;">${escapeHtml(a.student_name)}</span>
                            <span class="badge-branch">${escapeHtml(a.branch)}</span>
                            <span class="badge" style="background: #fef3c7; color: #92400e; font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px;">
                                ${escapeHtml(a.session_label || a.session_type)}
                            </span>
                        </div>
                        <div style="font-size: 0.82rem; color: #4b5563; margin-bottom: 0.4rem;">
                            Email: <strong>${escapeHtml(a.student_email)}</strong> • ${escapeHtml(a.message)}
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            ${a.call_number ? `<a href="${studentCallHref}" class="btn btn-outline btn-sm" style="font-size: 0.76rem; padding: 0.2rem 0.55rem; color: #1d4ed8; border-color: #bfdbfe;">📞 Call Student: ${escapeHtml(a.call_number)}</a>` : ''}
                            ${rawPhone ? `<a href="${waHref}" target="_blank" class="btn btn-outline btn-sm" style="font-size: 0.76rem; padding: 0.2rem 0.55rem; color: #15803d; border-color: #bbf7d0;">💬 WhatsApp</a>` : ''}
                            ${a.parent_phone ? `<a href="${parentCallHref}" class="btn btn-outline btn-sm" style="font-size: 0.76rem; padding: 0.2rem 0.55rem; color: #7c3aed; border-color: #ddd6fe;">👨‍👩‍👧 Call Parent: ${escapeHtml(a.parent_phone)}</a>` : ''}
                        </div>
                    </div>
                    <div>
                        <button type="button" class="btn btn-sm btn-ack-alert" data-email="${escapeHtml(a.student_email)}" data-session="${escapeHtml(a.session_type)}" data-date="${escapeHtml(a.date)}" style="background: #10b981; color: white; border: none; font-weight: 600; padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer;">
                            ✓ Okay
                        </button>
                    </div>
                </div>
            `;
        }).join("");

        // Attach Okay button listener
        absenteeList.querySelectorAll(".btn-ack-alert").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const email = e.currentTarget.getAttribute("data-email");
                const session = e.currentTarget.getAttribute("data-session");
                const date = e.currentTarget.getAttribute("data-date");
                btn.disabled = true;
                btn.textContent = "Updating...";
                try {
                    const res = await fetch(getApiUrl(`/api/admin/acknowledge-alert?token=${encodeURIComponent(authToken)}`), {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, session_type: session, date })
                    });
                    if (res.ok) {
                        loadDashboardData();
                    }
                } catch (err) {
                    console.error("Failed acknowledging alert:", err);
                    btn.disabled = false;
                    btn.textContent = "✓ Okay";
                }
            });
        });
    }

    // QR Refresh Handler
    if (adminQrRefreshBtn) {
        adminQrRefreshBtn.addEventListener("click", async () => {
            if (!confirm("Refresh the Daily QR Codes for Popoola Branch and Kilimanjaro Branch?")) return;
            adminQrRefreshBtn.disabled = true;
            adminQrRefreshBtn.textContent = "Refreshing...";
            try {
                const res = await fetch(getApiUrl(`/api/admin/refresh-qr?token=${encodeURIComponent(authToken)}`), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert(`Daily QR Code refreshed successfully!\nDate: ${data.qr_info.date} at ${data.qr_info.time}\n\nYou can now print the updated posters.`);
                } else {
                    alert(data.message || "Failed to refresh QR codes.");
                }
            } catch (err) {
                alert("Network error refreshing QR codes.");
            } finally {
                adminQrRefreshBtn.disabled = false;
                adminQrRefreshBtn.textContent = "🔄 QR Refresh";
            }
        });
    }

    // Load Attendance Records
    async function loadRecords(silent = false) {
        if (!authToken) return;

        const search = searchInput ? searchInput.value.trim() : "";
        const branch = branchFilter ? branchFilter.value : "ALL";
        const session = sessionFilter ? sessionFilter.value : "ALL";
        const date = dateFilter ? dateFilter.value : "";
        const status = statusFilter ? statusFilter.value : "ALL";

        const url = `/api/admin/records?token=${encodeURIComponent(authToken)}&search=${encodeURIComponent(search)}&date=${encodeURIComponent(date)}&status=${encodeURIComponent(status)}&branch=${encodeURIComponent(branch)}`;

        try {
            const res = await fetch(getApiUrl(url));
            if (res.status === 401) return;

            const data = await res.json();
            let records = data.records || [];
            if (session && session !== "ALL") {
                records = records.filter(r => (r.session_type || "Morning Session") === session);
            }
            renderRecordsTable(records);
        } catch (err) {
            if (!silent) console.error("Error loading records:", err);
        }
    }

    // Render Table
    function renderRecordsTable(records) {
        if (recordCountEl) recordCountEl.textContent = `${records.length} record${records.length === 1 ? '' : 's'}`;

        if (!records || records.length === 0) {
            recordsTableBody.innerHTML = "";
            tableEmptyState.style.display = "block";
            return;
        }

        tableEmptyState.style.display = "none";
        recordsTableBody.innerHTML = records.map(r => {
            const isInside = r.status === 'CLOCKED_IN';
            const badgeClass = isInside ? 'badge-status-in' : 'badge-status-out';
            const badgeText = isInside ? '● In Session' : '✓ Completed';
            const timeOutDisplay = r.time_out ? `<span class="time-mono">${r.time_out}</span>` : `<span style="color:var(--text-muted)">--</span>`;
            const durationDisplay = r.duration_formatted ? `<span class="time-mono" style="color:var(--purple-700);font-weight:600">${r.duration_formatted}</span>` : `<span style="color:var(--text-muted)">--</span>`;
            const branchText = r.branch || "Popoola Branch";
            const sessionText = r.session_type || "Morning Session";
            const studentPhone = r.call_number || "--";
            const parentPhone = r.parent_phone ? `<span style="font-size:0.75rem;color:var(--text-muted)">Parent: ${escapeHtml(r.parent_phone)}</span>` : "";

            return `
                <tr>
                    <td style="color:var(--text-muted);font-family:var(--font-mono);font-size:0.78rem">#${r.id}</td>
                    <td>
                        <div style="display:flex;flex-direction:column;">
                            <span style="font-weight:600;color:var(--text-main);">${escapeHtml(r.student_name)}</span>
                            <span style="font-size:0.78rem;color:var(--text-muted);">${escapeHtml(r.student_email)}</span>
                        </div>
                    </td>
                    <td><span class="badge-branch">${escapeHtml(branchText)}</span></td>
                    <td><span class="badge" style="background:var(--purple-50);color:var(--purple-800);font-size:0.78rem;padding:0.2rem 0.5rem;border-radius:4px;">${escapeHtml(sessionText)}</span></td>
                    <td>
                        <div style="display:flex;flex-direction:column;font-size:0.78rem;">
                            <span class="time-mono" style="color:var(--blue-700);font-weight:600">${escapeHtml(studentPhone)}</span>
                            ${parentPhone}
                        </div>
                    </td>
                    <td class="time-mono">${escapeHtml(r.date)}</td>
                    <td><span class="time-mono highlight-blue">${escapeHtml(r.time_in)}</span></td>
                    <td>${timeOutDisplay}</td>
                    <td>${durationDisplay}</td>
                    <td><span class="${badgeClass}">${badgeText}</span></td>
                    <td>
                        <button class="btn btn-outline btn-sm btn-delete" data-id="${r.id}" title="Delete record" style="padding:0.25rem 0.5rem;color:var(--red-600);border-color:var(--red-100);">
                            🗑️
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        // Delete listeners
        document.querySelectorAll(".btn-delete").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const id = e.currentTarget.getAttribute("data-id");
                if (confirm(`Are you sure you want to delete attendance record #${id}?`)) {
                    await deleteRecord(id);
                }
            });
        });
    }

    async function deleteRecord(id) {
        try {
            const res = await fetch(getApiUrl(`/api/admin/record/${id}?token=${encodeURIComponent(authToken)}`), {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok && data.success) {
                loadRecords();
                loadDashboardData();
            } else {
                alert(data.message || "Failed to delete record.");
            }
        } catch (err) {
            alert("Error communicating with server.");
        }
    }

    // Export CSV
    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
            const search = searchInput ? searchInput.value.trim() : "";
            const branch = branchFilter ? branchFilter.value : "ALL";
            const date = dateFilter ? dateFilter.value : "";
            const status = statusFilter ? statusFilter.value : "ALL";
            const exportUrl = getApiUrl(`/api/admin/export?token=${encodeURIComponent(authToken)}&search=${encodeURIComponent(search)}&date=${encodeURIComponent(date)}&status=${encodeURIComponent(status)}&branch=${encodeURIComponent(branch)}`);
            window.location.href = exportUrl;
        });
    }

    // Clear Records from database
    const clearAllBtn = document.getElementById("clearAllBtn");
    if (clearAllBtn) {
        clearAllBtn.addEventListener("click", async () => {
            const branch = branchFilter ? branchFilter.value : "ALL";
            const targetScope = branch === "ALL" ? "all branches" : branch;
            if (!confirm(`⚠️ PERMANENT DATABASE DELETION:\nAre you sure you want to permanently clear attendance records for ${targetScope} from the database?\n\nThis will remove attendance records and reset the register.`)) {
                return;
            }
            try {
                const res = await fetch(getApiUrl(`/api/admin/clear-records?token=${encodeURIComponent(authToken)}&branch=${encodeURIComponent(branch)}`), {
                    method: "DELETE"
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert(data.message || "Database records cleared successfully.");
                    loadRecords();
                    loadDashboardData();
                } else {
                    alert(data.message || "Failed to clear records.");
                }
            } catch (err) {
                alert("Error communicating with server.");
            }
        });
    }

    // Event Filters
    if (searchInput) searchInput.addEventListener("input", debounce(() => loadRecords(), 300));
    if (branchFilter) branchFilter.addEventListener("change", () => {
        loadDashboardData();
        loadRecords();
    });
    if (sessionFilter) sessionFilter.addEventListener("change", () => loadRecords());
    if (dateFilter) dateFilter.addEventListener("change", () => loadRecords());
    if (statusFilter) statusFilter.addEventListener("change", () => loadRecords());
    if (refreshBtn) refreshBtn.addEventListener("click", () => {
        loadDashboardData();
        loadRecords();
    });

    // Manual Entry Modal
    if (openManualBtn) {
        openManualBtn.addEventListener("click", () => {
            manualModal.classList.add("open");
            manualForm.reset();
            document.getElementById("manualDate").value = new Date().toISOString().split("T")[0];
            manualAlert.style.display = "none";
        });
    }

    if (closeManualBtn) {
        closeManualBtn.addEventListener("click", () => {
            manualModal.classList.remove("open");
        });
    }

    if (manualForm) {
        manualForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("manualName").value.trim();
            const email = document.getElementById("manualEmail").value.trim().toLowerCase();
            const branch = document.getElementById("manualBranch").value.trim();
            const session_type = document.getElementById("manualSession") ? document.getElementById("manualSession").value.trim() : "Morning Session";
            const call_number = document.getElementById("manualCallNumber") ? document.getElementById("manualCallNumber").value.trim() : "";
            const parent_phone = document.getElementById("manualParentPhone") ? document.getElementById("manualParentPhone").value.trim() : "";
            const date = document.getElementById("manualDate").value.trim();
            const time_in = document.getElementById("manualTimeIn").value.trim();
            const time_out = document.getElementById("manualTimeOut").value.trim();
            const notes = document.getElementById("manualNotes").value.trim();

            if (!name || !email || !date || !time_in || !branch) {
                showManualAlert("Name, Email, Branch, Date, and Time In are required.", "danger");
                return;
            }

            try {
                const res = await fetch(getApiUrl(`/api/admin/manual-record?token=${encodeURIComponent(authToken)}`), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name,
                        email,
                        branch,
                        session_type,
                        call_number,
                        whatsapp_number: call_number,
                        parent_phone,
                        date,
                        time_in,
                        time_out,
                        notes
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    manualModal.classList.remove("open");
                    loadDashboardData();
                    loadRecords();
                } else {
                    showManualAlert(data.message || "Failed to create record.", "danger");
                }
            } catch (err) {
                showManualAlert("Network error.", "danger");
            }
        });
    }

    function showManualAlert(msg, type = "danger") {
        manualAlert.className = `alert alert-${type}`;
        manualAlert.textContent = msg;
        manualAlert.style.display = "flex";
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(func, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Start initialization
    checkAuth();
});
