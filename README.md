git clone https://github.com/yourusername/CyberSentinel.git
cd CyberSentinel

# Navigate to backend folder
cd backend
# (recommended)
python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python ml_model/download_dataset.py
python ml_model/train_model_simple.py


## frontend
# Navigate to project root
cd ..

# Install dependencies
npm install
```

### 5. Get VirusTotal API Key (Optional but Recommended)

1. Sign up at [VirusTotal](https://www.virustotal.com/gui/join-us)
2. Get your free API key from your profile
3. Add it to `backend/.env`:
```
   VIRUSTOTAL_API_KEY=your_actual_api_key_here



# Start Backend (Terminal 1)
cd backend
python app.py

# terminal 2
npm run dev
