import { useState } from 'react';

const TaskForm = ({ domains, onSubmit, loading }) => {
  const [formState, setFormState] = useState({
    domain: '',
    urls: '',
    instruction: '',
    enableComparison: false,
    taskName: '',
    tags: '',
    isScheduled: false,
    scheduleType: 'daily',
    scheduleTime: '',
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormState((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formState);
  };

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>New Analysis</h2>
      <div className="form-group">
        <label htmlFor="domain">Domain</label>
        <select
          id="domain"
          name="domain"
          value={formState.domain}
          onChange={handleChange}
          required
        >
          <option value="">Select domain</option>
          {Object.entries(domains).map(([key, value]) => (
            <option key={key} value={key}>
              {value.name}
            </option>
          ))}
        </select>
        <span className="hint">Tailor extraction & analysis to a content type.</span>
      </div>

      <div className="form-group">
        <label>Website URLs</label>
        <textarea
          name="urls"
          rows="3"
          placeholder="https://example.com&#10;https://another-site.com"
          value={formState.urls}
          onChange={handleChange}
          required
        />
        <span className="hint">Enter one URL per line. Add 2+ to compare.</span>
      </div>

      <div className="form-group">
        <label>What should we extract?</label>
        <textarea
          name="instruction"
          rows="3"
          placeholder="e.g., Pull product names, prices, ratings, and highlights"
          value={formState.instruction}
          onChange={handleChange}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="taskName">Task name (optional)</label>
        <input
          type="text"
          id="taskName"
          name="taskName"
          placeholder="Summer laptop research"
          value={formState.taskName}
          onChange={handleChange}
        />
      </div>

      <div className="form-group">
        <label htmlFor="tags">Tags (comma-separated, optional)</label>
        <input
          type="text"
          id="tags"
          name="tags"
          placeholder="research, important, weekly"
          value={formState.tags}
          onChange={handleChange}
        />
        <span className="hint">Add tags to categorize and filter tasks later.</span>
      </div>

      <div className="checkbox-section">
        <div className="checkbox-option">
          <label className="checkbox-label" htmlFor="enableComparison">
            <input
              type="checkbox"
              id="enableComparison"
              name="enableComparison"
              checked={formState.enableComparison}
              onChange={handleChange}
              className="custom-checkbox"
            />
            <span className="checkbox-custom"></span>
            <div className="checkbox-content">
              <div className="checkbox-title">
                <span className="checkbox-icon">🔗</span>
                Enable multi-website comparison
              </div>
              <div className="checkbox-description">
                {/* Compare data across multiple websites to identify similarities, differences, and insights */}
              </div>
            </div>
          </label>
        </div>

        <div className="checkbox-option">
          <label className="checkbox-label" htmlFor="isScheduled">
            <input
              type="checkbox"
              id="isScheduled"
              name="isScheduled"
              checked={formState.isScheduled}
              onChange={handleChange}
              className="custom-checkbox"
            />
            <span className="checkbox-custom"></span>
            <div className="checkbox-content">
              <div className="checkbox-title">
                <span className="checkbox-icon">⏰</span>
                Schedule as recurring task
              </div>
              <div className="checkbox-description">
              {/* Automatically run this analysis on a schedule (daily, weekly, or one-time) */}
              </div>
            </div>
          </label>
        </div>
      </div>

      {formState.isScheduled && (
        <div className="form-group" style={{ paddingLeft: '24px', borderLeft: '3px solid #6366f1' }}>
          <div className="form-group">
            <label htmlFor="scheduleType">Schedule Type</label>
            <select
              id="scheduleType"
              name="scheduleType"
              value={formState.scheduleType}
              onChange={handleChange}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="once">Once (at specific time)</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="scheduleTime">Schedule Time</label>
            <input
              type={formState.scheduleType === 'once' || formState.scheduleType === 'weekly' ? 'datetime-local' : 'time'}
              id="scheduleTime"
              name="scheduleTime"
              value={formState.scheduleTime}
              onChange={handleChange}
              required={formState.isScheduled}
            />
            <span className="hint">
              {formState.scheduleType === 'daily' && 'Time to run daily (e.g., 09:00)'}
              {formState.scheduleType === 'weekly' && 'Pick any date/time - we\'ll use the day of week and time (e.g., Monday 09:00)'}
              {formState.scheduleType === 'once' && 'Date and time to run once'}
            </span>
          </div>
        </div>
      )}

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? 'Analyzing...' : formState.isScheduled ? 'Schedule Task' : 'Start Analysis'}
      </button>
    </form>
  );
};

export default TaskForm;

