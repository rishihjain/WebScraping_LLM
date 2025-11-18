import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchTask } from '../api.js';

const renderValue = (value, depth = 0) => {
  if (value === null || value === undefined) return <span className="muted">N/A</span>;
  
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="muted">Empty array</span>;
    return (
      <div className="data-array">
        {value.map((item, idx) => (
          <div key={idx} className="data-array-item">
            <span className="array-index">[{idx}]</span>
            <div className="array-content">{renderValue(item, depth + 1)}</div>
          </div>
        ))}
      </div>
    );
  }
  
  if (typeof value === 'object') {
    return (
      <div className={`data-object ${depth > 0 ? 'nested' : ''}`}>
        {Object.entries(value).map(([key, val]) => (
          <div key={key} className="data-field">
            <div className="data-key">
              <span className="key-label">{key.replace(/_/g, ' ')}</span>
              <span className="key-type">{getValueType(val)}</span>
            </div>
            <div className="data-value">{renderValue(val, depth + 1)}</div>
          </div>
        ))}
      </div>
    );
  }
  
  return <span className="data-primitive">{String(value)}</span>;
};

const getValueType = (value) => {
  if (Array.isArray(value)) return `array[${value.length}]`;
  if (typeof value === 'object' && value !== null) return 'object';
  return typeof value;
};

const ExtractedDataPage = () => {
  const { taskId, resultIndex } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState(null);

  useEffect(() => {
    const loadTask = async () => {
      setLoading(true);
      try {
        const data = await fetchTask(taskId);
        setTask(data);
        
        const idx = parseInt(resultIndex || '0');
        const successes = data.results?.filter((r) => r.status === 'success') || [];
        if (successes[idx]) {
          setSelectedResult(successes[idx]);
        }
      } catch (error) {
        alert(error.response?.data?.error || error.message);
        navigate(`/task/${taskId}`);
      } finally {
        setLoading(false);
      }
    };
    loadTask();
  }, [taskId, resultIndex, navigate]);

  if (loading) {
    return (
      <div className="detail-page">
        <p>Loading extracted data...</p>
      </div>
    );
  }

  if (!task || !selectedResult) {
    return (
      <div className="detail-page">
        <p>Data not found</p>
        <button className="btn btn-secondary" onClick={() => navigate(`/task/${taskId}`)}>
          ← Back to analysis
        </button>
      </div>
    );
  }

  const extractedData = selectedResult.data?.extracted_data || {};

  return (
    <div className="detail-page">
      <button className="btn btn-secondary" onClick={() => navigate(`/task/${taskId}`)}>
        ← Back to analysis
      </button>
      
      <div className="detail-header">
        <div>
          <h2>Extracted Data</h2>
          <p className="muted">
            {task.name || `Task #${task.id}`} · {selectedResult.url || 'Website'}
          </p>
        </div>
      </div>

      <div className="extracted-data-container">
        <div className="data-stats">
          <div className="stat-item">
            <span className="stat-label">Total Fields</span>
            <span className="stat-value">{Object.keys(extractedData).length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Data Type</span>
            <span className="stat-value">Structured JSON</span>
          </div>
        </div>

        <div className="extracted-data-content">
          {Object.keys(extractedData).length === 0 ? (
            <div className="empty-state">
              <p>No data extracted from this website.</p>
            </div>
          ) : (
            renderValue(extractedData)
          )}
        </div>
      </div>
    </div>
  );
};

export default ExtractedDataPage;

