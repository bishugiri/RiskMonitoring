# 📧 Email Notification Setup Guide

This guide will help you set up email notifications that automatically send article summaries every time you collect news articles.

## 🎯 **What You'll Get:**

Every time you click "Collect Articles", you'll receive a beautiful HTML email containing:
- 📊 **Collection Summary**: Total articles, counterparties, sentiment distribution
- 📋 **Article Summaries**: Title, source, date, counterparty, sentiment score
- 🎭 **Sentiment Analysis**: Color-coded sentiment indicators
- 🔍 **Keyword Matches**: Which keywords were found in each article
- 🏢 **Counterparty Tags**: Easy identification of which company each article relates to

## 🚀 **Quick Setup (3 Steps)**

### **Step 1: Edit Email Configuration**
Open `email_config.json` and update with your details:

```json
{
  "sender_email": "your_email@gmail.com",
  "sender_password": "your_gmail_app_password",
  "recipient_emails": [
    "your_email@company.com",
    "colleague@company.com",
    "manager@company.com"
  ],
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

### **Step 2: Get Gmail App Password**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. **Security** → **2-Step Verification** (enable if not already)
3. **Security** → **App passwords**
4. Generate app password for "Mail"
5. Copy the 16-character password
6. Paste it in `email_config.json` as `sender_password`

### **Step 3: Test the Setup**
1. Restart your Streamlit app
2. Go to sidebar → **📧 Email Notifications**
3. Click **📧 Test Email** to verify everything works

## 🔧 **Alternative Setup: Environment Variables**

Instead of editing the config file, you can set environment variables:

```bash
# Windows PowerShell
$env:EMAIL_SENDER="your_email@gmail.com"
$env:EMAIL_PASSWORD="your_app_password"
$env:EMAIL_RECIPIENTS="email1@example.com,email2@example.com"

# Windows Command Prompt
set EMAIL_SENDER=your_email@gmail.com
set EMAIL_PASSWORD=your_app_password
set EMAIL_RECIPIENTS=email1@example.com,email2@example.com
```

## 📧 **Email Providers Supported**

### **Gmail (Recommended)**
- **SMTP Server**: `smtp.gmail.com`
- **Port**: `587`
- **Requires**: App Password (not regular password)

### **Outlook/Hotmail**
- **SMTP Server**: `smtp-mail.outlook.com`
- **Port**: `587`
- **Requires**: App Password

### **Yahoo**
- **SMTP Server**: `smtp.mail.yahoo.com`
- **Port**: `587`
- **Requires**: App Password

### **Custom SMTP Server**
- Update `smtp_server` and `smtp_port` in config
- May require different authentication method

## 🎨 **Email Template Features**

### **Professional Design**
- **Responsive HTML**: Works on all devices
- **Color-coded sentiment**: Green (positive), Red (negative), Gray (neutral)
- **Company tags**: Easy identification of counterparties
- **Keyword highlights**: Shows which search terms matched

### **Content Summary**
- **Collection statistics**: Total articles, sentiment distribution
- **Article previews**: First 150 characters of each article
- **Source attribution**: News source and publication date
- **Sentiment scores**: Numerical and categorical sentiment analysis

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **"Authentication failed"**
   - Use App Password, not regular password
   - Enable 2-Factor Authentication first

2. **"Connection refused"**
   - Check firewall settings
   - Verify SMTP server and port
   - Try different port (465 for SSL)

3. **"Email not configured"**
   - Check `email_config.json` syntax
   - Verify file path is correct
   - Restart Streamlit app after changes

4. **"No recipients"**
   - Add at least one email address
   - Check JSON format (commas, quotes)

### **Testing Steps:**

1. **Verify configuration**:
   ```python
   from email_notifier import EmailNotifier
   notifier = EmailNotifier()
   print(f"Sender: {notifier.sender_email}")
   print(f"Recipients: {notifier.recipient_emails}")
   ```

2. **Test connection**:
   ```python
   # This will attempt to connect to SMTP server
   notifier.send_email("Test", "<h1>Test Email</h1>")
   ```

3. **Check logs**: Look for email-related messages in console output

## 📱 **Mobile & Desktop Compatibility**

- **HTML emails** work on all modern email clients
- **Responsive design** adapts to mobile screens
- **Professional appearance** in Outlook, Gmail, Apple Mail
- **Accessibility features** for screen readers

## 🔒 **Security Best Practices**

1. **Use App Passwords**: Never use your main Gmail password
2. **Restrict access**: Only share with trusted team members
3. **Regular rotation**: Change app passwords periodically
4. **Monitor usage**: Check Gmail security settings regularly

## 📊 **Customization Options**

### **Modify Email Template**
Edit `email_notifier.py` to customize:
- Email styling and colors
- Content layout and sections
- Sentiment thresholds
- Article preview length

### **Add More Recipients**
Simply add more email addresses to the `recipient_emails` list:
```json
"recipient_emails": [
  "analyst1@company.com",
  "analyst2@company.com",
  "risk_manager@company.com",
  "compliance@company.com"
]
```

### **Conditional Emails**
Modify the code to send emails only when:
- High-risk articles are found
- Negative sentiment exceeds threshold
- Specific counterparties are mentioned
- Articles match critical keywords

## 🎉 **Success Indicators**

When working correctly, you should see:
1. ✅ **"Email configured"** in sidebar
2. 📧 **"Email notification sent successfully!"** after collection
3. **Beautiful HTML emails** in your inbox
4. **Professional summaries** with all article details
5. **Real-time notifications** every time you collect articles

## 🆘 **Need Help?**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Gmail App Password setup
3. Test with a simple email first
4. Check Streamlit console for error messages
5. Verify JSON configuration syntax

---

**Happy monitoring! 📰📧**
