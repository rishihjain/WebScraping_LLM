# Quick Setup Guide

## Step-by-Step Installation

### 0. Check Python Version

First, verify you have the correct Python version:
```bash
python --version
```

**Required:** Python 3.9 or higher (Python 3.10+ recommended)

If you don't have Python 3.9+, download it from: https://www.python.org/downloads/

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you encounter any issues, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Install Playwright Browser

Playwright needs to download a browser to scrape websites:

```bash
playwright install chromium
```

### 3. Get Gemini API Key (Free)

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the generated key (it will look like: `AIzaSy...`)

**Note:** The Gemini API has a generous free tier, perfect for this project!

### 4. Create .env File

Create a file named `.env` in the project root directory with:

```
GEMINI_API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with the key you copied in step 3.

### 5. Run the Backend API

```bash
python app.py
```

The Flask API listens on `http://localhost:5000`.

### 6. Run the React Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

This starts Vite on `http://localhost:5173` with a proxy to the backend API.

### 7. Build the Frontend (optional)

When you're ready for production:

```bash
cd frontend
npm run build
```

Serve the generated `frontend/dist` folder (Flask automatically serves it if present).

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"
- Make sure you created the `.env` file in the project root
- Check that the file contains: `GEMINI_API_KEY=your_key_here`
- Restart the application after creating/editing `.env`

### Issue: Playwright browser not found
- Run: `playwright install chromium`
- Make sure you have internet connection for the first-time download

### Issue: Port 5000 already in use
- Change the port in `app.py` (last line): `app.run(debug=True, host='0.0.0.0', port=5001)`
- Or stop the other application using port 5000

### Issue: Module not found errors
- Make sure you installed all dependencies: `pip install -r requirements.txt`
- Try: `pip install --upgrade -r requirements.txt`
- For frontend errors, run `npm install` inside `frontend/`

## Testing the Platform

Try scraping a simple website:

1. **URL:** `https://example.com`
2. **Instruction:** `Extract the main heading and all paragraph text`
3. Click "Start Scraping"

You should see results appear in the tasks list below!

