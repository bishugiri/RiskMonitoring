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
from datetime import datetime
import time
from typing import Dict, List
import PyPDF2
import io
import logging
import requests
import openai
import plotly.express as px
import plotly.graph_objects as go

# --- Project Structure & Configuration ---
# Ensure project structure is accessible for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import core and config modules
from risk_monitor.core.news_collector import NewsCollector
from risk_monitor.core.risk_analyzer import RiskAnalyzer
from risk_monitor.config.settings import Config

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
    if method == 'lexicon':
        return analyze_sentiment_lexicon(text)
    elif method == 'llm':
        st.info("LLM-based sentiment analysis is processing...")
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
    if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""
    if 'pdf_filename' not in st.session_state: st.session_state.pdf_filename = ""
    if 'collect_news_trigger' not in st.session_state: st.session_state.collect_news_trigger = False
    if 'analyze_pdf_trigger' not in st.session_state: st.session_state.analyze_pdf_trigger = False
    if 'sentiment_method' not in st.session_state: st.session_state.sentiment_method = "lexicon"
    if 'last_run_metadata' not in st.session_state: st.session_state.last_run_metadata = {}

def load_master_articles():
    """Loads a list of articles from the master JSON file."""
    output_dir = "output"
    master_file = os.path.join(output_dir, "master_news_articles.json")
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(master_file):
        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('articles', []), data.get('metadata', {})
        except Exception as e:
            st.warning(f"⚠️ Could not load master file: {e}")
    return [], {}

def save_to_master_file(new_articles: List[Dict], search_metadata: Dict):
    """Saves new articles and metadata to the master JSON file."""
    output_dir = "output"
    master_file = os.path.join(output_dir, "master_news_articles.json")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        existing_articles, existing_metadata = load_master_articles()
        combined_articles = existing_articles + new_articles
        seen_urls = set()
        unique_articles = []
        for article in combined_articles:
            if article.get('url') and article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        existing_metadata.update(search_metadata)
        
        data_to_save = {
            "metadata": existing_metadata,
            "articles": unique_articles
        }
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        return True, "Results saved successfully!"
    except Exception as e:
        return False, f"Error saving results: {e}"

def extract_text_from_pdf(pdf_file):
    """Extracts all text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.getvalue()))
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def filter_text_by_keywords(text, keywords):
    """Filters text to only include paragraphs containing specific keywords."""
    if not keywords.strip(): return text
    keyword_list = [kw.strip().lower() for kw in keywords.split('\n') if kw.strip()]
    if not keyword_list: return text
    paragraphs = text.split('\n\n')
    relevant_paragraphs = [p for p in paragraphs if any(kw in p.lower() for kw in keyword_list)]
    return '\n\n'.join(relevant_paragraphs)

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

    if st.sidebar.button("📄 PDF Analysis", key="nav_pdf", use_container_width=True, type="primary" if st.session_state.current_page == "pdf_analysis" else "secondary"):
        st.session_state.current_page = "pdf_analysis"
        st.rerun()

    if st.sidebar.button("🤖 RAG Chat", key="nav_rag", use_container_width=True, type="primary" if st.session_state.current_page == "rag_chat" else "secondary"):
        st.session_state.current_page = "rag_chat"
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

def display_article_card(article: Dict):
    """Renders a card for a single article with sentiment and details."""
    sentiment = article.get('sentiment_category', 'Neutral').lower()
    color_class = f"sentiment-{sentiment}"
    
    st.markdown(f'<div class="article-card {color_class}">', unsafe_allow_html=True)
    st.markdown(f'<h3 class="article-title">{article.get("title", "Untitled")}</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<p style="color: var(--text-muted); font-size: 0.9rem;">**Source:** {article.get("source", "Unknown")} | **Published:** {date_str}</p>', unsafe_allow_html=True)
    
    st.markdown(f'<p>{article.get("summary", article.get("text", "No summary available"))[:300]}...</p>', unsafe_allow_html=True)
    
    sentiment_label = article.get("sentiment_category", "Neutral").upper()
    badge_class = f"badge-{sentiment.lower()}"
    st.markdown(f'<div style="text-align: right;"><span class="badge {badge_class}">{sentiment_label}</span></div>', unsafe_allow_html=True)

    with st.expander("Show Detailed Analysis"):
        st.markdown(f"**Sentiment Score:** `{article.get('sentiment_score', 'N/A')}`")
        if 'sentiment_justification' in article:
            st.info(f"**LLM Justification:** {article['sentiment_justification']}")
        else:
            st.info(f"**Lexicon Analysis:** Positive words: `{article.get('positive_count', 0)}`, Negative words: `{article.get('negative_count', 0)}`")
        
        st.markdown(f"**Full Article Text:**\n```\n{article.get('text', 'No text found.')[:1000]}...\n```")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main Application Logic ---
def main():
    """Main function to run the Streamlit application."""
    load_custom_css()
    initialize_session_state()
    
    st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
    navigation_sidebar()
    
    # --- Dashboard View ---
    if st.session_state.current_page == "dashboard":
        display_dashboard_header()
        display_dashboard_metrics()
        
        st.markdown("---")
        st.header("Latest Analyzed Articles")
        if not st.session_state.articles:
            st.info("💡 Run a news or PDF analysis to see the latest results here.")
        
        for article in st.session_state.articles[:5]:
            display_article_card(article)

    # --- News Analysis View ---
    elif st.session_state.current_page == "news_analysis":
        st.markdown('<div class="custom-container"><h2 style="margin: 0;">News Analysis</h2><p style="margin: 0.25rem 0 0; color: #4b5563;">Configure and run financial news analysis.</p></div>', unsafe_allow_html=True)
        
        search_tab, filters_tab, advanced_tab = st.tabs(["🔍 Search", "🔎 Filters", "⚙️ Advanced"])
        
        with search_tab:
            st.subheader("Search Mode")
            search_mode = st.radio("Choose how to search for articles:", ["Counterparty-based", "Custom Query"], index=0, horizontal=True)
            st.session_state.search_mode = search_mode
            
            if search_mode == "Counterparty-based":
                st.write("📋 **Enter companies to monitor (one per line):**")
                counterparties_input = st.text_area(
                    "Counterparties",
                    value="\n".join(st.session_state.counterparties),
                    placeholder="e.g., Apple Inc\nGoldman Sachs\nJPMorgan Chase",
                )
                st.session_state.counterparties = [c.strip() for c in counterparties_input.split("\n") if c.strip()]
            else:
                st.session_state.custom_query = st.text_input("Custom Search Query", value=st.session_state.get('custom_query', Config.SEARCH_QUERY))

            st.number_input("Articles per Search", min_value=1, max_value=20, value=st.session_state.get('num_articles', 5), step=1, format="%d", help="Max number of articles to collect per search term.", key="num_articles")

        with filters_tab:
            st.text_area("Keyword Filtering", value=st.session_state.keywords, placeholder="risk\nfinancial\nmarket\ncrisis", height=150, help="Only include articles containing these keywords.", key="keywords")

        with advanced_tab:
            sentiment_method = st.selectbox("Sentiment Analysis Method", ["Lexicon Based", "LLM Based"], index=0, help="Lexicon is fast and rule-based; LLM is more nuanced but requires an OpenAI API key.", key="sentiment_method_select")
            st.session_state.sentiment_method = sentiment_method.lower().replace(' ', '_')
            st.checkbox("Auto-save results", value=st.session_state.get('auto_save', True), help="Automatically save results to a master JSON file.", key="auto_save")
        
        st.markdown("---")
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
                
                # Add Pinecone integration option
                use_pinecone = st.checkbox("Store in Pinecone Database", value=True, help="Store analysis results in Pinecone vector database for semantic search")
                
                for i, query in enumerate(queries):
                    status_text.info(f"Collecting news for: **{query}**")
                    articles = news_collector.collect_articles(query, st.session_state.num_articles)
                    filtered_articles = filter_articles_by_keywords(articles, st.session_state.keywords)
                    collected_articles.extend(filtered_articles)
                    current_step += len(queries)
                    progress_bar.progress(current_step / total_steps)
                
                # Analyze articles with comprehensive analysis
                if collected_articles:
                    status_text.info("Analyzing articles and storing in database...")
                    
                    if use_pinecone:
                        try:
                            # Use new comprehensive analysis with Pinecone storage
                            analysis_results = analyzer.analyze_and_store_in_pinecone(
                                collected_articles, 
                                st.session_state.sentiment_method
                            )
                            
                            # Extract individual article results for display
                            individual_analyses = analysis_results['individual_analyses']
                            st.session_state.articles = []
                            
                            for i, (article, analysis) in enumerate(zip(collected_articles, individual_analyses)):
                                # Merge article data with analysis results
                                article.update({
                                    'sentiment_score': analysis['sentiment_analysis']['score'],
                                    'sentiment_category': analysis['sentiment_analysis']['category'],
                                    'sentiment_method': st.session_state.sentiment_method,
                                    'sentiment_justification': analysis['sentiment_analysis'].get('justification', ''),
                                    'risk_score': analysis['risk_analysis']['risk_score'],
                                    'risk_categories': analysis['risk_analysis']['risk_categories']
                                })
                                st.session_state.articles.append(article)
                            
                            # Store comprehensive results
                            st.session_state.last_analysis_results = analysis_results
                            
                            # Show storage statistics
                            storage_stats = analysis_results['analysis_summary']['storage_stats']
                            storage_type = analysis_results['analysis_summary']['storage_type']
                            if storage_type == "pinecone":
                                status_text.success(f"✅ Analysis complete! Stored {storage_stats['success_count']} articles in Pinecone database.")
                            else:
                                status_text.success(f"✅ Analysis complete! Stored {storage_stats['success_count']} articles locally (Pinecone unavailable).")
                            
                        except Exception as e:
                            status_text.error(f"❌ Pinecone storage failed: {e}")
                            # Fallback to regular analysis
                            for article in collected_articles:
                                sentiment_result = analyze_sentiment_sync(article['text'], st.session_state.sentiment_method)
                                article.update({
                                    'sentiment_score': sentiment_result.get('score'),
                                    'sentiment_category': sentiment_result.get('category'),
                                    'sentiment_method': st.session_state.sentiment_method,
                                    'sentiment_justification': sentiment_result.get('justification')
                                })
                            st.session_state.articles = collected_articles
                    else:
                        # Regular analysis without Pinecone
                        for article in collected_articles:
                            sentiment_result = analyze_sentiment_sync(article['text'], st.session_state.sentiment_method)
                            article.update({
                                'sentiment_score': sentiment_result.get('score'),
                                'sentiment_category': sentiment_result.get('category'),
                                'sentiment_method': st.session_state.sentiment_method,
                                'sentiment_justification': sentiment_result.get('justification')
                            })
                        st.session_state.articles = collected_articles
                        status_text.success("✅ Analysis complete!")
                
                metadata = {
                    'timestamp': datetime.now().isoformat(),
                    'articles_collected': len(collected_articles),
                    'negative_count': sum(1 for a in st.session_state.articles if a.get('sentiment_category') == 'Negative'),
                    'positive_count': sum(1 for a in st.session_state.articles if a.get('sentiment_category') == 'Positive')
                }
                st.session_state.last_run_metadata = metadata
                
                if st.session_state.auto_save:
                    save_success, save_message = save_to_master_file(st.session_state.articles, metadata)
                    if save_success:
                        status_text.success("✅ Results also saved to local file!")
                    else:
                        status_text.warning(f"⚠️ Could not save to local file: {save_message}")

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
                    summary_tab, articles_tab, pinecone_tab = st.tabs(["📊 Summary", "📰 Articles", "🗄️ Pinecone Stats"])
                    
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
                            st.metric("Stored in DB", f"{storage_stats['success_count']}/{storage_stats['total_count']}")
                        
                        # Sentiment distribution
                        st.subheader("Sentiment Distribution")
                        sentiment_dist = sentiment_summary['sentiment_distribution']
                        if sentiment_dist:
                            sentiment_df = pd.DataFrame(list(sentiment_dist.items()), columns=['Category', 'Count'])
                            fig = px.pie(sentiment_df, values='Count', names='Category', 
                                       color='Category',
                                       color_discrete_map={'Negative': '#E74C3C', 'Positive': '#2ECC71', 'Neutral': '#3498DB'},
                                       title="Article Sentiment Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Risk summary
                        st.subheader("Risk Analysis Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("High Risk", risk_summary['high_risk_articles'])
                        with col2:
                            st.metric("Medium Risk", risk_summary['medium_risk_articles'])
                        with col3:
                            st.metric("Low Risk", risk_summary['low_risk_articles'])
                    
                    with articles_tab:
                        for article in st.session_state.articles:
                            display_article_card(article)
                    
                    with pinecone_tab:
                        storage_type = analysis_results['analysis_summary']['storage_type']
                        if storage_type == "pinecone":
                            st.subheader("Pinecone Database Statistics")
                            try:
                                from risk_monitor.utils.pinecone_db import PineconeDB
                                pinecone_db = PineconeDB()
                                stats = pinecone_db.get_index_stats()
                                
                                if stats:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Vectors", stats.get('total_vector_count', 0))
                                    with col2:
                                        st.metric("Index Dimension", stats.get('dimension', 0))
                                    with col3:
                                        st.metric("Index Fullness", f"{stats.get('index_fullness', 0):.2%}")
                                    
                                    # Show storage results
                                    storage_stats = analysis_results['analysis_summary']['storage_stats']
                                    st.success(f"✅ Successfully stored {storage_stats['success_count']} out of {storage_stats['total_count']} articles")
                                    
                                    if storage_stats['error_count'] > 0:
                                        st.warning(f"⚠️ {storage_stats['error_count']} articles failed to store")
                                else:
                                    st.warning("Could not retrieve Pinecone statistics")
                            except Exception as e:
                                st.error(f"Error retrieving Pinecone stats: {e}")
                        else:
                            st.subheader("Local Storage Statistics")
                            try:
                                from risk_monitor.utils.local_storage import LocalStorage
                                local_storage = LocalStorage()
                                stats = local_storage.get_storage_stats()
                                
                                if stats:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Articles", stats.get('total_articles', 0))
                                    with col2:
                                        st.metric("Index Entries", stats.get('index_entries', 0))
                                    with col3:
                                        st.metric("Storage Path", "Local")
                                    
                                    # Show storage results
                                    storage_stats = analysis_results['analysis_summary']['storage_stats']
                                    st.success(f"✅ Successfully stored {storage_stats['success_count']} out of {storage_stats['total_count']} articles locally")
                                    
                                    if storage_stats['error_count'] > 0:
                                        st.warning(f"⚠️ {storage_stats['error_count']} articles failed to store")
                                    
                                    # Show sentiment distribution
                                    sentiment_dist = stats.get('sentiment_distribution', {})
                                    if sentiment_dist:
                                        st.subheader("Local Storage Sentiment Distribution")
                                        for category, count in sentiment_dist.items():
                                            st.write(f"**{category}:** {count}")
                                else:
                                    st.warning("Could not retrieve local storage statistics")
                            except Exception as e:
                                st.error(f"Error retrieving local storage stats: {e}")
                else:
                    # Fallback to simple article display
                    for article in st.session_state.articles:
                        display_article_card(article)
            else:
                st.warning("No articles found matching your criteria.")

    # --- PDF Analysis View ---
    elif st.session_state.current_page == "pdf_analysis":
        st.markdown('<div class="custom-container"><h2 style="margin: 0;">PDF Analysis</h2><p style="margin: 0.25rem 0 0; color: #4b5563;">Upload and analyze PDF documents for risk assessment.</p></div>', unsafe_allow_html=True)
        
        upload_tab, filters_tab, settings_tab = st.tabs(["📄 Upload PDF", "🔎 Filters", "⚙️ Settings"])
        
        with upload_tab:
            uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'], help="Upload a PDF document to analyze.")
            st.session_state.uploaded_file = uploaded_file
            if uploaded_file:
                st.success(f"✅ File uploaded: {uploaded_file.name}")

        with filters_tab:
            st.text_area("Keywords to Search", value=st.session_state.get('pdf_keywords', ""), placeholder="risk\nfinancial\ncrisis", height=150, help="Only analyze paragraphs containing these keywords.", key="pdf_keywords")

        with settings_tab:
            pdf_sentiment_method = st.selectbox("Sentiment Analysis Method", ["Lexicon Based", "LLM Based"], index=0, key="pdf_sentiment_method_select")
            st.session_state.sentiment_method = pdf_sentiment_method.lower().replace(' ', '_')
            st.checkbox("Auto-save results", value=st.session_state.get('auto_save_pdf', True), help="Automatically save analysis results.", key="auto_save_pdf")

        st.markdown("---")
        if st.button("📊 Analyze PDF", type="primary", use_container_width=True):
            if not st.session_state.uploaded_file:
                st.error("⚠️ Please upload a PDF file first.")
            else:
                st.session_state.analyze_pdf_trigger = True

        if st.session_state.analyze_pdf_trigger:
            st.session_state.analyze_pdf_trigger = False
            
            with st.spinner("📄 Extracting text and analyzing PDF..."):
                pdf_text = extract_text_from_pdf(st.session_state.uploaded_file)
                if not pdf_text:
                    st.error("❌ Failed to extract text from PDF.")
                    return
                
                st.session_state.pdf_text = filter_text_by_keywords(pdf_text, st.session_state.pdf_keywords)
                
                analyzer = RiskAnalyzer()
                mock_article = {
                    'title': f"PDF Document: {st.session_state.uploaded_file.name}",
                    'text': st.session_state.pdf_text,
                    'source': 'PDF Upload',
                    'url': 'N/A',
                    'publish_date': datetime.now().isoformat()
                }
                analysis_results = analyzer.analyze_articles([mock_article], st.session_state.sentiment_method)
            
            st.success("✅ PDF analysis complete!")
            st.markdown("---")
            st.subheader("📄 PDF Analysis Summary")
            
            if analysis_results:
                result = analysis_results[0]
                sentiment = result.get('sentiment_category', 'Neutral').lower()
                st.markdown(f'<div class="custom-container {f"sentiment-{sentiment}"}">', unsafe_allow_html=True)
                st.markdown(f"**Document:** `{st.session_state.uploaded_file.name}`")
                st.markdown(f"**Sentiment Category:** <span class='badge badge-{sentiment}'>{result.get('sentiment_category', 'N/A').upper()}</span>", unsafe_allow_html=True)
                st.markdown(f"**Sentiment Score:** `{result.get('sentiment_score', 'N/A')}`")
                
                with st.expander("View Analyzed Content"):
                    st.markdown("This section contains the text extracted from the PDF after applying keyword filters.")
                    st.code(st.session_state.pdf_text)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No relevant content was found in the PDF after filtering.")

    # --- RAG Chat View ---
    elif st.session_state.current_page == "rag_chat":
        st.title("🏦 Financial Data AI Agent Chat")
        st.markdown("Chat with AI about your stored financial data and get insights.")
        
        # Initialize RAG service
        try:
            from risk_monitor.core.rag_service import RAGService
            rag_service = RAGService()
            
            # Get database stats
            db_stats = rag_service.get_database_stats()
            
            # Display database info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Articles", db_stats.get('total_articles', 0))
            with col2:
                st.metric("🔢 Index Dimension", db_stats.get('index_dimension', 0))
            with col3:
                st.metric("📈 Index Fullness", f"{db_stats.get('index_fullness', 0):.2%}")
            
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
                        
                        # Use raw query format with conversation context
                        raw_query = user_query.strip()
                        if conversation_context:
                            enhanced_query = f"Context from previous conversation:\n{conversation_context}\n\nCurrent question: {raw_query}"
                        else:
                            enhanced_query = raw_query
                        
                        response = rag_service.chat_with_agent(enhanced_query)
                        
                        # Show articles used count
                        articles_used = response.get('articles_used', 0)
                        if articles_used > 0:
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
                    if hasattr(rag_service, 'last_articles') and rag_service.last_articles:
                        total_articles = len(rag_service.last_articles)
                        st.markdown(f"**📊 Total References Analyzed: {total_articles} articles**")
                        
                        # Show sentiment distribution
                        sentiment_counts = {}
                        for article in rag_service.last_articles:
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
                            current_articles = rag_service.last_articles[start_idx:end_idx]
                        else:
                            current_articles = rag_service.last_articles
                        
                        # Display current page articles
                        for i, article in enumerate(current_articles, start_idx + 1 if total_pages > 1 else 1):
                            sentiment = article.get('sentiment_category', 'Unknown').lower()
                            badge_class = f"badge-{sentiment}"
                            
                            with st.expander(f"📄 [REFERENCE {i}] {article.get('title', 'Unknown')}", expanded=False):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.markdown(f"**Source:** {article.get('source', 'Unknown')}")
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
                                
                                if article.get('keywords'):
                                    st.markdown("**Keywords:**")
                                    st.write(', '.join(article.get('keywords', [])))
                                
                                st.markdown("**Full Text (excerpt):**")
                                st.code(article.get('text', 'No text available')[:500] + "...", language='text')
                        
                        # Show pagination info if needed
                        if total_pages > 1:
                            st.markdown(f"*Showing page {page} of {total_pages} (References {start_idx + 1}-{end_idx} of {total_articles})*")
        
        except ImportError:
            st.error("❌ RAG service not available. Please ensure all dependencies are installed.")
        except Exception as e:
            st.error(f"❌ Error initializing RAG service: {str(e)}")

# Entry point of the script
if __name__ == "__main__":
    main()
