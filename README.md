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
   - Create a `.env` file in the project root and add your API key:
   ```
   SERPAPI_KEY=your_actual_api_key_here
   ```

## Usage

### 🌐 Web Interface (Recommended)

Launch the interactive Streamlit web application:

```bash
# Windows (double-click or run)
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
- **Risk Analysis**: See risk scores, sentiment, and category breakdown for news articles
- **Export Options**: Download results in JSON format

#### 📄 **PDF Analysis Mode**
- **PDF Upload**: Upload PDF documents for risk analysis
- **Text Extraction**: Automatically extract text from PDF files
- **Keyword Search**: Filter PDF content based on custom keywords
- **Risk Assessment**: Analyze extracted text for various risk categories
- **Text Preview**: View extracted text in expandable sections
- **Export Options**: Save analysis results and text previews

## Branch Workflow

- All development should be done on the `dev` branch.
- The `prod` branch is for deployment and production releases only.
- Use pull requests to merge changes from `dev` to `prod`.
- Branch protection is recommended for `prod` to prevent direct pushes.

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

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key**:
   - Create a `.env` file and add your SerpAPI key:
   ```
   SERPAPI_KEY=your_actual_api_key_here
   ```

3. **Launch web interface**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (from `dev`)
3. Make your changes
4. Add tests if applicable
5. Submit a pull request to `dev`

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