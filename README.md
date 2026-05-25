# CyberSentinel – AI-Powered Phishing Detection System

CyberSentinel is a full-stack cybersecurity web application that detects malicious URLs using a hybrid approach combining:

- Machine Learning (Random Forest)
- VirusTotal API
- Content Analysis
- Community Feedback + Retraining

It also includes a Chrome Extension for real-time protection.

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

- Real-time URL phishing detection
- Hybrid analysis using ML, API, and content analysis
- Admin panel for feedback review
- Model retraining system
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

Create a `.env` file inside the `backend` folder:

```env
VIRUSTOTAL_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key
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

## Default Admin Login

- Username: `admin`
- Password: `admin123`

---

## How It Works

1. User enters a URL or visits a website.
2. Extension or frontend sends the URL to the backend.
3. Backend performs:
   - ML prediction
   - VirusTotal check
   - Content analysis
4. Results are combined into a threat score.
5. Final verdict is returned: **Benign**, **Suspicious**, or **Phishing**.

---

## Model Retraining

- Users submit feedback.
- Admin approves feedback.
- Approved data is added to the dataset.
- Model is retrained using:

```bash
POST /api/admin/retrain-model
```

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
