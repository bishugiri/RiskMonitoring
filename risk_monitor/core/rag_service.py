"""
RAG (Retrieval-Augmented Generation) Service for Risk Monitor
Enables conversational AI that can query and analyze stored articles
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from risk_monitor.utils.pinecone_db import PineconeDB
from risk_monitor.config.settings import Config

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for conversational AI with Pinecone database"""
    
    def __init__(self):
        self.config = Config()
        self.pinecone_db = PineconeDB()
        # Use new OpenAI API
        import httpx
        self.client = OpenAI(api_key=self.config.get_openai_api_key(), http_client=httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        ))
        
        # Conversation cache for optimization
        self.conversation_cache = {
            'current_articles': [],
            'current_filters': {},
            'last_query': '',
            'cache_timestamp': None,
            'cache_duration': 300  # 5 minutes cache
        }
        
        print("🔧 RAG Service initialized with OpenAI client and PineconeDB")
        print("⚡ Conversation cache enabled for optimized follow-up queries")
        
    def _is_cache_valid(self, entity_filter: str = None, date_filter: str = None) -> bool:
        """Check if the conversation cache is still valid for the current filters"""
        if not self.conversation_cache['cache_timestamp']:
            return False
        
        # Check if cache has expired
        from datetime import datetime, timedelta
        cache_age = datetime.now() - self.conversation_cache['cache_timestamp']
        if cache_age.total_seconds() > self.conversation_cache['cache_duration']:
            print(f"⏰ Cache expired after {cache_age.total_seconds():.1f} seconds")
            return False
        
        # Check if filters match
        current_filters = self.conversation_cache['current_filters']
        if current_filters.get('entity_filter') != entity_filter:
            print(f"🔄 Entity filter changed: {current_filters.get('entity_filter')} → {entity_filter}")
            return False
        
        if current_filters.get('date_filter') != date_filter:
            print(f"🔄 Date filter changed: {current_filters.get('date_filter')} → {date_filter}")
            return False
        
        print(f"✅ Cache valid - using {len(self.conversation_cache['current_articles'])} cached articles")
        return True
    
    def _update_cache(self, articles: List[Dict], entity_filter: str = None, date_filter: str = None):
        """Update the conversation cache with new articles and filters"""
        self.conversation_cache['current_articles'] = articles
        self.conversation_cache['current_filters'] = {
            'entity_filter': entity_filter,
            'date_filter': date_filter
        }
        self.conversation_cache['cache_timestamp'] = datetime.now()
        print(f"💾 Cache updated with {len(articles)} articles")
    
    def search_articles_optimized(self, query: str, top_k: int = 5, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """OPTIMIZED search: Date → Entity → Query → Top 5 relevant articles"""
        print(f"⚡ OPTIMIZED SEARCH FLOW - INPUT:")
        print(f"   Query: '{query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        try:
            # Check if we can use cached articles for follow-up queries
            if self._is_cache_valid(entity_filter, date_filter) and self.conversation_cache['current_articles']:
                print(f"🚀 Using cached articles for follow-up query")
                cached_articles = self.conversation_cache['current_articles']
                
                # Apply semantic search on cached articles only
                print(f"🔍 Applying semantic search on {len(cached_articles)} cached articles...")
                relevant_articles = self._semantic_search_on_articles(cached_articles, query, top_k)
                print(f"✅ Found {len(relevant_articles)} relevant articles from cache")
                return relevant_articles
            
            # If no cache or cache invalid, perform full search
            print(f"🔄 Performing full database search (cache miss)")
            return self.search_articles_full(query, top_k, entity_filter, date_filter)
            
        except Exception as e:
            print(f"❌ Error in optimized search: {e}")
            logger.error(f"Error in optimized search: {e}")
            return []
    
    def _semantic_search_on_articles(self, articles: List[Dict], query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search on a subset of articles"""
        if not articles:
            return []
        
        try:
            # Create embeddings for the query
            query_embedding = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            ).data[0].embedding
            
            # Calculate similarity scores for each article
            scored_articles = []
            for article in articles:
                # Use title and text for similarity calculation
                article_text = f"{article.get('title', '')} {article.get('text', '')}"
                
                # Create embedding for article text
                article_embedding = self.client.embeddings.create(
                    input=article_text[:1000],  # Limit text length for efficiency
                    model="text-embedding-3-small"
                ).data[0].embedding
                
                # Calculate cosine similarity
                import numpy as np
                similarity = np.dot(query_embedding, article_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding)
                )
                
                scored_articles.append({
                    'article': article,
                    'score': similarity
                })
            
            # Sort by similarity score and return top_k
            scored_articles.sort(key=lambda x: x['score'], reverse=True)
            top_articles = [item['article'] for item in scored_articles[:top_k]]
            
            print(f"📊 Semantic search completed: {len(top_articles)} articles selected")
            return top_articles
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            logger.error(f"Error in semantic search: {e}")
            return articles[:top_k]  # Fallback to first top_k articles
    
    def search_articles_full(self, query: str, top_k: int = 5, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Full search: Date → Entity → Query → Top 5 relevant articles"""
        print(f"🔍 FULL SEARCH FLOW - INPUT:")
        print(f"   Query: '{query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        try:
            # Get total number of articles in database
            stats = self.pinecone_db.get_index_stats()
            total_articles = stats.get('total_vector_count', 0)
            print(f"📊 Database Stats: {total_articles} total articles")
            
            # OPTIMIZED FLOW: Date → Entity → Query → Top 5
            print(f"🔄 OPTIMIZED FLOW: Date → Entity → Query → Top {top_k}")
            
            # Step 1: Get ALL articles from database (no semantic search yet)
            print(f"📋 Step 1: Getting ALL articles from database...")
            all_articles = self.pinecone_db.get_all_articles(top_k=total_articles)
            print(f"✅ Retrieved {len(all_articles)} total articles")
            
            filtered_results = all_articles
            
            # Step 2: Apply DATE FILTER FIRST
            if date_filter and date_filter != "All Dates":
                print(f"📅 Step 2: Applying DATE FILTER FIRST - '{date_filter}'")
                original_count = len(filtered_results)
                
                from datetime import datetime, timedelta
                try:
                    if date_filter == "Last 7 days":
                        cutoff_date = datetime.now() - timedelta(days=7)
                    elif date_filter == "Last 30 days":
                        cutoff_date = datetime.now() - timedelta(days=30)
                    else:
                        # Specific date format: YYYY-MM-DD
                        cutoff_date = datetime.strptime(date_filter, "%Y-%m-%d")
                    
                    # Filter articles by date using analysis_timestamp
                    date_filtered_results = []
                    for article in filtered_results:
                        article_date = self._parse_article_date(article)
                        if article_date >= cutoff_date:
                            date_filtered_results.append(article)
                    
                    filtered_results = date_filtered_results
                    print(f"   ✅ Date filter result: {len(filtered_results)} articles (from {original_count})")
                    
                except Exception as e:
                    print(f"   ❌ Error applying date filter: {e}")
                    logger.error(f"Error applying date filter: {e}")
            else:
                print(f"📅 Step 2: No date filter applied")
            
            # Step 3: Apply ENTITY FILTER SECOND
            if entity_filter and entity_filter != "All Companies":
                print(f"🔍 Step 3: Applying ENTITY FILTER SECOND - '{entity_filter}'")
                original_count = len(filtered_results)
                
                # More flexible entity filtering - search in title, text, and entity field
                entity_filtered_results = []
                for article in filtered_results:
                    title = article.get('title', '').lower()
                    text = article.get('text', '').lower()
                    entity = article.get('entity', '').lower()
                    entity_filter_lower = entity_filter.lower()
                    
                    # Check if entity appears in title, text, or entity field
                    if (entity_filter_lower in title or 
                        entity_filter_lower in text or 
                        entity_filter_lower in entity):
                        entity_filtered_results.append(article)
                
                filtered_results = entity_filtered_results
                print(f"   ✅ Entity filter result: {len(filtered_results)} articles (from {original_count})")
            else:
                print(f"🔍 Step 3: No entity filter applied")
            
            # Step 4: Apply SEMANTIC SEARCH and get TOP 5
            print(f"🔍 Step 4: Applying SEMANTIC SEARCH - '{query}'")
            print(f"   ⚡ OPTIMIZATION: Getting top {top_k} most relevant articles only")
            
            if filtered_results:
                # Perform semantic search on filtered results
                relevant_articles = self._semantic_search_on_articles(filtered_results, query, top_k)
                print(f"   ✅ Semantic search result: {len(relevant_articles)} articles (from {len(filtered_results)})")
            else:
                print(f"   ⚠️  No articles to apply semantic search to")
                relevant_articles = []
            
            # Update cache with all filtered articles for follow-up queries
            self._update_cache(filtered_results, entity_filter, date_filter)
            
            print(f"📋 FILTERING STATUS:")
            print(f"   Date filter: Applied")
            print(f"   Entity filter: Applied")
            print(f"   Semantic search: Applied")
            print(f"   Final results: {len(relevant_articles)} articles (top {top_k})")
            print(f"📊 FINAL SEARCH RESULTS:")
            print(f"   Total articles found: {len(relevant_articles)}")
            print(f"   Searched: {len(filtered_results)} articles from {len(all_articles)} total")
            print(f"   Cache updated: {len(filtered_results)} articles for follow-up queries")
            
            logger.info(f"Optimized search completed: Found {len(relevant_articles)} relevant articles (searched {len(filtered_results)} articles from {len(all_articles)} total)")
            
            return relevant_articles
            
        except Exception as e:
            print(f"❌ Error in full search: {e}")
            logger.error(f"Error in full search: {e}")
            return []
    
    def search_articles(self, query: str, top_k: int = 50, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Search for articles using NEW FILTERING FLOW: Date → Entity → Query"""
        print(f"🔍 NEW FILTERING FLOW - INPUT:")
        print(f"   Query: '{query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        try:
            # Get total number of articles in database
            stats = self.pinecone_db.get_index_stats()
            total_articles = stats.get('total_vector_count', 0)
            print(f"📊 Database Stats: {total_articles} total articles")
            
            # NEW FLOW: Start with ALL articles, then apply filters progressively
            print(f"🔄 NEW FILTERING FLOW: Date → Entity → Query")
            
            # Step 1: Get ALL articles from database (no semantic search yet)
            print(f"📋 Step 1: Getting ALL articles from database...")
            all_articles = self.pinecone_db.get_all_articles(top_k=total_articles)
            print(f"✅ Retrieved {len(all_articles)} total articles")
            
            filtered_results = all_articles
            
            # Step 2: Apply DATE FILTER FIRST
            if date_filter and date_filter != "All Dates":
                print(f"📅 Step 2: Applying DATE FILTER FIRST - '{date_filter}'")
                original_count = len(filtered_results)
                
                from datetime import datetime, timedelta
                try:
                    if date_filter == "Last 7 days":
                        cutoff_date = datetime.now() - timedelta(days=7)
                    elif date_filter == "Last 30 days":
                        cutoff_date = datetime.now() - timedelta(days=30)
                    else:
                        # Specific date format: YYYY-MM-DD
                        cutoff_date = datetime.strptime(date_filter, "%Y-%m-%d")
                    
                    # Filter articles by date using analysis_timestamp
                    date_filtered_results = []
                    for article in filtered_results:
                        article_date = self._parse_article_date(article)
                        if article_date >= cutoff_date:
                            date_filtered_results.append(article)
                    
                    filtered_results = date_filtered_results
                    print(f"   ✅ Date filter result: {len(filtered_results)} articles (from {original_count})")
                    
                except Exception as e:
                    print(f"   ❌ Error applying date filter: {e}")
                    logger.error(f"Error applying date filter: {e}")
            else:
                print(f"📅 Step 2: No date filter applied")
            
            # Step 3: Apply ENTITY FILTER SECOND
            if entity_filter and entity_filter != "All Companies":
                print(f"🔍 Step 3: Applying ENTITY FILTER SECOND - '{entity_filter}'")
                original_count = len(filtered_results)
                
                # More flexible entity filtering - search in title, text, and entity field
                entity_filtered_results = []
                for article in filtered_results:
                    title = article.get('title', '').lower()
                    text = article.get('text', '').lower()
                    entity = article.get('entity', '').lower()
                    entity_filter_lower = entity_filter.lower()
                    
                    # Check if entity appears in title, text, or entity field
                    if (entity_filter_lower in title or 
                        entity_filter_lower in text or 
                        entity_filter_lower in entity):
                        entity_filtered_results.append(article)
                
                filtered_results = entity_filtered_results
                print(f"   ✅ Entity filter result: {len(filtered_results)} articles (from {original_count})")
            else:
                print(f"🔍 Step 3: No entity filter applied")
            
            # Step 4: Apply USER QUERY FILTER (semantic search on filtered results)
            if query and query.strip():
                print(f"🔍 Step 4: Applying USER QUERY FILTER - '{query}'")
                original_count = len(filtered_results)
                
                # Perform semantic search on the already filtered results
                if filtered_results:
                    # Get embeddings for filtered articles
                    query_embedding = self.pinecone_db.generate_embedding(query)
                    
                    # Calculate similarity scores for filtered articles
                    scored_articles = []
                    for article in filtered_results:
                        # Get article text for embedding
                        article_text = article.get('text', '')[:1000]  # Limit text length
                        if article_text:
                            try:
                                article_embedding = self.pinecone_db.generate_embedding(article_text)
                                # Calculate cosine similarity
                                similarity = self._calculate_cosine_similarity(query_embedding, article_embedding)
                                scored_articles.append((article, similarity))
                            except Exception as e:
                                # If embedding fails, use low similarity
                                scored_articles.append((article, 0.0))
                        else:
                            scored_articles.append((article, 0.0))
                    
                    # Sort by similarity score and take top results
                    scored_articles.sort(key=lambda x: x[1], reverse=True)
                    filtered_results = [article for article, score in scored_articles[:top_k]]
                    
                    print(f"   ✅ Query filter result: {len(filtered_results)} articles (from {original_count})")
                else:
                    print(f"   ⚠️  No articles to apply query filter to")
            else:
                print(f"🔍 Step 4: No query filter applied")
            
            print(f"📋 FILTERING STATUS:")
            print(f"   Date filter: {'Applied' if date_filter and date_filter != 'All Dates' else 'None'}")
            print(f"   Entity filter: {'Applied' if entity_filter and entity_filter != 'All Companies' else 'None'}")
            print(f"   Query filter: {'Applied' if query and query.strip() else 'None'}")
            print(f"   Final filtered results: {len(filtered_results)} articles")
            
            # Log comprehensive search results
            print(f"📊 FINAL SEARCH RESULTS:")
            print(f"   Total articles found: {len(filtered_results)}")
            print(f"   Searched: {len(all_articles)} articles from {total_articles} total")
            logger.info(f"New filtering flow completed: Found {len(filtered_results)} relevant articles for query: '{query}' (searched {len(all_articles)} articles from {total_articles} total)")
            
            # If we have results, log some statistics for debugging
            if filtered_results:
                sentiment_distribution = {}
                for article in filtered_results:
                    sentiment = article.get('sentiment_category', 'Unknown')
                    sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
                
                print(f"📊 Sentiment distribution: {sentiment_distribution}")
                logger.info(f"Sentiment distribution in results: {sentiment_distribution}")
                
                # DEBUG: Show detailed info about filtered results
                print(f"\n📋 FILTERED RESULTS DETAILS:")
                for i, article in enumerate(filtered_results[:5], 1):  # Show first 5
                    print(f"   Article {i}:")
                    print(f"      Title: {article.get('title', 'Unknown')[:60]}...")
                    print(f"      Text length: {len(article.get('text', ''))} chars")
                    print(f"      Sentiment: {article.get('sentiment_category', 'Unknown')} (score: {article.get('sentiment_score', 0)})")
                    print(f"      Risk Score: {article.get('risk_score', 0)}")
                    print(f"      Entity: {article.get('entity', 'None')}")
                    print(f"      Analysis Timestamp: {article.get('analysis_timestamp', 'None')}")
                    print()
            
            print(f"✅ NEW FILTERING FLOW - OUTPUT: {len(filtered_results)} articles")
            print("=" * 80)
            return filtered_results
        except Exception as e:
            print(f"❌ Error in new filtering flow: {e}")
            logger.error(f"Error in new filtering flow: {e}")
            return []
    
    def _parse_article_date(self, article: Dict) -> datetime:
        """Parse article date using ONLY analysis_timestamp for filtering"""
        # Use ONLY analysis_timestamp from metadata (when stored in database)
        try:
            analysis_timestamp = article.get('analysis_timestamp', '')
            
            if analysis_timestamp:
                parsed_date = datetime.fromisoformat(analysis_timestamp.replace('Z', '+00:00'))
                return parsed_date
        except Exception as e:
            logger.debug(f"Could not parse analysis_timestamp: {e}")
        
        # If analysis_timestamp is not available, return minimum date (article will be included in all filters)
        return datetime.min

    def _get_date_source(self, article: Dict) -> str:
        """Get the source of the date used for filtering"""
        analysis_timestamp = article.get('analysis_timestamp', '')
        
        if analysis_timestamp:
            return "Database Storage Date (analysis_timestamp)"
        
        return "No Date Available"
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _summarize_articles_for_context(self, articles: List[Dict], max_chars: int) -> List[Dict]:
        """Summarize articles to fit within context limits"""
        print(f"   📝 SUMMARIZATION PROCESS:")
        print(f"      Target max chars: {max_chars}")
        
        summarized_articles = []
        current_total = 0
        
        for i, article in enumerate(articles):
            original_text = article.get('text', '')
            original_length = len(original_text)
            
            # Calculate target length for this article
            remaining_chars = max_chars - current_total
            if remaining_chars <= 0:
                print(f"      ⚠️  Article {i+1}: Skipped (context full)")
                break
            
            # If article is too long, summarize it
            if original_length > remaining_chars:
                target_length = min(remaining_chars, 2000)  # Cap at 2000 chars per article
                print(f"      📝 Article {i+1}: Summarizing {original_length} -> {target_length} chars")
                
                # Create summary by taking first part and key points
                summary_text = self._create_article_summary(original_text, target_length)
                article['text'] = summary_text
                article['_summarized'] = True
            else:
                print(f"      ✅ Article {i+1}: Using full text ({original_length} chars)")
                article['_summarized'] = False
            
            summarized_articles.append(article)
            current_total += len(article.get('text', ''))
            
            if current_total >= max_chars:
                print(f"      ⚠️  Context limit reached after {i+1} articles")
                break
        
        print(f"      📊 Summarization complete: {len(summarized_articles)} articles, {current_total} total chars")
        return summarized_articles
    
    def _create_article_summary(self, text: str, max_length: int) -> str:
        """Create a concise summary of article text"""
        if len(text) <= max_length:
            return text
        
        # Take first part and add key points
        first_part = text[:max_length//2]
        
        # Find key sentences (simple heuristic)
        sentences = text.split('. ')
        key_sentences = []
        
        # Look for sentences with important keywords
        important_keywords = ['earnings', 'revenue', 'profit', 'loss', 'growth', 'decline', 'announce', 'launch', 'partnership']
        
        for sentence in sentences[1:]:  # Skip first sentence (already in first_part)
            if any(keyword in sentence.lower() for keyword in important_keywords):
                key_sentences.append(sentence)
                if len('. '.join(key_sentences)) > max_length//2:
                    break
        
        summary = first_part + "\n\nKey Points:\n" + '. '.join(key_sentences)
        
        # Truncate if still too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        if not date_str or date_str == 'N/A' or date_str == 'Unknown':
            return datetime.min
        
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return minimum date
            return datetime.min
        except Exception:
            return datetime.min
    
    def format_context_for_llm(self, articles: List[Dict]) -> str:
        """Format retrieved articles into context for LLM with COMPLETE article data"""
        print(f"\n📝 FORMAT CONTEXT FOR LLM - INPUT:")
        print(f"   Articles count: {len(articles)}")
        print("=" * 80)
        
        if not articles:
            print(f"❌ No articles provided")
            return "No relevant articles found."
        
        # STAGE 3: Optional Summarization for Context Management
        print(f"\n📋 STAGE 3: CONTEXT SIZE MANAGEMENT")
        max_context_chars = 40000  # Conservative limit to prevent token overflow
        total_text_length = sum(len(article.get('text', '')) for article in articles)
        print(f"   Total text length: {total_text_length} characters")
        print(f"   Context limit: {max_context_chars} characters")
        
        if total_text_length > max_context_chars:
            print(f"   ⚠️  Context size exceeds limit, applying summarization")
            articles = self._summarize_articles_for_context(articles, max_context_chars)
            print(f"   ✅ Summarization applied, {len(articles)} articles processed")
        else:
            print(f"   ✅ Context size within limits, no summarization needed")
        
        # Limit articles to prevent context length exceeded error
        max_articles = 15  # Reduced to accommodate full article data
        if len(articles) > max_articles:
            print(f"⚠️  Limiting articles from {len(articles)} to {max_articles}")
            logger.info(f"Limiting articles from {len(articles)} to {max_articles} to accommodate complete article data")
            articles = articles[:max_articles]
        
        print(f"📝 Processing {len(articles)} articles for context...")
        
        # DEBUG: Show input articles structure
        print(f"\n📋 INPUT ARTICLES STRUCTURE:")
        for i, article in enumerate(articles[:3], 1):  # Show first 3
            print(f"   Article {i} keys: {list(article.keys())}")
            print(f"      Title: {article.get('title', 'Unknown')[:50]}...")
            print(f"      Text length: {len(article.get('text', ''))} chars")
            print(f"      Has sentiment_analysis: {'sentiment_analysis' in article}")
            print(f"      Has risk_analysis: {'risk_analysis' in article}")
            print(f"      Has analysis_timestamp: {'analysis_timestamp' in article}")
            
            # Debug sentiment score extraction
            sentiment_analysis = article.get('sentiment_analysis', {})
            direct_sentiment_score = article.get('sentiment_score', 'Not found')
            direct_score = article.get('score', 'Not found')
            sentiment_score = sentiment_analysis.get('score', 'Not found') if isinstance(sentiment_analysis, dict) else 'Not found'
            print(f"      Sentiment score fields:")
            print(f"         sentiment_analysis.score: {sentiment_score}")
            print(f"         article.sentiment_score: {direct_sentiment_score}")
            print(f"         article.score: {direct_score}")
            
            # Debug risk score extraction
            risk_analysis = article.get('risk_analysis', {})
            direct_risk_score = article.get('risk_score', 'Not found')
            risk_score = risk_analysis.get('risk_score', 'Not found') if isinstance(risk_analysis, dict) else 'Not found'
            print(f"      Risk score fields:")
            print(f"         risk_analysis.risk_score: {risk_score}")
            print(f"         article.risk_score: {direct_risk_score}")
            print()
        
        context_parts = []
        
        # Add comprehensive dataset overview
        total_articles = len(articles)
        context_parts.append(f"""
## DATASET OVERVIEW
Total relevant articles found: {total_articles}
Query coverage: Complete article data with full metadata
Analysis scope: Full article content and comprehensive analysis
""")
        
        # Group articles by sentiment for better analysis
        sentiment_groups = {}
        for article in articles:
            sentiment = article.get('sentiment_category', 'Unknown')
            if sentiment not in sentiment_groups:
                sentiment_groups[sentiment] = []
            sentiment_groups[sentiment].append(article)
        
        # Add sentiment distribution
        sentiment_summary = []
        for sentiment, articles_list in sentiment_groups.items():
            sentiment_summary.append(f"{sentiment}: {len(articles_list)} articles")
        
        context_parts.append(f"""
## SENTIMENT DISTRIBUTION
{', '.join(sentiment_summary)}

## COMPLETE ARTICLE DATA
""")
        
        # Format each article with COMPLETE metadata and full content
        for i, article in enumerate(articles, 1):
            # Extract ALL available metadata fields
            title = article.get('title', 'Unknown Title')
            source_info = article.get('source', {})
            source_name = source_info.get('name', 'Unknown Source') if isinstance(source_info, dict) else str(source_info)
            url = article.get('url', '')
            link = article.get('link', '')
            publish_date = article.get('publish_date', 'Unknown Date')
            date = article.get('date', '')
            authors = article.get('authors', [])
            summary = article.get('summary', '')
            keywords = article.get('keywords', [])
            meta_description = article.get('meta_description', '')
            text = article.get('text', 'No text available')
            entity = article.get('entity', '')
            matched_keywords = article.get('matched_keywords', [])
            extraction_time = article.get('extraction_time', '')
            
            # Sentiment analysis data - check multiple possible fields
            sentiment_analysis = article.get('sentiment_analysis', {})
            
            # Try multiple possible sentiment score fields with priority order
            sentiment_score = 0
            if isinstance(sentiment_analysis, dict):
                sentiment_score = sentiment_analysis.get('score', 0)
            
            # If not found in sentiment_analysis, check direct article fields
            if sentiment_score == 0:
                sentiment_score = article.get('sentiment_score', 0)
            
            # If still not found, check other possible fields
            if sentiment_score == 0:
                sentiment_score = article.get('score', 0)
            
            # If still not found, check for any numeric sentiment field
            if sentiment_score == 0:
                for key, value in article.items():
                    if 'sentiment' in key.lower() and isinstance(value, (int, float)) and value != 0:
                        sentiment_score = value
                        break
            
            sentiment_category = sentiment_analysis.get('category', article.get('sentiment_category', 'Unknown')) if isinstance(sentiment_analysis, dict) else article.get('sentiment_category', 'Unknown')
            sentiment_justification = sentiment_analysis.get('justification', '') if isinstance(sentiment_analysis, dict) else ''
            
            # Risk analysis data - check multiple possible fields
            risk_analysis = article.get('risk_analysis', {})
            
            # Try multiple possible risk score fields with priority order
            risk_score = 0
            if isinstance(risk_analysis, dict):
                risk_score = risk_analysis.get('risk_score', 0)
            
            # If not found in risk_analysis, check direct article fields
            if risk_score == 0:
                risk_score = article.get('risk_score', 0)
            
            # If still not found, check other possible fields
            if risk_score == 0:
                risk_score = article.get('score', 0)
            
            # If still not found, check for any numeric risk field
            if risk_score == 0:
                for key, value in article.items():
                    if 'risk' in key.lower() and isinstance(value, (int, float)) and value != 0:
                        risk_score = value
                        break
            
            risk_categories = risk_analysis.get('risk_categories', {}) if isinstance(risk_analysis, dict) else {}
            risk_indicators = risk_analysis.get('risk_indicators', []) if isinstance(risk_analysis, dict) else []
            
            # Include COMPLETE article data
            article_context = f"""
### [REFERENCE {i}] - {title}

**COMPLETE ARTICLE METADATA:**
- Title: {title}
- Source: {source_name}
- URL: {url}
- Link: {link}
- Published Date: {publish_date}
- Date: {date}
- Date Source: {self._get_date_source(article)}
- Authors: {', '.join(authors) if authors else 'Unknown'}
- Entity: {entity}
- Extraction Time: {extraction_time}
- Meta Description: {meta_description}

**CONTENT DATA:**
- Summary: {summary if summary else 'No summary available'}
- Keywords: {', '.join(keywords) if keywords else 'No keywords'}
- Matched Keywords: {', '.join(matched_keywords) if matched_keywords else 'None'}

**SENTIMENT ANALYSIS:**
- Category: {sentiment_category}
- Score: {sentiment_score}
- Justification: {sentiment_justification}

**RISK ANALYSIS:**
- Risk Score: {risk_score}
- Risk Categories: {json.dumps(risk_categories, indent=2) if risk_categories else 'None'}
- Risk Indicators: {', '.join(risk_indicators) if risk_indicators else 'None'}

**FULL ARTICLE TEXT:**
{text}

---
"""
            context_parts.append(article_context)
        
        # Add flexible analysis instructions
        context_parts.append(f"""
## ANALYSIS INSTRUCTIONS
- You have access to {total_articles} articles with COMPLETE data including full text, metadata, and analysis
- Use the exact metadata and content provided to answer the user's query
- **CRITICAL**: When user asks for "full article" or specific article by title, provide the ENTIRE article text from the 'text' field
- **CRITICAL**: When user asks for links, provide the exact URL from the article metadata
- **CRITICAL**: When user asks for a specific article by title, find that exact article and provide its complete text content
- Choose the best output format based on the user's question
- Reference specific articles when making claims
- Provide accurate, data-driven responses using the complete information available
- Format your response in the most helpful way for the user's specific question

## SPECIFIC RESPONSE FORMATS:
- **For "provide me full article on [title]"**: Find the article with that exact title and provide its complete text content
- **For "provide me link"**: Provide the exact URL from the article metadata
- **For general analysis**: Provide comprehensive analysis with specific references
""")
        
        final_context = "\n".join(context_parts)
        print(f"📝 FORMAT CONTEXT FOR LLM - OUTPUT:")
        print(f"   Final context length: {len(final_context)} characters")
        print(f"   Articles processed: {len(articles)}")
        print(f"   Average article text length: {sum(len(article.get('text', '')) for article in articles) // len(articles) if articles else 0} chars")
        
        # Production-level context analysis
        print(f"\n📋 PRODUCTION CONTEXT ANALYSIS:")
        print(f"   Total context size: {len(final_context)} characters")
        print(f"   Estimated tokens: ~{len(final_context) // 4} tokens")
        print(f"   Context efficiency: {'✅ Optimal' if len(final_context) < 40000 else '⚠️ Large'}")
        
        # Show summarization status
        summarized_count = sum(1 for article in articles if article.get('_summarized', False))
        if summarized_count > 0:
            print(f"   Summarized articles: {summarized_count}/{len(articles)}")
        
        # DEBUG: Show context structure
        print(f"\n📋 CONTEXT STRUCTURE BREAKDOWN:")
        print(f"   Dataset overview: ~{len(context_parts[0])} chars")
        print(f"   Sentiment distribution: ~{len(context_parts[1])} chars")
        print(f"   Article data header: ~{len(context_parts[2])} chars")
        print(f"   Individual articles: ~{sum(len(part) for part in context_parts[3:-1])} chars")
        print(f"   Analysis instructions: ~{len(context_parts[-1])} chars")
        
        print("=" * 80)
        return final_context
    
    def generate_response(self, user_query: str, articles: List[Dict]) -> Dict[str, Any]:
        """Generate AI response based on retrieved articles"""
        print(f"\n🤖 GENERATE RESPONSE - INPUT:")
        print(f"   User Query: '{user_query}'")
        print(f"   Articles count: {len(articles)}")
        print("=" * 80)
        
        try:
            # Format context
            print(f"📝 Formatting context for LLM...")
            context = self.format_context_for_llm(articles)
            print(f"✅ Context formatted: {len(context)} characters")
            
            # DEBUG: Show context preview
            print(f"\n📋 CONTEXT PREVIEW (first 500 chars):")
            print(f"{context[:500]}...")
            print()
            
            # Create system prompt
            print(f"📝 Creating system prompt...")
            
            # Create system prompt with database schema
            system_prompt = """You are an expert AI Financial Assistant specializing in financial risk monitoring and market analysis. You have access to a comprehensive database of analyzed financial news articles, company reports, and market data with COMPLETE metadata, full article text, and detailed sentiment/risk analysis.

**CRITICAL: You are NOT performing real-time sentiment analysis. You are using PRE-STORED sentiment scores from the database. Do NOT analyze article text to generate sentiment scores. Use ONLY the sentiment scores provided in the metadata.**

**STRICT DATA USAGE RULES:**
- **ONLY use data provided in the articles from the database**
- **DO NOT generate, infer, or create any information not present in the provided data**
- **DO NOT use external knowledge or general financial knowledge**
- **DO NOT perform real-time analysis of article content**
- **If information is not in the provided articles, say "This information is not available in the provided data"**
- **Base ALL responses strictly on the article metadata and content provided**

## DATABASE JSON STRUCTURE (Pinecone Records):

Each article in the database is stored as a JSON record with the following exact structure:

```json
{
  "id": "unique_article_id",
  "article_id": "unique_article_id",
  "title": "Article Title",
  "text": "FULL ARTICLE CONTENT - Complete article text",
  "url": "https://article-url.com",
  "source": "Source Name",
  "publish_date": "YYYY-MM-DD or N/A",
  "authors": ["Author1", "Author2"] or [],
  "entity": "Company/Entity Name",
  "summary": "Article summary or empty string",
  "keywords": ["keyword1", "keyword2"] or [],
  "meta_description": "Meta description text",
  "extraction_time": 1756930962.399424,
  "analysis_timestamp": "2025-09-04T02:12:41.340621",
  
  // SENTIMENT ANALYSIS FIELDS (PRE-STORED):
  "sentiment_score": 0.0,  // EXACT numeric value (-1 to 1 scale)
  "sentiment_category": "Neutral",  // "Positive", "Negative", "Neutral"
  "sentiment_justification": "Detailed justification text",
  "sentiment_method": "dual",
  "positive_count": 0,
  "negative_count": 0,
  "total_relevant": 0,
  
  // RISK ANALYSIS FIELDS (PRE-STORED):
  "risk_score": 0,  // EXACT numeric value
  "risk_method": "Ilm_advanced",
  "risk_categories": {},  // JSON object with risk categories
  "risk_indicators": [],  // Array of risk indicators
  
  // ANALYSIS METADATA:
  "analysis_method": "dual",
  "storage_type": "database",
  "keywords_found": [],
  "full_analysis": "JSON string with detailed analysis",
  "full_article_data": "JSON string with article metadata"
}
```

## CRITICAL FIELD MAPPING FOR QUERIES:

**For Sentiment Score Queries:**
- PRIMARY: `sentiment_score` (direct field)
- FALLBACK: `sentiment_analysis.score` (if sentiment_analysis is a nested object)
- **USE EXACT VALUE**: If sentiment_score = 0.0, report "Sentiment Score: 0.0"
- **USE EXACT VALUE**: If sentiment_score = -0.2, report "Sentiment Score: -0.2"

**For Risk Score Queries:**
- PRIMARY: `risk_score` (direct field)
- FALLBACK: `risk_analysis.risk_score` (if risk_analysis is a nested object)
- **USE EXACT VALUE**: If risk_score = 1.8889308651303365, report "Risk Score: 1.8889308651303365"
- **USE EXACT VALUE**: If risk_score = 0, report "Risk Score: 0"

**For Article Content Queries:**
- PRIMARY: `text` field contains the FULL article content
- PRIMARY: `title` field contains the article title
- PRIMARY: `url` field contains the article URL

**For Article Metadata Queries:**
- `source`: Source name
- `entity`: Company/entity name
- `publish_date`: Publication date
- `authors`: Array of authors
- `summary`: Article summary
- `keywords`: Array of keywords

## YOUR EXPERTISE & CAPABILITIES:

**Financial Analysis Expertise:**
- Market sentiment analysis and trend identification
- Company performance evaluation and risk assessment
- Sector-specific insights and competitive analysis
- Financial metrics interpretation and forecasting
- Risk factor identification and impact assessment

**Data Analysis Capabilities:**
- **PRE-STORED sentiment analysis** with detailed scoring and categorization (do NOT perform real-time analysis)
- Risk assessment across multiple categories (market, geopolitical, sector, regulatory)
- Keyword-based risk indicator identification
- Source credibility and bias evaluation
- Temporal analysis and trend identification

## COMPLETE DATA STRUCTURE YOU CAN ACCESS:

**Complete Article Data:**
- FULL ARTICLE TEXT: Complete article content stored in the 'text' field
- Title, source, publish date, authors, URL, link
- Summary, keywords, meta description, entity
- Extraction timestamps and analysis methodology

**Sentiment Analysis (PRE-STORED DATA):**
- Sentiment score (-1 to 1 scale) and category (Positive/Negative/Neutral) - **USE THESE EXACT VALUES**
- Sentiment justification and detailed analysis - **USE PRE-STORED JUSTIFICATION**
- Positive/negative keyword counts and total relevant terms - **USE PRE-STORED COUNTS**
- **DO NOT PERFORM REAL-TIME SENTIMENT ANALYSIS**

**Risk Analysis:**
- Overall risk score and detailed risk categories
- Specific risk indicators and keywords found
- Risk severity scoring and categorization
- Complete risk assessment data

**Complete Metadata:**
- All article metadata including source details, dates, authors
- Matched keywords and entity information
- Full analysis results with timestamps

## RESPONSE GUIDELINES:

**1. Complete Data Utilization:**
- You have access to FULL ARTICLE TEXT for each article
- Use ALL relevant articles from the database for complete analysis
- Reference specific articles using [REFERENCE X] format
- Include exact sentiment scores, risk scores, and specific data points
- Provide source diversity by citing multiple sources and time periods
- **STRICT RULE: Only use information present in the provided articles**
- **STRICT RULE: Do not add external knowledge or assumptions**

**2. Query-Specific Responses:**
- **"Summarize this article"**: Provide detailed summaries with key insights from the FULL TEXT
- **"Show me the full article"** or **"provide me full article"**: Share the COMPLETE article text from the 'text' field
- **"What does the article say about..."**: Use the FULL TEXT to answer specific questions
- **"Give me the article with title..."** or **"provide me full article on this [title]"**: Find that exact article and provide its COMPLETE text content
- **"What are the main points?"**: Extract key points from the FULL ARTICLE TEXT
- **"provide me link"** or **"give me the link"**: Provide the exact URL from the article metadata

**3. CRITICAL INSTRUCTIONS FOR SPECIFIC ARTICLE REQUESTS:**
- When user asks for a specific article by title, you MUST find that exact article in the provided data
- You MUST provide the complete text content from the 'text' field of that specific article
- You MUST provide the exact URL from the metadata of that specific article
- Do NOT provide summaries or analysis - provide the actual article content
- Format the response as: "Here is the complete article: [FULL TEXT]" followed by "Link: [URL]"
- **If the specific article is not found in the provided data, say: "The article '[title]' is not found in the provided database"**

**4. CRITICAL INSTRUCTIONS FOR METRIC QUERIES:**
- When user asks for "sentiment score of [article title]", find that exact article and provide ONLY the exact numeric sentiment score
- When user asks for "risk score of [article title]", find that exact article and provide ONLY the exact numeric risk score
- When user asks for "metrics and link", provide ONLY the exact scores and URL, no additional commentary
- Use the EXACT numeric values from the metadata (e.g., -0.4, 10.0), not rounded or approximated values
- Format metric responses as: "Sentiment Score: [exact number]" and "Risk Score: [exact number]"
- **CRITICAL**: Look for sentiment scores in these fields: 'sentiment_analysis.score', 'sentiment_score', 'score'
- **CRITICAL**: Look for risk scores in these fields: 'risk_analysis.risk_score', 'risk_score'
- **CRITICAL**: Do NOT default to 0 if the actual score is different (e.g., -0.2, 0.8, 1.8889308651303365)
- **CRITICAL**: Use the exact numeric value as stored in the database, even if it's negative or decimal
- **EXAMPLE**: If the data shows "Sentiment Score: -0.2", respond with "Sentiment Score: -0.2", NOT "Sentiment Score: 0"
- **EXAMPLE**: If the data shows "Risk Score: 1.8889308651303365", respond with "Risk Score: 1.8889308651303365", NOT "Risk Score: 0"
- **If the specific article or metric is not found, say: "The requested information is not available in the provided data"**

**4. Financial Intelligence:**
- Offer actionable insights based on sentiment and risk analysis **FROM THE PROVIDED DATA ONLY**
- Identify trends, patterns, and anomalies in the data **FROM THE PROVIDED DATA ONLY**
- Provide context for financial implications and market impact **BASED ON THE PROVIDED DATA ONLY**
- Suggest potential investment or risk mitigation strategies **BASED ON THE PROVIDED DATA ONLY**
- **DO NOT use external financial knowledge or market insights**

**5. User Query Types You Can Handle:**
- **Article Summaries**: Provide detailed summaries with key insights from full text
- **Full Article Content**: When user asks for "full article" or "complete article", provide the ENTIRE article text from the 'text' field
- **Specific Article Requests**: When user asks for a specific article by title, find that exact article and provide its complete content
- **Article Links**: When user asks for links, provide the exact URL from the metadata
- **Headline Requests**: When user asks for "headlines" or "article headlines", provide ONLY the article titles in a simple list
- **Sentiment Analysis**: Use pre-stored sentiment scores from the database, do NOT perform real-time analysis
- **Risk Assessment**: Analyze risk factors and their implications
- **Company Analysis**: Evaluate company performance and outlook
- **Market Trends**: Identify sector and market-wide patterns
- **Comparative Analysis**: Compare companies, sectors, or time periods
- **Data Queries**: Answer questions about specific data points or metrics
- **Metric Queries**: When user asks for specific scores, provide ONLY the exact numeric values from metadata

**6. Response Flexibility:**
- Choose the most appropriate response format based on the user's question
- You can provide summaries, detailed analysis, bullet points, tables, or any format that best serves the user
- Let the user's query guide your response structure
- Be flexible and adaptive in your communication style
- **CRITICAL**: When user asks for "full article" or specific article content, provide the COMPLETE text from the 'text' field, not just summaries

**7. Data Availability Handling:**
- **If no articles are provided**: Say "No articles are available in the database for this query"
- **If specific article not found**: Say "The article '[title]' is not found in the provided database"
- **If specific metric not available**: Say "The requested metric is not available in the provided data"
- **If data is incomplete**: Say "The requested information is incomplete in the provided data"
- **Never make up or infer information not present in the articles**

**7. Professional Communication:**
- Maintain a helpful, conversational tone
- Use clear, accessible language while being technically accurate
- Provide context for complex financial concepts
- Be transparent about data limitations or uncertainties

## IMPORTANT REMINDERS:

- You have access to COMPLETE article text and metadata - use it for detailed responses
- **CRITICAL**: When user asks for "full article" or specific article by title, provide the ENTIRE article text from the 'text' field
- **CRITICAL**: When user asks for links, provide the exact URL from the article metadata
- Choose the best output format for the user's specific question
- Always cite specific articles and data points to support your analysis
- Consider both positive and negative sentiment for balanced insights
- Evaluate risk factors across multiple categories
- Provide time-relevant context for financial analysis
- Be helpful, accurate, and actionable in your responses
- Format your response in the most useful way for the user's query

Remember: You are a trusted financial advisor AI that provides data-driven insights based on comprehensive analysis of real financial news and market data with access to complete article content. When users ask for specific articles or full content, provide the complete text, not just summaries."""

            # Create user prompt with context and database schema
            user_prompt = f"""User Question: {user_query}

Here is the COMPLETE relevant data from your financial database with FULL ARTICLE TEXT:

{context}

**DATABASE SCHEMA REFERENCE:**
Each article record contains these exact fields:
- `sentiment_score`: Direct numeric value (e.g., 0.0, -0.2, 0.8)
- `risk_score`: Direct numeric value (e.g., 0, 1.8889308651303365)
- `text`: Complete article content
- `title`: Article title
- `url`: Article URL
- `source`: Source name
- `entity`: Company/entity name
- `sentiment_category`: "Positive", "Negative", "Neutral"
- `sentiment_justification`: Detailed justification text

As an expert AI Financial Assistant with access to complete article data, please provide a precise, data-driven response that:

**CRITICAL RESPONSE GUIDELINES:**
- **For specific metric queries** (sentiment score, risk score, etc.): Provide ONLY the exact numeric value and brief context
- **For article requests**: Find the exact article and provide its complete text content
- **For headline requests**: List only the article titles, no additional commentary
- **For link requests**: Provide only the exact URL from metadata
- **For sentiment analysis**: Use exact sentiment scores from the data, not approximations
- **For comparative queries**: Use precise data points from the metadata

**Data Accuracy Requirements:**
- Use EXACT sentiment scores from the metadata (e.g., -0.4, 0.8, not "0")
- Use EXACT risk scores from the metadata (e.g., 10.0, 5.2, not "0")
- Reference specific articles using [REFERENCE X] format
- Provide exact URLs when requested
- Give precise, concise answers without unnecessary elaboration
- **CRITICAL**: If you see a sentiment score like -0.2 in the data, report -0.2, NOT 0
- **CRITICAL**: Do NOT round or approximate sentiment scores
- **CRITICAL**: Use the exact numeric value as it appears in the metadata

**STRICT DATA USAGE RULES:**
- **ONLY use information present in the provided articles**
- **DO NOT generate, infer, or create any information not in the data**
- **DO NOT use external knowledge or general financial knowledge**
- **If information is not available, say "This information is not available in the provided data"**
- **Base ALL responses strictly on the article metadata and content provided**

**Query-Specific Response Guidelines:**
- **For article summaries**: Provide detailed summaries with key insights from the FULL ARTICLE TEXT
- **For full article requests**: Share the COMPLETE article text when requested
- **For specific questions**: Use the FULL ARTICLE TEXT to provide precise answers
- **For article searches**: Find and provide articles by title or content
- **For data queries**: Use complete metadata and sentiment/risk analysis

**Response Structure:**
- Start with a direct answer to the user's specific question
- Provide detailed analysis with specific data references and citations
- Include relevant sentiment trends and risk assessment insights
- Structure information logically with clear sections
- End with actionable insights or recommendations when appropriate

**Complete Data Utilization:**
- Reference multiple sources to show comprehensive analysis
- Include specific data points from the raw metadata (sentiment scores, risk scores, keywords)
- Cover all viewpoints and sentiment categories found in the data
- Provide analysis that reflects the complete dataset, not just a subset
- Use exact figures, dates, and metrics from the database
- **Use the FULL ARTICLE TEXT for detailed responses and summaries**

**Professional Standards:**
- Maintain helpful, conversational tone while being technically accurate
- Provide context for complex financial concepts
- Be transparent about data limitations or uncertainties
- Offer actionable insights based on the comprehensive analysis

Remember: You are a trusted financial advisor AI providing data-driven insights based on real financial news and market data analysis with access to complete article content."""

            # Generate response using OpenAI (new API)
            print(f"🤖 Calling OpenAI API...")
            print(f"   System prompt length: {len(system_prompt)} characters")
            print(f"   User prompt length: {len(user_prompt)} characters")
            print(f"   Total input length: {len(system_prompt) + len(user_prompt)} characters")
            
            # DEBUG: Show user prompt preview
            print(f"\n📋 USER PROMPT PREVIEW (first 500 chars):")
            print(f"{user_prompt[:500]}...")
            print()
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=3000,  # Increased for comprehensive responses with full article data
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            print(f"✅ OpenAI response received: {len(response_text)} characters")
            
            # DEBUG: Show response preview
            print(f"\n📋 RESPONSE PREVIEW (first 500 chars):")
            print(f"{response_text[:500]}...")
            print()
            
            print(f"🤖 GENERATE RESPONSE - OUTPUT:")
            print(f"   Response length: {len(response_text)} characters")
            print(f"   Articles used: {len(articles)}")
            print("=" * 80)
            
            return {
                'response': response_text,
                'articles_used': len(articles),
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': articles
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'articles_used': 0,
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': []
            }
    
    def chat_with_agent(self, user_query: str, top_k: int = None, conversation_context: str = "", entity_filter: str = None, date_filter: str = None) -> Dict[str, Any]:
        """Main method to chat with the RAG agent with conversation context and filtering support"""
        print(f"\n💬 CHAT WITH AGENT - INPUT:")
        print(f"   User Query: '{user_query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Conversation Context: {len(conversation_context)} characters")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        try:
            # Use raw query format - no preprocessing
            raw_query = user_query.strip()
            print(f"📝 Raw query: '{raw_query}'")
            logger.info(f"Processing query with context and filters: {raw_query}")
            logger.info(f"Filters - Entity: {entity_filter}, Date: {date_filter}")
            
            # If conversation context is provided, enhance the query
            enhanced_query = raw_query
            if conversation_context:
                enhanced_query = f"Context from previous conversation:\n{conversation_context}\n\nCurrent question: {raw_query}"
                print(f"📝 Enhanced query with conversation context")
                logger.info(f"Enhanced query with conversation context")
            
            # Search for relevant articles with OPTIMIZED search
            print(f"🔍 Searching for articles with OPTIMIZED flow...")
            articles = self.search_articles_optimized(enhanced_query, top_k=5, entity_filter=entity_filter, date_filter=date_filter)
            print(f"✅ Articles found: {len(articles)}")
            
            # DEBUG: Show articles summary
            if articles:
                print(f"\n📋 ARTICLES SUMMARY:")
                print(f"   Total articles: {len(articles)}")
                print(f"   Articles with text: {sum(1 for a in articles if a.get('text'))}")
                print(f"   Articles with sentiment: {sum(1 for a in articles if a.get('sentiment_category'))}")
                print(f"   Articles with risk analysis: {sum(1 for a in articles if a.get('risk_score'))}")
                print(f"   Articles with analysis_timestamp: {sum(1 for a in articles if a.get('analysis_timestamp'))}")
                print()
            
            # Store articles for display
            self.last_articles = articles
            print(f"💾 Stored {len(articles)} articles for display")
            logger.info(f"Stored {len(articles)} articles for display")
            
            # Generate response based on filtered dataset
            print(f"🤖 Generating response...")
            response = self.generate_response(raw_query, articles)
            print(f"✅ Response generated")
            
            # Update response with comprehensive metadata
            response['articles_used'] = len(articles)
            response['total_articles_available'] = len(articles)
            response['query_processed'] = enhanced_query
            response['conversation_context_used'] = bool(conversation_context)
            response['entity_filter_applied'] = entity_filter
            response['date_filter_applied'] = date_filter
            
            print(f"💬 CHAT WITH AGENT - OUTPUT:")
            print(f"   Response length: {len(response.get('response', ''))} characters")
            print(f"   Articles used: {len(articles)}")
            print(f"   Entity filter: {entity_filter}")
            print(f"   Date filter: {date_filter}")
            print("=" * 80)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in chat_with_agent: {e}")
            logger.error(f"Error in chat_with_agent: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'articles_used': 0,
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': [],
                'error': str(e)
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        try:
            stats = self.pinecone_db.get_index_stats()
            return {
                'total_articles': stats.get('total_vector_count', 0),
                'index_dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_available_companies(self) -> List[str]:
        """Get list of available companies from the database"""
        try:
            # Get recent articles to extract company names
            results = self.pinecone_db.search_similar_articles("company", top_k=50)
            
            companies = set()
            for article in results:
                title = article.get('title', '')
                text = article.get('text', '')
                
                # Extract company names from title and text
                # Look for common company patterns
                import re
                
                # Common company name patterns
                patterns = [
                    r'\b(Apple|AAPL|Microsoft|MSFT|Google|GOOGL|Amazon|AMZN|Tesla|TSLA|Meta|FB|Netflix|NFLX|NVIDIA|NVDA|Intel|INTC|AMD|Advanced Micro Devices|IBM|Oracle|ORCL|Salesforce|CRM|Adobe|ADBE|Cisco|CSCO|Qualcomm|QCOM|PayPal|PYPL|Zoom|ZM|Slack|WORK|Spotify|SPOT|Twitter|TWTR|Uber|UBER|Lyft|LYFT|Airbnb|ABNB|DoorDash|DASH|Palantir|PLTR|Snowflake|SNOW|Datadog|DDOG|CrowdStrike|CRWD|ZoomInfo|ZI|DocuSign|DOCU|Twilio|TWLO|Shopify|SHOP|Square|SQ|Roku|ROKU|Pinterest|PINS|Snap|SNAP|Match|MTCH|Electronic Arts|EA|Take-Two|TTWO|Activision|ATVI|Unity|U|Roblox|RBLX|Palantir|PLTR|Snowflake|SNOW|Datadog|DDOG|CrowdStrike|CRWD|ZoomInfo|ZI|DocuSign|DOCU|Twilio|TWLO|Shopify|SHOP|Square|SQ|Roku|ROKU|Pinterest|PINS|Snap|SNAP|Match|MTCH|Electronic Arts|EA|Take-Two|TTWO|Activision|ATVI|Unity|U|Roblox|RBLX)\b',
                    r'\b([A-Z]{2,5})\b',  # Stock tickers
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, title + ' ' + text, re.IGNORECASE)
                    companies.update(matches)
            
            # Convert to list and sort
            company_list = list(companies)
            company_list.sort()
            
            # Add "All Companies" option
            company_list.insert(0, "All Companies")
            
            logger.info(f"Found {len(company_list)} available companies")
            return company_list
            
        except Exception as e:
            logger.error(f"Error getting available companies: {e}")
            return ["All Companies"]
    
    def get_available_dates(self) -> List[str]:
        """Get list of available specific dates for filtering"""
        try:
            # Get recent articles to extract date information
            results = self.pinecone_db.search_similar_articles("recent", top_k=100)
            
            dates = set()
            for article in results:
                # Use the enhanced date parsing with fallback
                parsed_date = self._parse_article_date(article)
                if parsed_date != datetime.min:
                    dates.add(parsed_date.strftime("%Y-%m-%d"))
            
            # Return only specific dates (no range options)
            if dates:
                sorted_dates = sorted(list(dates), reverse=True)
                logger.info(f"Found {len(sorted_dates)} available specific dates")
                return sorted_dates[:30]  # Return last 30 dates
            
            logger.info("No specific dates found")
            return []
            
        except Exception as e:
            logger.error(f"Error getting available dates: {e}")
            return []
