# PROJECT BLACKBOOK: AI-POWERED WEB SCRAPING PLATFORM

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Schema](#4-database-schema)
5. [API Documentation](#5-api-documentation)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Core Features](#7-core-features)
8. [User Flow Diagrams](#8-user-flow-diagrams)
9. [Installation & Setup](#9-installation--setup)
10. [Use Cases & Examples](#10-use-cases--examples)
11. [Future Enhancements](#11-future-enhancements)

---

## 1. PROJECT OVERVIEW

### 1.1 Project Name
**AI Web Intelligence Platform** (AI-Powered Web Scraping Platform)

### 1.2 Project Description
An intelligent web scraping platform that uses natural language instructions to extract and analyze data from websites. The system leverages Large Language Models (Google Gemini) to understand user intent and extract structured data from web pages, supporting multiple domains and providing comparative analysis across multiple websites.

### 1.3 Key Highlights
- **Natural Language Instructions**: Describe what you need and the scraper figures it out
- **Domain-Specific Intelligence**: Tailor extractions for e-commerce, news, jobs, real estate, restaurants, or general sites
- **Structured Reports**: Every run includes summaries, key points, insights, and direct answers to the user request
- **Multi-Site Comparison**: Side-by-side pros/cons, similarity/difference lists, and recommendation tables
- **Interactive Q&A**: Ask follow-up questions about any task and get grounded answers
- **Modern React UI**: Vite + React dashboard with live task feed and detail drawer
- **Multiple Output Formats**: Download structured data as JSON, CSV, or TXT
- **Automated Scheduling**: Schedule recurring scraping tasks
- **Multilingual Support**: Supports 11+ Indian languages
- **Re-run Analysis**: Re-execute analysis for existing tasks

### 1.4 Problem Statement
Traditional web scraping requires:
- Writing custom code for each website
- Understanding HTML structure
- Handling dynamic content
- Adapting to site changes
- Manual data processing

**Our Solution:** Use LLMs to understand natural language instructions and automatically extract relevant data without writing site-specific code.

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │TaskDetail │  │TaskList  │  │QnASection│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼───────────────────────────────────────┐
│              BACKEND (Flask API Server)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   app.py     │  │  database.py │  │ scheduler.py │      │
│  │  (Routes)    │  │  (SQLite)    │  │  (APScheduler)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│              CORE SCRAPING ENGINE                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  scraper.py  │  │domain_analyzer│  │  Playwright  │     │
│  │  (WebScraper)│  │  (DomainAI)  │  │  BeautifulSoup│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│              EXTERNAL SERVICES                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Google Gemini API (LLM)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

#### 2.2.1 Backend Components

**1. app.py (Flask Application)**
- RESTful API endpoints
- Request/response handling
- Task orchestration
- File downloads

**2. scraper.py (WebScraper Class)**
- HTML fetching (Playwright + Requests)
- HTML cleaning and preprocessing
- Language detection
- Schema.org extraction
- LLM-based data extraction
- Analysis generation

**3. domain_analyzer.py (DomainAnalyzer Class)**
- Domain-specific prompts
- Analysis templates
- Comparison generation
- Q&A handling

**4. database.py (Database Class)**
- SQLite database operations
- Task CRUD operations
- Filtering and searching
- JSON serialization

**5. scheduler.py (TaskScheduler Class)**
- APScheduler integration
- Recurring task management
- One-time task scheduling

#### 2.2.2 Frontend Components

**1. Dashboard.jsx**
- Task creation form
- Statistics display
- Task filtering

**2. TaskList.jsx**
- Task cards display
- Bulk operations
- Task actions (star, archive, delete, rerun)

**3. TaskDetail.jsx**
- Individual website results
- Multi-website comparison
- Technical details

**4. QnASection.jsx**
- Interactive Q&A interface
- Question history
- Supporting points

**5. TaskForm.jsx**
- URL input
- Instruction input
- Domain selection
- Scheduling options

---

## 3. TECHNOLOGY STACK

### 3.1 Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Backend language |
| Flask | 3.0.0 | Web framework |
| Flask-CORS | 4.0.0 | Cross-origin requests |
| Playwright | 1.40.0 | Dynamic content scraping |
| BeautifulSoup4 | 4.12.2 | HTML parsing |
| lxml | 4.9.3 | XML/HTML parser |
| requests | 2.31.0 | HTTP requests |
| google-generativeai | 0.3.1 | Gemini API client |
| pandas | 2.1.3 | Data processing |
| APScheduler | 3.10.4 | Task scheduling |
| python-dotenv | 1.0.0 | Environment variables |
| SQLite | Built-in | Database |

### 3.2 Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI framework |
| React Router DOM | 6.30.2 | Routing |
| Vite | 5.0.0 | Build tool |
| Axios | 1.6.7 | HTTP client |
| dayjs | 1.11.10 | Date formatting |

### 3.3 External Services

- **Google Gemini API** (gemini-2.5-flash model) - LLM for intelligent extraction
- **Playwright Chromium** - Browser automation for dynamic content

---

## 4. DATABASE SCHEMA

### 4.1 Tasks Table

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    urls TEXT NOT NULL,                    -- JSON array of URLs
    instruction TEXT NOT NULL,
    status TEXT DEFAULT 'pending',         -- pending, processing, completed, error
    results TEXT,                          -- JSON array of results
    errors TEXT,                           -- JSON array of errors
    domain TEXT DEFAULT 'general',
    comparison TEXT,                       -- JSON comparison data
    created_at TEXT NOT NULL,
    completed_at TEXT,
    tags TEXT,                             -- JSON array of tags
    starred INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    progress TEXT,                         -- JSON progress object
    current_url_index INTEGER DEFAULT 0,
    total_urls INTEGER DEFAULT 0,
    estimated_time_remaining INTEGER,
    language TEXT,
    is_scheduled INTEGER DEFAULT 0,
    schedule_type TEXT,
    next_run TEXT
);
```

### 4.2 Scheduled Tasks Table

```sql
CREATE TABLE scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    schedule_type TEXT NOT NULL,           -- once, daily, weekly
    schedule_time TEXT,
    next_run TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (task_id) REFERENCES tasks (id)
);
```

### 4.3 Data Flow

```
User Input → Task Creation → Database Storage → Scraping Process → 
Results Storage → Comparison Generation → Frontend Display
```

---

## 5. API DOCUMENTATION

### 5.1 API Endpoints

#### 5.1.1 Domain Management
```
GET /api/domains
Response: { "domains": { "ecommerce": {...}, "news": {...}, ... } }
```

#### 5.1.2 Task Management

**Create Scraping Task**
```
POST /api/scrape
Body: {
    "urls": ["url1", "url2"],
    "instruction": "Extract product names and prices",
    "domain": "ecommerce",
    "enable_comparison": true,
    "task_name": "Product Comparison",
    "tags": ["products", "comparison"],
    "is_scheduled": false
}
Response: { "task_id": 1, "status": "processing" }
```

**Get All Tasks**
```
GET /api/tasks?domain=ecommerce&status=completed&starred=true&archived=false&search=product&sort_by=created_at&sort_order=DESC
Response: { "tasks": [...] }
```

**Get Task Details**
```
GET /api/tasks/<task_id>
Response: { "task": {...} }
```

**Delete Task**
```
DELETE /api/tasks/<task_id>
Response: { "message": "Task deleted successfully" }
```

**Bulk Delete Tasks**
```
POST /api/tasks/bulk-delete
Body: { "task_ids": [1, 2, 3] }
Response: { "deleted_count": 3 }
```

**Star/Unstar Task**
```
POST /api/tasks/<task_id>/star
Response: { "starred": true }
```

**Archive/Unarchive Task**
```
POST /api/tasks/<task_id>/archive
Response: { "archived": true }
```

**Update Task Tags**
```
PUT /api/tasks/<task_id>/tags
Body: { "tags": ["tag1", "tag2"] }
Response: { "message": "Tags updated successfully" }
```

**Re-run Analysis**
```
POST /api/tasks/<task_id>/rerun
Response: { "task_id": 1, "message": "Analysis re-run completed", "status": "completed" }
```

#### 5.1.3 Q&A System
```
POST /api/tasks/<task_id>/ask
Body: { "question": "What is the best product?" }
Response: { "answer": "...", "supporting_points": [...] }
```

#### 5.1.4 Progress Tracking
```
GET /api/tasks/<task_id>/progress
Response: {
    "progress": {
        "current": 1,
        "total": 3,
        "stage": "scraping",
        "message": "Scraping URL 1/3: ...",
        "current_url": "..."
    }
}
```

#### 5.1.5 Scheduling
```
POST /api/schedule
Body: {
    "task_name": "Daily Price Check",
    "urls": ["url1"],
    "instruction": "Extract prices",
    "schedule_type": "daily",
    "schedule_time": "14:30",
    "domain": "ecommerce"
}
Response: { "task_id": 1, "schedule_type": "daily", "next_run": "..." }
```

#### 5.1.6 Downloads
```
GET /api/download/<task_id>/json
GET /api/download/<task_id>/csv
GET /api/download/<task_id>/txt
Response: File download
```

---

## 6. FRONTEND ARCHITECTURE

### 6.1 Component Hierarchy

```
App.jsx
├── Dashboard.jsx
│   ├── TaskForm.jsx
│   ├── TaskFilters.jsx
│   └── TaskList.jsx
│       └── TaskCard (with actions)
├── TaskDetail.jsx
│   ├── Individual Results
│   ├── Comparison Section
│   ├── Technical Details
│   └── QnASection.jsx
└── ExtractedDataPage.jsx
```

### 6.2 Routing Structure

```
/ → Dashboard
/task/:taskId → TaskDetail
/task/:taskId/data/:resultIndex → ExtractedDataPage
```

### 6.3 State Management
- Local component state (useState)
- API calls via axios
- URL parameters for task IDs

### 6.4 Styling
- CSS file (`styles.css`)
- Minimal, professional design
- Responsive layout

---

## 7. CORE FEATURES

### 7.1 Natural Language Extraction
- Users describe what to extract in plain English
- LLM interprets instructions and extracts relevant data
- No need for CSS selectors or XPath

### 7.2 Domain-Specific Intelligence

**Supported Domains (19 total):**
1. E-Commerce
2. News & Media
3. Business & Finance
4. Job Listings
5. Real Estate
6. Restaurant & Food
7. Social Media
8. Education & Courses
9. Healthcare & Medical
10. Travel & Tourism
11. Technology & Software
12. Legal Services
13. Entertainment & Media
14. Sports & Fitness
15. Research & Academic
16. Financial Markets
17. Recipes & Cooking
18. Software Documentation
19. Forums & Discussions

Each domain has:
- Specific extraction parameters
- Analysis focus areas
- Custom Q&A style

### 7.3 Multi-Website Comparison
- Side-by-side comparison
- Similarities and differences
- Recommendation tables
- Cross-website analysis

### 7.4 Interactive Q&A
- Ask follow-up questions about completed tasks
- Answers grounded in extracted data
- Supporting points with evidence
- Question history

### 7.5 Task Management
- Star important tasks
- Archive completed tasks
- Tag organization
- Search and filter
- Bulk operations
- Re-run analysis

### 7.6 Scheduling
- One-time scheduled tasks
- Daily recurring tasks
- Weekly recurring tasks
- Automatic execution

### 7.7 Progress Tracking
- Real-time progress updates
- Current URL being scraped
- Stage indicators (fetching, cleaning, extracting, analyzing)
- Estimated time remaining

### 7.8 Multilingual Support
- Automatic language detection
- Support for 11+ Indian languages:
  - Hindi, Marathi, Gujarati, Bengali, Telugu, Tamil, Kannada, Malayalam, Punjabi, Odia, Urdu
- Language-specific extraction

### 7.9 Export Options
- JSON (structured data)
- CSV (spreadsheet format)
- TXT (plain text)

### 7.10 Advanced Extraction
- Schema.org structured data extraction
- Code snippet extraction
- Complexity analysis (Big O notation)
- Use case identification
- Image and video metadata extraction

---

## 8. USER FLOW DIAGRAMS

### 8.1 Task Creation Flow

```
User opens Dashboard
    ↓
Enters URLs (one or more)
    ↓
Writes natural language instruction
    ↓
Selects domain (optional)
    ↓
Enables comparison (if multiple URLs)
    ↓
Optionally schedules task
    ↓
Clicks "Scrape"
    ↓
Task created in database
    ↓
Backend starts scraping process
    ↓
Real-time progress updates
    ↓
Results stored in database
    ↓
Comparison generated (if enabled)
    ↓
Task marked as completed
    ↓
User views results in TaskDetail page
```

### 8.2 Scraping Process Flow

```
Receive URL + Instruction
    ↓
Fetch HTML (Playwright for dynamic content)
    ↓
Parse HTML (BeautifulSoup)
    ↓
Detect Language
    ↓
Extract Schema.org data (if available)
    ↓
Clean HTML (remove noise, preserve important content)
    ↓
Generate domain-specific prompt
    ↓
Send to LLM (Gemini API)
    ↓
Extract structured data
    ↓
Merge Schema.org data (priority)
    ↓
Generate analysis
    ↓
Return results
```

### 8.3 Comparison Generation Flow

```
Multiple successful results received
    ↓
Extract key data points from each result
    ↓
Generate comparison prompt
    ↓
Send to LLM with all results
    ↓
LLM generates:
    - Summary
    - Similarities
    - Differences
    - Recommendations
    - User request answer
    ↓
Store comparison in database
    ↓
Display in TaskDetail page
```

### 8.4 Q&A Flow

```
User views completed task
    ↓
Clicks Q&A section
    ↓
Enters question
    ↓
Question sent to backend with task results
    ↓
LLM analyzes question + extracted data
    ↓
Generates answer with supporting points
    ↓
Answer displayed with evidence
    ↓
Question saved to history
```

---

## 9. INSTALLATION & SETUP

### 9.1 Prerequisites
- Python 3.9+ (3.10+ recommended)
- Node.js 18+
- Google account (for Gemini API key)
- Internet connection

### 9.2 Backend Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Playwright browser
playwright install chromium

# 3. Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 4. Run Flask server
python app.py
```

### 9.3 Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Run development server
npm run dev
```

### 9.4 Production Build

```bash
# Build frontend
cd frontend
npm run build

# Backend will serve from frontend/dist
python app.py
```

### 9.5 Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 9.6 Getting Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Add it to your `.env` file

---

## 10. USE CASES & EXAMPLES

### 10.1 E-Commerce Product Comparison

**Use Case:** Compare product prices and features across multiple e-commerce sites

**Example:**
- **URLs:** Amazon product page, Flipkart product page
- **Domain:** E-Commerce
- **Instruction:** "Extract product name, price, rating, number of reviews, key features, and availability status"
- **Result:** Side-by-side comparison with price differences, feature highlights, and recommendations

### 10.2 News Article Analysis

**Use Case:** Extract and compare news headlines from different sources

**Example:**
- **URLs:** BBC News, CNN
- **Domain:** News & Media
- **Instruction:** "Extract main headlines, article titles, categories, and featured stories"
- **Result:** Comparison of news coverage, trending topics, and editorial focus

### 10.3 Job Market Research

**Use Case:** Analyze job listings across multiple job boards

**Example:**
- **URLs:** Indeed, LinkedIn Jobs
- **Domain:** Job Listings
- **Instruction:** "Extract job titles, company names, locations, salary ranges, and job types"
- **Result:** Market analysis, salary trends, location distribution

### 10.4 Code Documentation Extraction

**Use Case:** Extract code examples and complexity analysis from documentation

**Example:**
- **URLs:** Algorithm documentation pages
- **Domain:** Software Documentation
- **Instruction:** "Extract code for algorithms, time and space complexity analysis, and practical use cases"
- **Result:** Code snippets, Big O notation, and application scenarios

### 10.5 Real Estate Market Analysis

**Use Case:** Compare property listings across real estate platforms

**Example:**
- **URLs:** Zillow, Realtor.com
- **Domain:** Real Estate
- **Instruction:** "Extract property types, price ranges, locations, and key features"
- **Result:** Market comparison, price trends, location analysis

### 10.6 Recipe Comparison

**Use Case:** Compare recipes from different cooking websites

**Example:**
- **URLs:** AllRecipes, Food Network
- **Domain:** Recipes & Cooking
- **Instruction:** "Extract recipe name, ingredients, cooking time, difficulty level, and ratings"
- **Result:** Ingredient comparison, cooking time analysis, difficulty assessment

---

## 11. FUTURE ENHANCEMENTS

### 11.1 Planned Features
1. User authentication and multi-user support
2. API rate limiting and caching
3. Advanced filtering and sorting
4. Custom domain templates
5. Webhook notifications
6. Data visualization charts
7. Export to Excel format
8. Browser extension
9. Mobile app
10. Cloud deployment support

### 11.2 Technical Improvements
1. Distributed scraping with worker queues
2. Redis caching for frequently accessed data
3. PostgreSQL migration for scalability
4. GraphQL API option
5. Real-time WebSocket updates
6. Advanced error recovery
7. Proxy rotation support
8. CAPTCHA solving integration

---

## 12. PROJECT STATISTICS

### 12.1 Code Metrics
- **Backend Files:** 5 Python files
- **Frontend Files:** 10+ React components
- **Total Lines of Code:** ~5000+
- **API Endpoints:** 16
- **Supported Domains:** 19
- **Supported Languages:** 11+ Indian languages

### 12.2 Key Achievements
- ✅ Natural language instruction processing
- ✅ Multi-domain support
- ✅ Real-time progress tracking
- ✅ Interactive Q&A system
- ✅ Automated scheduling
- ✅ Multi-format exports
- ✅ Professional UI/UX
- ✅ Multilingual support
- ✅ Re-run analysis feature

---

## 13. PROJECT STRUCTURE

### 13.1 Directory Structure
```
web_scraping_using_llm/
├── app.py                 # Flask API server
├── scraper.py             # Core scraping engine
├── domain_analyzer.py     # Domain-specific logic
├── database.py            # Database operations
├── scheduler.py          # Task scheduling
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── PROJECT_BLACKBOOK.md   # This document
├── README.md              # Quick start guide
├── SETUP.md               # Detailed setup instructions
├── TESTING_EXAMPLES.md    # Testing examples
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main app component
│   │   ├── api.js         # API client
│   │   ├── main.jsx       # Entry point
│   │   ├── styles.css     # Global styles
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TaskDetail.jsx
│   │   │   └── ExtractedDataPage.jsx
│   │   └── components/
│   │       ├── TaskForm.jsx
│   │       ├── TaskList.jsx
│   │       ├── TaskFilters.jsx
│   │       ├── QnASection.jsx
│   │       ├── ProgressBar.jsx
│   │       └── TaskDrawer.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── dist/              # Production build (generated)
└── scraping_db.sqlite     # SQLite database (generated)
```

### 13.2 Development Workflow
1. Backend development (Python/Flask)
2. Frontend development (React/Vite)
3. Integration testing
4. User acceptance testing
5. Deployment

---

## 14. TROUBLESHOOTING

### 14.1 Common Issues

**Issue: Gemini API Key Error**
- **Solution:** Ensure `.env` file exists with `GEMINI_API_KEY=your_key`
- **Check:** API key is valid and has quota remaining

**Issue: Playwright Browser Not Found**
- **Solution:** Run `playwright install chromium`
- **Check:** Playwright is installed: `pip list | grep playwright`

**Issue: Frontend Not Connecting to Backend**
- **Solution:** Ensure Flask server is running on port 5000
- **Check:** Vite proxy configuration in `vite.config.js`

**Issue: Database Errors**
- **Solution:** Delete `scraping_db.sqlite` and restart (will recreate)
- **Check:** SQLite is available in Python

**Issue: CORS Errors**
- **Solution:** Flask-CORS is installed and configured
- **Check:** `app.py` has `CORS(app)` enabled

---

## 15. CONCLUSION

The AI-Powered Web Scraping Platform demonstrates:
- **Modern web development practices** - React, Flask, RESTful APIs
- **LLM integration** - Intelligent data extraction using Google Gemini
- **Scalable architecture** - Modular design, easy to extend
- **User-friendly interface** - Professional, minimal, intuitive UI
- **Practical real-world applications** - Market research, competitive analysis, data automation

The platform is suitable for:
- Market research and competitive analysis
- Data collection automation
- Content monitoring
- Academic research
- Business intelligence

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Project Status:** Production Ready  
**Maintained By:** Project Team

---

*This blackbook provides a complete overview of the project architecture, features, and implementation details. Use it as a reference for understanding the system and onboarding new team members.*

