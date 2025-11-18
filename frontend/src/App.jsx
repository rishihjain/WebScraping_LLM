import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/Dashboard.jsx';
import TaskDetailPage from './pages/TaskDetail.jsx';
import ExtractedDataPage from './pages/ExtractedDataPage.jsx';

const App = () => (
  <BrowserRouter>
    <div className="app-shell">
      <div className="app-container">
        <header>
          <h1>AI Web Intelligence</h1>
          <p>
            Domain-aware scraping, structured insights, multi-site comparisons, and interactive Q&A —
            all powered by natural language.
          </p>
        </header>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/task/:taskId" element={<TaskDetailPage />} />
          <Route path="/task/:taskId/data/:resultIndex" element={<ExtractedDataPage />} />
        </Routes>
      </div>
    </div>
  </BrowserRouter>
);

export default App;

