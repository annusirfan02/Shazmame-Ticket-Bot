import os
import re

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

SENTENCE_COUNT = int(os.environ.get("SUMMARY_SENTENCE_COUNT", "5"))


def _strip_html(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", text)).strip()


def _build_source_text(ticket_data):
    parts = []

    subject = ticket_data.get("subject")
    if subject:
        parts.append(subject)

    description = _strip_html(ticket_data.get("description_text") or ticket_data.get("description"))
    if description:
        parts.append(description)

    for conversation in ticket_data.get("conversations") or []:
        body = _strip_html(conversation.get("body_text") or conversation.get("body"))
        if body:
            parts.append(body)

    return ". ".join(parts)


def generate_summary(ticket_data):
    """
    Generate a summary of a ticket (subject + description + full conversation
    history) using the sumy LsaSummarizer — no AI API involved.
    Falls back to the raw description if summarization fails for any reason.
    """
    source_text = _build_source_text(ticket_data)

    try:
        parser = PlaintextParser.from_string(source_text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        sentences = summarizer(parser.document, SENTENCE_COUNT)
        summary_text = " ".join(str(sentence) for sentence in sentences).strip()
        if not summary_text:
            raise ValueError("sumy produced an empty summary")
    except Exception:
        summary_text = _strip_html(
            ticket_data.get("description_text") or ticket_data.get("description")
        ) or "No summary could be generated for this ticket."

    return summary_text
