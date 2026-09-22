const axios = require('axios');

const DOMAIN = process.env.FRESHDESK_DOMAIN;
const API_KEY = process.env.FRESHDESK_API_KEY;

function client() {
  if (!DOMAIN || !API_KEY) {
    throw new Error('FRESHDESK_DOMAIN and FRESHDESK_API_KEY must be set');
  }
  return axios.create({
    baseURL: `https://${DOMAIN}/api/v2`,
    auth: { username: API_KEY, password: 'X' },
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Fetch a ticket with its full conversation thread.
 */
async function getTicketDetails(ticketId) {
  const http = client();
  const { data: ticket } = await http.get(`/tickets/${ticketId}`, {
    params: { include: 'conversations,requester' },
  });

  return ticket;
}

/**
 * Fetch company details (used to verify the Relationship ID custom field).
 */
async function getCompanyDetails(companyId) {
  const http = client();
  const { data } = await http.get(`/companies/${companyId}`);
  return data;
}

/**
 * Add a private note to a ticket.
 */
async function addPrivateNote(ticketId, content) {
  const http = client();
  const { data } = await http.post(`/tickets/${ticketId}/notes`, {
    body: content,
    private: true,
  });
  return data;
}

/**
 * Send an email reply to the ticket requester through Freshdesk.
 */
async function sendEmailReply(ticketId, summaryText) {
  const http = client();
  const { data } = await http.post(`/tickets/${ticketId}/reply`, {
    body: summaryText,
  });
  return data;
}

module.exports = {
  getTicketDetails,
  getCompanyDetails,
  addPrivateNote,
  sendEmailReply,
};
