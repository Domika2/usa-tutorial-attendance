// Dual Branch QR Posters Studio Logic
document.addEventListener("DOMContentLoaded", async () => {
    const centreInput = document.getElementById("centreNameInput");
    const baseUrlInput = document.getElementById("baseUrlInput");
    const regenerateBtn = document.getElementById("regenerateBtn");
    const refreshQrBtn = document.getElementById("refreshQrBtn");
    const printBtn = document.getElementById("printBtn");

    const studioCentreHeader = document.getElementById("studioCentreHeader");
    const activeTokenDisplay = document.getElementById("activeTokenDisplay");

    const popoolaPosterTitle = document.getElementById("popoolaPosterTitle");
    const kilimanjaroPosterTitle = document.getElementById("kilimanjaroPosterTitle");

    const popoolaQrContainer = document.getElementById("popoolaQrContainer");
    const kilimanjaroQrContainer = document.getElementById("kilimanjaroQrContainer");

    const popoolaTokenText = document.getElementById("popoolaTokenText");
    const kilimanjaroTokenText = document.getElementById("kilimanjaroTokenText");

    const popoolaUrlHint = document.getElementById("popoolaUrlHint");
    const kilimanjaroUrlHint = document.getElementById("kilimanjaroUrlHint");

    let currentQrInfo = {
        token: "daily_qr_token",
        date: new Date().toISOString().split("T")[0],
        time: ""
    };

    function getApiUrl(endpoint) {
        if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
        return endpoint;
    }

    // 1. Fetch current server and QR info
    async function loadInitialData() {
        try {
            const [serverRes, qrRes] = await Promise.all([
                fetch(getApiUrl("/api/server-info")),
                fetch(getApiUrl("/api/admin/qr-info"))
            ]);

            const serverInfo = await serverRes.json();
            const qrInfo = await qrRes.json();

            currentQrInfo = qrInfo;

            const defaultBaseUrl = serverInfo ? serverInfo.host : window.location.origin;
            const defaultCentreName = serverInfo ? serverInfo.centre_name : "USA Tutorial Centre";

            if (centreInput) centreInput.value = defaultCentreName;
            if (baseUrlInput) baseUrlInput.value = defaultBaseUrl;
            if (studioCentreHeader) studioCentreHeader.textContent = defaultCentreName;

            renderPosters();
        } catch (err) {
            console.error("Could not fetch server or QR info:", err);
            renderPosters();
        }
    }

    // 2. Render both branch posters
    function renderPosters() {
        const centreName = (centreInput ? centreInput.value.trim() : "") || "USA Tutorial Centre";
        const baseUrl = (baseUrlInput ? baseUrlInput.value.trim() : window.location.origin).replace(/\/$/, "");

        const token = currentQrInfo.token || "daily_qr_token";
        const dateStr = currentQrInfo.date || new Date().toISOString().split("T")[0];
        const timeStr = currentQrInfo.time || "";

        if (activeTokenDisplay) {
            activeTokenDisplay.textContent = `${token} (${dateStr}${timeStr ? ' at ' + timeStr : ''})`;
        }

        // Branch URLs that direct to the main portal with branch and token parameters
        const popoolaUrl = `${baseUrl}/index.html?branch=Popoola+Branch&token=${encodeURIComponent(token)}`;
        const kilimanjaroUrl = `${baseUrl}/index.html?branch=Kilimanjaro+Branch&token=${encodeURIComponent(token)}`;

        // Update titles
        if (popoolaPosterTitle) popoolaPosterTitle.textContent = centreName;
        if (kilimanjaroPosterTitle) kilimanjaroPosterTitle.textContent = centreName;
        if (studioCentreHeader) studioCentreHeader.textContent = centreName;

        // Update badges and URL hints
        const passText = `Pass: ${token} • ${dateStr}`;
        if (popoolaTokenText) popoolaTokenText.textContent = passText;
        if (kilimanjaroTokenText) kilimanjaroTokenText.textContent = passText;

        if (popoolaUrlHint) popoolaUrlHint.textContent = popoolaUrl;
        if (kilimanjaroUrlHint) kilimanjaroUrlHint.textContent = kilimanjaroUrl;

        // Clear existing canvases
        if (popoolaQrContainer) popoolaQrContainer.innerHTML = "";
        if (kilimanjaroQrContainer) kilimanjaroQrContainer.innerHTML = "";

        // Generate Popoola Branch QR Code
        if (popoolaQrContainer) {
            new QRCode(popoolaQrContainer, {
                text: popoolaUrl,
                width: 250,
                height: 250,
                colorDark: "#1e3a8a",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }

        // Generate Kilimanjaro Branch QR Code
        if (kilimanjaroQrContainer) {
            new QRCode(kilimanjaroQrContainer, {
                text: kilimanjaroUrl,
                width: 250,
                height: 250,
                colorDark: "#581c87",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    }

    // 3. Handle QR Refresh button
    if (refreshQrBtn) {
        refreshQrBtn.addEventListener("click", async () => {
            const adminToken = sessionStorage.getItem("admin_auth_token") || "admin_secret_token_2026";
            refreshQrBtn.disabled = true;
            refreshQrBtn.textContent = "Refreshing QR...";

            try {
                const res = await fetch(getApiUrl(`/api/admin/refresh-qr?token=${encodeURIComponent(adminToken)}`), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    currentQrInfo = data.qr_info;
                    renderPosters();
                    alert(`QR codes refreshed successfully for both branches!\nNew Daily Pass: ${data.qr_info.token}\nDate: ${data.qr_info.date} at ${data.qr_info.time}`);
                } else {
                    alert(data.message || "Failed to refresh QR codes. Please ensure you are signed in as admin.");
                }
            } catch (err) {
                alert("Network error refreshing QR codes.");
                console.error(err);
            } finally {
                refreshQrBtn.disabled = false;
                refreshQrBtn.textContent = "🔄 Refresh Daily QR Codes";
            }
        });
    }

    // 4. Re-render button
    if (regenerateBtn) {
        regenerateBtn.addEventListener("click", renderPosters);
    }

    // 5. Dynamic text updates
    if (centreInput) {
        centreInput.addEventListener("input", () => {
            const val = centreInput.value || "USA Tutorial Centre";
            if (popoolaPosterTitle) popoolaPosterTitle.textContent = val;
            if (kilimanjaroPosterTitle) kilimanjaroPosterTitle.textContent = val;
            if (studioCentreHeader) studioCentreHeader.textContent = val;
        });
    }

    // 6. Print Button
    if (printBtn) {
        printBtn.addEventListener("click", () => {
            window.print();
        });
    }

    // Initial load
    await loadInitialData();
});
