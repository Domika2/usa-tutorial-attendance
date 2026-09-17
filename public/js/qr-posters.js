// Permanent 24/7 Attendance QR Studio Logic
document.addEventListener("DOMContentLoaded", async () => {
    const posterSelect = document.getElementById("posterSelect");
    const centreInput = document.getElementById("centreNameInput");
    const baseUrlInput = document.getElementById("baseUrlInput");
    const regenerateBtn = document.getElementById("regenerateBtn");
    const printBtn = document.getElementById("printBtn");

    const studioCentreHeader = document.getElementById("studioCentreHeader");
    const activeTokenDisplay = document.getElementById("activeTokenDisplay");
    const postersContainer = document.getElementById("postersContainer");

    const singlePosterFrame = document.getElementById("singlePosterFrame");
    const popoolaPosterFrame = document.getElementById("popoolaPosterFrame");
    const kilimanjaroPosterFrame = document.getElementById("kilimanjaroPosterFrame");

    const singlePosterTitle = document.getElementById("singlePosterTitle");
    const popoolaPosterTitle = document.getElementById("popoolaPosterTitle");
    const kilimanjaroPosterTitle = document.getElementById("kilimanjaroPosterTitle");

    const singleQrContainer = document.getElementById("singleQrContainer");
    const popoolaQrContainer = document.getElementById("popoolaQrContainer");
    const kilimanjaroQrContainer = document.getElementById("kilimanjaroQrContainer");

    const singleTokenText = document.getElementById("singleTokenText");
    const popoolaTokenText = document.getElementById("popoolaTokenText");
    const kilimanjaroTokenText = document.getElementById("kilimanjaroTokenText");

    const singleUrlHint = document.getElementById("singleUrlHint");
    const popoolaUrlHint = document.getElementById("popoolaUrlHint");
    const kilimanjaroUrlHint = document.getElementById("kilimanjaroUrlHint");

    // Static permanent session key
    const PERMANENT_TOKEN = "PERMANENT_SESSION_KEY";
    let currentQrInfo = {
        token: PERMANENT_TOKEN,
        is_permanent: true,
        validity: "24/7 Indefinite"
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

            if (qrInfo && qrInfo.token) {
                currentQrInfo = qrInfo;
            }

            const defaultBaseUrl = serverInfo ? serverInfo.host : window.location.origin;
            const defaultCentreName = serverInfo ? serverInfo.centre_name : "USA Tutorial Centre";

            if (centreInput) centreInput.value = defaultCentreName;
            if (baseUrlInput) baseUrlInput.value = defaultBaseUrl;
            if (studioCentreHeader) studioCentreHeader.textContent = defaultCentreName;

            updatePosterView();
            renderPosters();
        } catch (err) {
            console.error("Could not fetch server or QR info:", err);
            updatePosterView();
            renderPosters();
        }
    }

    // 2. Switch between Single Poster, Branch Posters, or All
    function updatePosterView() {
        const selected = posterSelect ? posterSelect.value : "single";

        if (selected === "single") {
            if (singlePosterFrame) {
                singlePosterFrame.style.display = "block";
                singlePosterFrame.classList.remove("hidden-for-print");
            }
            if (popoolaPosterFrame) {
                popoolaPosterFrame.style.display = "none";
                popoolaPosterFrame.classList.add("hidden-for-print");
            }
            if (kilimanjaroPosterFrame) {
                kilimanjaroPosterFrame.style.display = "none";
                kilimanjaroPosterFrame.classList.add("hidden-for-print");
            }
            if (postersContainer) postersContainer.classList.add("single-view");
        } else if (selected === "popoola") {
            if (singlePosterFrame) {
                singlePosterFrame.style.display = "none";
                singlePosterFrame.classList.add("hidden-for-print");
            }
            if (popoolaPosterFrame) {
                popoolaPosterFrame.style.display = "block";
                popoolaPosterFrame.classList.remove("hidden-for-print");
            }
            if (kilimanjaroPosterFrame) {
                kilimanjaroPosterFrame.style.display = "none";
                kilimanjaroPosterFrame.classList.add("hidden-for-print");
            }
            if (postersContainer) postersContainer.classList.add("single-view");
        } else if (selected === "kilimanjaro") {
            if (singlePosterFrame) {
                singlePosterFrame.style.display = "none";
                singlePosterFrame.classList.add("hidden-for-print");
            }
            if (popoolaPosterFrame) {
                popoolaPosterFrame.style.display = "none";
                popoolaPosterFrame.classList.add("hidden-for-print");
            }
            if (kilimanjaroPosterFrame) {
                kilimanjaroPosterFrame.style.display = "block";
                kilimanjaroPosterFrame.classList.remove("hidden-for-print");
            }
            if (postersContainer) postersContainer.classList.add("single-view");
        } else {
            // "all" - Show Popoola and Kilimanjaro side-by-side
            if (singlePosterFrame) {
                singlePosterFrame.style.display = "none";
                singlePosterFrame.classList.add("hidden-for-print");
            }
            if (popoolaPosterFrame) {
                popoolaPosterFrame.style.display = "block";
                popoolaPosterFrame.classList.remove("hidden-for-print");
            }
            if (kilimanjaroPosterFrame) {
                kilimanjaroPosterFrame.style.display = "block";
                kilimanjaroPosterFrame.classList.remove("hidden-for-print");
            }
            if (postersContainer) postersContainer.classList.remove("single-view");
        }
    }

    // 3. Render all permanent static QR posters
    function renderPosters() {
        const centreName = (centreInput ? centreInput.value.trim() : "") || "USA Tutorial Centre";
        const baseUrl = (baseUrlInput ? baseUrlInput.value.trim() : window.location.origin).replace(/\/$/, "");

        const token = currentQrInfo.token || PERMANENT_TOKEN;

        if (activeTokenDisplay) {
            activeTokenDisplay.textContent = token;
        }

        // Permanent static URL payloads
        const singleUrl = `${baseUrl}/clock-in.html?attendance_token=${encodeURIComponent(token)}`;
        const popoolaUrl = `${baseUrl}/clock-in.html?branch=Popoola+Branch&attendance_token=${encodeURIComponent(token)}`;
        const kilimanjaroUrl = `${baseUrl}/clock-in.html?branch=Kilimanjaro+Branch&attendance_token=${encodeURIComponent(token)}`;

        // Update titles
        if (singlePosterTitle) singlePosterTitle.textContent = centreName;
        if (popoolaPosterTitle) popoolaPosterTitle.textContent = centreName;
        if (kilimanjaroPosterTitle) kilimanjaroPosterTitle.textContent = centreName;
        if (studioCentreHeader) studioCentreHeader.textContent = centreName;

        // Static permanent pass tags
        const staticTag = `Valid 24/7 • Permanent Session Key`;
        if (singleTokenText) singleTokenText.textContent = staticTag;
        if (popoolaTokenText) popoolaTokenText.textContent = `Popoola Branch • ${staticTag}`;
        if (kilimanjaroTokenText) kilimanjaroTokenText.textContent = `Kilimanjaro Branch • ${staticTag}`;

        // URL hints
        if (singleUrlHint) singleUrlHint.textContent = singleUrl;
        if (popoolaUrlHint) popoolaUrlHint.textContent = popoolaUrl;
        if (kilimanjaroUrlHint) kilimanjaroUrlHint.textContent = kilimanjaroUrl;

        // Clear existing canvases
        if (singleQrContainer) singleQrContainer.innerHTML = "";
        if (popoolaQrContainer) popoolaQrContainer.innerHTML = "";
        if (kilimanjaroQrContainer) kilimanjaroQrContainer.innerHTML = "";

        // Generate Single Attendance Poster QR Code
        if (singleQrContainer && window.QRCode) {
            new QRCode(singleQrContainer, {
                text: singleUrl,
                width: 250,
                height: 250,
                colorDark: "#0f766e",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }

        // Generate Popoola Branch QR Code
        if (popoolaQrContainer && window.QRCode) {
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
        if (kilimanjaroQrContainer && window.QRCode) {
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

    // Event listeners
    if (posterSelect) {
        posterSelect.addEventListener("change", () => {
            updatePosterView();
        });
    }

    if (regenerateBtn) {
        regenerateBtn.addEventListener("click", renderPosters);
    }

    if (centreInput) {
        centreInput.addEventListener("input", () => {
            const val = centreInput.value || "USA Tutorial Centre";
            if (singlePosterTitle) singlePosterTitle.textContent = val;
            if (popoolaPosterTitle) popoolaPosterTitle.textContent = val;
            if (kilimanjaroPosterTitle) kilimanjaroPosterTitle.textContent = val;
            if (studioCentreHeader) studioCentreHeader.textContent = val;
        });
    }

    if (baseUrlInput) {
        baseUrlInput.addEventListener("input", renderPosters);
    }

    if (printBtn) {
        printBtn.addEventListener("click", () => {
            window.print();
        });
    }

    // Initial load
    await loadInitialData();
});

