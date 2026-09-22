import os
import requests

FRESHDESK_DOMAIN = os.environ.get("FRESHDESK_DOMAIN")
FRESHDESK_API_KEY = os.environ.get("FRESHDESK_API_KEY")


def _base_url():
    if not FRESHDESK_DOMAIN or not FRESHDESK_API_KEY:
        raise RuntimeError("FRESHDESK_DOMAIN and FRESHDESK_API_KEY must be set")
    return f"https://{FRESHDESK_DOMAIN}/api/v2"


def _auth():
    return (FRESHDESK_API_KEY, "X")


def get_ticket_details(ticket_id):
    """Fetch a ticket with its full conversation thread and company info."""
    url = f"{_base_url()}/tickets/{ticket_id}"
    response = requests.get(
        url,
        auth=_auth(),
        params={"include": "conversations,company,requester"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def get_company_details(company_id):
    """Fetch company details (used to verify the Relationship ID custom field)."""
    url = f"{_base_url()}/companies/{company_id}"
    response = requests.get(url, auth=_auth(), timeout=20)
    response.raise_for_status()
    return response.json()


def add_private_note(ticket_id, content):
    """Add a private note to a ticket."""
    url = f"{_base_url()}/tickets/{ticket_id}/notes"
    response = requests.post(
        url,
        auth=_auth(),
        json={"body": content, "private": True},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def send_email_reply(ticket_id, summary_text, client_name="Customer"):
    """Send a formatted summary email to the client through Freshdesk's reply endpoint."""
    url = f"{_base_url()}/tickets/{ticket_id}/reply"
    response = requests.post(
        url,
        auth=_auth(),
        json={"body": summary_text},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
