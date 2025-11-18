import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const fetchDomains = () => api.get('/domains').then((res) => res.data.domains || {});

export const fetchTasks = (filters = {}, sortBy = 'created_at', sortOrder = 'DESC', search = '') => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, value);
    }
  });
  if (sortBy) params.append('sort_by', sortBy);
  if (sortOrder) params.append('sort_order', sortOrder);
  if (search) params.append('search', search);
  return api.get(`/tasks?${params.toString()}`).then((res) => res.data.tasks || []);
};

export const fetchTask = (taskId) => api.get(`/tasks/${taskId}`).then((res) => res.data);

export const createTask = (payload) => api.post('/scrape', payload).then((res) => res.data);

export const scheduleTask = (payload) => api.post('/schedule', payload).then((res) => res.data);

export const askQuestion = (taskId, question) =>
  api.post(`/tasks/${taskId}/ask`, { question }).then((res) => res.data);

export const downloadResults = (taskId, format) => {
  window.open(`/api/download/${taskId}/${format}`, '_blank');
};

// Task management APIs
export const deleteTask = (taskId) => api.delete(`/tasks/${taskId}`).then((res) => res.data);

export const bulkDeleteTasks = (taskIds) => 
  api.post('/tasks/bulk-delete', { task_ids: taskIds }).then((res) => res.data);

export const toggleStarTask = (taskId) => 
  api.post(`/tasks/${taskId}/star`).then((res) => res.data);

export const toggleArchiveTask = (taskId) => 
  api.post(`/tasks/${taskId}/archive`).then((res) => res.data);

export const updateTaskTags = (taskId, tags) => 
  api.put(`/tasks/${taskId}/tags`, { tags }).then((res) => res.data);

export const getTaskProgress = (taskId) => 
  api.get(`/tasks/${taskId}/progress`).then((res) => res.data);

