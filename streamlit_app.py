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

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
from risk_analyzer import RiskAnalyzer
from config import Config

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
    with st.container():
        st.markdown('''<div style="background-color:#222A35;padding:1.5rem 1rem 1rem 1rem;border-radius:10px;margin-bottom:2rem;">
        <h3 style="color:#1f77b4;margin-bottom:1rem;">News Search Configuration</h3>''', unsafe_allow_html=True)
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
        num_articles = st.slider(
            "Articles per Counterparty/Query",
            min_value=3,
            max_value=20,
            value=st.session_state.get('num_articles', 5)
        )
        st.session_state.num_articles = num_articles

        # API key input
        api_key = st.text_input(
            "SerpAPI Key",
            type="password",
            value=st.session_state.get('api_key', ""),
            help="Enter your SerpAPI key (or set in .env file)"
        )
        st.session_state.api_key = api_key

        # Auto-save option
        auto_save = st.checkbox(
            "Auto-save results",
            value=st.session_state.get('auto_save', True)
        )
        st.session_state.auto_save = auto_save

        # Action button
        if st.button("📰 Collect Articles", type="primary"):
            st.session_state.collect_news_trigger = True
        st.markdown('</div>', unsafe_allow_html=True)

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
        if controls['api_key']:
            Config.SERPAPI_KEY = controls['api_key']
        if not Config.SERPAPI_KEY:
            msg = "❌ SerpAPI key is required. Please enter your API key in the sidebar or set it in the .env file."
            st.error(msg)
            log_lines.append(f"[ERROR] {msg}")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return False
        Config.validate_config()
        all_articles = []
        if controls['search_mode'] == "Counterparty-based":
            if not st.session_state.counterparties:
                msg = "❌ Please add at least one counterparty to monitor."
                st.error(msg)
                log_lines.append(f"[ERROR] {msg}")
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(log_lines))
                return False
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
            st.session_state.articles = all_articles
            if controls['auto_save']:
                filename = f"news_articles_{timestamp}.json"
                filepath = collector.save_articles(all_articles, filename)
                log_lines.append(f"[INFO] Articles saved to {filepath}")
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

def display_articles():
    """Display collected articles in a clean format"""
    if not st.session_state.articles:
        return
    
    st.markdown('<h3 style="font-size: 1.3rem; color: #1f77b4; margin-bottom: 1rem;">📰 Collected Articles (' + str(len(st.session_state.articles)) + ' found)</h3>', unsafe_allow_html=True)
    
    # Display search info
    if st.session_state.counterparties:
        st.info(f"**Counterparties monitored:** {', '.join(st.session_state.counterparties)}")
    if st.session_state.keywords.strip():
        keywords_display = ', '.join([kw.strip() for kw in st.session_state.keywords.split('\n') if kw.strip()])
        st.info(f"**Keywords filtered:** {keywords_display}")
    
    # Display each article
    for i, article in enumerate(st.session_state.articles, 1):
        with st.container():
            # Prepare counterparty and keyword tags
            counterparty_tag = ""
            if article.get('counterparty'):
                counterparty_tag = f'<span class="counterparty-tag">🏢 {article.get("counterparty")}</span>'
            
            keyword_tags = ""
            if article.get('matched_keywords'):
                for keyword in article.get('matched_keywords', []):
                    keyword_tags += f'<span class="counterparty-tag">🔍 {keyword}</span>'
            
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{i}. {article.get('title', 'No title')}</div>
                <div class="article-source">📰 Source: {article.get('source', 'Unknown source')}</div>
                <div class="article-date">📅 Date: {article.get('publish_date', 'Unknown date')[:10] if article.get('publish_date') else 'Unknown date'}</div>
                {counterparty_tag}
                {keyword_tags}
                <div class="article-text">{article.get('text', 'No content available')[:500]}...</div>
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
        articles_data.append({
            'No.': i,
            'Title': article.get('title', 'N/A'),
            'Counterparty': article.get('counterparty', 'N/A'),
            'Source': article.get('source', 'N/A'),
            'Date': article.get('publish_date', 'N/A')[:10] if article.get('publish_date') else 'N/A',
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
        st.text_area("PDF Content", st.session_state.pdf_text, height=400, disabled=True)

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
    st.markdown('<h2 style="font-size: 1.5rem; color: #1f77b4; margin-bottom: 1rem;">🔍 News Search</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Search for news articles about specific counterparties or custom queries.</p>', unsafe_allow_html=True)

    news_search_panel()

    if st.session_state.get('collect_news_trigger', False):
        st.session_state.is_processing = True
        controls = {
            'search_mode': st.session_state.search_mode,
            'custom_query': st.session_state.get('custom_query', ""),
            'num_articles': st.session_state.num_articles,
            'api_key': st.session_state.api_key,
            'collect_button': True,
            'auto_save': st.session_state.auto_save
        }
        success = collect_news(controls)
        st.session_state.is_processing = False
        st.session_state.collect_news_trigger = False

    if st.session_state.articles:
        display_articles()
        display_articles_table()
        export_results()

    if not st.session_state.articles and not st.session_state.is_processing:
        st.info("""
        👋 **Welcome to the News Search!**
        Configure and collect news using the panel above.
        """)

def pdf_analysis_page():
    st.markdown('<h2 style="font-size: 1.5rem; color: #1f77b4; margin-bottom: 1rem;">📄 PDF Analysis</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Upload and analyze PDF documents for risk assessment.</p>', unsafe_allow_html=True)

    pdf_analysis_panel()

    if st.session_state.get('analyze_pdf_trigger', False) and st.session_state.get('uploaded_file'):
        st.session_state.is_processing = True
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
        Configure and analyze a PDF using the panel above.
        """)

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Navigation sidebar
    navigation_sidebar()
    
    # Display current page
    if st.session_state.current_page == "news_search":
        news_search_page()
    else:
        pdf_analysis_page()

if __name__ == "__main__":
    main() 