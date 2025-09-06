#!/usr/bin/env python3
"""
Streamlit Web Application for Financial Risk Monitoring Tool
Provides an interactive web interface for collecting and analyzing financial news
and documents.
"""
import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any
import logging
import requests
import openai
import plotly.express as px
import plotly.graph_objects as go
import hashlib

# --- Project Structure & Configuration ---
# Ensure project structure is accessible for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import core and config modules
from risk_monitor.core.news_collector import NewsCollector
from risk_monitor.core.risk_analyzer import RiskAnalyzer
from risk_monitor.config.settings import Config

# Add caching for better performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_analysis_results(articles_hash: str, sentiment_method: str):
    """Cache analysis results to improve performance"""
    return None  # Will be populated by actual analysis

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_cached_sentiment_distribution(articles: List[Dict]):
    """Cache sentiment distribution calculation"""
    positive_count = sum(1 for a in articles if a.get('sentiment_category') == 'Positive')
    negative_count = sum(1 for a in articles if a.get('sentiment_category') == 'Negative')
    neutral_count = len(articles) - positive_count - negative_count
    
    return {
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count,
        'total': len(articles)
    }

# --- Custom CSS for a professional, elegant UI ---
def load_custom_css():
    """Loads and applies custom CSS for the Streamlit app's visual style."""
    st.markdown("""
    <style>
    /* Elegant and professional color palette */
    :root {
        --primary-blue: #005A9C; /* A rich, professional blue */
        --secondary-blue: #EBF5FF; /* Light, elegant background for highlights */
        --success-green: #2ECC71; /* Clear success indicator */
        --warning-yellow: #F1C40F; /* Standard warning color */
        --error-red: #E74C3C;     /* Distinct error color */
        --background-light: #F8F9FA; /* A very light grey background */
        --text-dark: #2C3E50;      /* Dark text for high readability */
        --card-background: #FFFFFF; /* White cards for a clean look */
        --border-color: #DEE2E6;   /* Subtle border color */
        --text-muted: #6C757D;
    }

    /* Main app styling */
    .stApp {
        background-color: var(--background-light);
        color: var(--text-dark);
        font-family: 'Open Sans', sans-serif; /* A more modern, clean font */
        padding-top: 0 !important; /* Remove excessive padding */
    }
    
    /* Streamlit header and deploy button - clean positioning */
    .stApp header {
        background-color: transparent !important;
        box-shadow: none !important;
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        left: auto !important;
        z-index: 1000 !important;
        width: auto !important;
        height: auto !important;
    }
    
    .stToolbar {
        background-color: transparent !important;
        box-shadow: none !important;
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        padding: 8px !important;
    }
    
    /* Deploy button and status widget positioning */
    [data-testid="stDeployButton"] {
        position: fixed !important;
        top: 8px !important;
        right: 8px !important;
        z-index: 1001 !important;
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
    }
    
    [data-testid="stStatusWidget"] {
        position: fixed !important;
        top: 8px !important;
        right: 60px !important;
        z-index: 1001 !important;
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
    }
    
    /* Ensure main content doesn't overlap with header */
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Header styling for the main application title */
    .main-header {
        background: linear-gradient(90deg, #005A9C 0%, #0077B6 100%);
        padding: 2.5rem 2rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
        opacity: 0; /* Start invisible for fade-in effect */
        animation: fadeIn 1s ease-in-out forwards;
    }
    .main-header h1 {
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin: 0;
        padding: 0;
        color: white;
    }
    .main-header p {
        font-size: 1.2rem !important;
        opacity: 0.9 !important;
        margin: 0.5rem 0 0 !important;
        font-weight: 300 !important;
    }

    /* Card styling with smooth hover animations */
    .stMetric, .custom-container, .article-card {
        background-color: var(--card-background);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border-color);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        margin-bottom: 1.5rem;
        opacity: 0;
        animation: fadeInUp 0.5s ease-in-out forwards;
    }
    
    /* Hide default Streamlit footer but keep header visible */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ensure Streamlit header is visible */
    header {visibility: visible !important;}
    .stApp > header {visibility: visible !important;}
    
    /* Ensure all Streamlit header elements are visible */
    [data-testid="stHeader"] {visibility: visible !important;}
    [data-testid="stToolbar"] {visibility: visible !important;}
    .stToolbar {visibility: visible !important;}
    .stHeader {visibility: visible !important;}
    
    /* Streamlit header and deploy button - clean positioning */
    .stApp header {
        background-color: transparent !important;
        box-shadow: none !important;
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        left: auto !important;
        z-index: 1000 !important;
        width: auto !important;
        height: auto !important;
    }
    
    .stToolbar {
        background-color: transparent !important;
        box-shadow: none !important;
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        padding: 8px !important;
    }
    
    /* Deploy button and status widget positioning */
    [data-testid="stDeployButton"] {
        position: fixed !important;
        top: 8px !important;
        right: 8px !important;
        z-index: 1001 !important;
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
    }
    
    [data-testid="stStatusWidget"] {
        position: fixed !important;
        top: 8px !important;
        right: 60px !important;
        z-index: 1001 !important;
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
    }
    
    /* Ensure main content doesn't overlap with header */
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* JavaScript to force deploy button positioning */
    </style>
    <script>
    // Force deploy button to stay in top right corner
    function fixDeployButtonPosition() {
        const deployButton = document.querySelector('[data-testid="stDeployButton"]');
        if (deployButton) {
            // Ultra-aggressive positioning
            deployButton.style.position = 'fixed';
            deployButton.style.top = '0';
            deployButton.style.right = '0';
            deployButton.style.zIndex = '9999';
            deployButton.style.transform = 'none';
            deployButton.style.margin = '0';
            deployButton.style.padding = '0';
            deployButton.style.left = 'auto';
            deployButton.style.bottom = 'auto';
            deployButton.style.width = 'auto';
            deployButton.style.height = 'auto';
            deployButton.style.float = 'none';
            deployButton.style.clear = 'none';
            deployButton.style.display = 'block';
            deployButton.style.visibility = 'visible';
            deployButton.style.opacity = '1';
            
            // Force remove any parent positioning that might interfere
            let parent = deployButton.parentElement;
            while (parent && parent !== document.body) {
                if (parent.style.position === 'relative' || parent.style.position === 'absolute') {
                    parent.style.position = 'static';
                }
                parent = parent.parentElement;
            }
        }
    }
    
    // Run on page load and after any dynamic content changes
    document.addEventListener('DOMContentLoaded', fixDeployButtonPosition);
    window.addEventListener('load', fixDeployButtonPosition);
    window.addEventListener('resize', fixDeployButtonPosition);
    window.addEventListener('scroll', fixDeployButtonPosition);
    
    // Use MutationObserver to watch for dynamic changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' || mutation.type === 'attributes') {
                fixDeployButtonPosition();
            }
        });
    });
    
    // Start observing with more comprehensive options
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });
    
    // Run more frequently to ensure positioning
    setInterval(fixDeployButtonPosition, 500);
    
    // Additional check when Streamlit finishes loading
    if (window.parent !== window) {
        window.parent.addEventListener('load', fixDeployButtonPosition);
    }
    </script>
    <style>
    
    /* Additional styling for Streamlit header visibility - transparent background */
    .stApp header {background-color: transparent !important; box-shadow: none !important;}
    .stToolbar {background-color: transparent !important; box-shadow: none !important;}
    .stToolbarItems {display: flex !important; align-items: center !important; justify-content: flex-end !important;}
    
    /* Final override to ensure deploy button never moves from top right */
    * [data-testid="stDeployButton"] {position: fixed !important; top: 0 !important; right: 0 !important; z-index: 1000 !important; transform: none !important; margin: 0 !important; padding: 0 !important; left: auto !important; bottom: auto !important;}
    
    /* Ultra-aggressive positioning to stick at top right corner */
    [data-testid="stDeployButton"], 
    .stApp [data-testid="stDeployButton"], 
    header [data-testid="stDeployButton"],
    .stToolbar [data-testid="stDeployButton"],
    .stToolbarItems [data-testid="stDeployButton"] {
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        z-index: 9999 !important;
        transform: none !important;
        margin: 0 !important;
        padding: 0 !important;
        left: auto !important;
        bottom: auto !important;
        width: auto !important;
        height: auto !important;
        float: none !important;
        clear: none !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Prevent parent containers from affecting deploy button positioning */
    .stApp, .stApp > div, header, .stToolbar, .stToolbarItems {
        position: static !important;
    }
    
    /* Ensure deploy button is always visible and positioned correctly */
    [data-testid="stDeployButton"] {
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        z-index: 9999 !important;
        transform: none !important;
        margin: 0 !important;
        padding: 0 !important;
        left: auto !important;
        bottom: auto !important;
        width: auto !important;
        height: auto !important;
        float: none !important;
        clear: none !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }
    
    /* Ensure proper spacing and visibility for all header elements - transparent backgrounds */
    [data-testid="stToolbar"] {display: flex !important; visibility: visible !important; justify-content: flex-end !important; background: transparent !important;}
    [data-testid="stStatusWidget"] {display: inline-block !important; visibility: visible !important; margin-left: 8px !important; opacity: 1 !important; background: transparent !important;}
    [data-testid="stDeployButton"] {display: inline-block !important; visibility: visible !important; margin-left: 8px !important; background: transparent !important; position: fixed !important; top: 0 !important; right: 0 !important; z-index: 1000 !important;}
    
    /* Ensure the running status widget and its contents are fully visible */
    [data-testid="stStatusWidget"] * {visibility: visible !important; opacity: 1 !important;}
    [data-testid="stStatusWidget"] .stStatusWidget * {visibility: visible !important; opacity: 1 !important;}
    
    /* Ensure the running animation icon is visible */
    [data-testid="stStatusWidget"] .stStatusWidget__status-icon {visibility: visible !important; opacity: 1 !important; animation: spin 2s linear infinite !important;}
    
    /* Define the spinning animation for the running status */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* Force right alignment for all toolbar items */
    .stToolbarItems > * {margin-left: 8px !important;}
    [data-testid="stToolbar"] > div {justify-content: flex-end !important;}
    
    /* Ensure header stays in top right corner */
    .stApp > header {width: auto !important; min-width: 200px !important;}
    [data-testid="stHeader"] {width: auto !important; min-width: 200px !important;}
    [data-testid="stToolbar"] {width: auto !important; min-width: 200px !important;}
    
    /* Prevent any layout shifts */
    .stApp {overflow-x: hidden !important;}
    
    /* Ensure status widget is never hidden by any CSS */
    [data-testid="stStatusWidget"] {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important; border: none !important; box-shadow: none !important; position: relative !important; z-index: 1000 !important; !important;}
    
    /* Override any potential hiding with maximum specificity */
    .stApp [data-testid="stStatusWidget"] {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    .stApp [data-testid="stStatusWidget"] * {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    
    /* Override any potential hiding of Streamlit status elements - always visible */
    [data-testid="stStatusWidget"] {display: inline-block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; background: transparent !important; border: none !important; box-shadow: none !important;}
    [data-testid="stStatusWidget"] * {display: inline-block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; background: transparent !important;}
    
    /* Ensure the running status text is visible - always visible */
    [data-testid="stStatusWidget"] .stStatusWidget__status-text {display: inline-block !important; visibility: visible !important; opacity: 1 !important; color: #666 !important; font-size: 12px !important; background: transparent !important;}
    
    /* Ensure status is always visible - override any hiding */
    [data-testid="stStatusWidget"] {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important; border: none !important; box-shadow: none !important; position: relative !important; z-index: 1000 !important;}
    
    /* Force visibility for all status elements */
    [data-testid="stStatusWidget"] .stStatusWidget {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    [data-testid="stStatusWidget"] .stStatusWidget > div {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    [data-testid="stStatusWidget"] .stStatusWidget span {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    
    /* Force visibility of all Streamlit status elements - transparent background */
    .stStatusWidget {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important; border: none !important; box-shadow: none !important;}
    .stStatusWidget * {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    
    /* Ensure the running animation is not hidden - always visible */
    .stStatusWidget__status {display: inline-block !important; visibility: visible !important; opacity: 1 !important; background: transparent !important;}
    .stStatusWidget__status-icon {display: inline-block !important; visibility: visible !important; opacity: 1 !important; animation: spin 2s linear infinite !important; background: transparent !important;}
    
    /* Sticky footer styling */
    .sticky-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f8f9fa;
        border-top: 1px solid #dee2e6;
        padding: 0.75rem 0;
        text-align: center;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Add bottom margin to main content to prevent overlap with sticky footer */
    .main .block-container {
        padding-bottom: 4rem !important;
    }
    .custom-container:hover, .article-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        transform: translateY(-5px);
    }
    .article-card {
        animation-delay: 0.2s; /* Staggered animation */
    }
    
    /* Sidebar styling with gradient background and smooth transitions */
    .st-emotion-cache-1wv7cff { /* Target the sidebar background */
        background: linear-gradient(180deg, var(--background-light) 0%, var(--card-background) 100%);
        border-right: 1px solid var(--border-color);
        transition: width 0.3s ease-in-out;
        z-index: 100 !important; /* Ensure sidebar doesn't overlap header */
    }

    /* Navigation buttons in the sidebar with improved hover effects */
    .nav-button-container .stButton > button {
        background-color: transparent;
        color: var(--text-dark);
        border: none;
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
        font-weight: 500;
        text-align: left;
        padding: 12px 16px;
        border-radius: 8px;
        width: 100%;
        margin-bottom: 5px;
    }
    .nav-button-container .stButton > button:hover {
        background-color: var(--secondary-blue);
        color: var(--primary-blue);
        border-left: 4px solid var(--primary-blue);
        transform: translateX(5px);
    }
    .nav-button-container .stButton[data-testid="stButton-primary"] > button {
        background-color: var(--secondary-blue) !important;
        color: var(--primary-blue) !important;
        border-left: 4px solid var(--primary-blue) !important;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }

    /* Primary action button styling with subtle animation */
    .stButton > button {
        background-color: var(--primary-blue);
        color: white;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: background-color 0.3s, transform 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #0077B6;
        transform: scale(1.02);
    }

    /* Badges for sentiment categories */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: transform 0.2s;
    }
    .badge:hover {
        transform: scale(1.1);
    }
    .badge-positive {
        background-color: #D6F5E3;
        color: #28B463;
    }
    .badge-neutral {
        background-color: #E3F2FD;
        color: #1976D2;
    }
    .badge-negative {
        background-color: #FADBD8;
        color: #C0392B;
    }

    /* Sentiment border for article cards */
    .sentiment-positive { border-left: 4px solid var(--success-green); }
    .sentiment-negative { border-left: 4px solid var(--error-red); }
    .sentiment-neutral { border-left: 4px solid #3498DB; }
    
    /* Article text styling for better readability */
    .article-card p {
        line-height: 1.6;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }
    
    /* Text area styling for article content */
    .stTextArea textarea {
        font-family: 'Open Sans', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        white-space: pre-wrap !important;
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        color: #2C3E50 !important;
        font-weight: normal !important;
    }
    
    /* More specific styling for article content text areas */
    .stTextArea textarea[data-testid="stTextArea"] {
        color: #2C3E50 !important;
        font-weight: normal !important;
        background-color: #ffffff !important;
    }
    
    /* Override any Streamlit default styling */
    .stTextArea textarea:disabled {
        color: #2C3E50 !important;
        font-weight: normal !important;
        background-color: #ffffff !important;
        opacity: 1 !important;
    }
    
    /* Force text color for all text areas */
    .stTextArea textarea,
    .stTextArea textarea:disabled,
    .stTextArea textarea:enabled {
        color: #2C3E50 !important;
        font-weight: normal !important;
        background-color: #ffffff !important;
    }
    
    /* Additional specificity for article content */
    .stTextArea textarea[data-testid="stTextArea"] {
        color: #2C3E50 !important;
        font-weight: normal !important;
        background-color: #ffffff !important;
    }
    
    /* Article title styling */
    .article-title {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: var(--primary-blue) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.3 !important;
    }
    
    /* Global component styling */
    h1, h2, h3, h4, h5, h6 { color: var(--primary-blue); font-family: 'Open Sans', sans-serif; }
    .stProgress > div > div > div > div { background-color: var(--primary-blue); }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [aria-selected="true"] { color: var(--primary-blue); border-bottom: 2px solid var(--primary-blue); }
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid;
    }
    .stInfo { background-color: #E0F2FF; border-left-color: var(--primary-blue); }
    .stSuccess { background-color: #D6F5E3; border-left-color: var(--success-green); }
    .stWarning { background-color: #FEF9E7; border-left-color: var(--warning-yellow); }
    .stError { background-color: #FADBD8; border-left-color: var(--error-red); }

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sentiment Analysis Configuration & Functions (Unchanged from previous versions) ---
FINANCE_POSITIVE_WORDS = [
    "profit", "growth", "revenue", "earnings", "surge", "rally", "bullish", "optimistic",
    "strong", "robust", "healthy", "expansion", "investment", "opportunity", "recovery",
    "bounce", "positive", "gain", "increase", "rise", "climb", "soar", "jump", "leap",
    "success", "achievement", "breakthrough", "innovation", "leadership", "excellence",
    "outperform", "beat", "exceed", "outpace", "accelerate", "boost", "enhance", "improve",
    "strengthen", "solidify", "stabilize", "secure", "confident", "assured", "promising",
    "bright", "upward", "ascending", "prosperous", "thriving", "flourishing", "booming"
]
FINANCE_NEGATIVE_WORDS = [
    "loss", "decline", "drop", "fall", "crash", "bearish", "pessimistic", "weak",
    "poor", "unhealthy", "contraction", "recession", "downturn", "slump", "plunge",
    "negative", "decrease", "reduce", "diminish", "shrink", "contract", "deteriorate",
    "worsen", "fail", "bankruptcy", "default", "crisis", "panic", "fear", "anxiety",
    "uncertainty", "volatility", "risk", "danger", "threat", "concern", "worry",
    "stress", "pressure", "strain", "burden", "liability", "debt", "losses", "deficit",
    "shortfall", "gap", "hole", "weakness", "vulnerability", "exposure", "susceptible",
    "fragile", "unstable", "unreliable", "unpredictable", "chaotic", "turbulent"
]
def analyze_sentiment_lexicon(text: str) -> Dict:
    if not text:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    text_lower = text.lower()
    positive_count = sum(1 for word in FINANCE_POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in FINANCE_NEGATIVE_WORDS if word in text_lower)
    total_relevant = positive_count + negative_count
    if total_relevant == 0:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    score = (positive_count - negative_count) / total_relevant
    if score > 0.1:
        category = 'Positive'
    elif score < -0.1:
        category = 'Negative'
    else:
        category = 'Neutral'
    return {
        'score': round(score, 3),
        'category': category,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'total_relevant': total_relevant
    }

def analyze_sentiment_sync(text: str, method: str = 'lexicon') -> Dict:
    """Synchronous sentiment analysis wrapper that properly handles LLM vs lexicon methods"""
    if method == 'lexicon':
        return analyze_sentiment_lexicon(text)
    elif method == 'llm':
        # Import the proper LLM sentiment analysis function
        from risk_monitor.utils.sentiment import analyze_sentiment_sync as proper_analyze_sentiment_sync
        try:
            # Get OpenAI API key from config
            config = Config()
            openai_api_key = config.get_openai_api_key()
            if openai_api_key:
                st.info("LLM-based sentiment analysis is processing...")
                return proper_analyze_sentiment_sync(text, 'llm', openai_api_key)
            else:
                st.warning("OpenAI API key not found, falling back to lexicon analysis")
                return analyze_sentiment_lexicon(text)
        except Exception as e:
            st.error(f"LLM sentiment analysis failed: {e}")
            st.info("Falling back to lexicon analysis")
            return analyze_sentiment_lexicon(text)
    else:
        return analyze_sentiment_lexicon(text)

# --- Streamlit Session State & Helper Functions ---
def initialize_session_state():
    """Initializes a new session state with default values."""
    if 'articles' not in st.session_state: st.session_state.articles = []
    if 'counterparties' not in st.session_state: st.session_state.counterparties = []
    if 'keywords' not in st.session_state: st.session_state.keywords = ""
    if 'current_page' not in st.session_state: st.session_state.current_page = "dashboard"
    if 'collect_news_trigger' not in st.session_state: st.session_state.collect_news_trigger = False
    if 'sentiment_method' not in st.session_state: st.session_state.sentiment_method = "llm"
    if 'last_run_metadata' not in st.session_state: st.session_state.last_run_metadata = {}
    
    # Initialize AI Financial Assistant session state variables
    if 'rag_service' not in st.session_state: st.session_state.rag_service = None
    if 'nasdaq_companies' not in st.session_state: st.session_state.nasdaq_companies = None
    if 'db_stats' not in st.session_state: st.session_state.db_stats = None





def get_nasdaq_100_companies():
    """Returns the NASDAQ-100 companies list."""
    return [
        ("AAPL", "Apple Inc"),
        ("ADBE", "Adobe Inc"),
        ("ADI", "Analog Devices Inc"),
        ("ADP", "Automatic Data Processing Inc"),
        ("ADSK", "Autodesk Inc"),
        ("AEP", "American Electric Power Company Inc"),
        ("ALGN", "Align Technology Inc"),
        ("AMAT", "Applied Materials Inc"),
        ("AMD", "Advanced Micro Devices Inc"),
        ("AMGN", "Amgen Inc"),
        ("AMZN", "Amazon.com Inc"),
        ("ANSS", "ANSYS Inc"),
        ("ASML", "ASML Holding NV"),
        ("ATVI", "Activision Blizzard Inc"),
        ("AVGO", "Broadcom Inc"),
        ("AZN", "AstraZeneca PLC"),
        ("BIIB", "Biogen Inc"),
        ("BKNG", "Booking Holdings Inc"),
        ("BKR", "Baker Hughes Company"),
        ("CDNS", "Cadence Design Systems Inc"),
        ("CEG", "Constellation Energy Corp"),
        ("CHTR", "Charter Communications Inc"),
        ("CMCSA", "Comcast Corporation"),
        ("COST", "Costco Wholesale Corporation"),
        ("CPRT", "Copart Inc"),
        ("CRWD", "CrowdStrike Holdings Inc"),
        ("CSCO", "Cisco Systems Inc"),
        ("CSGP", "CoStar Group Inc"),
        ("CTAS", "Cintas Corporation"),
        ("CTSH", "Cognizant Technology Solutions Corp"),
        ("DDOG", "Datadog Inc"),
        ("DLTR", "Dollar Tree Inc"),
        ("DXCM", "DexCom Inc"),
        ("EA", "Electronic Arts Inc"),
        ("EBAY", "eBay Inc"),
        ("ENPH", "Enphase Energy Inc"),
        ("EXC", "Exelon Corporation"),
        ("FANG", "Diamondback Energy Inc"),
        ("FAST", "Fastenal Company"),
        ("FTNT", "Fortinet Inc"),
        ("GILD", "Gilead Sciences Inc"),
        ("GOOG", "Alphabet Inc Class C"),
        ("GOOGL", "Alphabet Inc Class A"),
        ("HON", "Honeywell International Inc"),
        ("IDXX", "IDEXX Laboratories Inc"),
        ("ILMN", "Illumina Inc"),
        ("INTC", "Intel Corporation"),
        ("INTU", "Intuit Inc"),
        ("ISRG", "Intuitive Surgical Inc"),
        ("JD", "JD.com Inc"),
        ("KLAC", "KLA Corporation"),
        ("LCID", "Lucid Group Inc"),
        ("LRCX", "Lam Research Corporation"),
        ("LULU", "Lululemon Athletica Inc"),
        ("MAR", "Marriott International Inc"),
        ("MCHP", "Microchip Technology Inc"),
        ("MDLZ", "Mondelez International Inc"),
        ("MELI", "MercadoLibre Inc"),
        ("META", "Meta Platforms Inc"),
        ("MNST", "Monster Beverage Corporation"),
        ("MRVL", "Marvell Technology Inc"),
        ("MSFT", "Microsoft Corporation"),
        ("MU", "Micron Technology Inc"),
        ("NFLX", "Netflix Inc"),
        ("NVDA", "NVIDIA Corporation"),
        ("NXPI", "NXP Semiconductors NV"),
        ("ODFL", "Old Dominion Freight Line Inc"),
        ("OKTA", "Okta Inc"),
        ("ORCL", "Oracle Corporation"),
        ("PANW", "Palo Alto Networks Inc"),
        ("PAYX", "Paychex Inc"),
        ("PCAR", "PACCAR Inc"),
        ("PEP", "PepsiCo Inc"),
        ("PLTR", "Palantir Technologies Inc"),
        ("PYPL", "PayPal Holdings Inc"),
        ("QCOM", "QUALCOMM Incorporated"),
        ("REGN", "Regeneron Pharmaceuticals Inc"),
        ("ROST", "Ross Stores Inc"),
        ("SBUX", "Starbucks Corporation"),
        ("SGEN", "Seagen Inc"),
        ("SIRI", "Sirius XM Holdings Inc"),
        ("SNPS", "Synopsys Inc"),
        ("TEAM", "Atlassian Corporation"),
        ("TMUS", "T-Mobile US Inc"),
        ("TSLA", "Tesla Inc"),
        ("TXN", "Texas Instruments Incorporated"),
        ("VRTX", "Vertex Pharmaceuticals Inc"),
        ("WBA", "Walgreens Boots Alliance Inc"),
        ("WDAY", "Workday Inc"),
        ("XEL", "Xcel Energy Inc"),
        ("ZM", "Zoom Video Communications Inc"),
        ("ZS", "Zscaler Inc")
    ]

def filter_articles_by_keywords(articles: List[Dict], keywords: str) -> List[Dict]:
    """Filters a list of articles to only include those containing specific keywords."""
    if not keywords.strip(): return articles
    keyword_list = [kw.strip().lower() for kw in keywords.split('\n') if kw.strip()]
    if not keyword_list: return articles
    filtered_articles = []
    for article in articles:
        title = article.get('title', '').lower()
        text = article.get('text', '').lower()
        if any(keyword in title or keyword in text for keyword in keyword_list):
            filtered_articles.append(article)
    return filtered_articles

# --- Scheduler Configuration Functions ---
def load_scheduler_config():
    """Load scheduler configuration from JSON file."""
    import os
    # Use absolute path to risk_monitor directory scheduler config
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheduler_config.json")
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading scheduler config: {e}")
        return {}

def save_scheduler_config(config):
    """Save scheduler configuration to JSON file."""
    import os
    # Use absolute path to risk_monitor directory scheduler config
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheduler_config.json")
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return True, "Configuration saved successfully!"
    except Exception as e:
        return False, f"Error saving configuration: {e}"

def restart_scheduler():
    """Restart the scheduler by stopping and starting it."""
    try:
        import subprocess
        import time
        
        # Stop existing scheduler
        stop_result = subprocess.run(['pkill', '-f', 'run_data_refresh.py'], capture_output=True, text=True)
        
        # Wait a moment for processes to stop
        time.sleep(2)
        
        # Get the path to the run_data_refresh.py script
        import os
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "run_data_refresh.py")
        
        # Check if script exists
        if not os.path.exists(script_path):
            return False, f"Scheduler script not found at: {script_path}"
        
        # Get the virtual environment Python path
        venv_python = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "bin", "python")
        
        # Check if virtual environment exists, otherwise use system python3
        if os.path.exists(venv_python):
            python_cmd = venv_python
        else:
            python_cmd = "python3"
        
        # Start new scheduler using proper nohup syntax
        start_result = subprocess.run(
            f'nohup {python_cmd} {script_path} > scheduler_background.log 2>&1 &',
            capture_output=True, text=True, shell=True
        )
        
        if start_result.returncode == 0:
            # Wait a moment and check if it actually started
            time.sleep(2)
            is_running, _, _ = get_scheduler_status()
            if is_running:
                return True, "Scheduler restarted successfully!"
            else:
                return False, "Scheduler restart command executed but process not detected. Check scheduler_background.log for errors."
        else:
            return False, f"Error restarting scheduler: {start_result.stderr}"
    except Exception as e:
        return False, f"Error restarting scheduler: {e}"

def stop_scheduler():
    """Stop the scheduler."""
    try:
        import subprocess
        import time
        
        # First check if scheduler is actually running
        is_running, process_ids, _ = get_scheduler_status()
        if not is_running:
            return True, "Scheduler was not running."
        
        # Stop the scheduler
        result = subprocess.run(['pkill', '-f', 'run_data_refresh.py'], capture_output=True, text=True)
        
        # Wait a moment for processes to stop
        time.sleep(2)
        
        # Verify it actually stopped
        is_still_running, _, _ = get_scheduler_status()
        if not is_still_running:
            return True, "Scheduler stopped successfully!"
        else:
            return False, "Scheduler stop command executed but process still detected. Try using 'Restart Scheduler' instead."
    except Exception as e:
        return False, f"Error stopping scheduler: {e}"

def start_scheduler():
    """Start the scheduler."""
    try:
        import subprocess
        import os
        
        # Get the path to the run_data_refresh.py script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "run_data_refresh.py")
        
        # Check if script exists
        if not os.path.exists(script_path):
            return False, f"Scheduler script not found at: {script_path}"
        
        # Get the virtual environment Python path
        venv_python = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "bin", "python")
        
        # Check if virtual environment exists, otherwise use system python3
        if os.path.exists(venv_python):
            python_cmd = venv_python
        else:
            python_cmd = "python3"
        
        # Test if Python can run the script first
        test_result = subprocess.run([python_cmd, script_path, '--test'], capture_output=True, text=True, timeout=10)
        
        # Start the scheduler in the background
        result = subprocess.run(
            f'nohup {python_cmd} {script_path} > scheduler_background.log 2>&1 &',
            capture_output=True, text=True, shell=True
        )
        
        if result.returncode == 0:
            # Wait a moment and check if it actually started
            import time
            time.sleep(2)
            is_running, _, _ = get_scheduler_status()
            if is_running:
                return True, "Scheduler started successfully!"
            else:
                return False, "Scheduler command executed but process not detected. Check scheduler_background.log for errors."
        else:
            return False, f"Error starting scheduler: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Scheduler test timed out. Check dependencies and configuration."
    except Exception as e:
        return False, f"Error starting scheduler: {e}"



def update_email_subscription(enabled: bool):
    """Update email subscription status."""
    try:
        config = load_scheduler_config()
        config["email_enabled"] = enabled
        success, message = save_scheduler_config(config)
        if success:
            status = "enabled" if enabled else "disabled"
            return True, f"Email subscription {status} successfully!"
        return False, message
    except Exception as e:
        return False, f"Error updating email subscription: {e}"

def get_scheduler_status():
    """Check if scheduler is currently running."""
    try:
        import subprocess
        import os
        from datetime import datetime
        
        # Check for run_data_refresh.py processes with more specific matching
        result = subprocess.run(['pgrep', '-f', 'run_data_refresh.py'], capture_output=True, text=True)
        is_running = result.returncode == 0 and result.stdout.strip()
        process_ids = result.stdout.strip().split('\n') if is_running else []
        
        # Verify the processes are actually our scheduler processes
        if is_running:
            verified_processes = []
            project_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            for pid in process_ids:
                try:
                    # Check if the process is actually running and is our script
                    ps_result = subprocess.run(['ps', '-p', pid, '-o', 'command='], capture_output=True, text=True)
                    if ps_result.returncode == 0:
                        cmd_line = ps_result.stdout.strip()
                        # Check if it's our specific script (relaxed path checking since ps might not show full path)
                        if ('run_data_refresh.py' in cmd_line and 
                            '--test' not in cmd_line):  # Exclude test processes
                            verified_processes.append(pid)
                except:
                    continue
            process_ids = verified_processes
            is_running = len(verified_processes) > 0
        
        # Also check for the shell script process
        shell_result = subprocess.run(['pgrep', '-f', 'run_scheduler_with_email.sh'], capture_output=True, text=True)
        shell_running = shell_result.returncode == 0 and shell_result.stdout.strip()
        
        # Scheduler is running if either process is active
        is_running = is_running or shell_running
        
        # Get additional status information
        status_info = {
            'is_running': is_running,
            'process_ids': process_ids,
            'last_run': None,
            'next_run': None,
            'log_file_exists': os.path.exists('logs/scheduler.log'),
            'background_log_exists': os.path.exists('scheduler_background.log')
        }
        
        # Check last run time from log file and verify scheduler is actually working
        if status_info['log_file_exists']:
            try:
                with open('logs/scheduler.log', 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Look for the last "Starting daily news collection" entry
                        for line in reversed(lines):
                            if "Starting daily news collection" in line:
                                # Extract timestamp from log line
                                timestamp_str = line.split(' - ')[0]
                                try:
                                    last_run = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                    status_info['last_run'] = last_run
                                    break
                                except:
                                    pass
                        
                        # If we have a running process but no recent daily collection, 
                        # check if scheduler is actively monitoring (look for "Scheduler started" message)
                        if is_running and not status_info.get('last_run'):
                            for line in reversed(lines[-10:]):  # Check last 10 lines
                                if "Scheduler started - monitoring for scheduled runs" in line:
                                    # Scheduler is actively running and monitoring
                                    break
                                elif "Scheduled enhanced daily news collection" in line:
                                    # Scheduler is configured and running
                                    break
            except:
                pass
        
        return is_running, process_ids, status_info
    except Exception as e:
        return False, [], {}

# --- UI/UX Components ---
def display_dashboard_header():
    """Displays the main dashboard header with title and subtitle."""
    st.markdown('<div class="main-header"><div><h1>Risk Monitoring Dashboard</h1><p>Financial news and document analysis at a glance.</p></div></div>', unsafe_allow_html=True)

def display_dashboard_metrics():
    """Displays key metrics on the dashboard."""
    articles = st.session_state.get('articles', [])
    num_articles = len(articles)
    
    positive_count = sum(1 for a in articles if a.get('sentiment_category') == 'Positive')
    negative_count = sum(1 for a in articles if a.get('sentiment_category') == 'Negative')
    neutral_count = num_articles - positive_count - negative_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Articles Analyzed", value=num_articles, delta=f"Last run: {st.session_state.get('last_run_metadata', {}).get('articles_collected', 0)}")
    with col2:
        st.metric(label="Risks Detected (Negative)", value=negative_count, delta=f"Last run: {st.session_state.get('last_run_metadata', {}).get('negative_count', 0)}", delta_color="inverse")
    with col3:
        st.metric(label="Opportunities Found (Positive)", value=positive_count, delta=f"Last run: {st.session_state.get('last_run_metadata', {}).get('positive_count', 0)}", delta_color="normal")

    if num_articles > 0:
        st.subheader("Sentiment Distribution")
        sentiment_data = pd.DataFrame({
            'Sentiment': ['Positive', 'Negative', 'Neutral'],
            'Count': [positive_count, negative_count, neutral_count]
        })
        fig = px.pie(
            sentiment_data,
            values='Count',
            names='Sentiment',
            color='Sentiment',
            color_discrete_map={'Negative': '#E74C3C', 'Positive': '#2ECC71', 'Neutral': '#3498DB'},
            title="Distribution of Article Sentiment"
        )
        st.plotly_chart(fig, use_container_width=True)

def navigation_sidebar():
    """Renders the main navigation sidebar."""
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 2rem 1rem; background: linear-gradient(180deg, #005A9C 0%, #0077B6 100%); color: white; border-radius: 8px;">
        <div style="font-size: 3rem;">📊</div>
        <div style="font-weight: 700; font-size: 1.5rem;">Risk Monitor</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">Financial Analysis Tool</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### Navigation", unsafe_allow_html=True)
    st.sidebar.markdown('<div class="nav-button-container">', unsafe_allow_html=True)
    
    if st.sidebar.button("📊 Dashboard", key="nav_dashboard", use_container_width=True, type="primary" if st.session_state.current_page == "dashboard" else "secondary"):
        st.session_state.current_page = "dashboard"
        st.rerun()

    if st.sidebar.button("📰 News Analysis", key="nav_news", use_container_width=True, type="primary" if st.session_state.current_page == "news_analysis" else "secondary"):
        st.session_state.current_page = "news_analysis"
        st.rerun()

    if st.sidebar.button("🤖 AI Financial Assistant", key="nav_rag", use_container_width=True, type="primary" if st.session_state.current_page == "rag_chat" else "secondary"):
        st.session_state.current_page = "rag_chat"
        st.rerun()

    if st.sidebar.button("⏰ Scheduler Config", key="nav_scheduler", use_container_width=True, type="primary" if st.session_state.current_page == "scheduler_config" else "secondary"):
        st.session_state.current_page = "scheduler_config"
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

def display_article_card(article: Dict, index: int = None):
    """Renders a card for a single article with sentiment and details."""
    sentiment = article.get('sentiment_category', 'Neutral').lower()
    color_class = f"sentiment-{sentiment}"
    
    st.markdown(f'<div class="article-card {color_class}">', unsafe_allow_html=True)
    st.markdown(f'<h3 class="article-title">{article.get("title", "Untitled")}</h3>', unsafe_allow_html=True)
    
    # Handle source information properly
    source_info = article.get('source', {})
    if isinstance(source_info, dict):
        # Extract source details from dictionary
        source_name = source_info.get('name', 'Unknown')
        source_icon = source_info.get('icon', '')
        authors = source_info.get('authors', [])
        
        # Format source display with icon and authors
        source_display = source_name
        if source_icon:
            source_display = f"<img src='{source_icon}' width='16' height='16' style='vertical-align: middle; margin-right: 5px;' />{source_name}"
        
        if authors:
            authors_str = ', '.join(authors) if isinstance(authors, list) else str(authors)
            source_display += f" by {authors_str}"
    else:
        # Fallback for string source
        source_display = str(source_info) if source_info else 'Unknown'
    
    # Handle publish_date which can be string, datetime object, or None
    publish_date = article.get('publish_date')
    if publish_date:
        if isinstance(publish_date, str):
            try:
                date_str = datetime.fromisoformat(publish_date).strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                date_str = 'N/A'
        elif isinstance(publish_date, datetime):
            date_str = publish_date.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = 'N/A'
    else:
        date_str = 'N/A'
    
    # Display source and publish date with proper formatting
    st.markdown(f'<p style="color: var(--text-muted); font-size: 0.9rem;"><strong>Source:</strong> {source_display} | <strong>Published:</strong> {date_str}</p>', unsafe_allow_html=True)
    
    # Add article URL if available
    article_url = article.get('url') or article.get('link')
    if article_url:
        st.markdown(f'<p style="color: var(--text-muted); font-size: 0.9rem;"><strong>URL:</strong> <a href="{article_url}" target="_blank" style="color: #005A9C; text-decoration: none;">{article_url}</a></p>', unsafe_allow_html=True)
    
    st.markdown(f'<p>{article.get("summary", article.get("text", "No summary available"))[:300]}...</p>', unsafe_allow_html=True)
    
    sentiment_label = article.get("sentiment_category", "Neutral").upper()
    badge_class = f"badge-{sentiment.lower()}"
    st.markdown(f'<div style="text-align: right;"><span class="badge {badge_class}">{sentiment_label}</span></div>', unsafe_allow_html=True)

    with st.expander("Show Detailed Analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Sentiment Score:** `{article.get('sentiment_score', 'N/A')}`")
        
        with col2:
            st.markdown(f"**Risk Score:** `{article.get('risk_score', 'N/A')}`")
        
        # Enhanced Insight Display
        st.markdown("---")
        st.markdown("### 🧠 **Sentiment Analysis Insight**")
        
        # Check for different types of sentiment analysis data
        sentiment_data = article.get('sentiment_analysis', {})
        
        # Priority order: reasoning > justification > key_factors > market_impact
        insight_text = None
        insight_source = None
        
        if isinstance(sentiment_data, dict):
            # Structured analysis with reasoning
            if sentiment_data.get('reasoning'):
                insight_text = sentiment_data.get('reasoning')
                insight_source = "Structured Analysis"
            # LLM analysis with justification
            elif sentiment_data.get('justification'):
                insight_text = sentiment_data.get('justification')
                insight_source = "LLM Analysis"
            # Key factors
            elif sentiment_data.get('key_factors'):
                factors = sentiment_data.get('key_factors', [])
                if isinstance(factors, list) and factors:
                    insight_text = f"Key factors: {', '.join(factors)}"
                    insight_source = "LLM Analysis"
            # Market impact
            elif sentiment_data.get('market_impact'):
                insight_text = sentiment_data.get('market_impact')
                insight_source = "LLM Analysis"
        
        # Fallback to direct article fields
        if not insight_text:
            if article.get('sentiment_justification'):
                insight_text = article.get('sentiment_justification')
                insight_source = "LLM Analysis"
            elif article.get('reasoning'):
                insight_text = article.get('reasoning')
                insight_source = "Structured Analysis"
        
        # Debug: Show what data is available (remove this after testing)
        if st.checkbox("🔍 Debug: Show Analysis Data", key=f"debug_{index}_{hash(article.get('title', ''))}"):
            st.json({
                'sentiment_data': sentiment_data,
                'sentiment_justification': article.get('sentiment_justification'),
                'sentiment_method': article.get('sentiment_method'),
                'insight_text': insight_text,
                'insight_source': insight_source
            })
        
        # Display the insight
        if insight_text:
            st.success(f"**💡 Insight ({insight_source}):** {insight_text}")
            
            # Additional details if available
            if isinstance(sentiment_data, dict):
                if sentiment_data.get('confidence'):
                    st.markdown(f"**Confidence Level:** `{sentiment_data.get('confidence', 'N/A')}`")
                
                if sentiment_data.get('entity'):
                    st.markdown(f"**Main Entity:** `{sentiment_data.get('entity', 'N/A')}`")
                
                if sentiment_data.get('event_type'):
                    st.markdown(f"**Event Type:** `{sentiment_data.get('event_type', 'N/A')}`")
                
                if sentiment_data.get('key_quotes'):
                    quotes = sentiment_data.get('key_quotes', [])
                    if quotes and isinstance(quotes, list) and quotes:
                        st.markdown("**Key Evidence:**")
                        for i, quote in enumerate(quotes[:3], 1):  # Show max 3 quotes
                            st.markdown(f"• {quote}")
        else:
            # Fallback to lexicon analysis
            positive_count = article.get('positive_count', 0)
            negative_count = article.get('negative_count', 0)
            st.info(f"**📊 Lexicon Analysis:** Found {positive_count} positive and {negative_count} negative financial indicators.")
            if positive_count > negative_count:
                st.markdown("*Overall positive sentiment due to more positive financial indicators.*")
            elif negative_count > positive_count:
                st.markdown("*Overall negative sentiment due to more negative financial indicators.*")
            else:
                st.markdown("*Neutral sentiment due to balanced positive and negative indicators.*")
        
        # Display full article text with better formatting and word wrap
        st.markdown("**Full Article Text:**")
        article_text = article.get('text', 'No text found.')
        if article_text:
            # Use st.text_area for better word wrap and readability
            st.text_area(
                "Article Content",
                value=article_text,
                height=300,
                disabled=True,
                help="Full article text with proper word wrapping",
                key=f"article_text_display_{index}_{hash(article.get('title', ''))}_{hash(article.get('url', ''))}" if index is not None else f"article_text_display_{hash(article.get('title', ''))}_{hash(article.get('url', ''))}"
            )
        else:
            st.info("No article text available.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main Application Logic ---
def main():
    """Main function to run the Streamlit application."""
    load_custom_css()
    initialize_session_state()
    
    navigation_sidebar()
    
    # --- Dashboard View ---
    if st.session_state.current_page == "dashboard":
        display_dashboard_header()
        display_dashboard_metrics()
        
        st.markdown("---")
        st.header("Latest Analyzed Articles")
        if not st.session_state.articles:
            st.info("💡 Run a news analysis to see the latest results here.")
        
        for i, article in enumerate(st.session_state.articles[:5], 1):
            display_article_card(article, i)

    # --- News Analysis View ---
    elif st.session_state.current_page == "news_analysis":
        st.markdown('<div class="custom-container"><h2 style="margin: 0;">News Analysis</h2><p style="margin: 0.25rem 0 0; color: #4b5563;">Configure and run financial news analysis.</p></div>', unsafe_allow_html=True)
        
        search_tab, filters_tab, advanced_tab = st.tabs(["🔍 Search", "🔎 Filters", "⚙️ Advanced"])
        
        with search_tab:
            st.subheader("Search Mode")
            search_mode = st.radio("Choose how to search for articles:", ["Counterparty-based", "Custom Query"], index=0, horizontal=True)
            st.session_state.search_mode = search_mode
            
            if search_mode == "Counterparty-based":
                st.write("🏢 **Select companies to monitor:**")
                
                # Get NASDAQ-100 companies list
                nasdaq_100_companies = get_nasdaq_100_companies()
                
                # Create dropdown options with NASDAQ-100 companies
                dropdown_options = [f"{symbol} - {name}" for symbol, name in nasdaq_100_companies]
                dropdown_options.insert(0, "All Companies")
                
                # Add custom company input option
                dropdown_options.append("➕ Enter Custom Company...")
                
                # Multi-select for counterparties
                selected_companies = st.multiselect(
                    "Select Companies/Entities",
                    options=dropdown_options,
                    default=st.session_state.get('selected_counterparties', []),
                    help="Choose from NASDAQ-100 companies or enter custom companies"
                )
                
                # Handle custom company input
                if "➕ Enter Custom Company..." in selected_companies:
                    # Remove the custom option from selection
                    selected_companies = [c for c in selected_companies if c != "➕ Enter Custom Company..."]
                    
                    custom_companies_input = st.text_area(
                        "Enter custom company names (one per line):",
                        placeholder="e.g., Goldman Sachs\nJPMorgan Chase\nCustom Company Name",
                        help="Enter company names or ticker symbols, one per line"
                    )
                    
                    if custom_companies_input.strip():
                        custom_companies = [c.strip() for c in custom_companies_input.split("\n") if c.strip()]
                        selected_companies.extend(custom_companies)
                
                # Store selected counterparties in session state
                st.session_state.selected_counterparties = selected_companies
                
                # Convert to the format expected by the rest of the application
                if "All Companies" in selected_companies:
                    st.session_state.counterparties = ["All Companies"]
                else:
                    # Use full entity names from dropdown selections
                    counterparties = []
                    for selection in selected_companies:
                        if " - " in selection:
                            # Use full entity name (e.g., "AAPL - Apple Inc" -> "AAPL - Apple Inc")
                            counterparties.append(selection)
                        else:
                            # Custom company name
                            counterparties.append(selection)
                    st.session_state.counterparties = counterparties
            else:
                st.session_state.custom_query = st.text_input("Custom Search Query", value=st.session_state.get('custom_query', Config.SEARCH_QUERY))

            st.number_input("Articles per Search", min_value=1, max_value=20, value=st.session_state.get('num_articles', 5), step=1, format="%d", help="Max number of articles to collect per search term.", key="num_articles")

        with filters_tab:
            st.text_area("Keyword Filtering", value=st.session_state.keywords, placeholder="risk\nfinancial\nmarket\ncrisis", height=150, help="Only include articles containing these keywords.", key="keywords")

        with advanced_tab:
            sentiment_method = st.selectbox("Sentiment Analysis Method", ["LLM Based", "Lexicon Based"], index=0, help="LLM is more nuanced and provides detailed insights; Lexicon is fast and rule-based.", key="sentiment_method_select")
            # Convert to the format expected by RiskAnalyzer
            if sentiment_method == "LLM Based":
                st.session_state.sentiment_method = "llm"
            else:
                st.session_state.sentiment_method = "lexicon"
            
            # Auto-save functionality removed - all data stored in database
        
        st.markdown("---")
        
        # Add clear results button if articles exist
        if st.session_state.articles:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🗑️ Clear Previous Results", help="Clear all previously analyzed articles"):
                    st.session_state.articles = []
                    st.session_state.last_analysis_results = {}
                    st.success("Previous results cleared! Run a new analysis to see updated insights.")
                    st.rerun()
            with col2:
                if st.button("📰 Collect and Analyze Articles", type="primary", use_container_width=True):
                    st.session_state.collect_news_trigger = True
        else:
            if st.button("📰 Collect and Analyze Articles", type="primary", use_container_width=True):
                st.session_state.collect_news_trigger = True
            
        if st.session_state.collect_news_trigger:
            st.session_state.collect_news_trigger = False
            progress_container = st.empty()
            with progress_container.container():
                st.subheader("Processing Articles...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
            try:
                queries = st.session_state.counterparties if st.session_state.search_mode == "Counterparty-based" else [st.session_state.custom_query]
                queries = [q for q in queries if q.strip()]
                if not queries:
                    status_text.warning("⚠️ No search queries provided.")
                    progress_container.empty()
                    return

                news_collector = NewsCollector()
                analyzer = RiskAnalyzer()
                collected_articles = []
                total_steps = len(queries) * st.session_state.num_articles
                current_step = 0
                
                # Always store in sentiment-db (unified database)
                for i, query in enumerate(queries):
                    status_text.info(f"Collecting news for: **{query}**")
                    articles = news_collector.collect_articles(query, st.session_state.num_articles)
                    filtered_articles = filter_articles_by_keywords(articles, st.session_state.keywords)
                    collected_articles.extend(filtered_articles)
                    current_step += len(queries)
                    progress_bar.progress(current_step / total_steps)
                
                # Analyze articles with comprehensive analysis
                if collected_articles:
                    status_text.info("Analyzing articles and storing in sentiment-db...")
                    
                    # Always store in sentiment-db
                    try:
                        # Use comprehensive analysis with storage in sentiment-db
                        # Get selected entity from counterparties (use full entity name)
                        selected_entity = None
                        if st.session_state.counterparties and len(st.session_state.counterparties) == 1 and st.session_state.counterparties[0] != "All Companies":
                            selected_entity = st.session_state.counterparties[0]  # Use full entity name like "AAPL - Apple Inc"
                        
                        analysis_results = analyzer.analyze_and_store_in_pinecone(
                            collected_articles, 
                            st.session_state.sentiment_method,
                            store_in_db=True,  # Always store in sentiment-db
                            selected_entity=selected_entity
                        )
                        
                        # Extract individual article results for display
                        individual_analyses = analysis_results['individual_analyses']
                        st.session_state.articles = []
                        
                        for i, (article, analysis) in enumerate(zip(collected_articles, individual_analyses)):
                            # Merge article data with analysis results
                            sentiment_analysis = analysis['sentiment_analysis']
                            article.update({
                                'sentiment_score': sentiment_analysis['score'],
                                'sentiment_category': sentiment_analysis['category'],
                                'sentiment_method': st.session_state.sentiment_method,
                                'sentiment_justification': sentiment_analysis.get('justification', ''),
                                'risk_score': analysis['risk_analysis']['overall_risk_score'],
                                'risk_categories': analysis['risk_analysis']['risk_categories']
                            })
                            st.session_state.articles.append(article)
                        
                        # Store comprehensive results
                        st.session_state.last_analysis_results = analysis_results
                        
                        # Show storage statistics (always sentiment-db)
                        storage_stats = analysis_results['analysis_summary']['storage_stats']
                        storage_type = analysis_results['analysis_summary']['storage_type']
                        

                        
                        if storage_type == "analysis_db" or storage_type == "pinecone":
                            status_text.success(f"🔥 Analysis complete! {storage_stats['success_count']} articles stored in Sentiment Database (sentiment-db).")
                            # Debug info
                            with st.expander("🔍 Sentiment Database Details"):
                                st.write(f"**Database:** sentiment-db")
                                st.write(f"**Success Count:** {storage_stats['success_count']}")
                                st.write(f"**Error Count:** {storage_stats['error_count']}")
                                st.write(f"**Total Count:** {storage_stats['total_count']}")
                                st.write(f"**Status:** 🔥 SUCCESSFULLY STORED")
                        elif storage_type == "failed":
                            status_text.error(f"❌ CRITICAL ERROR: Failed to store articles in sentiment-db!")
                            # Debug info
                            with st.expander("🔍 Error Details"):
                                st.write(f"**Storage Type:** {storage_type}")
                                st.write(f"**Success Count:** {storage_stats['success_count']}")
                                st.write(f"**Error Count:** {storage_stats['error_count']}")
                                st.write(f"**Total Count:** {storage_stats['total_count']}")
                                st.write(f"**Status:** ❌ STORAGE FAILED")
                        else:
                            # Unknown storage type - show as warning
                            status_text.warning(f"⚠️ Analysis complete but storage status unclear: {storage_type}")
                            # Debug info
                            with st.expander("🔍 Storage Details"):
                                st.write(f"**Storage Type:** {storage_type}")
                                st.write(f"**Success Count:** {storage_stats['success_count']}")
                                st.write(f"**Error Count:** {storage_stats['error_count']}")
                                st.write(f"**Total Count:** {storage_stats['total_count']}")
                                st.write(f"**Status:** ⚠️ UNKNOWN STORAGE STATUS")
                        
                    except Exception as e:
                            status_text.error(f"❌ Analysis and storage failed: {e}")
                            st.session_state.articles = []
                
                metadata = {
                    'timestamp': datetime.now().isoformat(),
                    'articles_collected': len(collected_articles),
                    'negative_count': sum(1 for a in st.session_state.articles if a.get('sentiment_category') == 'Negative'),
                    'positive_count': sum(1 for a in st.session_state.articles if a.get('sentiment_category') == 'Positive')
                }
                st.session_state.last_run_metadata = metadata
                
                # Auto-save functionality removed - all data stored in database

            except Exception as e:
                status_text.error(f"❌ An error occurred: {e}")
            
            st.markdown("---")
            st.subheader("📰 Analysis Results")
            if st.session_state.articles:
                st.success(f"Found and analyzed {len(st.session_state.articles)} articles.")
                
                # Display comprehensive analysis summary if available
                if hasattr(st.session_state, 'last_analysis_results'):
                    analysis_results = st.session_state.last_analysis_results
                    
                    # Create tabs for different views
                    summary_tab, articles_tab = st.tabs(["📊 Summary", "📰 Articles"])
                    
                    with summary_tab:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Articles", analysis_results['analysis_summary']['total_articles'])
                        
                        with col2:
                            sentiment_summary = analysis_results['sentiment_summary']
                            st.metric("Avg Sentiment", f"{sentiment_summary['average_sentiment_score']:.3f}")
                        
                        with col3:
                            risk_summary = analysis_results['risk_summary']
                            st.metric("Avg Risk Score", f"{risk_summary['average_risk_score']:.3f}")
                        
                        with col4:
                            storage_stats = analysis_results['analysis_summary']['storage_stats']
                            storage_type = analysis_results['analysis_summary']['storage_type']
                            if storage_type == "analysis_db" or storage_type == "pinecone":
                                st.metric("Sentiment DB", f"{storage_stats['success_count']}/{storage_stats['total_count']}", help="Stored in sentiment-db")
                            elif storage_type == "failed":
                                st.metric("Storage Failed", f"{storage_stats['success_count']}/{storage_stats['total_count']}", help="Failed to store in sentiment-db")
                            else:
                                st.metric("Unknown Status", f"{storage_stats['success_count']}/{storage_stats['total_count']}", help="Storage status unclear")
                        
                        # Additional metrics row
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Positive Articles", sentiment_summary['positive_count'])
                        with col2:
                            st.metric("Negative Articles", sentiment_summary['negative_count'])
                        with col3:
                            st.metric("Neutral Articles", sentiment_summary['neutral_count'])
                        with col4:
                            st.metric("Avg Confidence", f"{risk_summary['average_confidence']:.3f}")
                        
                        # Sentiment distribution only
                        st.subheader("Sentiment Distribution")
                        sentiment_dist = sentiment_summary['sentiment_distribution']
                        if sentiment_dist:
                            sentiment_df = pd.DataFrame(list(sentiment_dist.items()), columns=['Category', 'Count'])
                            fig = px.pie(sentiment_df, values='Count', names='Category', 
                                       color='Category',
                                       color_discrete_map={'Negative': '#E74C3C', 'Positive': '#2ECC71', 'Neutral': '#3498DB'},
                                       title="Article Sentiment Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with articles_tab:
                        for article in st.session_state.articles:
                            display_article_card(article)
                else:
                    # Fallback to simple article display
                    for article in st.session_state.articles:
                        display_article_card(article)
            else:
                st.warning("No articles found matching your criteria.")



    # --- AI Financial Assistant View ---
    elif st.session_state.current_page == "rag_chat":
        st.title("🤖 AI Financial Assistant")
        st.markdown("Chat with AI about your stored financial data and get insights.")
        
        # Initialize RAG service and load data asynchronously
        try:
            # Initialize RAG service only once (lazy loading)
            if st.session_state.rag_service is None:
                # Initialize RAG service lazily with progress indicator
                if 'rag_init_started' not in st.session_state:
                    st.session_state.rag_init_started = True
                    st.session_state.rag_init_complete = False
                
                # Show loading state and initialize
                if not st.session_state.get('rag_init_complete', False):
                    with st.spinner("🔄 Initializing AI Financial Assistant..."):
                        try:
                            from risk_monitor.core.rag_service import RAGService
                            st.session_state.rag_service = RAGService()
                            st.session_state.rag_init_complete = True
                        except Exception as e:
                            st.session_state.rag_init_error = str(e)
                            st.session_state.rag_init_complete = True
            
            # Load database stats only when needed (lazy loading)
            if st.session_state.db_stats is None and st.session_state.rag_service:
                if 'db_stats_init_started' not in st.session_state:
                    st.session_state.db_stats_init_started = True
                    st.session_state.db_stats_init_complete = False
                
                # Show loading state and load stats
                if not st.session_state.get('db_stats_init_complete', False):
                    with st.spinner("📊 Loading database statistics..."):
                        try:
                            st.session_state.db_stats = st.session_state.rag_service.get_database_stats()
                            st.session_state.db_stats_init_complete = True
                        except Exception as e:
                            st.session_state.db_stats_error = str(e)
                            st.session_state.db_stats_init_complete = True
            
            # Load NASDAQ companies list only once (lightweight, can be synchronous)
            if st.session_state.nasdaq_companies is None:
                st.session_state.nasdaq_companies = get_nasdaq_100_companies()
            
            # Check for initialization errors
            if st.session_state.get('rag_init_error'):
                st.error(f"❌ Failed to initialize AI Financial Assistant: {st.session_state.rag_init_error}")
                st.stop()
            
            if st.session_state.get('db_stats_error'):
                st.error(f"❌ Failed to load database statistics: {st.session_state.db_stats_error}")
                st.stop()
            
            # Display database info with filters (only when fully loaded)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Articles", st.session_state.db_stats.get('total_articles', 0))
            
            # Add filter dropdowns in place of Index Dimension and Index Fullness
            with col2:
                # Company/Entity filter with NASDAQ-100 companies and custom input
                try:
                    # Use cached NASDAQ-100 companies list
                    nasdaq_100_companies = st.session_state.nasdaq_companies
                    
                    # Create dropdown options with NASDAQ-100 companies
                    dropdown_options = [f"{symbol} - {name}" for symbol, name in nasdaq_100_companies]
                    dropdown_options.insert(0, "All Companies")
                    
                    # Add custom company input option
                    dropdown_options.append("➕ Enter Custom Company...")
                    
                    selected_company_option = st.selectbox(
                        "🏢 Select Company/Entity",
                        options=dropdown_options,
                        index=0,
                        help="Choose from NASDAQ-100 companies or enter a custom company name"
                    )
                    
                    # Handle custom company input
                    if selected_company_option == "➕ Enter Custom Company...":
                        custom_company = st.text_input(
                            "Enter custom company name or ticker:",
                            placeholder="e.g., TSLA, Tesla, or any company name",
                            help="Enter any company name or stock ticker symbol"
                        )
                        selected_company = custom_company if custom_company.strip() else "All Companies"
                    elif selected_company_option == "All Companies":
                        selected_company = "All Companies"
                    else:
                        # Extract symbol from NASDAQ-100 selection
                        selected_company = selected_company_option.split(" - ")[0]
                        
                except Exception as e:
                    st.error(f"Error loading companies: {e}")
                    selected_company = "All Companies"
            
            with col3:
                # Calendar date selector only
                try:
                    # Get available dates from database
                    available_dates = st.session_state.rag_service.get_available_dates()
                    
                    # Convert available dates to datetime objects for min/max
                    available_datetimes = []
                    if available_dates:
                        for date_str in available_dates:
                            try:
                                available_datetimes.append(datetime.strptime(date_str, "%Y-%m-%d").date())
                            except:
                                continue
                    
                    # Set min/max dates for calendar
                    min_date = min(available_datetimes) if available_datetimes else datetime.now().date() - timedelta(days=365)
                    max_date = max(available_datetimes) if available_datetimes else datetime.now().date()
                    
                    # Default to today's date
                    default_date = datetime.now().date()
                    
                    # Use calendar picker
                    selected_calendar_date = st.date_input(
                        "📅 Select Date",
                        value=default_date,
                        min_value=min_date,
                        max_value=max_date,
                        help="Use the calendar to pick a specific date"
                    )
                    
                    # Convert to string format
                    selected_date = selected_calendar_date.strftime("%Y-%m-%d")
                        
                except Exception as e:
                    st.error(f"Error loading dates: {e}")
                    # Fallback to today's date
                    selected_date = datetime.now().strftime("%Y-%m-%d")
            
            # NEW FLOW: Require both filters to be selected
            st.markdown("---")
            
            # Check if both filters are selected (required for new flow)
            if selected_company == "All Companies":
                st.warning("⚠️ **Required:** Please select a Company/Entity before asking questions.")
                st.markdown("---")
                return  # Don't show chat interface until company filter is selected
            
            # Show active filters
            st.success(f"✅ **Active Filters:** Company: {selected_company} | Date: {selected_date}")
            
            st.markdown("---")
            
            # Initialize chat history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Render chat history using Streamlit's native chat_message (inspired by banking AI)
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]):
                    if chat["role"] == "assistant":
                        # Show articles used count for AI messages
                        articles_used = chat.get('articles_used', 0)
                        if articles_used > 0:
                            st.caption(f"📰 Analyzed {articles_used} articles from your database")
                        st.markdown(chat["content"])
                    else:
                        st.markdown(chat["content"])
            
            # Chat input using Streamlit's native chat_input (inspired by banking AI)
            user_query = st.chat_input("Ask about companies, market sentiment, risks, or financial insights...")
            
            if user_query:
                # Display user message immediately (like banking AI)
                with st.chat_message("user"):
                    st.markdown(user_query)
                
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "role": "user", 
                    "type": "text", 
                    "content": user_query,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Limit chat history to 10 conversations (20 messages: 10 user + 10 AI)
                if len(st.session_state.chat_history) >= 20:
                    st.session_state.chat_history = st.session_state.chat_history[2:]
                
                # Get AI response with context from previous messages
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Analyzing your financial data..."):
                        # Pass conversation context to RAG service
                        conversation_context = ""
                        if len(st.session_state.chat_history) > 1:
                            # Include last few messages for context
                            recent_messages = st.session_state.chat_history[-6:]  # Last 3 exchanges
                            conversation_context = "\n".join([
                                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                                for msg in recent_messages[:-1]  # Exclude current user message
                            ])
                        
                        # Use raw query format with conversation context and filters
                        raw_query = user_query.strip()
                        if conversation_context:
                            enhanced_query = f"Context from previous conversation:\n{conversation_context}\n\nCurrent question: {raw_query}"
                        else:
                            enhanced_query = raw_query
                        
                        # Apply filters to the query
                        entity_filter = selected_company if selected_company != "All Companies" else None
                        date_filter = selected_date  # Always a specific date now
                        
                        response = st.session_state.rag_service.chat_with_agent(
                            enhanced_query, 
                            conversation_context=conversation_context,
                            entity_filter=entity_filter,
                            date_filter=date_filter
                        )
                        
                        # Show articles used count and filters
                        articles_used = response.get('articles_used', 0)
                        if articles_used > 0:
                            filter_info = []
                            if response.get('entity_filter_applied'):
                                filter_info.append(f"Company: {response['entity_filter_applied']}")
                            if response.get('date_filter_applied'):
                                filter_info.append(f"Date: {response['date_filter_applied']}")
                            
                            if filter_info:
                                st.caption(f"📰 Analyzed {articles_used} articles from your database (Filters: {', '.join(filter_info)})")
                            else:
                                st.caption(f"📰 Analyzed {articles_used} articles from your database")
                        
                        # Add AI response to history
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "type": "text", 
                            "content": response['response'],
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "articles_used": articles_used
                        })
                        
                        st.markdown(response['response'])
            
            # Clear chat button
            if st.session_state.chat_history:
                st.markdown("---")
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Clear", type="secondary"):
                        st.session_state.chat_history = []
                        st.rerun()
            
            # Show recent articles used with detailed metadata
            if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'assistant':
                last_response = st.session_state.chat_history[-1]
                if 'articles_used' in last_response and last_response['articles_used'] > 0:
                    st.markdown("---")
                    st.markdown("### 📰 Data Sources Used")
                    st.markdown("*These are the actual articles from your database that were analyzed to generate the response above.*")
                    
                    # Get ALL the articles from the last response (no limit)
                    if hasattr(st.session_state.rag_service, 'last_articles') and st.session_state.rag_service.last_articles:
                        total_articles = len(st.session_state.rag_service.last_articles)
                        st.markdown(f"**📊 Total References Analyzed: {total_articles} articles**")
                        
                        # Show sentiment distribution
                        sentiment_counts = {}
                        for article in st.session_state.rag_service.last_articles:
                            sentiment = article.get('sentiment_category', 'Unknown')
                            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                        
                        if sentiment_counts:
                            st.markdown("**📈 Sentiment Distribution:**")
                            for sentiment, count in sentiment_counts.items():
                                st.markdown(f"- {sentiment}: {count} articles")
                        
                        st.markdown("---")
                        
                        # Display ALL articles with pagination for better UX
                        articles_per_page = 5
                        total_pages = (total_articles + articles_per_page - 1) // articles_per_page
                        
                        if total_pages > 1:
                            page = st.selectbox(
                                "Select page to view references:",
                                options=range(1, total_pages + 1),
                                format_func=lambda x: f"Page {x} (References {(x-1)*articles_per_page + 1}-{min(x*articles_per_page, total_articles)})"
                            )
                            start_idx = (page - 1) * articles_per_page
                            end_idx = min(start_idx + articles_per_page, total_articles)
                            current_articles = st.session_state.rag_service.last_articles[start_idx:end_idx]
                        else:
                            current_articles = st.session_state.rag_service.last_articles
                        
                        # Display current page articles
                        for i, article in enumerate(current_articles, start_idx + 1 if total_pages > 1 else 1):
                            sentiment = article.get('sentiment_category', 'Unknown').lower()
                            badge_class = f"badge-{sentiment}"
                            
                            with st.expander(f"📄 [REFERENCE {i}] {article.get('title', 'Unknown')}", expanded=False):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    # Handle source information properly
                                    source_info = article.get('source', {})
                                    if isinstance(source_info, dict):
                                        source_name = source_info.get('name', 'Unknown')
                                        authors = source_info.get('authors', [])
                                        source_display = source_name
                                        if authors:
                                            authors_str = ', '.join(authors) if isinstance(authors, list) else str(authors)
                                            source_display += f" by {authors_str}"
                                    else:
                                        source_display = str(source_info) if source_info else 'Unknown'
                                    
                                    st.markdown(f"**Source:** {source_display}")
                                    st.markdown(f"**URL:** {article.get('url', 'N/A')}")
                                    st.markdown(f"**Published:** {article.get('publish_date', 'Unknown')}")
                                    if article.get('authors'):
                                        st.markdown(f"**Authors:** {', '.join(article.get('authors', []))}")
                                
                                with col2:
                                    st.markdown(f"**Sentiment:** <span class='badge {badge_class}'>{article.get('sentiment_category', 'Unknown').upper()}</span>", unsafe_allow_html=True)
                                    st.markdown(f"**Sentiment Score:** `{article.get('sentiment_score', 0)}`")
                                    st.markdown(f"**Risk Score:** `{article.get('risk_score', 0)}`")
                                
                                st.markdown("**Summary:**")
                                st.info(article.get('summary', 'No summary available'))
                                
                                # Enhanced Insight Display for RAG
                                st.markdown("---")
                                st.markdown("### 🧠 **Sentiment Analysis Insight**")
                                
                                # Check for different types of sentiment analysis data
                                sentiment_data = article.get('sentiment_analysis', {})
                                
                                # Priority order: reasoning > justification > key_factors > market_impact
                                insight_text = None
                                insight_source = None
                                
                                if isinstance(sentiment_data, dict):
                                    # Structured analysis with reasoning
                                    if sentiment_data.get('reasoning'):
                                        insight_text = sentiment_data.get('reasoning')
                                        insight_source = "Structured Analysis"
                                    # LLM analysis with justification
                                    elif sentiment_data.get('justification'):
                                        insight_text = sentiment_data.get('justification')
                                        insight_source = "LLM Analysis"
                                    # Key factors
                                    elif sentiment_data.get('key_factors'):
                                        factors = sentiment_data.get('key_factors', [])
                                        if isinstance(factors, list) and factors:
                                            insight_text = f"Key factors: {', '.join(factors)}"
                                            insight_source = "LLM Analysis"
                                    # Market impact
                                    elif sentiment_data.get('market_impact'):
                                        insight_text = sentiment_data.get('market_impact')
                                        insight_source = "LLM Analysis"
                                
                                # Fallback to direct article fields
                                if not insight_text:
                                    if article.get('sentiment_justification'):
                                        insight_text = article.get('sentiment_justification')
                                        insight_source = "LLM Analysis"
                                    elif article.get('reasoning'):
                                        insight_text = article.get('reasoning')
                                        insight_source = "Structured Analysis"
                                
                                # Display the insight
                                if insight_text:
                                    st.success(f"**💡 Insight ({insight_source}):** {insight_text}")
                                    
                                    # Additional details if available
                                    if isinstance(sentiment_data, dict):
                                        if sentiment_data.get('confidence'):
                                            st.markdown(f"**Confidence Level:** `{sentiment_data.get('confidence', 'N/A')}`")
                                        
                                        if sentiment_data.get('entity'):
                                            st.markdown(f"**Main Entity:** `{sentiment_data.get('entity', 'N/A')}`")
                                        
                                        if sentiment_data.get('event_type'):
                                            st.markdown(f"**Event Type:** `{sentiment_data.get('event_type', 'N/A')}`")
                                        
                                        if sentiment_data.get('key_quotes'):
                                            quotes = sentiment_data.get('key_quotes', [])
                                            if quotes and isinstance(quotes, list) and quotes:
                                                st.markdown("**Key Evidence:**")
                                                for j, quote in enumerate(quotes[:3], 1):  # Show max 3 quotes
                                                    st.markdown(f"• {quote}")
                                else:
                                    # Fallback to lexicon analysis
                                    positive_count = article.get('positive_count', 0)
                                    negative_count = article.get('negative_count', 0)
                                    st.info(f"**📊 Lexicon Analysis:** Found {positive_count} positive and {negative_count} negative financial indicators.")
                                    if positive_count > negative_count:
                                        st.markdown("*Overall positive sentiment due to more positive financial indicators.*")
                                    elif negative_count > positive_count:
                                        st.markdown("*Overall negative sentiment due to more negative financial indicators.*")
                                    else:
                                        st.markdown("*Neutral sentiment due to balanced positive and negative indicators.*")
                                
                                if article.get('keywords'):
                                    st.markdown("**Keywords:**")
                                    st.write(', '.join(article.get('keywords', [])))
                                
                                st.markdown("**Full Text (excerpt):**")
                                article_text = article.get('text', 'No text available')
                                if article_text:
                                    st.text_area(
                                        "Article Content",
                                        value=article_text[:1000] + "..." if len(article_text) > 1000 else article_text,
                                        height=200,
                                        disabled=True,
                                        help="Article text excerpt with proper word wrapping",
                                        key=f"article_content_rag_{i}_{hash(article.get('title', ''))}"
                                    )
                                else:
                                    st.info("No article text available.")
                        
                        # Show pagination info if needed
                        if total_pages > 1:
                            st.markdown(f"*Showing page {page} of {total_pages} (References {start_idx + 1}-{end_idx} of {total_articles})*")
        
        except ImportError:
            st.error("❌ RAG service not available. Please ensure all dependencies are installed.")
        except Exception as e:
            st.error(f"❌ Error initializing RAG service: {str(e)}")

    # --- Scheduler Configuration View ---
    elif st.session_state.current_page == "scheduler_config":
        st.markdown('<div class="custom-container"><h2 style="margin: 0;">⏰ Scheduler Configuration</h2><p style="margin: 0.25rem 0 0; color: #4b5563;">Configure automated news collection and analysis scheduling.</p></div>', unsafe_allow_html=True)
        
        # Load current configuration
        config = load_scheduler_config()
        
        # Create tabs for different configuration sections
        schedule_tab, entities_tab, analysis_tab, email_tab, monitoring_tab = st.tabs(["⏰ Schedule", "🏢 Companies", "🔍 Analysis", "📧 Email", "📊 Monitoring"])
        
        with schedule_tab:
            st.subheader("Daily Schedule Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                run_time = st.time_input(
                    "Daily Run Time",
                    value=datetime.strptime(config.get("run_time", "08:00"), "%H:%M").time(),
                    help="Time when the scheduler will run daily"
                )
                config["run_time"] = run_time.strftime("%H:%M")
            
            with col2:
                timezone_options = [
                    "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
                    "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai",
                    "UTC"
                ]
                timezone = st.selectbox(
                    "Timezone",
                    options=timezone_options,
                    index=timezone_options.index(config.get("timezone", "US/Eastern")) if config.get("timezone") in timezone_options else 0,
                    help="Timezone for the scheduled run"
                )
                config["timezone"] = timezone
            
            articles_per_entity = st.number_input(
                "Articles per Company",
                min_value=1,
                max_value=20,
                value=config.get("articles_per_entity", 5),
                help="Number of articles to collect per company"
            )
            config["articles_per_entity"] = articles_per_entity
            
        with entities_tab:
            st.subheader("Companies to Monitor")
            st.markdown("Configure which companies the scheduler should monitor for news.")
            
            # Default entities
            default_entities = ["NVDA", "NVIDIA CORPORATION", "MSFT", "MICROSOFT CORP", "AAPL", "APPLE INC.", "AVGO", "BROADCOM INC.", "META", "META PLATFORMS INC", "AMZN", "AMAZON.COM INC"]
            
            # Initialize session state for companies input if not exists
            if "companies_input" not in st.session_state:
                st.session_state.companies_input = "\n".join(config.get("entities", default_entities))
            
            entities_input = st.text_area(
                "Companies (one per line)",
                value=st.session_state.companies_input,
                height=200,
                help="Enter company names or stock symbols, one per line",
                key="companies_textarea"
            )
            config["entities"] = [e.strip() for e in entities_input.split("\n") if e.strip()]
            
            st.info(f"Currently monitoring {len(config['entities'])} companies")
            
            # NASDAQ-100 companies dropdown
            st.markdown("**Add Companies from NASDAQ-100:**")
            
            # NASDAQ-100 companies list (cleaned and deduplicated)
            nasdaq_100_companies = [
                ("AAPL", "Apple Inc"),
                ("ADBE", "Adobe Inc"),
                ("ADI", "Analog Devices Inc"),
                ("ADP", "Automatic Data Processing Inc"),
                ("ADSK", "Autodesk Inc"),
                ("AEP", "American Electric Power Company Inc"),
                ("ALGN", "Align Technology Inc"),
                ("AMAT", "Applied Materials Inc"),
                ("AMD", "Advanced Micro Devices Inc"),
                ("AMGN", "Amgen Inc"),
                ("AMZN", "Amazon.com Inc"),
                ("ANSS", "ANSYS Inc"),
                ("ASML", "ASML Holding NV"),
                ("ATVI", "Activision Blizzard Inc"),
                ("AVGO", "Broadcom Inc"),
                ("AZN", "AstraZeneca PLC"),
                ("BIIB", "Biogen Inc"),
                ("BKNG", "Booking Holdings Inc"),
                ("BKR", "Baker Hughes Company"),
                ("CDNS", "Cadence Design Systems Inc"),
                ("CEG", "Constellation Energy Corp"),
                ("CHTR", "Charter Communications Inc"),
                ("CMCSA", "Comcast Corporation"),
                ("COST", "Costco Wholesale Corporation"),
                ("CPRT", "Copart Inc"),
                ("CRWD", "CrowdStrike Holdings Inc"),
                ("CSCO", "Cisco Systems Inc"),
                ("CSGP", "CoStar Group Inc"),
                ("CTAS", "Cintas Corporation"),
                ("CTSH", "Cognizant Technology Solutions Corp"),
                ("DDOG", "Datadog Inc"),
                ("DLTR", "Dollar Tree Inc"),
                ("DXCM", "DexCom Inc"),
                ("EA", "Electronic Arts Inc"),
                ("EBAY", "eBay Inc"),
                ("ENPH", "Enphase Energy Inc"),
                ("EXC", "Exelon Corporation"),
                ("FANG", "Diamondback Energy Inc"),
                ("FAST", "Fastenal Company"),
                ("FTNT", "Fortinet Inc"),
                ("GILD", "Gilead Sciences Inc"),
                ("GOOG", "Alphabet Inc Class C"),
                ("GOOGL", "Alphabet Inc Class A"),
                ("HON", "Honeywell International Inc"),
                ("IDXX", "IDEXX Laboratories Inc"),
                ("ILMN", "Illumina Inc"),
                ("INTC", "Intel Corporation"),
                ("INTU", "Intuit Inc"),
                ("ISRG", "Intuitive Surgical Inc"),
                ("JD", "JD.com Inc"),
                ("KLAC", "KLA Corporation"),
                ("LCID", "Lucid Group Inc"),
                ("LRCX", "Lam Research Corporation"),
                ("LULU", "Lululemon Athletica Inc"),
                ("MAR", "Marriott International Inc"),
                ("MCHP", "Microchip Technology Inc"),
                ("MDLZ", "Mondelez International Inc"),
                ("MELI", "MercadoLibre Inc"),
                ("META", "Meta Platforms Inc"),
                ("MNST", "Monster Beverage Corporation"),
                ("MRVL", "Marvell Technology Inc"),
                ("MSFT", "Microsoft Corporation"),
                ("MU", "Micron Technology Inc"),
                ("NFLX", "Netflix Inc"),
                ("NVDA", "NVIDIA Corporation"),
                ("NXPI", "NXP Semiconductors NV"),
                ("ODFL", "Old Dominion Freight Line Inc"),
                ("OKTA", "Okta Inc"),
                ("ORCL", "Oracle Corporation"),
                ("PANW", "Palo Alto Networks Inc"),
                ("PAYX", "Paychex Inc"),
                ("PCAR", "PACCAR Inc"),
                ("PEP", "PepsiCo Inc"),
                ("PLTR", "Palantir Technologies Inc"),
                ("PYPL", "PayPal Holdings Inc"),
                ("QCOM", "QUALCOMM Incorporated"),
                ("REGN", "Regeneron Pharmaceuticals Inc"),
                ("ROST", "Ross Stores Inc"),
                ("SBUX", "Starbucks Corporation"),
                ("SGEN", "Seagen Inc"),
                ("SIRI", "Sirius XM Holdings Inc"),
                ("SNPS", "Synopsys Inc"),
                ("TEAM", "Atlassian Corporation"),
                ("TMUS", "T-Mobile US Inc"),
                ("TSLA", "Tesla Inc"),
                ("TXN", "Texas Instruments Incorporated"),
                ("VRTX", "Vertex Pharmaceuticals Inc"),
                ("WBA", "Walgreens Boots Alliance Inc"),
                ("WDAY", "Workday Inc"),
                ("XEL", "Xcel Energy Inc"),
                ("ZM", "Zoom Video Communications Inc"),
                ("ZS", "Zscaler Inc")
            ]
            
            # Remove duplicates and sort
            unique_companies = []
            seen_symbols = set()
            for symbol, name in nasdaq_100_companies:
                if symbol not in seen_symbols:
                    unique_companies.append((symbol, name))
                    seen_symbols.add(symbol)
            
            # Sort by symbol
            unique_companies.sort(key=lambda x: x[0])
            
            # Create dropdown for NASDAQ-100 companies
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Create options for dropdown
                dropdown_options = [f"{symbol} - {name}" for symbol, name in unique_companies]
                selected_company = st.selectbox(
                    "Select a NASDAQ-100 company to add:",
                    options=["Select a company..."] + dropdown_options,
                    help="Choose from the top 100 companies listed on NASDAQ"
                )
            
            with col2:
                if st.button("➕ Add Selected", type="primary", disabled=selected_company == "Select a company..."):
                    if selected_company != "Select a company...":
                        # Use full entity name (e.g., "AAPL - Apple Inc")
                        full_entity_name = selected_company
                        if full_entity_name not in config["entities"]:
                            config["entities"].append(full_entity_name)
                            # Update the companies input field
                            st.session_state.companies_input = "\n".join(config["entities"])
                            st.success(f"✅ Added {full_entity_name}")
                            st.rerun()
                    else:
                        st.warning(f"⚠️ {full_entity_name} is already in the list")
        
        with analysis_tab:
            st.subheader("Analysis Configuration")
            
            # Keywords configuration
            st.markdown("**Keyword Filtering**")
            default_keywords = ["risk", "financial", "market", "crisis", "volatility", "earnings", "revenue", "stock", "trading", "investment"]
            keywords_input = st.text_area(
                "Keywords (one per line)",
                value="\n".join(config.get("keywords", default_keywords)),
                height=150,
                help="Only articles containing these keywords will be analyzed",
                key="keywords_input_scheduler"
            )
            config["keywords"] = [k.strip() for k in keywords_input.split("\n") if k.strip()]
            
            st.markdown("**Analysis Options**")
            col1, col2 = st.columns(2)
            
            with col1:
                use_openai = st.checkbox(
                    "Enable OpenAI LLM Analysis",
                    value=config.get("use_openai", True),
                    help="Use OpenAI for advanced sentiment analysis"
                )
                config["use_openai"] = use_openai
            
                enable_dual_sentiment = st.checkbox(
                    "Enable Dual Sentiment Analysis",
                    value=config.get("enable_dual_sentiment", True),
                    help="Perform both lexicon and LLM sentiment analysis"
                )
                config["enable_dual_sentiment"] = enable_dual_sentiment
            
            with col2:
                enable_pinecone_storage = st.checkbox(
                    "Enable Pinecone Vector Storage",
                    value=config.get("enable_pinecone_storage", True),
                    help="Store articles in Pinecone vector database"
                )
            config["enable_pinecone_storage"] = enable_pinecone_storage
        
        with email_tab:
            st.subheader("Email Notification Settings")
            
            email_enabled = st.checkbox(
                "Enable Email Notifications",
                value=config.get("email_enabled", True),
                help="Send daily email reports"
            )
            config["email_enabled"] = email_enabled
            
            if email_enabled:
                enable_detailed_email = st.checkbox(
                    "Enable Detailed Email Reports",
                    value=config.get("enable_detailed_email", True),
                    help="Include detailed analysis and article summaries in emails"
                )
                config["enable_detailed_email"] = enable_detailed_email
                
                # Email recipients
                recipients_input = st.text_area(
                    "Email Recipients (one per line)",
                    value="\n".join(config.get("email_recipients", ["be2020se709@gces.edu.np"])),
                    height=100,
                    help="Email addresses to receive daily reports",
                    key="email_recipients_input"
                )
                config["email_recipients"] = [r.strip() for r in recipients_input.split("\n") if r.strip()]
                
                # Email configuration status
                st.markdown("**Email Configuration Status:**")
                try:
                    smtp_host = Config.get_smtp_host()
                    smtp_user = Config.get_smtp_user()
                    email_from = Config.get_email_from()
                    
                    if smtp_host and smtp_user and email_from:
                        st.success(f"✅ Email configured: {email_from} via {smtp_host}")
                    else:
                        st.warning("⚠️ Email not fully configured. Check .streamlit/secrets.toml")
                except Exception as e:
                    st.error(f"❌ Email configuration error: {e}")
        
        with monitoring_tab:
            st.subheader("Scheduler Status & Monitoring")
            
            # Check scheduler status
            is_running, process_ids, status_info = get_scheduler_status()
            
            # Display detailed scheduler status
            st.markdown("**📊 Scheduler Status:**")
            
            # Real-time status indicator
            if is_running:
                st.markdown("""
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3 style="color: #155724; margin: 0;">🟢 SCHEDULER ACTIVE</h3>
                    <p style="color: #155724; margin: 0.5rem 0 0;">The scheduler is currently running in the background and monitoring your configured companies.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3 style="color: #721c24; margin: 0;">🔴 SCHEDULER INACTIVE</h3>
                    <p style="color: #721c24; margin: 0.5rem 0 0;">The scheduler is not running. Use the commands below to start it.</p>
                </div>
                """, unsafe_allow_html=True)
            
                col1, col2 = st.columns(2)
                with col1:
                    if is_running:
                        st.success(f"✅ **ACTIVE** - Scheduler is running")
                        st.info(f"**Process IDs:** {', '.join(process_ids)}")
                    else:
                        st.error("❌ **INACTIVE** - Scheduler is not running")
                        st.warning("No background scheduler process detected")
                
                with col2:
                    if st.button("🔄 Refresh Status", type="secondary"):
                        st.rerun()
            
            # Additional status information
            st.markdown("**📋 Status Details:**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Last run information
                if status_info.get('last_run'):
                    last_run = status_info['last_run']
                    st.metric(
                        label="Last Run",
                        value=last_run.strftime("%H:%M"),
                        delta=f"{last_run.strftime('%Y-%m-%d')}"
                    )
                else:
                    st.metric(label="Last Run", value="Unknown")
            
            with col2:
                # Log file status
                log_status = "✅ Available" if status_info.get('log_file_exists') else "❌ Missing"
                st.metric(label="Log File", value=log_status)
            
            with col3:
                # Background log status
                bg_log_status = "✅ Available" if status_info.get('background_log_exists') else "❌ Missing"
                st.metric(label="Background Log", value=bg_log_status)
        
            with col2:
                if st.button("Refresh Status", type="secondary"):
                    st.rerun()
            
            # Email subscription controls
            st.markdown("**Email Subscription Controls:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📧 Subscribe to Email Reports", type="primary"):
                    success, message = update_email_subscription(True)
                    if success:
                        st.success("✅ Email subscription enabled! You will receive daily reports.")
                        st.rerun()
                    else:
                        st.error(f"❌ Error enabling email: {message}")
            
            with col2:
                if st.button("📧 Unsubscribe from Email Reports", type="secondary"):
                    success, message = update_email_subscription(False)
                    if success:
                        st.success("✅ Email subscription disabled! Daily news collection and analysis will continue.")
                        st.rerun()
                    else:
                        st.error(f"❌ Error disabling email: {message}")
            
            # Current email status
            email_status = "🟢 Enabled" if config.get("email_enabled", False) else "🔴 Disabled"
            st.info(f"**Current Email Status:** {email_status}")
            
            # Scheduler control information
            st.markdown("**Scheduler Controls:**")
            
            # Create columns for control buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 Restart Scheduler", type="primary", help="Stop and restart the scheduler with current configuration"):
                    with st.spinner("Restarting scheduler..."):
                        success, message = restart_scheduler()
                        if success:
                            st.success(message)
                            time.sleep(1)  # Brief pause to let process start
                            st.rerun()
                        else:
                            st.error(message)
            
            with col2:
                if st.button("▶️ Start Scheduler", type="secondary", help="Start the scheduler if it's not running"):
                    with st.spinner("Starting scheduler..."):
                        success, message = start_scheduler()
                        if success:
                            st.success(message)
                            time.sleep(1)  # Brief pause to let process start
                            st.rerun()
                        else:
                            st.error(message)
            
            with col3:
                if st.button("⏹️ Stop Scheduler", type="secondary", help="Stop the currently running scheduler"):
                    with st.spinner("Stopping scheduler..."):
                        success, message = stop_scheduler()
                        if success:
                            st.success(message)
                            time.sleep(1)  # Brief pause to let process stop
                            st.rerun()
                        else:
                            st.error(message)
            
            with col4:
                if st.button("🔄 Refresh Status", type="secondary", help="Refresh scheduler status"):
                    st.rerun()
            
            st.info("""
            **Note:** 
            - Restarting the scheduler will apply your configuration changes immediately
            - Daily news collection and analysis will continue regardless of email subscription status
            - The scheduler runs in the background and will automatically restart on system reboot
            """)
            
            # Log monitoring
            st.markdown("**Recent Logs:**")
            log_files = ["logs/scheduler.log", "scheduler_background.log"]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-10:] if len(lines) > 10 else lines
                        
                        with st.expander(f"📄 {log_file} (last 10 lines)"):
                            st.code("".join(recent_lines), language="text")
                    except Exception as e:
                        st.warning(f"Could not read {log_file}: {e}")
        
        # Save configuration section
        st.markdown("---")
        st.subheader("💾 Save Configuration")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info("""
            💡 **Configuration Changes:**
            - Click 'Save Configuration' to save your changes
            - **Important:** After changing entities or major settings, use 'Restart Scheduler' to apply changes
            - The scheduler will continue running with old configuration until restarted
            """)
        
        with col2:
            if st.button("💾 Save Configuration", type="primary"):
                success, message = save_scheduler_config(config)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
        
        with col3:
            if st.button("🔄 Reset to Defaults", type="secondary"):
                # Reset to default configuration
                default_config = {
                    "run_time": "08:00",
                    "timezone": "US/Eastern",
                    "articles_per_entity": 5,
                    "entities": ["NVDA", "NVIDIA CORPORATION", "MSFT", "MICROSOFT CORP", "AAPL", "APPLE INC.", "AVGO", "BROADCOM INC.", "META", "META PLATFORMS INC", "AMZN", "AMAZON.COM INC"],
                    "keywords": ["risk", "financial", "market", "crisis", "volatility", "earnings", "revenue", "stock", "trading", "investment"],
                    "use_openai": True,
                    "email_enabled": True,
                    "email_recipients": ["be2020se709@gces.edu.np"],
                    "enable_pinecone_storage": True,
                    "enable_dual_sentiment": True,
                    "enable_detailed_email": True
                }
                success, message = save_scheduler_config(default_config)
                if success:
                    st.success("Configuration reset to defaults!")
                    st.rerun()
                else:
                    st.error(f"Error resetting configuration: {message}")
        
        # Configuration preview
        st.markdown("---")
        st.subheader("📋 Configuration Preview")
        with st.expander("View Current Configuration JSON", expanded=False):
            st.json(config)
    
    # Copyright footer - sticky at bottom
    st.markdown("""
    <div class="sticky-footer">
        <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">
            © 2025 Er. Bibit Kunwar Chhetri. All rights reserved.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Add caching for better performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_analysis_results(articles_hash: str, sentiment_method: str):
    """Cache analysis results to improve performance"""
    return None  # Will be populated by actual analysis

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_cached_sentiment_distribution(articles: List[Dict]):
    """Cache sentiment distribution calculation"""
    positive_count = sum(1 for a in articles if a.get('sentiment_category') == 'Positive')
    negative_count = sum(1 for a in articles if a.get('sentiment_category') == 'Negative')
    neutral_count = len(articles) - positive_count - negative_count
    
    return {
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count,
        'total': len(articles)
    }

# Entry point of the script
if __name__ == "__main__":
    main()
