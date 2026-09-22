# Shazmame Ticket Bot

Freshdesk automation: adds a private "escalate if unresolved" note on new tickets for a
specific company, and when that ticket is later tagged `escalate-unresolved`, generates a
summary locally with `node-summarizer` (no external AI API) and emails it to the customer
via Freshdesk.

## How it works

1. Two Freshdesk Automator rules call this webhook (`POST /api/webhook`):
   - **Ticket Created** rule → sends `{ "event": "ticket_created", "ticket_id": "{{ticket.id}}" }`
   - **Tag Added** rule (condition: tag `escalate-unresolved` added) → sends
     `{ "event": "ticket_updated", "ticket_id": "{{ticket.id}}", "tags": "{{ticket.tags}}" }`
2. On `ticket_created`, the bot fetches the ticket's company and checks the company's
   Relationship ID custom field against `TARGET_RELATIONSHIP_ID`. If it matches, it adds a
   private note asking the agent to tag the ticket `escalate-unresolved` if unresolved.
3. On `ticket_updated`, the bot confirms the escalation tag was newly added and the company
   matches, then fetches full ticket + conversation history, runs it through `node-summarizer`
   (extractive, rank-based summary — no external AI API), and sends the result to the customer
   through Freshdesk's reply endpoint.

## Freshdesk setup (Admin → Automations → Ticket Creation / Ticket Updates)

**Rule A — Ticket Created**
- Condition: Company is the target account (or leave unconditional; the bot re-verifies)
- Action: Trigger Webhook → POST → `https://<your-vercel-app>.vercel.app/api/webhook?secret=<WEBHOOK_SECRET>`
- Content type: JSON
- Body: `{ "event": "ticket_created", "ticket_id": "{{ticket.id}}" }`

**Rule B — Ticket Updates (tag added)**
- Condition: Tag is added → `escalate-unresolved`
- Action: Trigger Webhook → POST → same URL
- Body: `{ "event": "ticket_updated", "ticket_id": "{{ticket.id}}", "tags": "{{ticket.tags}}" }`

The Relationship ID is read from the **Company's** custom field. Set
`FRESHDESK_RELATIONSHIP_FIELD_KEY` in your env to match the actual custom field key in your
Freshdesk account (default: `relationship_id`).

## Environment variables

See [.env.example](.env.example). Required: `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`.
Optional: `TARGET_RELATIONSHIP_ID`, `FRESHDESK_RELATIONSHIP_FIELD_KEY`, `ESCALATION_TAG`,
`SUMMARY_SENTENCE_COUNT`, `WEBHOOK_SECRET`.

## Deploy

```bash
npm install
vercel deploy --prod
```

Set the environment variables above in the Vercel project settings before deploying.

## Local testing

```bash
npm install
vercel dev
curl -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"ticket_created","ticket_id":123}'
```
