#!/usr/bin/env python3
"""
Streamlit Web Application for Risk Monitoring Tool
Provides an interactive web interface for collecting and analyzing financial news
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime
import time
from typing import Dict, List, Optional
import PyPDF2
import io
import logging
import re
import requests
import openai

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
from risk_analyzer import RiskAnalyzer
from config import Config

# Sentiment Analysis Configuration
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
    """
    Analyze sentiment using lexicon-based approach
    Returns: {'score': float, 'category': str, 'positive_count': int, 'negative_count': int}
    """
    if not text:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    
    # Convert to lowercase for matching
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count positive and negative words
    positive_count = sum(1 for word in FINANCE_POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in FINANCE_NEGATIVE_WORDS if word in text_lower)
    
    # Calculate total relevant words
    total_relevant = positive_count + negative_count
    
    if total_relevant == 0:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    
    # Calculate sentiment score: (Positive - Negative) / Total
    score = (positive_count - negative_count) / total_relevant
    
    # Categorize sentiment
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

async def analyze_sentiment_llm(text: str) -> Dict:
    """
    Analyze sentiment using OpenAI GPT-4o
    Returns: {'score': float, 'category': str, 'justification': str}
    """
    if not text:
        return {'score': 0.0, 'category': 'Neutral', 'justification': 'No text provided'}
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        prompt = f"""
You are a financial news sentiment analysis assistant. Analyze the sentiment of the following financial news article text. 
Provide your analysis in JSON format with the following structure:
{{
  "score": <numerical score between -1.0 and 1.0>,
  "justification": "<brief explanation of your sentiment analysis>"
}}

Article text:
{text[:2000]}

Focus on financial and market sentiment. Consider factors like:
- Market impact and investor sentiment
- Financial performance indicators
- Risk and opportunity assessment
- Overall market outlook
"""
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        response_text = response.choices[0].message.content
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        llm_result = json.loads(json_str)
        score = float(llm_result['score'])
        justification = llm_result['justification']
        # Categorize sentiment
        if score > 0.1:
            category = 'Positive'
        elif score < -0.1:
            category = 'Negative'
        else:
            category = 'Neutral'
        return {
            'score': round(score, 3),
            'category': category,
            'justification': justification
        }
    except Exception as e:
        st.warning(f"OpenAI sentiment analysis failed: {e}. Falling back to lexicon-based analysis.")
        return analyze_sentiment_lexicon(text)

def analyze_sentiment_sync(text: str, method: str = 'lexicon') -> Dict:
    """
    Synchronous wrapper for sentiment analysis
    """
    if method == 'lexicon':
        return analyze_sentiment_lexicon(text)
    elif method == 'llm':
        # For now, return lexicon-based as fallback since async isn't fully supported in Streamlit
        st.info("LLM-based sentiment analysis is being processed...")
        return analyze_sentiment_lexicon(text)
    else:
        return analyze_sentiment_lexicon(text)

# Page configuration
st.set_page_config(
    page_title="Risk Monitoring Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1.5rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid #e3f2fd;
    }
    .sub-header {
        font-size: 1.1rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .article-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .article-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .article-source {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .article-date {
        color: #888;
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }
    .article-text {
        color: #333;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    .article-link {
        color: #007bff;
        text-decoration: none;
    }
    .article-link:hover {
        text-decoration: underline;
    }
    .counterparty-tag {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .nav-button {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .nav-button:hover {
        background-color: #e9ecef;
        border-color: #adb5bd;
    }
    .nav-button.active {
        background-color: #1f77b4;
        color: white;
        border-color: #1f77b4;
    }
    /* Reduce font size and padding for all text inputs and text areas */
    .stTextInput input, .stTextArea textarea {
        font-size: 14px !important;
        padding: 4px 8px !important;
    }
    /* Reduce font size for headers */
    .main-header, .sub-header, h1, h2, h3, h4, h5, h6 {
        font-size: 1.2em !important;
        margin-bottom: 0.5em !important;
    }
    /* Reduce padding and margin for Streamlit containers */
    .st-cq, .st-b6, .st-cx, .st-cy, .stContainer, .block-container {
        padding: 8px !important;
        margin-bottom: 8px !important;
    }
    /* Reduce padding for text area and input widgets */
    textarea, input[type="text"], input[type="search"] {
        padding: 4px 8px !important;
        font-size: 14px !important;
    }
    /* Compact radio button group spacing */
    .stRadio > div[role='radiogroup'] > label {
        margin-bottom: 0.2rem !important;
        margin-top: 0.2rem !important;
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
    }
    /* Further reduce space below radio group */
    .stRadio {
        margin-bottom: 0.1rem !important;
    }
    /* Consistent font size for all items in Configure News Analysis */
    .stExpanderContent label,
    .stExpanderContent .stTextInput input,
    .stExpanderContent .stTextArea textarea,
    .stExpanderContent .stNumberInput input,
    .stExpanderContent .stRadio label,
    .stExpanderContent .stCheckbox,
    .stExpanderContent .stSlider,
    .stExpanderContent .stHelp {
        font-size: 1rem !important;
    }
    /* Sentiment analysis styling */
    .sentiment-positive {
        background-color: #d4edda !important;
        color: #155724 !important;
        border-left: 4px solid #28a745 !important;
    }
    .sentiment-negative {
        background-color: #f8d7da !important;
        color: #721c24 !important;
        border-left: 4px solid #dc3545 !important;
    }
    .sentiment-neutral {
        background-color: #e2e3e5 !important;
        color: #383d41 !important;
        border-left: 4px solid #6c757d !important;
    }
    .sentiment-container {
        padding: 0.5rem !important;
        border-radius: 0.25rem !important;
        margin-bottom: 0.5rem !important;
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'articles' not in st.session_state:
        st.session_state.articles = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'counterparties' not in st.session_state:
        st.session_state.counterparties = []
    if 'keywords' not in st.session_state:
        st.session_state.keywords = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "news_search"
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = ""
    if 'pdf_filename' not in st.session_state:
        st.session_state.pdf_filename = ""
    if 'show_news_modal' not in st.session_state:
        st.session_state.show_news_modal = False
    if 'show_pdf_modal' not in st.session_state:
        st.session_state.show_pdf_modal = False
    if 'collect_news_trigger' not in st.session_state:
        st.session_state.collect_news_trigger = False
    if 'analyze_pdf_trigger' not in st.session_state:
        st.session_state.analyze_pdf_trigger = False
    if 'show_master_file' not in st.session_state:
        st.session_state.show_master_file = False
    if 'sentiment_method' not in st.session_state:
        st.session_state.sentiment_method = "lexicon"

def display_header():
    """Display the main header"""
    st.markdown('<h1 class="main-header">📰 Risk Monitoring Tool</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Monitor financial risks by collecting and analyzing news for specific counterparties or analyzing PDF documents</p>', unsafe_allow_html=True)

def navigation_sidebar():
    """Create navigation sidebar"""
    st.sidebar.title("🧭 Navigation")
    
    # Navigation buttons
    if st.sidebar.button("🔍 News Search", key="nav_news", use_container_width=True):
        st.session_state.current_page = "news_search"
        st.session_state.show_news_modal = True
        st.session_state.show_pdf_modal = False
        st.rerun()
    
    if st.sidebar.button("📄 PDF Analysis", key="nav_pdf", use_container_width=True):
        st.session_state.current_page = "pdf_analysis"
        st.session_state.show_pdf_modal = True
        st.session_state.show_news_modal = False
        st.rerun()
    
    # Display current page
    st.sidebar.markdown("---")
    if st.session_state.current_page == "news_search":
        st.sidebar.success("📍 Current: News Search")
    else:
        st.sidebar.info("📍 Current: PDF Analysis")

def manage_counterparties():
    """Manage counterparty list in sidebar"""
    st.sidebar.header("🏢 Counterparties")
    
    # Add new counterparty
    with st.sidebar.expander("➕ Add Counterparty", expanded=False):
        new_counterparty = st.text_input(
            "Counterparty Name",
            placeholder="e.g., Apple Inc, Goldman Sachs",
            key="new_counterparty_input"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Add", key="add_counterparty"):
                if new_counterparty.strip() and new_counterparty.strip() not in st.session_state.counterparties:
                    st.session_state.counterparties.append(new_counterparty.strip())
                    st.rerun()
        
        with col2:
            if st.button("Clear", key="clear_counterparty"):
                # Clear the input by rerunning the app
                st.rerun()
    
    # Display current counterparties
    if st.session_state.counterparties:
        st.sidebar.subheader("📋 Current Counterparties")
        
        for i, counterparty in enumerate(st.session_state.counterparties):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {counterparty}")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.counterparties.pop(i)
                    st.rerun()
        
        # Clear all counterparties
        if st.button("🗑️ Clear All Counterparties", key="clear_all_counterparties"):
            st.session_state.counterparties = []
            st.rerun()
    else:
        st.sidebar.info("No counterparties added yet. Add some to start monitoring!")

def news_search_panel():
    """Show configuration panel for news search in the main area"""
    # Counterparty management
    counterparties = st.text_area(
        "Enter counterparties (one per line)",
        value="\n".join(st.session_state.counterparties) if st.session_state.counterparties else "",
        placeholder="e.g., Apple Inc\nGoldman Sachs"
    )
    st.session_state.counterparties = [c.strip() for c in counterparties.split("\n") if c.strip()]

    # Keywords input
    keywords = st.text_area(
        "Keywords (one per line)",
        value=st.session_state.keywords,
        placeholder="Enter keywords to filter news\nExample:\nrisk\nfinancial\nmarket\ncrisis",
        height=100
    )
    st.session_state.keywords = keywords

    # Search mode selection
    search_mode = st.radio(
        "Choose search mode:",
        ["Counterparty-based", "Custom Query"],
        index=0 if not st.session_state.get('search_mode') or st.session_state.get('search_mode') == "Counterparty-based" else 1
    )
    st.session_state.search_mode = search_mode

    # Custom query input (only shown if custom mode selected)
    custom_query = ""
    if search_mode == "Custom Query":
        custom_query = st.text_input(
            "Custom Search Query",
            value=st.session_state.get('custom_query', Config.SEARCH_QUERY),
            help="Enter your custom search query for news articles"
        )
        st.session_state.custom_query = custom_query

    # Number of articles per counterparty/query
    num_articles = st.number_input(
        "Articles per Counterparty/Query",
        min_value=1,
        max_value=20,
        value=st.session_state.get('num_articles', 5),
        step=1,
        format="%d"
    )
    st.session_state.num_articles = num_articles

    # Auto-save option
    auto_save = st.checkbox(
        "Auto-save results",
        value=st.session_state.get('auto_save', True)
    )
    st.session_state.auto_save = auto_save

    # Sentiment Analysis Configuration
    st.markdown("---")
    st.markdown("**🎭 Sentiment Analysis Configuration**")
    sentiment_method = st.selectbox(
        "Sentiment Score Method",
        ["Lexicon Based", "LLM Based"],
        index=0 if st.session_state.get('sentiment_method', 'lexicon') == 'lexicon' else 1,
        help="Choose the method for analyzing article sentiment"
    )
    st.session_state.sentiment_method = sentiment_method.lower().replace(' ', '_')
    
    if sentiment_method == "Lexicon Based":
        st.info("📊 Using finance-specific keyword lexicon for sentiment analysis")
    else:
        st.info("🤖 Using LLM (Gemini) for advanced sentiment analysis")

    # Action button
    if st.button("📰 Collect Articles", type="primary"):
        st.session_state.collect_news_trigger = True
        st.session_state.show_news_modal = False  # Collapse the expander after collecting

def pdf_analysis_panel():
    """Show configuration panel for PDF analysis in the main area"""
    with st.container():
        st.markdown('''<div style="background-color:#222A35;padding:1.5rem 1rem 1rem 1rem;border-radius:10px;margin-bottom:2rem;">
        <h3 style="color:#1f77b4;margin-bottom:1rem;">PDF Analysis Configuration</h3>''', unsafe_allow_html=True)
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF document to analyze for risks"
        )
        st.session_state.uploaded_file = uploaded_file

        # Keywords for PDF analysis
        pdf_keywords = st.text_area(
            "Keywords to search for (one per line)",
            value=st.session_state.get('pdf_keywords', ""),
            placeholder="Enter keywords to search in PDF\nExample:\nrisk\nfinancial\nmarket\ncrisis",
            height=100
        )
        st.session_state.pdf_keywords = pdf_keywords

        # Auto-save option
        auto_save_pdf = st.checkbox(
            "Auto-save results",
            value=st.session_state.get('auto_save_pdf', True)
        )
        st.session_state.auto_save_pdf = auto_save_pdf

        # Action button
        if st.button("📊 Analyze PDF", type="primary"):
            st.session_state.analyze_pdf_trigger = True
        st.markdown('</div>', unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def filter_text_by_keywords(text, keywords):
    """Filter text based on keywords and return relevant sections"""
    if not keywords.strip():
        return text
    
    keyword_list = [kw.strip().lower() for kw in keywords.split('\n') if kw.strip()]
    if not keyword_list:
        return text
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    relevant_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        for keyword in keyword_list:
            if keyword in paragraph_lower:
                relevant_paragraphs.append(paragraph)
                break
    
    return '\n\n'.join(relevant_paragraphs)

def analyze_pdf_document(uploaded_file, keywords):
    """Analyze uploaded PDF document"""
    try:
        # Extract text from PDF
        with st.spinner("📄 Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
        
        if not pdf_text:
            st.error("❌ Could not extract text from PDF. Please try a different file.")
            return None
        
        # Store PDF text in session state
        st.session_state.pdf_text = pdf_text
        st.session_state.pdf_filename = uploaded_file.name
        
        # Filter text by keywords if provided
        if keywords.strip():
            original_length = len(pdf_text)
            filtered_text = filter_text_by_keywords(pdf_text, keywords)
            st.session_state.pdf_text = filtered_text
            
            st.info(f"🔍 Filtered PDF text from {original_length} to {len(filtered_text)} characters matching keywords")
        
        # Analyze the text for risks
        with st.spinner("🔍 Analyzing PDF for risks..."):
            analyzer = RiskAnalyzer()
            
            # Create a mock article structure for analysis
            mock_article = {
                'title': f"PDF Document: {uploaded_file.name}",
                'text': st.session_state.pdf_text,
                'source': 'PDF Upload',
                'url': 'N/A',
                'publish_date': datetime.now().isoformat()
            }
            
            analysis = analyzer.analyze_articles([mock_article])
        
        return analysis
        
    except Exception as e:
        st.error(f"❌ Error analyzing PDF: {e}")
        return None

def filter_articles_by_keywords(articles: List[Dict], keywords: str) -> List[Dict]:
    """Filter articles based on keywords"""
    if not keywords.strip():
        return articles
    
    keyword_list = [kw.strip().lower() for kw in keywords.split('\n') if kw.strip()]
    if not keyword_list:
        return articles
    
    filtered_articles = []
    
    for article in articles:
        # Check if any keyword is present in title or text
        title = article.get('title', '').lower()
        text = article.get('text', '').lower()
        
        for keyword in keyword_list:
            if keyword in title or keyword in text:
                # Add keyword info to article
                article['matched_keywords'] = article.get('matched_keywords', []) + [keyword]
                filtered_articles.append(article)
                break
    
    return filtered_articles

def load_master_articles():
    """Load existing articles from master file"""
    master_file = os.path.join(Config.OUTPUT_DIR, "master_news_articles.json")
    if os.path.exists(master_file):
        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('articles', []), data.get('metadata', {})
        except Exception as e:
            st.warning(f"⚠️ Could not load master file: {e}")
            return [], {}
    return [], {}

def save_to_master_file(new_articles: List[Dict], search_metadata: Dict):
    """Save new articles to master file, appending to existing data"""
    master_file = os.path.join(Config.OUTPUT_DIR, "master_news_articles.json")
    
    # Load existing data
    existing_articles, existing_metadata = load_master_articles()
    
    # Add session metadata to new articles
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    for article in new_articles:
        article['session_id'] = session_id
        article['search_metadata'] = search_metadata
        # Ensure sentiment_analysis is always present
        if 'sentiment_analysis' not in article:
            article['sentiment_analysis'] = {'score': 0.0, 'category': 'Neutral'}
    
    # Combine articles (new articles first for recent access)
    all_articles = new_articles + existing_articles
    
    # Update metadata
    if 'total_sessions' not in existing_metadata:
        existing_metadata['total_sessions'] = 0
    existing_metadata['total_sessions'] += 1
    existing_metadata['last_updated'] = datetime.now().isoformat()
    existing_metadata['total_articles'] = len(all_articles)
    existing_metadata['sessions'] = existing_metadata.get('sessions', [])
    existing_metadata['sessions'].append({
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'articles_count': len(new_articles),
        'search_metadata': search_metadata
    })
    
    # Save to master file
    master_data = {
        'metadata': existing_metadata,
        'articles': all_articles
    }
    
    try:
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False, default=str)
        return master_file
    except Exception as e:
        st.error(f"❌ Error saving to master file: {e}")
        return None

def get_master_file_stats():
    """Get statistics about the master file"""
    master_file = os.path.join(Config.OUTPUT_DIR, "master_news_articles.json")
    if os.path.exists(master_file):
        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata = data.get('metadata', {})
                articles = data.get('articles', [])
                return {
                    'total_articles': len(articles),
                    'total_sessions': metadata.get('total_sessions', 0),
                    'last_updated': metadata.get('last_updated', 'Unknown'),
                    'file_size_mb': round(os.path.getsize(master_file) / (1024 * 1024), 2)
                }
        except Exception as e:
            return None
    return None

def display_master_file_info():
    """Display information about the master file"""
    stats = get_master_file_stats()
    if stats:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Master File Stats")
        st.sidebar.metric("Total Articles", stats['total_articles'])
        st.sidebar.metric("Total Sessions", stats['total_sessions'])
        st.sidebar.metric("File Size", f"{stats['file_size_mb']} MB")
        st.sidebar.caption(f"Last Updated: {stats['last_updated'][:19]}")
        
        # Add button to view master file
        if st.sidebar.button("📋 View Master File", key="view_master"):
            st.session_state.show_master_file = True
            st.rerun()
    else:
        st.sidebar.markdown("---")
        st.sidebar.info("📊 No master file found yet")

def display_master_file():
    """Display the master file contents"""
    if not st.session_state.get('show_master_file', False):
        return
    
    st.markdown('<h2 style="font-size: 1.5rem; color: #1f77b4; margin-bottom: 1rem;">📋 Master News Articles File</h2>', unsafe_allow_html=True)
    
    master_file = os.path.join(Config.OUTPUT_DIR, "master_news_articles.json")
    if not os.path.exists(master_file):
        st.warning("No master file found.")
        return
    
    try:
        with open(master_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        articles = data.get('articles', [])
        
        # Display metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", len(articles))
        with col2:
            st.metric("Total Sessions", metadata.get('total_sessions', 0))
        with col3:
            st.metric("File Size", f"{round(os.path.getsize(master_file) / (1024 * 1024), 2)} MB")
        with col4:
            st.metric("Last Updated", metadata.get('last_updated', 'Unknown')[:10])
        
        # Session history
        if metadata.get('sessions'):
            st.markdown('<h3 style="font-size: 1.2rem; color: #1f77b4; margin-bottom: 0.5rem;">📈 Session History</h3>', unsafe_allow_html=True)
            sessions_data = []
            for session in metadata['sessions'][-10:]:  # Show last 10 sessions
                sessions_data.append({
                    'Session ID': session['session_id'],
                    'Date': session['timestamp'][:10],
                    'Time': session['timestamp'][11:19],
                    'Articles': session['articles_count'],
                    'Search Mode': session['search_metadata'].get('search_mode', 'N/A'),
                    'Query': session['search_metadata'].get('query', 'N/A')
                })
            
            df_sessions = pd.DataFrame(sessions_data)
            st.dataframe(df_sessions, use_container_width=True)
        
        # Recent articles
        st.markdown('<h3 style="font-size: 1.2rem; color: #1f77b4; margin-bottom: 0.5rem;">📰 Recent Articles (Last 20)</h3>', unsafe_allow_html=True)
        recent_articles = articles[:20]  # Show most recent 20 articles
        
        articles_data = []
        for i, article in enumerate(recent_articles, 1):
            articles_data.append({
                'No.': i,
                'Title': article.get('title', 'N/A')[:50] + '...' if len(article.get('title', '')) > 50 else article.get('title', 'N/A'),
                'Counterparty': article.get('counterparty', 'N/A'),
                'Source': article.get('source', 'N/A'),
                'Date': article.get('publish_date', 'N/A')[:10] if article.get('publish_date') else 'N/A',
                'Session': article.get('session_id', 'N/A'),
                'URL': article.get('url', 'N/A')
            })
        
        df_articles = pd.DataFrame(articles_data)
        st.dataframe(df_articles, use_container_width=True)
        
        # Close button
        if st.button("❌ Close Master File View", key="close_master"):
            st.session_state.show_master_file = False
            st.rerun()
            
    except Exception as e:
        st.error(f"Error reading master file: {e}")

def collect_news(controls: Dict):
    """Collect news articles and log details to a file"""
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"news_collect_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)
    log_lines = []
    try:
        log_lines.append(f"[INFO] Collect News Run at {timestamp}")
        log_lines.append(f"Search Mode: {controls['search_mode']}")
        if controls['search_mode'] == "Counterparty-based":
            log_lines.append(f"Counterparties: {st.session_state.counterparties}")
        else:
            log_lines.append(f"Custom Query: {controls['custom_query']}")
        log_lines.append(f"Keywords: {st.session_state.keywords}")
        log_lines.append(f"Num Articles: {controls['num_articles']}")
        api_key = Config.get_serpapi_key()
        if not api_key:
            msg = "❌ SerpAPI key is required. Please enter your API key in the sidebar or set it in the .env file."
            st.error(msg)
            log_lines.append(f"[ERROR] {msg}")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return False
        Config.validate_config()
        all_articles = []
        search_metadata = {
            'search_mode': controls['search_mode'],
            'keywords': st.session_state.keywords,
            'num_articles': controls['num_articles'],
            'timestamp': timestamp
        }
        
        if controls['search_mode'] == "Counterparty-based":
            if not st.session_state.counterparties:
                msg = "❌ Please add at least one counterparty to monitor."
                st.error(msg)
                log_lines.append(f"[ERROR] {msg}")
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(log_lines))
                return False
            search_metadata['counterparties'] = st.session_state.counterparties
            search_metadata['query'] = ', '.join(st.session_state.counterparties)
            
            for counterparty in st.session_state.counterparties:
                with st.spinner(f"🔍 Searching for articles about: '{counterparty}'..."):
                    collector = NewsCollector()
                    articles = collector.collect_articles(
                        query=counterparty,
                        num_articles=controls['num_articles']
                    )
                    for article in articles:
                        article['counterparty'] = counterparty
                    all_articles.extend(articles)
                    log_lines.append(f"[INFO] {len(articles)} articles collected for {counterparty}")
                    time.sleep(2)
        else:
            query = controls['custom_query'] or Config.SEARCH_QUERY
            search_metadata['query'] = query
            search_metadata['custom_query'] = controls.get('custom_query', '')
            
            with st.spinner(f"🔍 Searching for articles with query: '{query}'..."):
                collector = NewsCollector()
                all_articles = collector.collect_articles(
                    query=query,
                    num_articles=controls['num_articles']
                )
            log_lines.append(f"[INFO] {len(all_articles)} articles collected for query '{query}'")
        
        filtered_count = len(all_articles)
        if all_articles:
            if st.session_state.keywords.strip():
                original_count = len(all_articles)
                all_articles = filter_articles_by_keywords(all_articles, st.session_state.keywords)
                filtered_count = len(all_articles)
                log_lines.append(f"[INFO] Filtered {original_count} articles to {filtered_count} articles matching keywords")
            
            # Perform sentiment analysis on articles
            sentiment_method = st.session_state.get('sentiment_method', 'lexicon')
            search_metadata['sentiment_method'] = sentiment_method
            
            with st.spinner(f"🎭 Analyzing sentiment using {sentiment_method.replace('_', ' ').title()} method..."):
                for article in all_articles:
                    # Combine title and text for sentiment analysis
                    article_text = f"{article.get('title', '')} {article.get('text', '')}"
                    
                    # Perform sentiment analysis
                    sentiment_result = analyze_sentiment_sync(article_text, sentiment_method)
                    article['sentiment_analysis'] = sentiment_result
                    
                    # Add sentiment method info
                    article['sentiment_method'] = sentiment_method
            
            log_lines.append(f"[INFO] Sentiment analysis completed using {sentiment_method} method")
            
            st.session_state.articles = all_articles
            
            # Save to master file
            master_file_path = save_to_master_file(all_articles, search_metadata)
            if master_file_path:
                log_lines.append(f"[INFO] Articles saved to master file: {master_file_path}")
                st.success(f"✅ Articles saved to master file! Total sessions: {get_master_file_stats()['total_sessions'] if get_master_file_stats() else 0}")
            
            # Also save individual session file if auto-save is enabled
            if controls['auto_save']:
                filename = f"news_articles_{timestamp}.json"
                filepath = collector.save_articles(all_articles, filename)
                log_lines.append(f"[INFO] Individual session file saved to {filepath}")
            
            log_lines.append(f"[SUCCESS] News collection completed successfully! {filtered_count} articles.")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return True
        else:
            msg = "❌ No articles found. Please try different search terms or keywords."
            st.error(msg)
            log_lines.append(f"[ERROR] {msg}")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return False
    except ValueError as e:
        msg = f"❌ Configuration error: {e}"
        st.error(msg)
        log_lines.append(f"[ERROR] {msg}")
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return False
    except Exception as e:
        msg = f"❌ Error collecting news: {e}"
        st.error(msg)
        log_lines.append(f"[ERROR] {msg}")
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return False

def strip_html_tags(text):
    """Remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def display_articles():
    """Display collected articles in a clean format"""
    if not st.session_state.articles:
        return
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">📰 Collected Articles (' + str(len(st.session_state.articles)) + ' found)</h3>', unsafe_allow_html=True)
    if st.session_state.counterparties:
        st.info(f"**Counterparties monitored:** {', '.join(st.session_state.counterparties)}")
    if st.session_state.keywords.strip():
        keywords_display = ', '.join([kw.strip() for kw in st.session_state.keywords.split('\n') if kw.strip()])
        st.info(f"**Keywords filtered:** {keywords_display}")
    
    # Show sentiment method used
    sentiment_method = st.session_state.get('sentiment_method', 'lexicon')
    method_display = sentiment_method.replace('_', ' ').title()
    st.info(f"**🎭 Sentiment Analysis Method:** {method_display}")
    
    for i, article in enumerate(st.session_state.articles, 1):
        with st.container():
            # Strip HTML tags from article text
            full_text = strip_html_tags(article.get('text', 'No content available'))
            words = full_text.split()
            preview_text = ' '.join(words[:100])
            show_more = len(words) > 100
            # Prepare source and author info
            source = article.get('source', 'Unknown source')
            authors = ', '.join(article.get('authors', [])) if article.get('authors') else ''
            # Prepare counterparty and keyword tags
            counterparty_tag = ''
            if article.get('counterparty'):
                counterparty_tag = f'<span class="counterparty-tag" style="font-size:0.8em;">🏢 {article.get("counterparty")}</span>'
            keyword_tags = ''
            if article.get('matched_keywords'):
                for keyword in article.get('matched_keywords', []):
                    keyword_tags += f'<span class="counterparty-tag" style="font-size:0.8em;">🔍 {keyword}</span>'
            
            # Prepare sentiment analysis plain text
            sentiment_text = ''
            if article.get('sentiment_analysis'):
                sentiment = article['sentiment_analysis']
                category = sentiment.get('category', 'Neutral')
                score = sentiment.get('score', 0.0)
                # Set color based on sentiment
                if category == 'Positive':
                    sentiment_color = '#28a745'  # green
                elif category == 'Negative':
                    sentiment_color = '#dc3545'  # red
                else:
                    sentiment_color = '#ffc107'  # yellow
                sentiment_text = f"<span style='color:{sentiment_color}; font-weight:bold;'>Sentiment: {category} (Score: {score})</span>"
                # Add lexicon details if available
                if sentiment_method == 'lexicon' and 'positive_count' in sentiment:
                    sentiment_text += f" | Positive: {sentiment['positive_count']}, Negative: {sentiment['negative_count']}"
                # Add LLM justification if available
                if sentiment_method == 'llm' and 'justification' in sentiment:
                    sentiment_text += f" | {sentiment['justification']}"
            
            # Render the card
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{i}. {article.get('title', 'No title')}</div>
                <div style='font-size:0.9em; color:#888; margin-bottom:0.5em;'>📰 {source}{' | ✍️ ' + authors if authors else ''}</div>
                <div class="article-date" style='margin-bottom:1em;'>📅 Date: {article.get('publish_date', 'Unknown date')[:10] if article.get('publish_date') else 'Unknown date'}</div>
                <div class='article-text' style='margin-bottom:1em;'>{preview_text}{'...' if show_more else ''}</div>
                <div style='margin-bottom:0.5em; color:#1f77b4; font-size:0.95em;'>{sentiment_text}</div>
            """, unsafe_allow_html=True)
            if show_more:
                with st.expander("Show more"):
                    st.write(full_text)
            st.markdown(f"""
                <div style='margin-top:0.5em;'>{counterparty_tag} {keyword_tags}</div>
                <a href="{article.get('url', '#')}" target="_blank" class="article-link">🔗 Read full article</a>
            </div>
            """, unsafe_allow_html=True)

def display_articles_table():
    """Display articles in a table format"""
    if not st.session_state.articles:
        return
    
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">📋 Articles Summary Table</h3>', unsafe_allow_html=True)
    
    # Prepare data for table
    articles_data = []
    for i, article in enumerate(st.session_state.articles, 1):
        # Get sentiment info
        sentiment_info = article.get('sentiment_analysis', {})
        sentiment_category = sentiment_info.get('category', 'N/A')
        sentiment_score = sentiment_info.get('score', 'N/A')
        
        articles_data.append({
            'No.': i,
            'Title': article.get('title', 'N/A'),
            'Counterparty': article.get('counterparty', 'N/A'),
            'Source': article.get('source', 'N/A'),
            'Date': article.get('publish_date', 'N/A')[:10] if article.get('publish_date') else 'N/A',
            'Sentiment': sentiment_category,
            'Score': sentiment_score,
            'Keywords': ', '.join(article.get('matched_keywords', [])) if article.get('matched_keywords') else 'N/A',
            'URL': article.get('url', 'N/A')
        })
    
    df_articles = pd.DataFrame(articles_data)
    st.dataframe(df_articles, use_container_width=True)

def display_pdf_analysis(analysis):
    """Display PDF analysis results"""
    if not analysis or not isinstance(analysis, dict) or 'summary' not in analysis:
        st.warning("No valid PDF analysis results to display.")
        return
    
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">📊 PDF Analysis Results</h3>', unsafe_allow_html=True)
    
    # Display summary
    summary = analysis['summary']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Risk Score", f"{summary['risk_score']:.2f}/10")
    
    with col2:
        st.metric("Sentiment Score", f"{summary['sentiment_score']:.2f}")
    
    with col3:
        st.metric("Risk Categories", len(analysis['risk_categories']))
    
    # Display risk categories
    if analysis['risk_categories']:
        st.markdown('<h4 style="font-size: 1.1rem; color: #1f77b4; margin-bottom: 0.5rem;">📈 Risk Categories Found</h4>', unsafe_allow_html=True)
        for category, data in analysis['risk_categories'].items():
            if category != 'positive_sentiment':
                st.write(f"**{category.replace('_', ' ').title()}**: {data['total_articles']} mentions, "
                        f"Average severity: {data['avg_severity']:.2f}")
    
    # Display top risks
    if analysis['top_risks']:
        st.markdown('<h4 style="font-size: 1.1rem; color: #1f77b4; margin-bottom: 0.5rem;">⚠️ Top Risk Indicators</h4>', unsafe_allow_html=True)
        for i, risk in enumerate(analysis['top_risks'][:5], 1):
            st.write(f"{i}. **{risk['title']}** (Risk Score: {risk['risk_score']:.2f})")

def display_pdf_text():
    """Display extracted PDF text"""
    if not st.session_state.pdf_text:
        return
    
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">📄 Extracted PDF Text</h3>', unsafe_allow_html=True)
    
    # Show file info
    st.info(f"**File:** {st.session_state.pdf_filename}")
    st.info(f"**Text Length:** {len(st.session_state.pdf_text)} characters")
    
    # Display text in expandable section
    with st.expander("📖 View Extracted Text", expanded=False):
        st.markdown(f'<div class="article-text">{st.session_state.pdf_text}</div>', unsafe_allow_html=True)

def export_results():
    """Export results section"""
    if not st.session_state.articles and not st.session_state.pdf_text:
        return
        
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">💾 Export Results</h3>', unsafe_allow_html=True)
    
    if st.session_state.articles:
        if st.button("📄 Export Articles (JSON)"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_articles_{timestamp}.json"
            
            # Save to output directory
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.articles, f, indent=2, ensure_ascii=False, default=str)
            
            st.success(f"✅ Articles exported to {filepath}")
    
    if st.session_state.pdf_text:
        if st.button("📄 Export PDF Analysis (JSON)"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pdf_analysis_{timestamp}.json"
            
            # Create analysis data
            analysis_data = {
                'filename': st.session_state.pdf_filename,
                'text_length': len(st.session_state.pdf_text),
                'extraction_time': datetime.now().isoformat(),
                'text_preview': st.session_state.pdf_text[:1000] + "..." if len(st.session_state.pdf_text) > 1000 else st.session_state.pdf_text
            }
            
            # Save to output directory
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=str)
            
            st.success(f"✅ PDF analysis exported to {filepath}")

def news_search_page():
    st.markdown('<h2 style="font-size: 1.5rem; color: #1f77b4; margin-bottom: 0.5rem;">🔍 News Search</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 1rem;">Search for news articles about specific counterparties or custom queries.</p>', unsafe_allow_html=True)

    # Configuration panel in expandable section
    # Collapse expander if processing or if articles are found
    should_expand = st.session_state.get("show_news_modal", False) and not st.session_state.is_processing and not st.session_state.articles
    
    with st.expander("⚙️ Configure News Analysis", expanded=should_expand):
        news_search_panel()

    if st.session_state.get('collect_news_trigger', False):
        st.session_state.is_processing = True
        st.session_state.show_news_modal = False  # Collapse expander immediately when processing starts
        controls = {
            'search_mode': st.session_state.search_mode,
            'custom_query': st.session_state.get('custom_query', ""),
            'num_articles': st.session_state.num_articles,
            'collect_button': True,
            'auto_save': st.session_state.auto_save
        }
        success = collect_news(controls)
        st.session_state.is_processing = False
        st.session_state.collect_news_trigger = False
        # Keep expander collapsed after processing completes

    if st.session_state.articles:
        display_articles()
        display_articles_table()
        export_results()

    if not st.session_state.articles and not st.session_state.is_processing:
        st.info("""
        👋 **Welcome to the News Search!**
        Click 'Configure News Analysis' to set up and collect news.
        """)

def pdf_analysis_page():
    st.markdown('<h2 style="font-size: 1.5rem; color: #1f77b4; margin-bottom: 1rem;">📄 PDF Analysis</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Upload and analyze PDF documents for risk assessment.</p>', unsafe_allow_html=True)

    # Configuration panel in expandable section
    # Collapse expander if processing or if PDF text is found
    should_expand = st.session_state.get("show_pdf_modal", False) and not st.session_state.is_processing and not st.session_state.pdf_text
    
    with st.expander("⚙️ Configure PDF Analysis", expanded=should_expand):
        pdf_analysis_panel()

    if st.session_state.get('analyze_pdf_trigger', False) and st.session_state.get('uploaded_file'):
        st.session_state.is_processing = True
        st.session_state.show_pdf_modal = False  # Collapse expander immediately when processing starts
        analysis = analyze_pdf_document(st.session_state.uploaded_file, st.session_state.pdf_keywords)
        if analysis:
            st.session_state.is_processing = False
            st.session_state.analyze_pdf_trigger = False
            st.rerun()
        st.session_state.is_processing = False
        st.session_state.analyze_pdf_trigger = False

    if st.session_state.pdf_text:
        display_pdf_text()
        if st.session_state.articles:
            display_pdf_analysis(st.session_state.articles)
        export_results()

    if not st.session_state.pdf_text and not st.session_state.is_processing:
        st.info("""
        👋 **Welcome to the PDF Analysis!**
        Click 'Configure PDF Analysis' to set up and analyze a PDF.
        """)

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Navigation sidebar
    navigation_sidebar()
    
    # Master file info in sidebar
    display_master_file_info()
    
    # Display current page
    if st.session_state.current_page == "news_search":
        news_search_page()
    else:
        pdf_analysis_page()
    
    # Display master file if requested
    display_master_file()

if __name__ == "__main__":
    main() 