#!/usr/bin/env python3
"""
Test script for email notifications
Run this to test if email configuration is working
"""

import json
import os
from email_notifier import EmailNotifier

def test_email_config():
    """Test email configuration"""
    print("🔍 Testing Email Configuration...")
    
    # Check if config file exists
    config_file = "email_config.json"
    if os.path.exists(config_file):
        print(f"✅ Config file found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"📧 Sender: {config.get('sender_email', 'Not set')}")
            print(f"🔑 Password: {'*' * len(config.get('sender_password', '')) if config.get('sender_password') else 'Not set'}")
            print(f"📬 Recipients: {config.get('recipient_emails', [])}")
            print(f"🌐 SMTP Server: {config.get('smtp_server', 'Not set')}")
            print(f"🔌 Port: {config.get('smtp_port', 'Not set')}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Error reading config file: {e}")
            return False
    else:
        print(f"❌ Config file not found: {config_file}")
        return False
    
    # Test email notifier
    try:
        print("\n🧪 Testing Email Notifier...")
        notifier = EmailNotifier()
        
        if notifier.sender_email:
            print(f"✅ Sender email loaded: {notifier.sender_email}")
        else:
            print("❌ Sender email not configured")
            return False
        
        if notifier.recipient_emails:
            print(f"✅ Recipients loaded: {len(notifier.recipient_emails)} addresses")
        else:
            print("❌ No recipient emails configured")
            return False
        
        # Test sending a simple email
        print("\n📤 Testing email sending...")
        test_subject = "Risk Monitor - Email Test"
        test_content = """
        <html>
        <body>
            <h1>🧪 Email Test Successful!</h1>
            <p>This is a test email from your Risk Monitor tool.</p>
            <p>If you received this, your email configuration is working correctly!</p>
            <p><strong>Time:</strong> {}</p>
        </body>
        </html>
        """.format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        success = notifier.send_email(test_subject, test_content)
        
        if success:
            print("✅ Test email sent successfully!")
            print("📧 Check your inbox for the test email")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email notifier: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Risk Monitor - Email Test")
    print("=" * 40)
    
    success = test_email_config()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Email test completed successfully!")
        print("Your email notifications are ready to use!")
    else:
        print("⚠️ Email test failed!")
        print("Please check your configuration and try again.")
        print("\n📖 See EMAIL_SETUP_GUIDE.md for detailed setup instructions.")
