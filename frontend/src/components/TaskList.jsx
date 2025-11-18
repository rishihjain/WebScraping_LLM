import { useState } from 'react';
import dayjs from 'dayjs';
import { Link } from 'react-router-dom';
import { deleteTask, toggleStarTask, toggleArchiveTask, updateTaskTags, bulkDeleteTasks } from '../api.js';
import ProgressBar from './ProgressBar.jsx';

const TaskCard = ({ task, onUpdate, onDelete }) => {
  const domainLabel = task.domain ? task.domain.replace('_', ' ') : 'general';
  const hasComparison = Boolean(task.comparison && !task.comparison.error);
  const [showActions, setShowActions] = useState(false);
  const [editingTags, setEditingTags] = useState(false);
  
  // Ensure tags is always an array
  const taskTags = Array.isArray(task.tags) ? task.tags : (task.tags ? [] : []);
  
  const [tagsInput, setTagsInput] = useState(
    taskTags.length > 0 ? taskTags.join(', ') : ''
  );

  const handleStar = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await toggleStarTask(task.id);
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update star status');
    }
  };

  const handleArchive = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await toggleArchiveTask(task.id);
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update archive status');
    }
  };

  const handleDelete = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(task.id);
        if (onDelete) onDelete(task.id);
      } catch (error) {
        alert('Failed to delete task');
      }
    }
  };

  const handleSaveTags = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
    try {
      await updateTaskTags(task.id, tags);
      setEditingTags(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update tags');
    }
  };

  const isProcessing = task.status === 'processing' || task.status === 'pending';

  return (
    <div className={`task-card ${task.archived ? 'archived' : ''}`}>
      <div className="task-card-header">
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className="icon-btn"
              onClick={handleStar}
              title={task.starred ? 'Unstar' : 'Star'}
            >
              {task.starred ? '⭐' : '☆'}
            </button>
            <Link to={`/task/${task.id}`} style={{ flex: 1, textDecoration: 'none', color: 'inherit' }}>
              <strong>{task.name || 'Untitled Task'}</strong>
            </Link>
            {task.is_scheduled && <span className="tag scheduled">Scheduled</span>}
            {hasComparison && <span className="tag comparison-tag">Comparison</span>}
            {task.language && task.language !== 'en' && (
              <span className="tag language">{task.language.toUpperCase()}</span>
            )}
          </div>
          <div className="hint" style={{ marginTop: '4px' }}>
            {domainLabel.toUpperCase()} • {Array.isArray(task.urls) ? task.urls.length : 0} URL(s)
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`status-pill status-${task.status || 'pending'}`}>{task.status}</span>
          <button
            className="icon-btn"
            onClick={() => setShowActions(!showActions)}
            title="Actions"
          >
            ⋮
          </button>
        </div>
      </div>

      {showActions && (
        <div className="task-actions" onClick={(e) => e.stopPropagation()}>
          <button onClick={handleArchive} className="action-btn">
            {task.archived ? '📦 Unarchive' : '📦 Archive'}
          </button>
          <button onClick={() => setEditingTags(!editingTags)} className="action-btn">
            🏷️ {editingTags ? 'Cancel Tags' : 'Edit Tags'}
          </button>
          <button onClick={handleDelete} className="action-btn delete">
            🗑️ Delete
          </button>
        </div>
      )}

      {editingTags && (
        <div className="tags-editor" onClick={(e) => e.stopPropagation()}>
          <input
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="tag1, tag2, tag3"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveTags(e);
              if (e.key === 'Escape') setEditingTags(false);
            }}
            autoFocus
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button onClick={handleSaveTags} className="btn btn-primary btn-sm">Save</button>
            <button onClick={() => setEditingTags(false)} className="btn btn-secondary btn-sm">Cancel</button>
          </div>
        </div>
      )}

      {taskTags.length > 0 && taskTags.some(tag => tag && tag.toString().trim()) && (
        <div className="task-tags">
          {taskTags.filter(tag => tag && tag.toString().trim()).map((tag, idx) => (
            <span key={idx} className="tag-small">{tag}</span>
          ))}
        </div>
      )}

      {isProcessing && task.total_urls && (
        <ProgressBar 
          taskId={task.id} 
          totalUrls={task.total_urls}
          onComplete={onUpdate}
        />
      )}

      <div style={{ marginTop: '12px', color: '#475569', fontSize: '0.9rem' }}>
        <div style={{ marginBottom: '4px' }}>{task.instruction?.substring(0, 100)}{task.instruction?.length > 100 ? '...' : ''}</div>
        <div>Created: {dayjs(task.created_at).format('MMM D, YYYY HH:mm')}</div>
        {task.completed_at && (
          <div>Completed: {dayjs(task.completed_at).format('MMM D, YYYY HH:mm')}</div>
        )}
        {task.next_run && (
          <div>Next run: {dayjs(task.next_run).format('MMM D, YYYY HH:mm')}</div>
        )}
      </div>
    </div>
  );
};

const TaskList = ({ tasks, domains, filters, sortBy, sortOrder, onUpdate, searchQuery }) => {
  const [selectedTasks, setSelectedTasks] = useState(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);

  const handleSelectTask = (taskId) => {
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(taskId)) {
      newSelected.delete(taskId);
    } else {
      newSelected.add(taskId);
    }
    setSelectedTasks(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const handleSelectAll = () => {
    if (selectedTasks.size === tasks.length) {
      setSelectedTasks(new Set());
      setShowBulkActions(false);
    } else {
      setSelectedTasks(new Set(tasks.map(t => t.id)));
      setShowBulkActions(true);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedTasks.size === 0) return;
    if (window.confirm(`Are you sure you want to delete ${selectedTasks.size} task(s)?`)) {
      try {
        await bulkDeleteTasks(Array.from(selectedTasks));
        setSelectedTasks(new Set());
        setShowBulkActions(false);
        if (onUpdate) onUpdate();
      } catch (error) {
        alert('Failed to delete tasks');
      }
    }
  };

  const handleTaskDelete = (taskId) => {
    const newSelected = new Set(selectedTasks);
    newSelected.delete(taskId);
    setSelectedTasks(newSelected);
    if (onUpdate) onUpdate();
  };

  if (tasks.length === 0) {
    return (
      <div className="card">
        <h2>Analysis History</h2>
        <p>No tasks found. {searchQuery || Object.keys(filters).length > 0 ? 'Try adjusting your filters.' : 'Run your first analysis to see it here.'}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2>Analysis History ({tasks.length})</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {showBulkActions && (
            <>
              <button onClick={handleBulkDelete} className="btn btn-secondary btn-sm">
                Delete Selected ({selectedTasks.size})
              </button>
              <button onClick={() => { setSelectedTasks(new Set()); setShowBulkActions(false); }} className="btn btn-secondary btn-sm">
                Clear Selection
              </button>
            </>
          )}
        </div>
      </div>

      <div className="tasks-list">
        {tasks.map((task) => (
          <div key={task.id} style={{ position: 'relative' }}>
            <input
              type="checkbox"
              checked={selectedTasks.has(task.id)}
              onChange={() => handleSelectTask(task.id)}
              style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 10 }}
              onClick={(e) => e.stopPropagation()}
            />
            <TaskCard 
              task={task} 
              onUpdate={onUpdate}
              onDelete={handleTaskDelete}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskList;

