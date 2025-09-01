"""
Configuration settings for the Risk Monitor application.
"""

import os
import datetime
import pytz
from pathlib import Path
from dotenv import load_dotenv

# Try to import streamlit for secrets support
try:
    import streamlit as st
except ImportError:
    st = None

# Load environment variables
load_dotenv()

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()


class Config:
    """Configuration class for the risk monitoring tool"""
    
    # SerpAPI Configuration
    SERPAPI_BASE_URL = "https://serpapi.com/search"
    
    # News Search Configuration
    SEARCH_QUERY = "top news for finance"
    NUM_ARTICLES = 10
    
    # Counterparty Monitoring Configuration
    DEFAULT_COUNTERPARTIES = [
        "Apple Inc",
        "Microsoft Corporation", 
        "Goldman Sachs",
        "JPMorgan Chase",
        "Bank of America"
    ]
    
    # Keyword Filtering Configuration
    DEFAULT_KEYWORDS = [
        "risk",
        "financial",
        "market",
        "crisis",
        "volatility"
    ]
    
    # Search Configuration
    ARTICLES_PER_COUNTERPARTY = 5
    SEARCH_DELAY = 2  # seconds between searches
    
    # Output Configuration
    OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
    LOG_DIR = os.path.join(ROOT_DIR, "logs")
    LOG_FILE = os.path.join(LOG_DIR, "risk_monitor.log")
    
    # Request Configuration
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Scheduler Configuration
    DEFAULT_SCHEDULER_TIME = "08:00"  # 8:00 AM ET
    DEFAULT_SCHEDULER_TIMEZONE = "US/Eastern"
    SCHEDULER_CONFIG_FILE = os.path.join(ROOT_DIR, "scheduler_config.json")
    
    # Pinecone Configuration
    PINECONE_INDEX_NAME = "sentiment-db"
    PINECONE_ENVIRONMENT = "us-east-1-aws"
    
    # Email defaults (can be overridden by env/secrets or scheduler_config)
    DEFAULT_EMAIL_FROM = "risk-monitor@localhost"
    DEFAULT_EMAIL_SUBJECT_PREFIX = "Risk Monitor"
    
    @staticmethod
    def get_serpapi_key():
        """Get SerpAPI key from environment or Streamlit secrets"""
        try:
            return st.secrets["SERPAPI_KEY"]
        except Exception:
            return os.getenv("SERPAPI_KEY")
    
    @staticmethod
    def get_openai_api_key():
        """Get OpenAI API key from environment or Streamlit secrets"""
        try:
            return st.secrets["OPENAI_API_KEY"]
        except Exception:
            return os.getenv("OPENAI_API_KEY")
    
    @staticmethod
    def get_pinecone_api_key():
        """Get Pinecone API key from environment or Streamlit secrets"""
        try:
            return st.secrets["PINECONE_API_KEY"]
        except Exception:
            return os.getenv("PINECONE_API_KEY")

    # Email/SMTP settings
    @staticmethod
    def get_smtp_host() -> str:
        try:
            return st.secrets["SMTP_HOST"]
        except Exception:
            return os.getenv("SMTP_HOST", "smtp.gmail.com")

    @staticmethod
    def get_smtp_port() -> int:
        try:
            return int(st.secrets["SMTP_PORT"])
        except Exception:
            return int(os.getenv("SMTP_PORT", "587"))

    @staticmethod
    def get_smtp_user() -> str | None:
        try:
            return st.secrets["SMTP_USER"]
        except Exception:
            return os.getenv("SMTP_USER")

    @staticmethod
    def get_smtp_password() -> str | None:
        try:
            return st.secrets["SMTP_PASSWORD"]
        except Exception:
            return os.getenv("SMTP_PASSWORD")

    @staticmethod
    def get_email_from() -> str:
        try:
            return st.secrets["EMAIL_FROM"]
        except Exception:
            return os.getenv("EMAIL_FROM", Config.DEFAULT_EMAIL_FROM)

    @staticmethod
    def get_email_recipients() -> list[str]:
        # Comma or semicolon separated list
        recipients = None
        try:
            recipients = st.secrets["EMAIL_RECIPIENTS"]
        except Exception:
            recipients = os.getenv("EMAIL_RECIPIENTS")
        if isinstance(recipients, list):
            return recipients
        if isinstance(recipients, str) and recipients.strip():
            parts = [p.strip() for p in re.split(r"[,;]", recipients) if p.strip()]  # type: ignore[name-defined]
            return parts
        return []

    @staticmethod
    def get_email_subject_prefix() -> str:
        try:
            return st.secrets["EMAIL_SUBJECT_PREFIX"]
        except Exception:
            return os.getenv("EMAIL_SUBJECT_PREFIX", Config.DEFAULT_EMAIL_SUBJECT_PREFIX)

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        serpapi_key = cls.get_serpapi_key()
        if not serpapi_key:
            raise ValueError("SERPAPI_KEY must be set as a Streamlit secret or environment variable")
        
        # Create output directory if it doesn't exist
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        
    @staticmethod
    def get_current_time_in_timezone(timezone_str="US/Eastern"):
        """Get current time in specified timezone"""
        try:
            tz = pytz.timezone(timezone_str)
            return datetime.datetime.now(tz)
        except Exception:
            # Default to UTC if timezone is invalid
            return datetime.datetime.now(pytz.UTC)
