# Shazmame Ticket Bot

Freshdesk automation: adds a private "priority agency" note on new tickets for a specific
company, and when that ticket is later tagged `escalate-unresolved`, generates a summary
locally with the `sumy` library (no external AI API) and emails it to the customer through
Freshdesk.

## How it works

1. A single Freshdesk webhook (`POST /api/webhook`) receives both **Ticket Created** and
   **Ticket Updated** events.
2. On `ticket_created`, the bot fetches the ticket's company and checks the company's
   Relationship ID custom field against `TARGET_RELATIONSHIP_ID` (`0-466-515`). If it
   matches, it adds a private note asking the agent to tag the ticket `escalate-unresolved`
   if it isn't resolved.
3. On `ticket_updated`, the bot checks whether `escalate-unresolved` was *newly* added
   (present now, absent before) and the company matches, then fetches the full ticket +
   conversation history, summarizes it with `sumy`'s `LsaSummarizer` (falling back to the
   raw description if summarization fails), and emails the summary to the client via
   Freshdesk's reply endpoint.
4. The webhook always returns `200 OK`, even on internal errors, so Freshdesk never retries
   delivery. Every action is logged as `TIMESTAMP TICKET-ID action description`.

## Freshdesk setup

1. Go to **Admin → Webhooks** (or Automations, depending on your plan) and create a webhook
   pointing at `https://<your-vercel-app>.vercel.app/api/webhook`.
2. Select events **Ticket Created** and **Ticket Updated**.
3. Make sure the payload includes at least `ticket_id`/`id`, and for updates, the tag list
   (`tags`) and previous tag list if your plan supports it (`previous_tags`) so newly-added
   detection works correctly.

The Relationship ID is read from the **Company's** custom field. Set
`FRESHDESK_RELATIONSHIP_FIELD_KEY` in your env to match the actual custom field key in your
Freshdesk account (default: `cf_relationship_id`).

## Environment variables

See [.env.example](.env.example). Required: `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`.
Optional: `TARGET_RELATIONSHIP_ID`, `FRESHDESK_RELATIONSHIP_FIELD_KEY`, `ESCALATION_TAG`,
`SUMMARY_SENTENCE_COUNT`, `WEBHOOK_SECRET`.

## Setup

```bash
git clone https://github.com/annusirfan02/Shazmame-Ticket-Bot.git
cd Shazmame-Ticket-Bot
pip install -r requirements.txt
python -m nltk.downloader punkt
cp .env.example .env   # then fill in real values
```

## Deploy

```bash
vercel --prod
```

Add the environment variables above in the Vercel dashboard (Project → Settings →
Environment Variables) before or right after deploying.

## Local testing

```bash
python api/webhook.py
curl -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"ticket_created","ticket_id":123}'
```
