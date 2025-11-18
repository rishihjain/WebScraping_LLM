import dayjs from 'dayjs';
import QnASection from './QnASection.jsx';
import { renderInlineMarkdown } from '../utils/markdown.jsx';

const Section = ({ title, children }) => (
  <div className="analysis-section">
    <h3>{title}</h3>
    {children}
  </div>
);

const List = ({ items }) => {
  if (!items || items.length === 0) return <p>Not available.</p>;
  return (
    <ul className="list">
      {items.map((item, idx) => (
        <li key={`${item}-${idx}`}>{renderInlineMarkdown(item)}</li>
      ))}
    </ul>
  );
};

const ComparisonPanel = ({ comparison }) => {
  if (!comparison || comparison.error) return null;

  return (
    <div className="comparison-panel">
      <h3>Multi-Website Comparison</h3>
      {comparison.summary && <p>{renderInlineMarkdown(comparison.summary)}</p>}
      {comparison.similarities && (
        <Section title="Similarities">
          <List items={comparison.similarities} />
        </Section>
      )}
      {comparison.differences && (
        <Section title="Differences">
          <List items={comparison.differences} />
        </Section>
      )}
      {comparison.recommendation && (
        <Section title="Recommendation">
          <p>{renderInlineMarkdown(comparison.recommendation)}</p>
        </Section>
      )}
    </div>
  );
};

const TaskDrawer = ({ task, onClose, onAsk }) => {
  if (!task) return null;

  const successResult = task.results?.find((r) => r.status === 'success');
  const analysis = successResult?.data?.analysis;
  const legacyInsights = successResult?.data?.insights;

  return (
    <div className={`drawer ${task ? 'open' : ''}`}>
      <div className="drawer-header">
        <div>
          <h2>{task.name || 'Task Details'}</h2>
          <p className="hint">{dayjs(task.created_at).format('MMM D, YYYY HH:mm')}</p>
        </div>
        <button className="btn btn-secondary" onClick={onClose}>
          Close
        </button>
      </div>

      {analysis ? (
        <>
          <Section title="Summary">
            <p>{renderInlineMarkdown(analysis.summary)}</p>
          </Section>
          <Section title="Key Points">
            <List items={analysis.key_points} />
          </Section>
          <Section title="Insights">
            <List items={analysis.insights} />
          </Section>
          <Section title="Answer to your request">
            <p>{renderInlineMarkdown(analysis.user_request_answer)}</p>
          </Section>
          {(analysis.opportunities?.length || analysis.risks?.length) && (
            <Section title="Opportunities & Risks">
              <strong>Opportunities</strong>
              <List items={analysis.opportunities} />
              <strong>Risks</strong>
              <List items={analysis.risks} />
            </Section>
          )}
        </>
      ) : legacyInsights ? (
        <Section title="Insights">
          <pre style={{ fontSize: '0.9rem', whiteSpace: 'pre-wrap', color: '#475569' }}>
            {legacyInsights}
          </pre>
        </Section>
      ) : (
        <p>No analysis available yet.</p>
      )}

      {task.results?.map((result, idx) => {
        const extracted = result.data?.extracted_data;
        return (
          <Section
            key={`${result.url}-${idx}`}
            title={`${result.status === 'success' ? 'Website' : 'Error'} ${idx + 1}: ${
              result.url || 'N/A'
            }`}
          >
            {result.status === 'success' ? (
              <pre style={{ fontSize: '0.85rem', color: '#475569', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(extracted, null, 2)}
              </pre>
            ) : (
              <p style={{ color: '#b91c1c' }}>{result.error || 'Unknown error'}</p>
            )}
          </Section>
        );
      })}

      <ComparisonPanel comparison={task.comparison} />

      <QnASection taskId={task.id} onAsk={onAsk} />
    </div>
  );
};

export default TaskDrawer;

