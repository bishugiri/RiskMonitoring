"""
Email utility for Risk Monitor.
Sends HTML emails via SMTP.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
import logging

from risk_monitor.config.settings import Config


logger = logging.getLogger(__name__)


def send_html_email(
    subject: str,
    html_body: str,
    recipients: List[str] | None = None,
    sender: str | None = None,
) -> None:
    """Send an HTML email using SMTP settings from Config/Secrets.

    Args:
        subject: Email subject (will be prefixed with configured prefix)
        html_body: HTML content
        recipients: List of recipient emails; if None, uses configured recipients
        sender: From address; if None, uses configured from
    """
    smtp_host = Config.get_smtp_host()
    smtp_port = Config.get_smtp_port()
    smtp_user = Config.get_smtp_user()
    smtp_password = Config.get_smtp_password()
    sender_addr = sender or Config.get_email_from()
    to_addrs = recipients or Config.get_email_recipients()
    subject_prefix = Config.get_email_subject_prefix()

    if not to_addrs:
        logger.warning("No email recipients configured; skipping email send")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{subject_prefix} | {subject}"
    msg["From"] = sender_addr
    msg["To"] = ", ".join(to_addrs)

    part_html = MIMEText(html_body, "html")
    msg.attach(part_html)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            # Use TLS if port 587 or STARTTLS supported
            try:
                server.starttls()
            except Exception:
                pass

            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)

            server.sendmail(sender_addr, to_addrs, msg.as_string())
            logger.info("Sent email to %s", to_addrs)
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        raise


def format_daily_summary_html(summary: dict, top_negative: list[dict]) -> str:
    """Build a simple HTML summary body for daily report."""
    total = summary.get("total_articles", 0)
    sent_score = summary.get("sentiment_score", 0)
    risk_score = summary.get("risk_score", 0)

    def extract_clean_source(article):
        """Extract clean source name from article data."""
        # Try to get clean source from various fields
        url = article.get("url", "")
        if url:
            # Extract domain from URL
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                return domain
            except:
                pass
        
        # Fall back to source name if available
        source = article.get("source")
        if isinstance(source, dict) and "name" in source:
            return source["name"]
        elif isinstance(source, str):
            return source
        
        return "Unknown"

    rows = []
    for i, art in enumerate(top_negative[:10], 1):
        s = art.get("sentiment_analysis", {})
        score = s.get("score", 0)
        cat = s.get("category", "Neutral")
        title = art.get("title", "Untitled")
        source = extract_clean_source(art)
        date = art.get("publish_date", "") or art.get("date", "")
        url = art.get("url", "#")
        
        # Format date
        if date:
            try:
                # Try to extract just the date part
                if "," in date:
                    date = date.split(",")[0]
                elif " " in date:
                    date = date.split(" ")[0]
            except:
                date = date[:10] if len(date) > 10 else date
        else:
            date = ""
        
        rows.append(
            f"<tr><td>{i}</td><td>{date}</td><td>{source}</td><td>{cat}</td><td>{score:.2f}</td><td><a href='{url}'>{title}</a></td></tr>"
        )

    table = (
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>"
        "<thead><tr><th>Rank</th><th>Date</th><th>Source</th><th>Sentiment</th><th>Score</th><th>Title</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial;">
      <h2>Daily Risk Monitor Summary</h2>
      <p><b>Total articles:</b> {total} &nbsp; | &nbsp; <b>Avg Sentiment:</b> {sent_score:.3f} &nbsp; | &nbsp; <b>Avg Risk:</b> {risk_score:.3f}</p>
      <h3>Top 10 Most Negative Articles</h3>
      {table}
    </div>
    """
    return html


