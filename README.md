# 🎓 USA Tutorial Centre (Unique Success Academy)
## Student QR Code Clock-In & Clock-Out System

A complete attendance tracking platform designed for **USA Tutorial Centre**. Students scan a printed **Entrance QR Code** upon arrival to clock in, and an **Exit QR Code** before leaving to clock out. All attendance logs are recorded in real-time and accessible via a secured **Admin Dashboard**.

---

## 🌟 Key Features

- 🏛️ **Official USA Tutorial Centre Identity**:
  - Features the official academy emblem and branding across all portals and printable materials.
  - High-resolution circular crest logo embedded into the Entrance and Exit door posters.

- 🔑 **Secure Admin Password Authentication**:
  - Administrators can create their custom password during initial setup or inside the dashboard.
  - PBKDF2-HMAC-SHA256 password hashing with cryptographic salt security.
  - Built-in "Change Password" modal for ongoing credential management.
  - Password visibility toggle (eye icon) for convenient login.

- 🟢 **Entrance QR Code Clock-In (`/clock-in.html`)**:
  - Students scan with their smartphone camera.
  - Caches student name and email locally on their device for instant future 1-tap clock-ins.
  - Records Student Name, Email, Tutorial Branch, Date, and Time In (12-hour AM/PM format).
  - Immediate visual confirmation checkmark with arrival timestamp.
  - Prevents accidental duplicate clock-ins within the same active session.

- 🔴 **Exit QR Code Clock-Out (`/clock-out.html`)**:
  - Students scan the separate exit QR code before going home.
  - Records departure Time Out and automatically calculates total study session duration (e.g. `2h 45m`).

- 📊 **Real-Time Admin Dashboard (`/admin.html`)**:
  - Protected with Admin Password authentication.
  - **Live Floor Monitor**: Shows student count currently in the centre vs departed.
  - Searchable by student name, email, or branch.
  - Date filter picker (view any day's register).
  - Status filter (Inside Now vs Completed).
  - **1-Click CSV Export**: Download attendance reports formatted for spreadsheets and parent reports.
  - **Manual Entry Modal**: Manually clock-in/out students who forgot their phone.
  - Delete / cleanup records.

- 🖨️ **Printable QR Posters Studio (`/qr-posters.html`)**:
  - High-resolution, crisp printable A4 / Letter posters with the official USA Tutorial Centre crest logo.
  - Fully customizable centre name and network host IP / domain.
  - Optimized `@media print` styling for crisp, clean physical paper prints.

---

## 🚀 How to Run

1. Open your terminal in this project directory:
   ```bash
   py server.py
   ```
2. The server will start on port `5000`:
   - **Main Hub**: `http://localhost:5000`
   - **Clock-In**: `http://localhost:5000/clock-in.html`
   - **Clock-Out**: `http://localhost:5000/clock-out.html`
   - **Admin Dashboard**: `http://localhost:5000/admin.html`
   - **QR Posters Studio**: `http://localhost:5000/qr-posters.html`

3. **Admin Password Setup**:
   - On your first visit to **Admin Access**, click **Create Admin Password**.
   - Enter your full name, desired username, and a password (at least 6 characters).
   - Once created, use your username and password to log in. You can change your password anytime using the **🔑 Password** button in the dashboard.

---

## 🌐 Deploying to Render

This project is pre-configured with a `render.yaml` blueprint for automatic deployment on [Render](https://render.com):

1. **Push this repository to GitHub**.
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** and select **Web Service** (or **Blueprint**).
4. Connect your GitHub repository.
5. Configure the following settings if creating manually:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Environment Variables**:
     - `PORT`: `10000` (Render will also provide this dynamically)
6. Click **Deploy Web Service**.
7. Once deployed, Render will provide a public URL (e.g. `https://your-service-name.onrender.com`).
   - The application automatically detects this domain and generates student QR codes using the public Render URL!


