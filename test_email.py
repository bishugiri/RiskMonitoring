#!/usr/bin/env python3
"""
Test script to verify email functionality
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from risk_monitor.utils.emailer import send_html_email
from risk_monitor.config.settings import Config

def test_email():
    """Test email sending functionality"""
    print("Testing email configuration...")
    
    # Test configuration
    print(f"SMTP Host: {Config.get_smtp_host()}")
    print(f"SMTP Port: {Config.get_smtp_port()}")
    print(f"SMTP User: {Config.get_smtp_user()}")
    print(f"Email From: {Config.get_email_from()}")
    print(f"Email Recipients: {Config.get_email_recipients()}")
    
    # Test email
    try:
        send_html_email(
            subject="Test Email - Risk Monitor",
            html_body="""
            <h2>Test Email</h2>
            <p>This is a test email from your Risk Monitor system.</p>
            <p>If you receive this, the email configuration is working correctly!</p>
            """,
            recipients=["be2020se@gces.edu.np"]
        )
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

if __name__ == "__main__":
    test_email()
