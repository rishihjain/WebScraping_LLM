import { useState, useEffect } from 'react';
import { renderInlineMarkdown } from '../utils/markdown.jsx';

const QnASection = ({ taskId, onAsk }) => {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(`qna_history_${taskId}`);
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
  }, [taskId]);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem(`qna_history_${taskId}`, JSON.stringify(history));
    }
  }, [history, taskId]);

  const submitQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const answer = await onAsk(taskId, question.trim());
      setHistory((prev) => [
        {
          question: question.trim(),
          answer: answer.answer || answer,
          supporting_points: answer.supporting_points || [],
          confidence: answer.confidence || 'n/a',
        },
        ...prev,
      ]);
      setQuestion('');
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    if (confirm('Clear all chat history for this task?')) {
      setHistory([]);
      localStorage.removeItem(`qna_history_${taskId}`);
    }
  };

  return (
    <div className="qna-box">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3>Ask follow-up questions</h3>
        {history.length > 0 && (
          <button 
            onClick={clearHistory} 
            className="btn btn-secondary"
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            Clear History
          </button>
        )}
      </div>
      <form onSubmit={submitQuestion} style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <input
          type="text"
          placeholder="e.g., Which product is cheaper?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{ flex: 1, padding: '10px 14px', borderRadius: '10px', border: '1px solid #e5e7eb' }}
        />
        <button type="submit" className="btn btn-secondary" disabled={loading}>
          {loading ? 'Asking...' : 'Ask'}
        </button>
      </form>
      <div className="qna-list">
        {history.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px', 
            color: '#9ca3af',
            fontStyle: 'italic' 
          }}>
            No questions asked yet. Start a conversation!
          </div>
        )}
        {history.map((item, idx) => (
          <div className="qna-item" key={idx}>
            <div className="qna-question">
              <strong>Q:</strong> {item.question}
            </div>
            <div className="qna-answer">
              <strong>A:</strong> {renderInlineMarkdown(item.answer)}
            </div>
            {item.supporting_points?.length > 0 && (
              <div className="qna-supporting">
                <strong>Supporting Points:</strong>
                <ul>
                  {item.supporting_points.map((point, pointIdx) => (
                    <li key={pointIdx}>{renderInlineMarkdown(point)}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="qna-meta">
              <span className="hint">
                <span style={{ fontWeight: 600 }}>Confidence:</span> 
                <span style={{ 
                  color: item.confidence === 'high' ? '#10b981' : 
                         item.confidence === 'medium' ? '#f59e0b' : '#ef4444',
                  fontWeight: 600
                }}>
                  {item.confidence}
                </span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default QnASection;

