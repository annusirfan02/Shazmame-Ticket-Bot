const { getTicketDetails, addPrivateNote, sendEmailReply } = require('../lib/freshdesk');
const { generateSummary } = require('../lib/summarizer');
const { isTargetCompany, hasEscalationTag } = require('../lib/validator');

const NEW_TICKET_NOTE =
  'If this ticket is not resolved, please add the tag: escalate-unresolved';

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (process.env.WEBHOOK_SECRET) {
    const provided = req.query.secret || req.headers['x-webhook-secret'];
    if (provided !== process.env.WEBHOOK_SECRET) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  // Always resolve with 200 below (even on internal errors) so Freshdesk
  // doesn't treat this as a failed delivery and retry the webhook.
  try {
    const payload = req.body || {};
    const event = payload.event;
    const ticketId = payload.ticket_id || payload.ticketId;

    if (!ticketId) {
      return res.status(200).json({ ok: false, reason: 'missing ticket_id' });
    }

    if (event === 'ticket_created') {
      const handled = await handleTicketCreated(ticketId);
      return res.status(200).json({ ok: true, handled: handled ? 'ticket_created' : 'ignored' });
    }

    if (event === 'ticket_updated') {
      const handled = await handleTicketUpdated(ticketId, payload);
      return res.status(200).json({ ok: true, handled: handled ? 'ticket_updated' : 'ignored' });
    }

    return res.status(200).json({ ok: true, handled: 'ignored', reason: 'unknown event' });
  } catch (err) {
    console.error('Webhook error:', err);
    return res.status(200).json({ ok: false, error: err.message });
  }
};

async function handleTicketCreated(ticketId) {
  const ticket = await getTicketDetails(ticketId);

  if (!(await isTargetCompany(ticket))) {
    return false;
  }

  await addPrivateNote(ticketId, NEW_TICKET_NOTE);
  return true;
}

async function handleTicketUpdated(ticketId, payload) {
  const tagAdded = hasEscalationTag(payload.previous_tags, payload.tags);
  if (!tagAdded) {
    return false;
  }

  const ticket = await getTicketDetails(ticketId);
  if (!(await isTargetCompany(ticket))) {
    return false;
  }

  const summary = await generateSummary(ticket);
  await sendEmailReply(ticketId, summary);
  return true;
}
