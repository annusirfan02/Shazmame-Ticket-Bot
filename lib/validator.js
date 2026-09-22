const { getCompanyDetails } = require('./freshdesk');

const TARGET_RELATIONSHIP_ID = process.env.TARGET_RELATIONSHIP_ID || '0-466-515';
const RELATIONSHIP_FIELD_KEY = process.env.FRESHDESK_RELATIONSHIP_FIELD_KEY || 'relationship_id';
const ESCALATION_TAG = process.env.ESCALATION_TAG || 'escalate-unresolved';

function companyMatchesRelationshipId(company) {
  if (!company) return false;

  const customFields = company.custom_fields || {};
  if (customFields[RELATIONSHIP_FIELD_KEY] === TARGET_RELATIONSHIP_ID) {
    return true;
  }

  // Fallback: some setups store the relationship id under a differently
  // named custom field. Scan all custom field values as a safety net.
  return Object.values(customFields).some((value) => value === TARGET_RELATIONSHIP_ID);
}

/**
 * Verify the ticket belongs to the target company (Relationship ID "0-466-515").
 * Fetches the company using `ticket.company_id`.
 */
async function isTargetCompany(ticket) {
  if (!ticket || !ticket.company_id) return false;

  const company = await getCompanyDetails(ticket.company_id);
  return companyMatchesRelationshipId(company);
}

/**
 * Normalize a Freshdesk tag value (array, comma-separated string, or null) to an array.
 */
function normalizeTags(tags) {
  if (!tags) return [];
  if (Array.isArray(tags)) return tags.map((t) => String(t).trim());
  return String(tags)
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
}

/**
 * Check whether the escalation tag was newly added in this update.
 * If `previousTags` is not available, falls back to checking it's present
 * in the current tags (use this when the automation rule already fires
 * only on "tag added" for this specific tag).
 */
function hasEscalationTag(previousTags, currentTags) {
  const current = normalizeTags(currentTags);
  if (!current.includes(ESCALATION_TAG)) return false;

  if (previousTags === undefined || previousTags === null) {
    return true;
  }

  const previous = normalizeTags(previousTags);
  return !previous.includes(ESCALATION_TAG);
}

module.exports = {
  isTargetCompany,
  hasEscalationTag,
  TARGET_RELATIONSHIP_ID,
  ESCALATION_TAG,
};
