# 🛡️ CyberGuard — Real-Time Threat Intelligence & SOC Dashboard

A modern, cloud-ready Cybersecurity Operations Center (SOC) dashboard built with Python & Flask. Monitors live security events, tracks critical vulnerabilities, detects brute-force attacks, and provides incident response logging with an audited threat stream.

![CyberGuard Dashboard](https://img.shields.io/badge/Status-Cloud--Ready-38BDF8?style=flat-square)
![Deploy to Render](https://img.shields.io/badge/Deploy-Render.com-00B0FF?style=flat-square&logo=render)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Framework-Flask-000000?style=flat-square&logo=flask)

---

## 🌟 Key Features

- **Live SOC Threat Feed**: Real-time event tracking categorized by Critical, High, Medium, and Low severity.
- **Incident Response CRUD**: Log new threats, edit forensic details, update containment status (Open / Investigating / Resolved), and delete resolved events.
- **Brute Force Protection**: Automatic threshold tripwire that logs brute force attacks if 5 failed logins occur.
- **Cloud-Ready Hybrid Database**:
  - **Zero-Configuration Mode**: Automatically provisions SQLite on Render with pre-seeded threat telemetry.
  - **Cloud MySQL Mode**: Fully compatible with remote MySQL (Aiven, TiDB Cloud, Clever Cloud, Railway) via environment variables.
- **REST Threat Ingestion API**: Secure external sensor telemetry via `POST /api/report-threat` with `X-API-Key`.
- **Health Check Endpoint**: Production-ready `/healthz` probe for Render zero-downtime health monitoring.

---

## 🚀 Live Hosting on Render (Render.com)

### Step 1: Push Project to GitHub

1. Open **GitHub** ([github.com](https://github.com)) and create a new repository (e.g. `CyberThreatDashboard`).
2. In your terminal or command prompt, link and push the repository:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/CyberThreatDashboard.git
git branch -M main
git push -u origin main
```

*(Or simply open **GitHub Desktop**, choose **Add Existing Repository**, select this folder, and click **Publish repository**).*

---

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign in (you can use your GitHub account).
2. Click **New +** in the top navigation bar and select **Web Service**.
3. Select **Build and deploy from a Git repository** and click **Next**.
4. Choose your `CyberThreatDashboard` repository from the list.
5. Render will automatically detect the settings from `render.yaml` / `Procfile`:
   - **Name**: `cyberguard-dashboard` (or any custom name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
6. Click **Deploy Web Service** at the bottom.
7. Within 1–2 minutes, Render will build and deploy your live dashboard. Your public URL will look like:
   `https://cyberguard-dashboard.onrender.com`

---

## 🔑 Default Credentials

- **URL**: `https://<your-render-subdomain>.onrender.com/login`
- **Username**: `admin`
- **Password**: `admin123`

---

## ⚙️ Optional Environment Variables (in Render Dashboard)

If you wish to customize security keys or connect an external managed MySQL database (e.g., Aiven, Clever Cloud, TiDB):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Auto-generated)* | Flask session signing key |
| `API_KEY` | `cyberguard123` | Security key for `/api/report-threat` |
| `DB_HOST` | *(Empty / SQLite)* | Remote MySQL host (optional) |
| `DB_PORT` | `3306` | Remote MySQL port (optional) |
| `DB_USER` | `root` | Remote MySQL username (optional) |
| `DB_PASSWORD` | `""` | Remote MySQL password (optional) |
| `DB_NAME` | `cybersecurity_db` | Remote MySQL database name (optional) |

---

## 📡 Automated Threat Reporting API

To report threats programmatically from firewalls, scripts, or external sensors:

```bash
curl -X POST https://<your-render-url>/api/report-threat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cyberguard123" \
  -d '{
    "threat_type": "DDoS UDP Flood",
    "severity": "Critical",
    "description": "Volumetric anomaly exceeding 100 Gbps on perimeter router"
  }'
```

---

## 💻 Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py
```

Access the dashboard at `http://127.0.0.1:5000`.
