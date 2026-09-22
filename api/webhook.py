import os
import sys
from datetime import datetime, timezone

# Ensure the project root (parent of this api/ directory) is on sys.path so
# `lib` resolves whether this runs via `python api/webhook.py`, `python -m
# api.webhook`, or Vercel's Python runtime.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify

from lib.freshdesk import get_ticket_details, add_private_note, send_email_reply
from lib.validator import is_target_company, has_escalation_tag
from lib.summarizer import generate_summary

app = Flask(__name__)

NEW_TICKET_NOTE = (
    "This ticket belongs to a priority agency. If this ticket is not resolved, "
    "please add the tag: escalate-unresolved to trigger the escalation process."
)


def log(ticket_id, action, description):
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"{timestamp} {ticket_id} {action} {description}", file=sys.stdout)


def build_summary_email(ticket, summary_text):
    client_name = (ticket.get("requester") or {}).get("name") or "Customer"
    created_at = ticket.get("created_at", "N/A")

    return (
        f"Dear {client_name},\n\n"
        "Please find below the summary of your support ticket that requires attention.\n\n"
        f"Ticket ID: {ticket.get('id')}\n"
        f"Subject: {ticket.get('subject')}\n"
        f"Status: {ticket.get('status')}\n"
        f"Priority: {ticket.get('priority')}\n"
        f"Created: {created_at}\n\n"
        "Issue Summary:\n"
        f"{summary_text}\n\n"
        "Please contact us if you need further assistance.\n\n"
        "Best regards,\n"
        "Support Team"
    )


@app.route("/api/webhook", methods=["POST"])
def webhook():
    # Always resolve with 200 (even on internal errors) so Freshdesk doesn't
    # treat this as a failed delivery and retry.
    payload = request.get_json(silent=True) or {}
    event = payload.get("event")
    ticket_id = payload.get("ticket_id")

    if not ticket_id:
        return jsonify({"ok": False, "reason": "missing ticket_id"}), 200

    try:
        if event == "ticket_created":
            handled = handle_ticket_created(ticket_id)
            return jsonify({"ok": True, "handled": "ticket_created" if handled else "ignored"}), 200

        if event == "ticket_updated":
            handled = handle_ticket_updated(ticket_id, payload)
            return jsonify({"ok": True, "handled": "ticket_updated" if handled else "ignored"}), 200

        log(ticket_id, "ignored", f"unknown event '{event}'")
        return jsonify({"ok": True, "handled": "ignored", "reason": "unknown event"}), 200
    except Exception as exc:
        log(ticket_id, "error", str(exc))
        return jsonify({"ok": False, "error": str(exc)}), 200


def handle_ticket_created(ticket_id):
    try:
        ticket = get_ticket_details(ticket_id)
    except Exception as exc:
        log(ticket_id, "error", f"get_ticket_details failed: {exc}")
        return False

    try:
        if not is_target_company(ticket):
            log(ticket_id, "ignored", "company does not match target relationship id")
            return False
    except Exception as exc:
        log(ticket_id, "error", f"is_target_company failed: {exc}")
        return False

    try:
        add_private_note(ticket_id, NEW_TICKET_NOTE)
        log(ticket_id, "note_added", "escalation reminder note added")
        return True
    except Exception as exc:
        log(ticket_id, "error", f"add_private_note failed: {exc}")
        return False


def handle_ticket_updated(ticket_id, payload):
    previous_tags = (payload.get("previous_tags") or payload.get("tags_before") or [])
    current_tags = (payload.get("tags") or payload.get("tags_after") or [])

    if not has_escalation_tag(previous_tags, current_tags):
        log(ticket_id, "ignored", "escalation tag not newly added")
        return False

    try:
        ticket = get_ticket_details(ticket_id)
    except Exception as exc:
        log(ticket_id, "error", f"get_ticket_details failed: {exc}")
        return False

    try:
        if not is_target_company(ticket):
            log(ticket_id, "ignored", "company does not match target relationship id")
            return False
    except Exception as exc:
        log(ticket_id, "error", f"is_target_company failed: {exc}")
        return False

    try:
        summary_text = generate_summary(ticket)
    except Exception as exc:
        log(ticket_id, "error", f"generate_summary failed, using fallback: {exc}")
        summary_text = ticket.get("description_text") or ticket.get("description") or ""

    email_body = build_summary_email(ticket, summary_text)

    try:
        send_email_reply(ticket_id, email_body)
        log(ticket_id, "email_sent", "escalation summary emailed to client")
        return True
    except Exception as exc:
        log(ticket_id, "error", f"send_email_reply failed: {exc}")
        return False


# Vercel's Python runtime looks for a WSGI-compatible `app` object.
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)))
