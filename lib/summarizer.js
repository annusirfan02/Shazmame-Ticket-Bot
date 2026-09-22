const { SummarizerManager } = require('node-summarizer');

const SENTENCE_COUNT = parseInt(process.env.SUMMARY_SENTENCE_COUNT || '5', 10);

function stripHtml(text) {
  return String(text || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildSourceText(ticket) {
  const parts = [];

  if (ticket.subject) parts.push(ticket.subject);
  parts.push(stripHtml(ticket.description_text || ticket.description));

  (ticket.conversations || []).forEach((c) => {
    const body = stripHtml(c.body_text || c.body);
    if (body) parts.push(body);
  });

  return parts.filter(Boolean).join('. ');
}

/**
 * Generate a summary of a ticket (subject + description + full conversation
 * history) using the local node-summarizer library — no external AI API.
 */
async function generateSummary(ticket) {
  const sourceText = buildSourceText(ticket);

  let summaryText = sourceText;
  try {
    const summarizer = new SummarizerManager(sourceText, SENTENCE_COUNT);
    const result = await summarizer.getSummaryByRank();
    if (result && typeof result.summary === 'string' && result.summary.trim()) {
      summaryText = result.summary.trim();
    }
  } catch (err) {
    console.error('Summarization failed, falling back to raw text:', err.message);
  }

  return [
    `Ticket Summary: ${ticket.subject || '(no subject)'}`,
    `Status: ${ticket.status} | Priority: ${ticket.priority}`,
    '',
    summaryText,
  ].join('\n');
}

module.exports = { generateSummary };
