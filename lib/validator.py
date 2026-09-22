import os

from lib.freshdesk import get_company_details

TARGET_RELATIONSHIP_ID = os.environ.get("TARGET_RELATIONSHIP_ID", "0-466-515")
RELATIONSHIP_FIELD_KEY = os.environ.get("FRESHDESK_RELATIONSHIP_FIELD_KEY", "cf_relationship_id")
ESCALATION_TAG = os.environ.get("ESCALATION_TAG", "escalate-unresolved")


def is_target_company(ticket):
    """Verify the ticket belongs to the target company (Relationship ID match)."""
    company_id = ticket.get("company_id")
    if not company_id:
        return False

    company = get_company_details(company_id)
    custom_fields = company.get("custom_fields") or {}

    if custom_fields.get(RELATIONSHIP_FIELD_KEY) == TARGET_RELATIONSHIP_ID:
        return True

    # Fallback: some accounts name the field differently; scan all values.
    return TARGET_RELATIONSHIP_ID in custom_fields.values()


def has_escalation_tag(previous_tags, current_tags):
    """Return True only if the escalation tag is newly added in this update."""
    previous_tags = previous_tags or []
    current_tags = current_tags or []

    return ESCALATION_TAG in current_tags and ESCALATION_TAG not in previous_tags
