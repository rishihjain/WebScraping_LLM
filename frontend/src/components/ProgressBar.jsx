import { useEffect, useState } from 'react';
import { getTaskProgress } from '../api.js';

const ProgressBar = ({ taskId, totalUrls, onComplete }) => {
  const [progress, setProgress] = useState(null);
  const [estimatedTime, setEstimatedTime] = useState(null);

  useEffect(() => {
    if (!taskId) return;

    const fetchProgress = async () => {
      try {
        const data = await getTaskProgress(taskId);
        setProgress(data.progress);
        setEstimatedTime(data.estimated_time_remaining);
        
        // If task is completed, notify parent
        if (data.status === 'completed' || data.status === 'error') {
          if (onComplete) onComplete();
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
      }
    };

    // Fetch immediately
    fetchProgress();

    // Poll every 2 seconds if task is still processing
    const interval = setInterval(() => {
      fetchProgress();
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, onComplete]);

  if (!progress || !progress.total || progress.total === 0) return null;

  const percentage = Math.round((progress.current / progress.total) * 100);
  const formatTime = (seconds) => {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="progress-container">
      <div className="progress-header">
        <div>
          <strong>{progress.message || `Processing ${progress.current}/${progress.total}...`}</strong>
          {progress.current_url && (
            <div className="progress-url">{progress.current_url}</div>
          )}
        </div>
        {estimatedTime && (
          <div className="progress-time">Est. {formatTime(estimatedTime)} remaining</div>
        )}
      </div>
      <div className="progress-bar-wrapper">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="progress-stats">
        <span>URL {progress.current} of {progress.total}</span>
        <span>{percentage}%</span>
      </div>
    </div>
  );
};

export default ProgressBar;

