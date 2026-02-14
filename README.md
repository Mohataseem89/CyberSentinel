<<<<<<< HEAD
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
=======
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
>>>>>>> ml-integration
