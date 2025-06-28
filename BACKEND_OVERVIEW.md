# Risk Monitoring Tool: Backend Overview

This document explains how the backend of the Risk Monitoring Tool works, step by step.

---

## 1. Configuration Loading
- The app loads configuration settings from `config.py`.
- Environment variables (like the SerpAPI key) are loaded using `python-dotenv`.
- Default values for search queries, number of articles, output directories, and logging are set here.

---

## 2. User Input (via Streamlit Web App)
- The user interacts with the app through `streamlit_app.py`.
- Users can:
  - Enter counterparties (companies/organizations to monitor)
  - Set keywords for filtering news
  - Choose the number of articles to fetch
  - Optionally upload PDF files for analysis

---

## 3. News Collection
- When the user initiates a news search, the app uses the `NewsCollector` class from `news_collector.py`.
- **Steps:**
  1. **Search News:**
     - Uses SerpAPI to search Google News for articles matching the query or counterparties.
     - Fetches metadata (title, link, source, date, etc.) for each article.
  2. **Extract Content:**
     - For each article, downloads and parses the full text using `newspaper3k`.
     - Extracts title, text, publish date, authors, summary, and keywords.
  3. **Combine Data:**
     - Merges search metadata with extracted content for each article.
  4. **Save Results:**
     - Saves the collected articles as a JSON file in the `output/` directory.

---

## 4. Risk Analysis
- The `RiskAnalyzer` class (in `risk_analyzer.py`) processes the collected articles.
- **Steps:**
  1. **Keyword Filtering:**
     - Filters articles based on user-specified keywords.
  2. **Risk Scoring:**
     - Analyzes article content for risk-related terms and sentiment.
     - Assigns risk and sentiment scores to each article.
  3. **Category Analysis:**
     - Groups risks by category (e.g., market, economic, geopolitical).
  4. **Summary Generation:**
     - Produces a summary of top risks, risk categories, and overall scores.
  5. **Save Analysis:**
     - Saves the risk analysis results as a JSON file in the `output/` directory.

---

## 5. PDF Analysis (Optional)
- Users can upload PDF files for risk analysis.
- The app extracts text from the PDF and analyzes it using the same risk analysis pipeline as for news articles.

---

## 6. Logging
- All major actions (search, extraction, analysis, errors) are logged to `risk_monitor.log` and the `logs/` directory.
- Logs help with debugging and tracking the tool's operation.

---

## 7. Output & Export
- Users can download collected articles and risk analysis results as JSON files.
- The app provides summaries and visualizations in the web interface.

---

## 8. Error Handling
- The backend includes error handling for:
  - Missing API keys
  - Network/API errors
  - Content extraction failures
  - Invalid user input
- Errors are shown in the UI and logged for review.

---

## Summary Diagram

```mermaid
graph TD;
    A[User Input (Streamlit)] --> B[NewsCollector: Search News]
    B --> C[Extract Article Content]
    C --> D[Save Articles to Output]
    D --> E[RiskAnalyzer: Analyze Articles]
    E --> F[Save Analysis to Output]
    F --> G[Display Results in UI]
    A --> H[PDF Upload (Optional)]
    H --> I[Extract PDF Text]
    I --> E
```

---

For more details, see the code comments in each module or the `README.md` for usage instructions. 