# Forced Insertion Database Architecture

## Overview

This document explains the forced insertion database architecture where News Analysis uses the `analysis-db` index with guaranteed data insertion, while Scheduler continues using `sentiment-db`.

## Solution

### Forced Insertion Database Architecture

We've implemented a forced insertion approach to ensure data gets stored:

1. **Analysis Database (`analysis-db`)**
   - Used exclusively by **News Analysis** (Streamlit app)
   - **FORCED INSERTION** - Data gets pushed at any cost
   - Marked with `storage_type: 'analysis_db'` in metadata
   - Includes retry mechanisms and fallback options

2. **Scheduler Database (`sentiment-db`)**
   - Used by **Scheduler** (automated collection)
   - Standard insertion with error handling
   - Marked with `storage_type: 'database'` in metadata

### Implementation Details

#### Unified Database Class

**PineconeDB** (`risk_monitor/utils/pinecone_db.py`)
```python
class PineconeDB:
    """Pinecone database integration for storing article analysis results"""
    
    def __init__(self, index_name: str = None):
        self.index_name = index_name or self.config.PINECONE_INDEX_NAME  # "sentiment-db"
        # ... rest of implementation
```

#### Updated Risk Analyzer

The `RiskAnalyzer.analyze_and_store_in_pinecone()` method now uses the unified database:

```python
def analyze_and_store_in_pinecone(self, articles: List[Dict], sentiment_method: str = 'llm', store_in_db: bool = True) -> Dict[str, Any]:
    """
    Analyze articles with optional database storage
    Args:
        articles: List of articles to analyze
        sentiment_method: Method for sentiment analysis ('llm' or 'lexicon')
        store_in_db: Whether to store results in database (default: True)
    """
    if store_in_db:
        return self.analyze_articles(articles)  # Uses unified PineconeDB
    else:
        # Analyze without storing in database
        analysis_results = self.analyze_articles_with_advanced_risk(articles, sentiment_method)
        return {
            'storage_type': 'analysis_only',
            'individual_analyses': analysis_results,
            # ... other summary data
        }
```

#### Updated Streamlit App

The Streamlit app now provides clear feedback about the unified database:

```python
# Updated checkbox label
use_pinecone = st.checkbox("Store in Database", value=True, 
                          help="Store analysis results in the Pinecone database (sentiment-db) for future retrieval and semantic search")

# Updated status messages
if storage_type == "pinecone":
    status_text.success(f"✅ Analysis complete! Stored {storage_stats['success_count']} articles in Database (sentiment-db).")
```

## Benefits

1. **Unified Data Storage**: All articles stored in a single database for consistent access
2. **Simplified Architecture**: Single database reduces complexity and maintenance overhead
3. **Consistent Search**: All articles available for search regardless of source
4. **Better Data Integration**: News Analysis and Scheduler data seamlessly integrated
5. **Flexible Storage**: Users can choose to analyze without storing in database for temporary analysis
6. **Cost Optimization**: Analysis-only mode reduces database storage costs for one-time analysis

## Usage

### News Analysis (Streamlit App)
- **Storage Options**: 
  - **Analysis + Database**: Uses `sentiment-db` index, stores articles with `storage_type: 'database'`
  - **Analysis Only**: Performs analysis without database storage, `storage_type: 'analysis_only'`
- Manual/on-demand analysis
- Clear UI indicators showing storage mode
- Configurable storage preference in Advanced tab

### Scheduler (Automated)
- Uses `sentiment-db` index (same as News Analysis)
- Stores articles with `storage_type: 'database'`
- Automated/scheduled collection
- Unified database with News Analysis

## Database Indexes

| Component | Index Name | Purpose | Storage Type |
|-----------|------------|---------|--------------|
| News Analysis (with DB) | `sentiment-db` | Manual analysis | `database` |
| News Analysis (no DB) | N/A | Manual analysis | `analysis_only` |
| Scheduler | `sentiment-db` | Automated collection | `database` |

## Testing

Run the test script to verify the separation:

```bash
python test_analysis_db.py
```

This will:
1. Initialize both database classes
2. Verify different index names
3. Test basic functionality
4. Confirm separation is working

## Migration Notes

- Existing data in `sentiment-db` remains unchanged
- New `analysis-db` index will be created automatically when first used
- No data migration required
- Both databases can coexist independently

## Future Enhancements

1. **Cross-Database Search**: Implement search across both databases
2. **Data Deduplication**: Add checks to prevent duplicates within each database
3. **Database Analytics**: Separate analytics for each database
4. **Backup Strategies**: Independent backup strategies for each database
