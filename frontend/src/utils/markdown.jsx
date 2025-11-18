// Helper function to parse inline markdown (bold, italic, etc.)
export const parseInlineMarkdown = (text) => {
  if (!text) return [{ type: 'text', content: '' }];
  
  const parts = [];
  let lastIndex = 0;
  
  // Find all markdown patterns with their positions
  const allMatches = [];
  
  // Find bold (**text**) - must be done first to avoid conflicts with italic
  const boldRegex = /\*\*([^*]+?)\*\*/g;
  let match;
  while ((match = boldRegex.exec(text)) !== null) {
    allMatches.push({
      index: match.index,
      end: match.index + match[0].length,
      type: 'bold',
      content: match[1]
    });
  }
  
  // Find code (`text`)
  const codeRegex = /`([^`]+?)`/g;
  while ((match = codeRegex.exec(text)) !== null) {
    allMatches.push({
      index: match.index,
      end: match.index + match[0].length,
      type: 'code',
      content: match[1]
    });
  }
  
  // Find italic (*text*) - but exclude if it's part of **
  const italicRegex = /\*([^*]+?)\*/g;
  while ((match = italicRegex.exec(text)) !== null) {
    // Check if this is not part of a bold marker
    const beforeChar = match.index > 0 ? text[match.index - 1] : '';
    const afterChar = match.index + match[0].length < text.length ? text[match.index + match[0].length] : '';
    
    if (beforeChar !== '*' && afterChar !== '*') {
      allMatches.push({
        index: match.index,
        end: match.index + match[0].length,
        type: 'italic',
        content: match[1]
      });
    }
  }
  
  // If no matches, return plain text
  if (allMatches.length === 0) {
    return [{ type: 'text', content: text }];
  }
  
  // Sort matches by index
  allMatches.sort((a, b) => a.index - b.index);
  
  // Remove overlapping matches (prioritize bold > code > italic)
  const filteredMatches = [];
  for (const match of allMatches) {
    let overlaps = false;
    for (const existing of filteredMatches) {
      if (match.index < existing.end && match.end > existing.index) {
        overlaps = true;
        break;
      }
    }
    if (!overlaps) {
      filteredMatches.push(match);
    }
  }
  
  // Build parts array
  filteredMatches.forEach((match) => {
    // Add text before this match
    if (match.index > lastIndex) {
      const beforeText = text.substring(lastIndex, match.index);
      if (beforeText) {
        parts.push({ type: 'text', content: beforeText });
      }
    }
    
    // Add the formatted part
    parts.push({ type: match.type, content: match.content });
    lastIndex = match.end;
  });
  
  // Add remaining text after last match
  if (lastIndex < text.length) {
    const afterText = text.substring(lastIndex);
    if (afterText) {
      parts.push({ type: 'text', content: afterText });
    }
  }
  
  return parts.length > 0 ? parts : [{ type: 'text', content: text }];
};

// Render inline markdown parts as React elements
export const renderInlineMarkdown = (text) => {
  const parts = parseInlineMarkdown(text);
  return parts.map((part, idx) => {
    if (part.type === 'bold') {
      return <strong key={idx}>{part.content}</strong>;
    } else if (part.type === 'italic') {
      return <em key={idx}>{part.content}</em>;
    } else if (part.type === 'code') {
      return <code key={idx} style={{ backgroundColor: '#f4f4f4', padding: '2px 4px', borderRadius: '3px' }}>{part.content}</code>;
    } else {
      return <span key={idx}>{part.content}</span>;
    }
  });
};

