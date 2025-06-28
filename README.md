# Risk Monitoring Tool

A comprehensive tool for monitoring financial risks by collecting and analyzing news articles from various sources using SerpAPI, with support for counterparty-based monitoring, keyword filtering, and PDF document analysis.

## Features

- 🔍 **News Collection**: Automatically searches and collects finance news articles using SerpAPI
- 🏢 **Counterparty Monitoring**: Monitor specific companies/organizations for risk-related news
- 🔍 **Keyword Filtering**: Filter articles based on custom keywords to focus on relevant content
- 📄 **PDF Analysis**: Upload and analyze PDF documents for risk assessment
- 🧭 **Dual Data Sources**: Navigate between news search and PDF analysis modes
- 📊 **Risk Analysis**: Analyzes articles for various risk categories (market, economic, geopolitical, sector)
- 📈 **Sentiment Analysis**: Calculates sentiment scores to gauge market mood
- 💾 **Data Export**: Saves collected articles and analysis results in JSON format
- 📋 **Detailed Reporting**: Provides comprehensive risk summaries and top risk identification
- 🔧 **Configurable**: Customizable search queries, article counts, and analysis parameters
- 🌐 **Web Interface**: Interactive Streamlit web application with navigation

## Risk Categories Analyzed

- **Market Risk**: Crashes, bear markets, volatility, corrections
- **Economic Risk**: Inflation, debt, interest rates, unemployment
- **Geopolitical Risk**: Wars, sanctions, trade conflicts, political instability
- **Sector Risk**: Tech bubbles, real estate, energy crises, cybersecurity
- **Positive Sentiment**: Growth, profits, opportunities, recovery

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Riskmonitortool
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your SerpAPI key**:
   - Get a free API key from [SerpAPI](https://serpapi.com/)
   - Create a `.env` file in the project root:
   ```bash
   cp env_example.txt .env
   ```
   - Edit `.env` and add your API key:
   ```
   SERPAPI_KEY=your_actual_api_key_here
   ```

## Usage

### 🌐 Web Interface (Recommended)

Launch the interactive Streamlit web application:

```bash
# Windows
run_streamlit.bat

# Or manually
streamlit run streamlit_app.py
```

The web interface provides two main data sources with easy navigation:

#### 🔍 **News Search Mode**
- **Counterparty Management**: Add, remove, and manage companies to monitor
- **Keyword Filtering**: Set custom keywords to filter relevant articles
- **Search Modes**: Choose between counterparty-based or custom query search
- **Interactive Controls**: Set search queries and number of articles via sidebar
- **Real-time Analysis**: View results as they're processed
- **Interactive Charts**: Explore risk data with Plotly visualizations
- **Export Options**: Download results in JSON format

#### 📄 **PDF Analysis Mode**
- **PDF Upload**: Upload PDF documents for risk analysis
- **Text Extraction**: Automatically extract text from PDF files
- **Keyword Search**: Filter PDF content based on custom keywords
- **Risk Assessment**: Analyze extracted text for various risk categories
- **Text Preview**: View extracted text in expandable sections
- **Export Options**: Save analysis results and text previews

### 📟 Command Line Interface

#### Basic Usage
Run the tool with default settings (searches for "top news for finance" and collects 10 articles):

```bash
python main.py
```

#### Counterparty-based Monitoring
Monitor specific companies/organizations:

```bash
# Monitor single counterparty
python main.py --counterparties "Apple Inc"

# Monitor multiple counterparties
python main.py --counterparties "Apple Inc, Goldman Sachs, Microsoft Corporation"

# With custom number of articles per counterparty
python main.py --counterparties "Apple Inc, Goldman Sachs" --num-articles 8
```

#### Keyword Filtering
Filter articles based on specific keywords:

```bash
# Filter by keywords
python main.py --keywords "risk, financial, crisis"

# Combine counterparty monitoring with keyword filtering
python main.py --counterparties "Apple Inc, Goldman Sachs" --keywords "risk, financial"
```

#### Advanced Usage

**Custom search query**:
```bash
python main.py --query "market crash 2024"
```

**Collect more articles**:
```bash
python main.py --num-articles 20
```

**Analyze existing data only** (skip collection):
```bash
python main.py --analyze-only
```

**Custom output filename**:
```bash
python main.py --output-file my_analysis.json
```

### Command Line Options

- `--query`: Custom search query (default: "top news for finance")
- `--counterparties`: Comma-separated list of counterparties to monitor
- `--keywords`: Comma-separated list of keywords to filter articles
- `--num-articles`: Number of articles to collect per counterparty/query (default: 10)
- `--analyze-only`: Only analyze existing data, skip collection
- `--output-file`: Custom output filename for results

## Web Interface Features

### 🧭 Navigation System

1. **Sidebar Navigation**
   - Easy switching between News Search and PDF Analysis modes
   - Current page indicator
   - Consistent interface across both modes

2. **Page-Specific Controls**
   - News Search: Counterparty management, keyword filtering, search modes
   - PDF Analysis: File upload, keyword search, analysis options

### 🔍 News Search Features

1. **Counterparty Management**
   - Add companies/organizations to monitor
   - Remove individual counterparties
   - Clear all counterparties at once
   - Visual counterparty tags on articles

2. **Keyword Filtering**
   - Multi-line keyword input
   - Real-time article filtering
   - Keyword match highlighting
   - Filter statistics display

3. **Search Modes**
   - Counterparty-based: Search for each counterparty separately
   - Custom Query: Use a single custom search query
   - Flexible switching between modes

### 📄 PDF Analysis Features

1. **Document Upload**
   - Support for PDF file uploads
   - Automatic text extraction
   - File validation and error handling

2. **Text Processing**
   - Full text extraction from PDFs
   - Keyword-based text filtering
   - Paragraph-level content analysis
   - Text preview with expandable sections

3. **Risk Assessment**
   - Same risk analysis engine as news articles
   - Risk score calculation
   - Sentiment analysis
   - Category-based risk breakdown

### 📊 Dashboard Components

1. **Summary Metrics**
   - Total articles/documents analyzed
   - Overall risk score (0-10)
   - Sentiment score (-10 to +10)
   - Number of risk categories found
   - Counterparties monitored (News mode)
   - Document information (PDF mode)

2. **Interactive Charts**
   - Risk categories bar chart
   - Keyword frequency analysis
   - News source analysis scatter plot
   - Risk score gauges for top articles

3. **Content Display**
   - Article cards with counterparty tags
   - PDF text preview with keyword highlighting
   - Risk indicators and keywords found
   - Direct links to source articles (News mode)

4. **Data Tables**
   - Complete article list with risk scores
   - Counterparty information for each article
   - Matched keywords for filtered content
   - Source-by-source analysis
   - Exportable data

### 🎛️ User Controls

- **Navigation**: Easy switching between data sources
- **Search Mode**: Choose between counterparty-based or custom query search
- **Counterparty Management**: Add, remove, and manage companies to monitor
- **Keyword Input**: Set custom keywords for content filtering
- **Article Count**: Select 3-20 articles per counterparty/query
- **API Key Input**: Secure password field for SerpAPI key
- **File Upload**: PDF document upload for analysis
- **Auto-save**: Automatically save results to output directory
- **Export Options**: Download articles and analysis as JSON

## Output

The tool generates different types of output files in the `output/` directory:

### 1. News Articles (`finance_news_YYYYMMDD_HHMMSS.json`)
Contains the raw collected articles with:
- Article title, URL, and source
- Full text content
- Publication date and authors
- Meta information (keywords, summary, description)
- **Counterparty information** (when using counterparty-based search)
- **Matched keywords** (when using keyword filtering)

### 2. Risk Analysis (`risk_analysis_YYYYMMDD_HHMMSS.json`)
Contains comprehensive risk analysis:
- Overall risk and sentiment scores
- Risk breakdown by category
- Top risk articles identified
- Keyword frequency analysis
- Source-by-source risk analysis
- **Counterparty-specific risk analysis**

### 3. PDF Analysis (`pdf_analysis_YYYYMMDD_HHMMSS.json`)
Contains PDF analysis results:
- Original filename
- Extracted text length
- Extraction timestamp
- Text preview (first 1000 characters)
- Risk analysis results

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                    RISK MONITORING TOOL                      ║
║                                                              ║
║  Collecting and analyzing financial news for risk assessment ║
╚══════════════════════════════════════════════════════════════╝

🏢 Monitoring 3 counterparties:
   • Apple Inc
   • Goldman Sachs
   • Microsoft Corporation

🔍 Searching for articles about: Apple Inc
🔍 Searching for articles about: Goldman Sachs
🔍 Searching for articles about: Microsoft Corporation

🔍 Filtered 15 articles to 8 articles matching keywords

============================================================
📊 RISK MONITORING SUMMARY
============================================================

📰 NEWS COLLECTION:
   • Articles collected: 8
   • Counterparties monitored: Apple Inc, Goldman Sachs, Microsoft Corporation
   • Keywords filtered: risk, financial, market
   • Collection time: 2024-01-15 14:30:25

🔍 RISK ANALYSIS:
   • Overall risk score: 6.45/10
   • Sentiment score: -2.30 (-10 to +10)
   • Risk categories found: 4

⚠️  TOP RISKS IDENTIFIED:
   1. Apple Inc Faces Market Volatility Amid Tech Sector Concerns...
      Risk Score: 8.20 | Source: reuters.com
   2. Goldman Sachs Reports Financial Risk Exposure in Q4...
      Risk Score: 7.85 | Source: bloomberg.com

📈 RISK CATEGORIES:
   • Market Risk: 6 articles, avg severity: 5.20
   • Economic Risk: 4 articles, avg severity: 4.15
   • Geopolitical Risk: 2 articles, avg severity: 3.80
============================================================
```

## Configuration

You can customize the tool's behavior by modifying `config.py`:

- `SEARCH_QUERY`: Default search query
- `NUM_ARTICLES`: Default number of articles to collect
- `DEFAULT_COUNTERPARTIES`: Default list of counterparties to monitor
- `DEFAULT_KEYWORDS`: Default keywords for filtering
- `ARTICLES_PER_COUNTERPARTY`: Default articles per counterparty
- `SEARCH_DELAY`: Delay between searches (seconds)
- `REQUEST_TIMEOUT`: API request timeout
- `MAX_RETRIES`: Maximum retry attempts for failed requests

## Risk Scoring

The tool uses a sophisticated scoring system:

- **Risk Score (0-10)**: Higher scores indicate greater risk
- **Sentiment Score (-10 to +10)**: Negative values indicate bearish sentiment
- **Category Severity**: Normalized risk level per 1000 characters of text

### Scoring Weights
- Market Risk: 1.5x weight
- Economic Risk: 1.3x weight  
- Geopolitical Risk: 1.2x weight
- Sector Risk: 1.0x weight
- Positive Sentiment: -0.5x weight (reduces risk score)

## Dependencies

- `requests`: HTTP requests for API calls
- `beautifulsoup4`: HTML parsing
- `python-dotenv`: Environment variable management
- `pandas`: Data manipulation
- `newspaper3k`: Article content extraction
- `lxml`: XML/HTML parsing
- `streamlit`: Web application framework
- `plotly`: Interactive charts and visualizations
- `PyPDF2`: PDF text extraction

## API Usage

This tool uses SerpAPI's Google News search. The free tier includes:
- 100 searches per month
- Google News results
- Basic search functionality

For higher usage limits, consider upgrading your SerpAPI plan.

## Error Handling

The tool includes comprehensive error handling:
- API rate limiting and retries
- Network timeout handling
- Invalid URL handling
- Content extraction failures
- Configuration validation
- Counterparty validation
- PDF file validation and error handling

## Logging

All operations are logged to:
- Console output (INFO level)
- `risk_monitor.log` file (detailed logging)

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key**:
   ```bash
   cp env_example.txt .env
   # Edit .env and add your SerpAPI key
   ```

3. **Launch web interface**:
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Or use command line**:
   ```bash
   # Monitor specific companies
   python main.py --counterparties "Apple Inc, Goldman Sachs" --keywords "risk, financial"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. The risk analysis provided should not be considered as financial advice. Always conduct your own research and consult with financial professionals before making investment decisions.

## Support

For issues and questions:
1. Check the logs in `risk_monitor.log`
2. Verify your SerpAPI key is valid
3. Ensure all dependencies are installed
4. Check your internet connection

## Future Enhancements

- Real-time monitoring with scheduled runs
- Email/SMS alerts for high-risk events
- Integration with trading platforms
- Machine learning-based risk prediction
- Advanced web dashboard features
- Historical risk trend analysis
- Mobile-responsive design improvements
- Counterparty risk scoring and ranking
- Automated counterparty discovery
- Multi-language support for international companies
- Support for additional document formats (DOCX, TXT)
- Advanced PDF text extraction with OCR
- Document comparison and trend analysis 