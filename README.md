# CyberSentinel – AI-Powered Phishing Detection System

CyberSentinel is a full-stack cybersecurity web application that detects malicious URLs using a hybrid approach combining:

- Machine Learning (Random Forest)
- VirusTotal API
- URL-only analysis (remote page-content fetching is disabled for SSRF protection)
- Community feedback for offline, reviewed model improvement

It also includes a Chrome extension prototype. It must not be described as
real-time protection until its detection and blocking behavior is independently validated.

---

## Screenshots

### Login Page
![Login Page](./assets/login.png)

### Home Page
![Home Page](./assets/home.png)

### Output
![Output](./assets/home1.png)

### Report URL (Feedback)
![Report URL](./assets/report_url.png)

### Feedback Review Panel
![Feedback Review Panel](./assets/feedback_review.png)

### QR Detection
![QR Detection](./assets/QR.png)

### URL Analytics
![URL Analytics](./assets/analytics.png)

### Analytics Using Visual Representation
![Analytics Chart](./assets/analytics1.png)

---

## Features

- URL risk detection using a versioned ML model and optional VirusTotal reputation
- Remote page-content fetching disabled to protect the server from SSRF
- Admin panel for feedback review
- Offline model training with manifest and evaluation report
- Chrome extension integration
- JWT-based authentication
- QR code URL analysis

---

## Tech Stack

### Frontend
- React (Vite)
- Tailwind CSS

### Backend
- Flask (Python)
- Flask-JWT-Extended

### Machine Learning
- scikit-learn
- pandas
- numpy

### Database
- SQLite / PostgreSQL

---

## Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CyberSentinel.git
cd CyberSentinel
```

### 2. Setup Backend

```bash
cd backend
```

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Download Dataset and Train Model
```bash
python ml/download_dataset.py
python ml/train_model.py
```

#### Add Environment Variables

Copy `backend/.env.example` to `backend/.env`, then set all required values.
Never commit the real `.env` file or reuse placeholder secrets.
If this repository was previously public, revoke and rotate every exposed API
key, database password, and signing secret before running the application.

```env
SECRET_KEY=generate-a-long-random-secret
JWT_SECRET_KEY=generate-a-different-long-random-secret
DB_USER=cybersentinel
DB_PASSWORD=your-local-database-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cybersentinel
VIRUSTOTAL_API_KEY=optional-api-key
```

Get a VirusTotal API key from: [VirusTotal](https://www.virustotal.com/gui/join-us)

#### Start Backend Server
```bash
python app.py
```

Backend will run on:
`http://localhost:5000`

---

### 3. Setup Frontend

Open a new terminal and go to the root folder:

```bash
cd ..
npm install
npm run dev
```

Frontend will run on:
`http://localhost:5173`

---

### 4. Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`.
2. Enable Developer Mode.
3. Click **Load Unpacked**.
4. Select the extension folder from this project.

---

There is no default administrator account. Create administrator access through
an audited bootstrap process before enabling administrative features.

---

## How It Works

1. User enters a URL or visits a website.
2. Extension or frontend sends the URL to the backend.
3. Backend performs lexical ML analysis and, when configured, a VirusTotal lookup.
   It does **not** open the submitted page or execute its content.
4. Available signals are combined into a provisional risk score.
5. Final verdict is returned: **Safe**, **Suspicious**, **Dangerous**, or **Unknown**.
   A result is a risk indicator, not a guarantee of safety.

---

## Model Retraining

Model retraining is intentionally disabled from the running API. A new artifact
must be trained and evaluated offline, producing all four files in
`backend/data/`: `phishing_model.pkl`, `feature_columns.pkl`,
`model_manifest.json`, and `model_evaluation.json`.

From the `backend` directory, run:

```bash
python ml/train_model.py
```

The running application accepts only a model whose manifest has the same
feature schema and class labels as the current code. Do not promote a model
until its generated evaluation report has been reviewed.

---

## Authors

### Mohataseem Khan
- LinkedIn: [Profile](https://www.linkedin.com/in/mohataseem-khan/)
- GitHub: [Mohataseem89](https://github.com/Mohataseem89)

### Rehan Khan
- LinkedIn: [Profile](https://www.linkedin.com/in/rehan-khan-5460b6352/)
- GitHub: [RehanKhan1704](https://github.com/RehanKhan1704)

### Saad Shaikh
- LinkedIn: [Profile](https://www.linkedin.com/in/saad-shaikh-1b9265259/)
- GitHub: [SS07158](https://github.com/SS07158)

### Ansari Husain
- LinkedIn: [Profile](https://www.linkedin.com/in/husain-ansari-7530572bb/)
- GitHub: [71-husain](https://github.com/71-husain)
