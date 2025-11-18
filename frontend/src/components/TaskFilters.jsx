import { useState } from 'react';

const TaskFilters = ({ domains, onFilterChange, filters, sortBy, sortOrder, onSortChange }) => {
  const [showFilters, setShowFilters] = useState(false);

  const handleFilterChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    onFilterChange({});
    onSortChange('created_at', 'DESC');
  };

  return (
    <div className="filters-container">
      <div className="filters-header">
        <button 
          type="button" 
          className="btn btn-secondary"
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? '▼' : '▶'} Filters & Sort
        </button>
        {(Object.keys(filters).length > 0 || sortBy !== 'created_at' || sortOrder !== 'DESC') && (
          <button 
            type="button" 
            className="btn btn-secondary"
            onClick={clearFilters}
            style={{ marginLeft: '8px' }}
          >
            Clear All
          </button>
        )}
      </div>

      {showFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Domain</label>
            <select
              value={filters.domain || ''}
              onChange={(e) => handleFilterChange('domain', e.target.value || null)}
            >
              <option value="">All Domains</option>
              {Object.entries(domains).map(([key, value]) => (
                <option key={key} value={key}>{value.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Status</label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value || null)}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Date From</label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => handleFilterChange('date_from', e.target.value || null)}
            />
          </div>

          <div className="filter-group">
            <label>Date To</label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => handleFilterChange('date_to', e.target.value || null)}
            />
          </div>

          <div className="filter-group">
            <label>Show</label>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input
                  type="checkbox"
                  checked={filters.starred === true}
                  onChange={(e) => handleFilterChange('starred', e.target.checked ? true : null)}
                />
                Starred Only
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input
                  type="checkbox"
                  checked={filters.archived === true}
                  onChange={(e) => handleFilterChange('archived', e.target.checked ? true : null)}
                />
                Archived Only
              </label>
            </div>
          </div>

          <div className="filter-group">
            <label>Sort By</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <select
                value={sortBy}
                onChange={(e) => onSortChange(e.target.value, sortOrder)}
              >
                <option value="created_at">Date</option>
                <option value="name">Name</option>
                <option value="status">Status</option>
                <option value="domain">Domain</option>
                <option value="completed_at">Completed Date</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => onSortChange(sortBy, e.target.value)}
              >
                <option value="DESC">Descending</option>
                <option value="ASC">Ascending</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskFilters;

