# AI-Powered Web Scraping Platform

An intelligent web scraping platform that uses natural language instructions to extract data from websites. Powered by LLM (Google Gemini) for intelligent content understanding.

## Features

- 🎯 **Natural Language Instructions**: Describe what you need and the scraper figures it out
- 🧠 **Domain-Specific Intelligence**: Tailor extractions for e-commerce, news, jobs, real estate, restaurants, or general sites
- 🧾 **Structured Reports**: Every run includes summaries, key points, insights, and direct answers to the user request
- 🔍 **Multi-Site Comparison**: Side-by-side pros/cons, similarity/difference lists, and recommendation tables
- 💬 **Interactive Q&A**: Ask follow-up questions about any task and get grounded answers
- 🖥️ **Modern React UI**: Vite + React dashboard with live task feed and detail drawer
- 📤 **Multiple Output Formats**: Download structured data as JSON, CSV, or TXT

## Setup

### Prerequisites
- **Python 3.9 or higher** (Python 3.10+ recommended)
- **Node.js 18+** (for the React frontend)
- Internet connection for API + scraping

### Installation Steps

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Playwright browser:**
```bash
playwright install chromium
```

3. **Get your free Gemini API key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated API key

4. **Set up environment variables:**
   - Create a `.env` file in the project root
   - Add your API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the backend API (Flask):**
```bash
python app.py
```

6. **Run the React frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```
The React dev server proxies API calls to `http://localhost:5000`.

## Usage

1. Enter one or more URLs in the dashboard
2. Describe what you want to extract in natural language (e.g., "Extract all product names and prices")
3. Click "Scrape" and wait for results
4. View, download, or schedule automated scraping tasks

## API Endpoints

- `GET /api/domains` – Available domain presets
- `POST /api/scrape` – Run a new analysis
- `GET /api/tasks` – List tasks
- `GET /api/tasks/<id>` – Task detail
- `POST /api/tasks/<id>/ask` – Q&A about a completed task
- `GET /api/download/<task_id>/<format>` – Download (json, csv, txt)

