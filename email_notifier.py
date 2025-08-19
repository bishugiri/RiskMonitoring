#!/usr/bin/env python3
"""
Email Notification System for Risk Monitoring Tool
Sends article summaries with sentiment scores to specified email addresses
"""

import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import logging

class EmailNotifier:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"  # Default to Gmail
        self.smtp_port = 587
        self.sender_email = None
        self.sender_password = None
        self.recipient_emails = []
        self.load_config()
    
    def load_config(self):
        """Load email configuration from environment variables or config file"""
        # Try to load from environment variables first
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        
        # Try to load from config file if environment variables not set
        if not self.sender_email or not self.sender_password:
            config_file = os.path.join(os.path.dirname(__file__), 'email_config.json')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.sender_email = config.get('sender_email')
                        self.sender_password = config.get('sender_password')
                        self.recipient_emails = config.get('recipient_emails', [])
                        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
                        self.smtp_port = config.get('smtp_port', 587)
                except Exception as e:
                    logging.error(f"Error loading email config: {e}")
        
        # Load recipient emails from environment if not in config
        if not self.recipient_emails:
            env_recipients = os.getenv('EMAIL_RECIPIENTS')
            if env_recipients:
                self.recipient_emails = [email.strip() for email in env_recipients.split(',')]
    
    def create_article_summary_email(self, articles: List[Dict], search_metadata: Dict) -> str:
        """Create HTML email content with article summaries"""
        
        # Email header
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #1f77b4; color: white; padding: 20px; border-radius: 10px; }}
                .summary-stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .article-card {{ background-color: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .article-title {{ font-size: 18px; font-weight: bold; color: #1f77b4; margin-bottom: 10px; }}
                .article-source {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
                .article-date {{ color: #888; font-size: 12px; margin-bottom: 10px; }}
                .sentiment {{ padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 12px; }}
                .sentiment-positive {{ background-color: #d4edda; color: #155724; }}
                .sentiment-negative {{ background-color: #f8d7da; color: #721c24; }}
                .sentiment-neutral {{ background-color: #e2e3e5; color: #383d41; }}
                .counterparty-tag {{ background-color: #e3f2fd; color: #1976d2; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px; }}
                .keywords {{ margin-top: 10px; }}
                .keyword-tag {{ background-color: #fff3cd; color: #856404; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-right: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 Risk Monitor - News Summary</h1>
                <p>Daily news collection completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Summary statistics
        total_articles = len(articles)
        counterparties = list(set([article.get('counterparty', 'Unknown') for article in articles]))
        sentiment_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
        
        for article in articles:
            sentiment = article.get('sentiment_analysis', {})
            category = sentiment.get('category', 'Neutral')
            sentiment_counts[category] = sentiment_counts.get(category, 0) + 1
        
        html_content += f"""
            <div class="summary-stats">
                <h2>📊 Collection Summary</h2>
                <p><strong>Total Articles:</strong> {total_articles}</p>
                <p><strong>Counterparties Monitored:</strong> {', '.join(counterparties)}</p>
                <p><strong>Search Mode:</strong> {search_metadata.get('search_mode', 'N/A')}</p>
                <p><strong>Keywords Applied:</strong> {search_metadata.get('keywords', 'N/A').replace(chr(10), ', ')}</p>
                <p><strong>Sentiment Distribution:</strong> Positive: {sentiment_counts['Positive']}, Negative: {sentiment_counts['Negative']}, Neutral: {sentiment_counts['Neutral']}</p>
            </div>
        """
        
        # Articles list
        html_content += "<h2>📋 Article Summaries</h2>"
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No Title')
            source = article.get('source', 'Unknown Source')
            date = article.get('publish_date', 'Unknown Date')
            counterparty = article.get('counterparty', 'Unknown')
            
            # Sentiment info
            sentiment = article.get('sentiment_analysis', {})
            sentiment_category = sentiment.get('category', 'Neutral')
            sentiment_score = sentiment.get('score', 0.0)
            
            # Sentiment color class
            if sentiment_category == 'Positive':
                sentiment_class = 'sentiment-positive'
            elif sentiment_category == 'Negative':
                sentiment_class = 'sentiment-negative'
            else:
                sentiment_class = 'sentiment-neutral'
            
            # Keywords
            keywords = article.get('matched_keywords', [])
            keyword_tags = ''.join([f'<span class="keyword-tag">🔍 {kw}</span>' for kw in keywords])
            
            # Article preview (first 150 characters)
            text = article.get('text', '')
            preview = text[:150] + '...' if len(text) > 150 else text
            
            html_content += f"""
                <div class="article-card">
                    <div class="article-title">{i}. {title}</div>
                    <div class="article-source">📰 {source}</div>
                    <div class="article-date">📅 {date[:10] if date else 'Unknown'}</div>
                    <div><span class="counterparty-tag">🏢 {counterparty}</span></div>
                    <div><span class="sentiment {sentiment_class}">🎭 {sentiment_category} (Score: {sentiment_score})</span></div>
                    <div style="margin: 10px 0; line-height: 1.4;">{preview}</div>
                    <div class="keywords">{keyword_tags}</div>
                </div>
            """
        
        html_content += """
            </body>
        </html>
        """
        
        return html_content
    
    def send_email(self, subject: str, html_content: str) -> bool:
        """Send email with HTML content"""
        if not self.sender_email or not self.sender_password:
            logging.error("Email credentials not configured")
            return False
        
        if not self.recipient_emails:
            logging.error("No recipient emails configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = subject
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logging.info(f"Email sent successfully to {len(self.recipient_emails)} recipients")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False
    
    def send_news_summary(self, articles: List[Dict], search_metadata: Dict) -> bool:
        """Send news summary email"""
        if not articles:
            logging.warning("No articles to send in summary")
            return False
        
        # Create email content
        html_content = self.create_article_summary_email(articles, search_metadata)
        
        # Create subject line
        total_articles = len(articles)
        counterparties = list(set([article.get('counterparty', 'Unknown') for article in articles]))
        subject = f"Risk Monitor: {total_articles} Articles for {', '.join(counterparties[:2])}{'...' if len(counterparties) > 2 else ''}"
        
        # Send email
        return self.send_email(subject, html_content)

def create_email_config_template():
    """Create a template email configuration file"""
    config_template = {
        "sender_email": "your_email@gmail.com",
        "sender_password": "your_app_password",
        "recipient_emails": [
            "recipient1@example.com",
            "recipient2@example.com"
        ],
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }
    
    config_file = os.path.join(os.path.dirname(__file__), 'email_config.json')
    with open(config_file, 'w') as f:
        json.dump(config_template, f, indent=2)
    
    print(f"Email configuration template created: {config_file}")
    print("Please update with your actual email credentials and recipient addresses")

if __name__ == "__main__":
    # Create configuration template if running directly
    create_email_config_template()
