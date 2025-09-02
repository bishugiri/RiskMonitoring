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


def format_daily_summary_html(summary: dict, top_negative: list[dict]) -> str:
    """Build a simple HTML summary body for daily report."""
    total = summary.get("total_articles", 0)
    sent_score = summary.get("sentiment_score", 0)
    risk_score = summary.get("risk_score", 0)

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


def format_detailed_email_html(summary: dict, top_negative: list[dict], all_articles: list[dict]) -> str:
    """Build a detailed HTML email with comprehensive analysis and insights."""
    total = summary.get("total_articles", 0)
    sent_score = summary.get("sentiment_score", 0)
    risk_score = summary.get("risk_score", 0)
    
    # Calculate additional metrics
    sentiment_distribution = {}
    entity_distribution = {}
    source_distribution = {}
    
    for article in all_articles:
        # Sentiment distribution
        sentiment = article.get("sentiment_analysis", {}).get("category", "Unknown")
        sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # Entity distribution
        entity = article.get("entity", "Unknown")
        entity_distribution[entity] = entity_distribution.get(entity, 0) + 1
        
        # Source distribution
        source = extract_clean_source(article)
        source_distribution[source] = source_distribution.get(source, 0) + 1

    # Create detailed article rows with insights
    detailed_rows = []
    for i, art in enumerate(top_negative[:10], 1):
        s = art.get("sentiment_analysis", {})
        score = s.get("score", 0)
        cat = s.get("category", "Neutral")
        title = art.get("title", "Untitled")
        source = extract_clean_source(art)
        date = art.get("publish_date", "") or art.get("date", "")
        url = art.get("url", "#")
        entity = art.get("entity", "Unknown")
        summary_text = art.get("summary", "")[:200] + "..." if len(art.get("summary", "")) > 200 else art.get("summary", "")
        
        # Format date
        if date:
            try:
                if "," in date:
                    date = date.split(",")[0]
                elif " " in date:
                    date = date.split(" ")[0]
            except:
                date = date[:10] if len(date) > 10 else date
        else:
            date = ""
        
        # Add justification if available
        justification = s.get("justification", "")
        if justification:
            insight = f"<br><small><i>Insight: {justification}</i></small>"
        else:
            insight = ""
        
        detailed_rows.append(f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{entity}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{source}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{cat}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{score:.2f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                <a href='{url}' style="color: #0066cc; text-decoration: none;">{title}</a>
                <br><small>{summary_text}</small>
                {insight}
            </td>
        </tr>
        """)

    # Create distribution tables
    sentiment_table = create_distribution_table("Sentiment Distribution", sentiment_distribution)
    entity_table = create_distribution_table("Entity Coverage", entity_distribution)
    source_table = create_distribution_table("Source Distribution", source_distribution)

    detailed_table = (
        "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:14px;'>"
        "<thead><tr style='background-color:#f8f9fa;'>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Rank</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Date</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Entity</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Source</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Sentiment</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Score</th>"
        "<th style='padding: 8px; border: 1px solid #ddd;'>Title & Summary</th>"
        "</tr></thead>"
        f"<tbody>{''.join(detailed_rows)}</tbody>"
        "</table>"
    )

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial; max-width: 1200px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px;">📊 Daily Risk Monitor Report</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Comprehensive Financial Risk Analysis</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #333;">📈 Executive Summary</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Total Articles</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #333;">{total}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Avg Sentiment</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: {get_sentiment_color(sent_score)};">{sent_score:.3f}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Avg Risk Score</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: {get_risk_color(risk_score)};">{risk_score:.3f}</p>
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 20px;">
            <h2 style="color: #333;">📊 Data Distribution</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                {sentiment_table}
                {entity_table}
                {source_table}
            </div>
        </div>
        
        <div style="margin-bottom: 20px;">
            <h2 style="color: #333;">🚨 Top 10 Most Negative Articles</h2>
            <p style="color: #666; margin-bottom: 15px;">Articles with the lowest sentiment scores requiring immediate attention:</p>
            {detailed_table}
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 20px;">
            <p style="margin: 0; font-size: 14px; color: #666;">
                <strong>Generated by:</strong> Risk Monitor Automation System<br>
                <strong>Analysis Method:</strong> Dual Sentiment Analysis (LLM + Lexicon)<br>
                <strong>Data Source:</strong> SerpAPI News Collection<br>
                <strong>Storage:</strong> Pinecone Vector Database
            </p>
        </div>
    </div>
    """
    return html


def create_distribution_table(title: str, data: dict) -> str:
    """Create a distribution table for email."""
    rows = []
    for key, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        rows.append(f"<tr><td style='padding: 6px; border: 1px solid #ddd;'>{key}</td><td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{value}</td></tr>")
    
    return f"""
    <div style="background: white; border: 1px solid #ddd; border-radius: 6px; overflow: hidden;">
        <h3 style="margin: 0; padding: 10px; background: #f8f9fa; border-bottom: 1px solid #ddd; font-size: 16px;">{title}</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Category</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Count</th>
                </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
    """


def get_sentiment_color(score: float) -> str:
    """Get color based on sentiment score."""
    if score > 0.1:
        return "#28a745"  # Green for positive
    elif score < -0.1:
        return "#dc3545"  # Red for negative
    else:
        return "#6c757d"  # Gray for neutral


def get_risk_color(score: float) -> str:
    """Get color based on risk score."""
    if score > 0.7:
        return "#dc3545"  # Red for high risk
    elif score > 0.4:
        return "#ffc107"  # Yellow for medium risk
    else:
        return "#28a745"  # Green for low risk


