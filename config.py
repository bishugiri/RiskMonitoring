import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the risk monitoring tool"""
    
    # SerpAPI Configuration
    SERPAPI_KEY = os.getenv('SERPAPI_KEY')
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
    OUTPUT_DIR = "output"
    LOG_FILE = "risk_monitor.log"
    
    # Request Configuration
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.SERPAPI_KEY:
            raise ValueError("SERPAPI_KEY environment variable is required")
        
        # Create output directory if it doesn't exist
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True) 