import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { fetchTask, downloadResults, askQuestion } from '../api.js';
import QnASection from '../components/QnASection.jsx';
import { renderInlineMarkdown } from '../utils/markdown.jsx';

const Section = ({ title, children }) => (
  <div className="analysis-card">
    <div className="analysis-card__header">
      <h3>{title}</h3>
    </div>
    <div>{children}</div>
  </div>
);

const Pill = ({ children }) => <span className="pill">{children}</span>;

const formatUserAnswer = (text) => {
  if (!text) return <p className="muted">No answer provided.</p>;
  
  // Convert to string if it's not already
  if (typeof text !== 'string') {
    if (Array.isArray(text)) {
      // If array, join elements (handling both strings and objects)
      text = text.map(item => {
        if (typeof item === 'string') return item;
        if (typeof item === 'object' && item !== null) {
          // Try to extract text from object items
          return item.text || item.answer || item.content || item.message || JSON.stringify(item);
        }
        return String(item);
      }).join('\n');
    } else if (typeof text === 'object' && text !== null) {
      // If it's an object, try to extract meaningful text content
      // Check for common text properties first
      if (text.text) {
        text = text.text;
      } else if (text.answer) {
        text = text.answer;
      } else if (text.content) {
        text = text.content;
      } else if (text.message) {
        text = text.message;
      } else if (text.description) {
        text = text.description;
      } else {
        // Try to extract all string values from the object
        const stringValues = [];
        const extractStrings = (obj, depth = 0) => {
          if (depth > 2) return; // Prevent infinite recursion
          for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
              const value = obj[key];
              if (typeof value === 'string' && value.trim()) {
                stringValues.push(value);
              } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                extractStrings(value, depth + 1);
              } else if (Array.isArray(value)) {
                value.forEach(item => {
                  if (typeof item === 'string' && item.trim()) {
                    stringValues.push(item);
                  }
                });
              }
            }
          }
        };
        extractStrings(text);
        text = stringValues.length > 0 ? stringValues.join('\n\n') : JSON.stringify(text, null, 2);
      }
    } else {
      text = String(text);
    }
  }
  
  // Normalize whitespace: replace multiple spaces with single space, preserve newlines
  text = text.replace(/[ \t]+/g, ' ');
  
  // Split by double newlines first (paragraphs)
  let paragraphs = text.split(/\n\n+/).filter(p => p.trim());
  
  // If no double newlines found, try to detect paragraph breaks
  if (paragraphs.length === 1) {
    if (text.includes('\n')) {
      // Split on single newlines that appear to be paragraph breaks
      // Pattern: end of sentence (period/question/exclamation) followed by newline and capital letter
      paragraphs = text.split(/\n(?=[A-Z])/).filter(p => p.trim());
      
      // If still one paragraph, try splitting on newlines that come after sentence endings
      if (paragraphs.length === 1) {
        paragraphs = text.split(/(?<=[.!?])\n+/).filter(p => p.trim());
      }
    } else {
      // No newlines at all - try to detect natural paragraph breaks
      // Look for: sentence ending + space + capital letter (likely new sentence/paragraph)
      // But be careful not to split mid-sentence (e.g., "Dr. Smith" or "U.S.A.")
      paragraphs = text.split(/(?<=[.!?])\s+(?=[A-Z][a-z])/).filter(p => p.trim());
    }
  }
  
  // Further split very long paragraphs (more than 250 chars) that might contain multiple distinct ideas
  // Look for patterns that suggest topic shifts
  paragraphs = paragraphs.flatMap(para => {
    if (para.length > 250) {
      // Check if paragraph contains multiple distinct topics
      // Pattern: sentence ending followed by a capitalized word that might start a new topic
      // Common topic starters: "The", "However", "Neither", "It", algorithm names, etc.
      const topicMarkers = /(?<=[.!?])\s+(The|However|Neither|It|This|That|These|Those|Bellman-Ford|Dijkstra|Formal|Practical|Applications?|Use cases?|Should be|Can be|Must be|Will be|Is|Are|Was|Were)\s+[A-Z]/i;
      
      if (topicMarkers.test(para)) {
        // Split on sentence endings that are followed by topic markers
        const splits = para.split(/(?<=[.!?])\s+(?=(?:The|However|Neither|It|This|That|These|Those|Bellman-Ford|Dijkstra|Formal|Practical|Applications?|Use cases?|Should be|Can be|Must be|Will be|Is|Are|Was|Were)\s+[A-Z])/i);
        return splits.length > 1 ? splits.filter(s => s.trim()) : [para];
      }
      
      // If no topic markers, split on sentence endings in very long text
      if (para.length > 400) {
        const sentences = para.split(/(?<=[.!?])\s+(?=[A-Z][a-z])/).filter(s => s.trim());
        return sentences.length > 1 ? sentences : [para];
      }
    }
    return [para];
  });
  
  return (
    <div className="formatted-text">
      {paragraphs.map((paragraph, pIdx) => {
        const trimmed = paragraph.trim();
        
        // Check for numbered lists
        if (/^\d+[\.\)]\s/.test(trimmed)) {
          const lines = trimmed.split(/\n/).filter(l => l.trim());
          return (
            <div key={pIdx} className="numbered-list">
              {lines.map((line, lIdx) => {
                // Remove the number prefix for parsing
                const lineContent = line.replace(/^\d+[\.\)]\s*/, '');
                return (
                  <p key={lIdx} className="numbered-point">
                    {renderInlineMarkdown(lineContent.trim())}
                  </p>
                );
              })}
            </div>
          );
        }
        
        // Check for bullet lists
        if (/^[-•*]\s/.test(trimmed)) {
          const lines = trimmed.split(/\n/).filter(l => l.trim());
          return (
            <div key={pIdx} className="bullet-list">
              {lines.map((line, lIdx) => {
                // Remove the bullet prefix for parsing
                const lineContent = line.replace(/^[-•*]\s*/, '');
                return (
                  <p key={lIdx} className="bullet-point">
                    {renderInlineMarkdown(lineContent.trim())}
                  </p>
                );
              })}
            </div>
          );
        }
        
        // Regular paragraph - split by sentences for better formatting
        const sentences = trimmed.split(/(?<=[.!?])\s+/).filter(s => s.trim());
        return (
          <div key={pIdx} className="paragraph-group">
            {sentences.map((sentence, sIdx) => (
              <p key={sIdx} className="answer-paragraph">
                {renderInlineMarkdown(sentence.trim())}
              </p>
            ))}
          </div>
        );
      })}
    </div>
  );
};

const TaskDetailPage = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const loadTask = async () => {
    setLoading(true);
    try {
      const data = await fetchTask(taskId);
      setTask(data);
    } catch (error) {
      alert(error.response?.data?.error || error.message);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  if (loading) {
    return <p>Loading analysis...</p>;
  }

  if (!task) {
    return null;
  }

  const successes = task.results?.filter((r) => r.status === 'success') || [];
  const comparison = task.comparison && !task.comparison.error ? task.comparison : null;

  return (
    <div className="detail-page">
      <button className="btn-back-dashboard" onClick={() => navigate('/')}>
        <span className="back-icon">←</span>
        <span>Back to Dashboard</span>
      </button>
      <div className="detail-header">
        <div>
          <h2>{task.name || `Task #${task.id}`}</h2>
          <p className="muted">
            {dayjs(task.created_at).format('MMM D, YYYY HH:mm')} · Domain:{' '}
            {task.domain?.toUpperCase()}
          </p>
        </div>
        <div className="detail-actions">
          <button className="btn btn-secondary" onClick={() => downloadResults(task.id, 'json')}>
            Download JSON
          </button>
          <button className="btn btn-secondary" onClick={() => downloadResults(task.id, 'csv')}>
            Download CSV
          </button>
          <button className="btn btn-secondary" onClick={() => downloadResults(task.id, 'txt')}>
            Download TXT
          </button>
        </div>
      </div>

      {successes.map((result, idx) => (
        <Section key={result.url || idx} title={`Website ${idx + 1}: ${result.url || 'N/A'}`}>
          <div className="pill-row">
            <Pill>Status: {result.status}</Pill>
          </div>
          <div style={{ marginTop: '16px' }}>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate(`/task/${task.id}/data/${idx}`)}
            >
              📊 View Extracted Data
            </button>
            <p className="hint" style={{ marginTop: '8px' }}>
              {Object.keys(result.data?.extracted_data || {}).length} fields extracted
            </p>
          </div>
        </Section>
      ))}

      {task.results?.some((r) => r.status === 'error') && (
        <Section title="Errors">
          {task.results
            .filter((r) => r.status === 'error')
            .map((error, idx) => (
              <p key={idx} className="error-text">
                {error.url}: {error.error}
              </p>
            ))}
        </Section>
      )}

      {successes.map((result, idx) => {
        const analysis = result.data?.analysis;
        const legacyInsights = result.data?.insights;
        if (!analysis && !legacyInsights) return null;
        return (
          <Section key={`analysis-${idx}`} title={`Insights for ${result.url || 'Website'}`}>
            {analysis ? (
              <>
                <p className="summary">{renderInlineMarkdown(analysis.summary)}</p>
                <div className="pill-row">
                  {analysis.key_points?.map((point, id) => (
                    <Pill key={id}>{point}</Pill>
                  ))}
                </div>
                <h4>Insights</h4>
                <ul>
                  {analysis.insights?.map((item, id) => (
                    <li key={id}>{renderInlineMarkdown(item)}</li>
                  ))}
                </ul>
                {analysis.opportunities?.length > 0 && (
                  <>
                    <h4>Opportunities</h4>
                    <ul>
                      {analysis.opportunities.map((item, id) => (
                        <li key={id}>{renderInlineMarkdown(item)}</li>
                      ))}
                    </ul>
                  </>
                )}
                {analysis.risks?.length > 0 && (
                  <>
                    <h4>Risks</h4>
                    <ul>
                      {analysis.risks.map((item, id) => (
                        <li key={id}>{renderInlineMarkdown(item)}</li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            ) : (
              <pre style={{ whiteSpace: 'pre-wrap' }}>{legacyInsights}</pre>
            )}
          </Section>
        );
      })}

      {/* Fallback: If no comparison but individual answers exist, show them */}
      {(!task.comparison || !task.comparison.user_request_answer) && successes.length > 0 && (
        <Section title="User Request Answer (Combined Analysis)">
          <div className="user-answer-formatted">
            {successes.map((result, idx) => {
              const analysis = result.data?.analysis;
              if (!analysis?.user_request_answer) return null;
              return (
                <div key={idx} style={{ marginBottom: idx < successes.length - 1 ? '24px' : '0' }}>
                  {successes.length > 1 && (
                    <p style={{ fontWeight: 600, marginBottom: '8px', color: '#6366f1' }}>
                      From {result.url || `Website ${idx + 1}`}:
                    </p>
                  )}
                  {formatUserAnswer(analysis.user_request_answer)}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {task.comparison && !task.comparison.error && (
        <Section title="Multi-Website Comparison">
          {task.comparison.summary && <p className="summary">{renderInlineMarkdown(task.comparison.summary)}</p>}
          
          {task.comparison.user_request_answer && (
            <>
              <h4>What Should We Extract? (Cross-Website Analysis)</h4>
              <div className="user-answer-formatted">
                {formatUserAnswer(task.comparison.user_request_answer)}
              </div>
            </>
          )}
          
          <div className="comparison-grid">
            <div>
              <h4>Similarities</h4>
              {task.comparison.similarities?.length ? (
                <ul>
                  {task.comparison.similarities.map((item, idx) => (
                    <li key={idx}>{renderInlineMarkdown(item)}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Not available.</p>
              )}
            </div>
            <div>
              <h4>Differences</h4>
              {task.comparison.differences?.length ? (
                <ul>
                  {task.comparison.differences.map((item, idx) => (
                    <li key={idx}>{renderInlineMarkdown(item)}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Not available.</p>
              )}
            </div>
          </div>
          {task.comparison.comparison_table && (
            <div className="comparison-visual">
              <h4>Comparison Metrics</h4>
              <div className="comparison-table-wrapper">
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Metric</th>
                      {successes.map((result, idx) => (
                        <th key={idx}>Website {idx + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {task.comparison.comparison_table.metrics?.map((metric, mIdx) => (
                      <tr key={mIdx}>
                        <td className="metric-name">{metric}</td>
                        {successes.map((result, rIdx) => {
                          // Try different possible structures
                          const urlKey = `website_${rIdx + 1}`;
                          const row = task.comparison.comparison_table.rows?.find(
                            r => r.metric === metric
                          );
                          let value = 'N/A';
                          if (row?.values) {
                            value = row.values[urlKey] || row.values[result.url] || Object.values(row.values)[rIdx] || 'N/A';
                          } else if (task.comparison.comparison_table[`website_${rIdx + 1}`]) {
                            const websiteData = task.comparison.comparison_table[`website_${rIdx + 1}`];
                            value = websiteData[mIdx] || 'N/A';
                          }
                          return (
                            <td key={rIdx} className="metric-value">
                              {value}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {task.comparison.websites && Object.keys(task.comparison.websites).length > 0 && (
            <div className="comparison-scores">
              <h4>Quick Scores</h4>
              <div className="score-cards">
                {Object.entries(task.comparison.websites).map(([url, analysis], idx) => (
                  <div key={url} className="score-card">
                    <div className="score-header">
                      <span className="score-label">Website {idx + 1}</span>
                      {analysis.score && (
                        <span className="score-value">{analysis.score}/10</span>
                      )}
                    </div>
                    {analysis.best_for && (
                      <p className="score-best-for">{analysis.best_for}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {task.comparison.recommendation && (
            <>
              <h4>Recommendation</h4>
              <p>{renderInlineMarkdown(task.comparison.recommendation)}</p>
            </>
          )}
        </Section>
      )}
      {task.comparison?.error && (
        <Section title="Multi-Website Comparison">
          <p className="error-text">Comparison generation failed: {task.comparison.error}</p>
        </Section>
      )}

      {/* Technical Details Section - Collapsible */}
      {task.comparison && !task.comparison.error && task.comparison.extraction_recommendations && (
        <Section title="Technical Details">
          <div className="technical-details">
            <button
              className="technical-details-toggle"
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              type="button"
            >
              <span>{showTechnicalDetails ? '▼' : '▶'}</span>
              <span>Extraction Recommendations</span>
              <span className="technical-details-badge">Developer Info</span>
            </button>
            
            {showTechnicalDetails && (
              <div className="technical-details-content">
                {task.comparison.extraction_recommendations.common_fields?.length > 0 && (
                  <div className="technical-section">
                    <h5>Common Fields (Available on All Sites)</h5>
                    <div className="pill-row">
                      {task.comparison.extraction_recommendations.common_fields.map((field, idx) => (
                        <Pill key={idx}>{field}</Pill>
                      ))}
                    </div>
                  </div>
                )}
                
                {task.comparison.extraction_recommendations.unique_fields && 
                 Object.keys(task.comparison.extraction_recommendations.unique_fields).length > 0 && (
                  <div className="technical-section">
                    <h5>Unique Fields (Site-Specific)</h5>
                    {Object.entries(task.comparison.extraction_recommendations.unique_fields).map(([url, fields], idx) => (
                      <div key={idx} className="unique-field-item">
                        <div className="unique-field-url">{url}</div>
                        <div className="pill-row" style={{ marginTop: '8px' }}>
                          {fields.map((field, fIdx) => (
                            <Pill key={fIdx}>{field}</Pill>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {task.comparison.extraction_recommendations.best_practices?.length > 0 && (
                  <div className="technical-section">
                    <h5>Best Practices</h5>
                    <ul className="best-practices-list">
                      {task.comparison.extraction_recommendations.best_practices.map((practice, idx) => (
                        <li key={idx}>{renderInlineMarkdown(practice)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </Section>
      )}

      <QnASection taskId={task.id} onAsk={askQuestion} />
    </div>
  );
};

export default TaskDetailPage;

