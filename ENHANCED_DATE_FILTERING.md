# Enhanced Date Filtering with Fallback Support

## 🐛 **Problem Solved**

### Original Issue
- **Error**: `"cannot access local variable 'datetime' where it is not associated with a value"`
- **Cause**: `datetime` import was inside `if` blocks but used in `else` block, creating scope issues
- **Impact**: Date filtering was completely broken, causing runtime errors

### Additional Enhancement
- **Problem**: Not every article has a `publish_date` field
- **Impact**: Articles without publish dates were excluded from date filtering
- **Solution**: Added fallback to `analysis_timestamp` (database insertion date)

## 🛠️ **Technical Implementation**

### 1. Fixed DateTime Scope Issue
```python
# BEFORE (Broken):
if date_filter == "Last 7 days":
    from datetime import datetime, timedelta  # Import inside if block
elif date_filter == "Last 30 days":
    from datetime import datetime, timedelta  # Import inside elif block
else:
    target_date = datetime.strptime(date_filter, "%Y-%m-%d")  # ❌ datetime not in scope

# AFTER (Fixed):
if date_filter and date_filter != "All Dates":
    from datetime import datetime, timedelta  # ✅ Import at top of section
    try:
        if date_filter == "Last 7 days":
            cutoff_date = datetime.now() - timedelta(days=7)
        elif date_filter == "Last 30 days":
            cutoff_date = datetime.now() - timedelta(days=30)
        else:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d")  # ✅ datetime in scope
```

### 2. Enhanced Date Parsing with Fallback
```python
def _parse_article_date(self, article: Dict) -> datetime:
    """Parse article date with fallback to analysis timestamp"""
    # First try to get publish_date
    publish_date = article.get('publish_date', '')
    if publish_date and publish_date != 'N/A' and publish_date != 'Unknown':
        parsed_date = self._parse_date(publish_date)
        if parsed_date != datetime.min:
            return parsed_date
    
    # Fallback to analysis_timestamp from full_analysis metadata
    try:
        full_analysis = article.get('full_analysis', {})
        if isinstance(full_analysis, dict):
            analysis_timestamp = full_analysis.get('analysis_timestamp', '')
            if analysis_timestamp:
                return datetime.fromisoformat(analysis_timestamp.replace('Z', '+00:00'))
    except Exception as e:
        logger.debug(f"Could not parse analysis_timestamp: {e}")
    
    # If all else fails, return minimum date (article will be included in all filters)
    return datetime.min
```

### 3. Date Source Tracking
```python
def _get_date_source(self, article: Dict) -> str:
    """Get the source of the date used for filtering"""
    publish_date = article.get('publish_date', '')
    if publish_date and publish_date != 'N/A' and publish_date != 'Unknown':
        return "Original Publish Date"
    
    full_analysis = article.get('full_analysis', {})
    if isinstance(full_analysis, dict) and full_analysis.get('analysis_timestamp'):
        return "Database Insertion Date"
    
    return "No Date Available"
```

## 📅 **Date Filtering Logic**

### Priority Order
1. **Original Publish Date** - When available and valid
2. **Database Insertion Date** - Fallback when publish_date is missing/invalid
3. **Minimum Date** - Last resort (article included in all filters)

### Supported Date Formats
- **Publish Date Formats**:
  - `"2025-09-01 10:30:00"`
  - `"2025-09-01"`
  - `"09/01/2025"`
  - `"2025-09-01T10:30:00"`

- **Analysis Timestamp Format**:
  - `"2025-09-02T15:45:30.123456"` (ISO format)

### Filter Options
- **"All Dates"** - No filtering applied
- **"Last 7 days"** - Articles from last 7 days
- **"Last 30 days"** - Articles from last 30 days
- **Specific dates** - Articles on or after specific date (e.g., "2025-09-01")

## 🧪 **Test Results**

### Test Cases Verified
1. ✅ **Article with publish_date** → Uses original publish date
2. ✅ **Article without publish_date** → Falls back to database insertion date
3. ✅ **Article with no dates** → Returns minimum date (included in all filters)
4. ✅ **Date filtering logic** → Correctly identifies recent vs old articles
5. ✅ **Available dates** → Successfully extracts dates from database

### Sample Output
```
📅 Testing _parse_article_date method:
  Article 1: Article with publish_date
    Parsed Date: 2025-09-01 10:30:00
    Date Source: Original Publish Date

  Article 2: Article without publish_date
    Parsed Date: 2025-09-02 12:30:00.123456
    Date Source: Database Insertion Date

  Article 3: Article with no dates
    Parsed Date: 0001-01-01 00:00:00
    Date Source: No Date Available
```

## 🎯 **Benefits**

### 1. **Robust Date Filtering**
- No more runtime errors due to scope issues
- Comprehensive coverage of articles with and without publish dates
- Graceful fallback mechanism

### 2. **Enhanced User Experience**
- Date filtering now works for all articles
- Clear indication of date source in AI responses
- More accurate temporal analysis

### 3. **Better Data Utilization**
- Articles without publish dates are no longer excluded
- Database insertion date provides temporal context
- Improved filtering accuracy

### 4. **Maintainable Code**
- Clean separation of concerns
- Proper error handling
- Clear logging for debugging

## 🔧 **Files Modified**

1. **`risk_monitor/core/rag_service.py`**:
   - Fixed datetime scope issue in `search_articles()`
   - Added `_parse_article_date()` method with fallback logic
   - Added `_get_date_source()` helper method
   - Updated `get_available_dates()` to use enhanced parsing
   - Enhanced `format_context_for_llm()` to show date source

## 🚀 **Ready for Production**

The enhanced date filtering system is now:
- ✅ **Error-free** - No more datetime scope issues
- ✅ **Comprehensive** - Handles all article types
- ✅ **Robust** - Graceful fallback mechanisms
- ✅ **User-friendly** - Clear date source indication
- ✅ **Tested** - Verified with comprehensive test cases

The system will now provide accurate date filtering for all articles, whether they have original publish dates or rely on database insertion timestamps.
