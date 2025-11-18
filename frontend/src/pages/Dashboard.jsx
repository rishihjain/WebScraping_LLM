import { useEffect, useState } from 'react';
import TaskForm from '../components/TaskForm.jsx';
import TaskList from '../components/TaskList.jsx';
import TaskFilters from '../components/TaskFilters.jsx';
import { fetchDomains, fetchTasks, createTask, scheduleTask } from '../api.js';

const DashboardPage = () => {
  const [domains, setDomains] = useState({});
  const [tasks, setTasks] = useState([]);
  const [creating, setCreating] = useState(false);
  const [filters, setFilters] = useState({});
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('DESC');
  const [searchQuery, setSearchQuery] = useState('');

  const loadDomains = async () => {
    const data = await fetchDomains();
    setDomains(data);
  };

  const loadTasks = async () => {
    const data = await fetchTasks(filters, sortBy, sortOrder, searchQuery);
    setTasks(data);
  };

  useEffect(() => {
    loadDomains();
  }, []);

  useEffect(() => {
    loadTasks();
    // Poll more frequently if there are processing tasks
    const hasProcessing = tasks.some(t => t.status === 'processing' || t.status === 'pending');
    const interval = setInterval(loadTasks, hasProcessing ? 3000 : 10000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy, sortOrder, searchQuery]);

  const handleCreateTask = async (formState) => {
    const urls = formState.urls
      .split('\n')
      .map((url) => url.trim())
      .filter(Boolean);

    if (formState.enableComparison && urls.length < 2) {
      alert('Please provide at least two URLs for comparison.');
      return;
    }

    const tags = formState.tags
      ? formState.tags.split(',').map(t => t.trim()).filter(Boolean)
      : [];

    setCreating(true);
    try {
      if (formState.isScheduled) {
        const payload = {
          task_name: formState.taskName || `Scheduled: ${formState.instruction.substring(0, 50)}`,
          urls,
          instruction: formState.instruction,
          domain: formState.domain,
          schedule_type: formState.scheduleType,
          schedule_time: formState.scheduleTime,
          tags,
        };
        await scheduleTask(payload);
        alert('Task scheduled successfully!');
      } else {
        const payload = {
          domain: formState.domain,
          urls,
          instruction: formState.instruction,
          enable_comparison: formState.enableComparison,
          task_name: formState.taskName || undefined,
          tags,
        };
        await createTask(payload);
        alert('Analysis started! It may take up to a minute.');
      }
      await loadTasks();
    } catch (error) {
      alert(error.response?.data?.error || error.message);
    } finally {
      setCreating(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleSortChange = (newSortBy, newSortOrder) => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
  };

  const stats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    processing: tasks.filter(t => t.status === 'processing' || t.status === 'pending').length,
    error: tasks.filter(t => t.status === 'error').length,
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="stats-grid">
          <div className="stat-card stat-total">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Tasks</div>
            </div>
          </div>
          <div className="stat-card stat-completed">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-value">{stats.completed}</div>
              <div className="stat-label">Completed</div>
            </div>
          </div>
          <div className="stat-card stat-processing">
            <div className="stat-icon">⚙️</div>
            <div className="stat-content">
              <div className="stat-value">{stats.processing}</div>
              <div className="stat-label">Processing</div>
            </div>
          </div>
          <div className="stat-card stat-error">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-value">{stats.error}</div>
              <div className="stat-label">Errors</div>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-form-section">
          <TaskForm domains={domains} onSubmit={handleCreateTask} loading={creating} />
        </div>
        <div className="dashboard-tasks-section">
          <div className="search-bar-container">
            <div className="search-icon">🔍</div>
            <input
              type="text"
              id="search"
              className="search-input"
              placeholder="Search tasks by name, URL, or instruction..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button 
                className="search-clear"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <TaskFilters
            domains={domains}
            filters={filters}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onFilterChange={handleFilterChange}
            onSortChange={handleSortChange}
          />
          <TaskList
            tasks={tasks}
            domains={domains}
            filters={filters}
            sortBy={sortBy}
            sortOrder={sortOrder}
            searchQuery={searchQuery}
            onUpdate={loadTasks}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

