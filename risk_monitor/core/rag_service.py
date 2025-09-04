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
        print("🔧 RAG Service initialized with OpenAI client and PineconeDB")
        
    def search_articles(self, query: str, top_k: int = 50, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Search for articles using NEW FILTERING FLOW: Date → Entity → Query"""
        print(f"🔍 NEW FILTERING FLOW - INPUT:")
        print(f"   Query: '{query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        # Check if this is a specific article request
        query_type_info = self.classify_query_type(query)
        if query_type_info['query_type'] in ['specific_article', 'full_article']:
            return self._handle_specific_article_request(query, entity_filter, date_filter)
        
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
            
            # Sentiment analysis data
            sentiment_analysis = article.get('sentiment_analysis', {})
            sentiment_category = sentiment_analysis.get('category', 'Unknown') if isinstance(sentiment_analysis, dict) else 'Unknown'
            sentiment_score = sentiment_analysis.get('score', 0) if isinstance(sentiment_analysis, dict) else 0
            sentiment_justification = sentiment_analysis.get('justification', '') if isinstance(sentiment_analysis, dict) else ''
            
            # Risk analysis data
            risk_analysis = article.get('risk_analysis', {})
            risk_score = risk_analysis.get('risk_score', 0) if isinstance(risk_analysis, dict) else 0
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
            # Classify query type
            query_type_info = self.classify_query_type(user_query)
            query_type = query_type_info['query_type']
            confidence = query_type_info['confidence']
            matched_patterns = query_type_info['matched_patterns']
            
            print(f"📝 Query Type Classification:")
            print(f"   Query: '{user_query}'")
            print(f"   Type: {query_type} (Confidence: {confidence:.2f})")
            print(f"   Matched Patterns: {matched_patterns}")
            
            # Format context based on query type
            context = self.format_context_for_query_type(articles, query_type)
            print(f"✅ Context formatted: {len(context)} characters")
            
            # DEBUG: Show context preview
            print(f"\n📋 CONTEXT PREVIEW (first 500 chars):")
            print(f"{context[:500]}...")
            print()
            
            # Create system prompt
            print(f"📝 Creating system prompt...")
            system_prompt = self.create_specialized_system_prompt(query_type, user_query)
            print(f"✅ System prompt created: {len(system_prompt)} characters")
            
            # Create user prompt with context
            user_prompt = f"""User Question: {user_query}

Here is the COMPLETE relevant data from your financial database with FULL ARTICLE TEXT:

{context}

As an expert AI Financial Assistant with access to complete article data, please provide a specialized response for this query type ({query_type}) that:

**Query Type: {query_type}**
**Confidence: {confidence:.2f}**
**Matched Patterns: {matched_patterns}**

**Specialized Analysis Requirements:**
- Focus on the specific query type and user intent
- Use the appropriate response format for this query type
- Leverage all relevant metadata and article content
- Provide targeted insights based on the query classification
- Include specific data points and references

**Response Guidelines for {query_type}:**
- Follow the specialized response format for this query type
- Use the complete article text when relevant
- Include specific sentiment scores, risk scores, and metadata
- Provide actionable insights based on the query type
- Structure the response appropriately for the user's intent

**Complete Data Utilization:**
- Reference specific articles using [REFERENCE X] format
- Include exact sentiment scores, risk scores, and metadata details
- Use the FULL ARTICLE TEXT when relevant to the query type
- Provide comprehensive analysis based on the complete dataset
- Include source diversity and multiple perspectives

**Professional Standards:**
- Maintain helpful, conversational tone while being technically accurate
- Provide context for complex financial concepts
- Be transparent about data limitations or uncertainties
- Offer actionable insights based on the comprehensive analysis

Remember: You are a trusted financial advisor AI providing specialized, data-driven insights based on real financial news and market data analysis with access to complete article content. Tailor your response specifically to the query type: {query_type}."""

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
            print(f"   Query Type: {query_type}")
            print(f"   Confidence: {confidence:.2f}")
            print("=" * 80)
            
            return {
                'response': response_text,
                'articles_used': len(articles),
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': articles,
                'query_type': query_type,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'articles_used': 0,
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': [],
                'error': str(e)
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
            
            # Search for relevant articles with filters
            print(f"🔍 Searching for articles...")
            articles = self.search_articles(enhanced_query, entity_filter=entity_filter, date_filter=date_filter)
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

    def _handle_specific_article_request(self, query: str, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Handle specific article requests by searching for exact matches"""
        print(f"🎯 HANDLING SPECIFIC ARTICLE REQUEST:")
        print(f"   Query: '{query}'")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        
        try:
            # Get all articles first
            stats = self.pinecone_db.get_index_stats()
            total_articles = stats.get('total_vector_count', 0)
            all_articles = self.pinecone_db.get_all_articles(top_k=total_articles)
            
            # Apply filters
            filtered_articles = all_articles
            
            # Apply date filter
            if date_filter and date_filter != "All Dates":
                filtered_articles = self._apply_date_filter(filtered_articles, date_filter)
            
            # Apply entity filter
            if entity_filter and entity_filter != "All Companies":
                filtered_articles = self._apply_entity_filter(filtered_articles, entity_filter)
            
            # Search for specific article matches
            query_lower = query.lower()
            matched_articles = []
            
            for article in filtered_articles:
                title = article.get('title', '').lower()
                text = article.get('text', '').lower()
                
                # Check for exact title matches
                if any(keyword in title for keyword in ['article', 'about', 'titled', 'called']):
                    # Extract potential article title from query
                    potential_title = query_lower.replace('article about', '').replace('article on', '').replace('article titled', '').replace('article called', '').strip()
                    if potential_title and potential_title in title:
                        matched_articles.append(article)
                        continue
                
                # Check for content matches
                if any(keyword in text for keyword in query_lower.split()):
                    matched_articles.append(article)
                    continue
                
                # Check for source matches
                source = article.get('source', '').lower()
                if any(keyword in source for keyword in query_lower.split()):
                    matched_articles.append(article)
                    continue
            
            # If no specific matches found, return top semantic matches
            if not matched_articles:
                print(f"   ⚠️ No specific matches found, using semantic search")
                return self.pinecone_db.search_similar_articles(query, top_k=10)
            
            print(f"   ✅ Found {len(matched_articles)} specific article matches")
            return matched_articles
            
        except Exception as e:
            print(f"   ❌ Error in specific article request: {e}")
            logger.error(f"Error in specific article request: {e}")
            return []

    def _apply_date_filter(self, articles: List[Dict], date_filter: str) -> List[Dict]:
        """Apply date filter to articles"""
        try:
            from datetime import datetime, timedelta
            
            if date_filter == "Last 7 days":
                cutoff_date = datetime.now() - timedelta(days=7)
            elif date_filter == "Last 30 days":
                cutoff_date = datetime.now() - timedelta(days=30)
            else:
                cutoff_date = datetime.strptime(date_filter, "%Y-%m-%d")
            
            filtered_results = []
            for article in articles:
                article_date = self._parse_article_date(article)
                if article_date >= cutoff_date:
                    filtered_results.append(article)
            
            return filtered_results
        except Exception as e:
            logger.error(f"Error applying date filter: {e}")
            return articles

    def _apply_entity_filter(self, articles: List[Dict], entity_filter: str) -> List[Dict]:
        """Apply entity filter to articles"""
        entity_filter_lower = entity_filter.lower()
        filtered_results = []
        
        for article in articles:
            title = article.get('title', '').lower()
            text = article.get('text', '').lower()
            entity = article.get('entity', '').lower()
            
            if (entity_filter_lower in title or 
                entity_filter_lower in text or 
                entity_filter_lower in entity):
                filtered_results.append(article)
        
        return filtered_results

    def classify_query_type(self, query: str) -> Dict[str, Any]:
        """Classify the type of query to determine the best response strategy"""
        query_lower = query.lower()
        
        # Define query patterns
        patterns = {
            'sentiment_trend': [
                'sentiment trend', 'overall sentiment', 'sentiment analysis', 
                'how is the sentiment', 'sentiment for', 'sentiment of'
            ],
            'risk_analysis': [
                'risk score', 'highest risk', 'risk indicators', 'risk factors',
                'risk assessment', 'risk analysis', 'risk level'
            ],
            'comparison': [
                'compare', 'comparison', 'between', 'versus', 'vs', 'difference',
                'similar', 'different', 'contrast'
            ],
            'headlines': [
                'headlines', 'headline', 'titles', 'article titles', 'news headlines',
                'show me headlines', 'list headlines'
            ],
            'full_article': [
                'full article', 'complete article', 'entire article', 'whole article',
                'article content', 'article text', 'full text', 'complete text'
            ],
            'specific_article': [
                'article about', 'article on', 'article titled', 'article called',
                'find article', 'show me article', 'get article'
            ],
            'data_query': [
                'how many', 'count', 'total', 'statistics', 'data', 'numbers',
                'metrics', 'figures', 'summary stats'
            ],
            'trend_analysis': [
                'trend', 'pattern', 'over time', 'development', 'evolution',
                'change', 'growth', 'decline'
            ],
            'source_analysis': [
                'source', 'sources', 'where', 'from where', 'which source',
                'credibility', 'bias'
            ],
            'date_specific': [
                'yesterday', 'today', 'this week', 'this month', 'recent',
                'latest', 'newest', 'oldest'
            ]
        }
        
        # Check for matches
        query_type = 'general'
        confidence = 0.0
        matched_patterns = []
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in query_lower:
                    matched_patterns.append(pattern)
                    if len(matched_patterns) == 1:  # First match
                        query_type = pattern_type
                        confidence = 0.8
                    else:  # Multiple matches
                        confidence = min(confidence + 0.1, 1.0)
        
        # Special handling for specific question types
        if 'headline' in query_lower and 'day' in query_lower:
            query_type = 'headline_of_day'
            confidence = 0.9
        
        if any(word in query_lower for word in ['entity', 'entities', 'company', 'companies']):
            query_type = 'entity_comparison'
            confidence = 0.8
        
        # Additional specific patterns
        if any(phrase in query_lower for phrase in ['what is the', 'what are the', 'what does the']):
            if 'article' in query_lower:
                query_type = 'specific_article'
                confidence = 0.9
        
        if any(phrase in query_lower for phrase in ['show me', 'give me', 'find me']):
            if 'article' in query_lower:
                query_type = 'specific_article'
                confidence = 0.8
            elif 'headline' in query_lower:
                query_type = 'headlines'
                confidence = 0.8
        
        if any(phrase in query_lower for phrase in ['compare', 'comparison', 'between', 'versus', 'vs']):
            query_type = 'comparison'
            confidence = 0.9
        
        if any(phrase in query_lower for phrase in ['trend', 'pattern', 'over time', 'evolution']):
            query_type = 'trend_analysis'
            confidence = 0.8
        
        if any(phrase in query_lower for phrase in ['how many', 'count', 'total', 'statistics']):
            query_type = 'data_query'
            confidence = 0.9
        
        return {
            'query_type': query_type,
            'confidence': confidence,
            'matched_patterns': matched_patterns,
            'original_query': query
        }

    def create_specialized_system_prompt(self, query_type: str, query: str) -> str:
        """Create a specialized system prompt based on query type"""
        
        base_prompt = """You are an expert AI Financial Assistant specializing in financial risk monitoring and market analysis. You have access to a comprehensive database of analyzed financial news articles with COMPLETE metadata, full article text, and detailed sentiment/risk analysis.

## YOUR EXPERTISE & CAPABILITIES:
- Financial analysis and market insights
- Sentiment analysis and trend identification
- Risk assessment and factor analysis
- Company performance evaluation
- Data-driven insights and recommendations

## COMPLETE DATA STRUCTURE YOU CAN ACCESS:
- **Full Article Text**: Complete article content in the 'text' field
- **Sentiment Analysis**: Scores (-1 to 1) and categories (Positive/Negative/Neutral)
- **Risk Analysis**: Risk scores and detailed risk categories
- **Complete Metadata**: Titles, sources, dates, URLs, entities, analysis timestamps
- **Entity Information**: Company names, tickers, and related entities

## RESPONSE GUIDELINES:
- Use ALL relevant articles from the database for comprehensive analysis
- Reference specific articles using [REFERENCE X] format
- Include exact sentiment scores, risk scores, and specific data points
- Provide source diversity by citing multiple sources
- Be helpful, accurate, and actionable in your responses"""

        # Specialized prompts for different query types
        specialized_prompts = {
            'sentiment_trend': """
## SENTIMENT TREND ANALYSIS SPECIALIZATION:
- Analyze sentiment patterns across all relevant articles
- Identify overall sentiment trends and shifts
- Provide sentiment distribution statistics
- Highlight significant sentiment changes
- Include specific sentiment scores and categories
- Show sentiment evolution over time if applicable

**Response Format:**
1. Overall sentiment summary with statistics
2. Sentiment distribution breakdown
3. Key sentiment drivers and factors
4. Trend analysis and insights
5. Recommendations based on sentiment data""",

            'risk_analysis': """
## RISK ANALYSIS SPECIALIZATION:
- Analyze risk scores across all articles
- Identify highest risk articles and factors
- Categorize risk types (market, geopolitical, sector, regulatory)
- Highlight risk indicators and keywords
- Provide risk assessment insights
- Compare risk levels across different entities/time periods

**Response Format:**
1. Overall risk assessment summary
2. Highest risk articles and their scores
3. Risk factor breakdown and analysis
4. Risk indicators and keywords found
5. Risk mitigation recommendations""",

            'comparison': """
## COMPARISON ANALYSIS SPECIALIZATION:
- Compare entities, time periods, or categories
- Identify similarities and differences
- Provide comparative statistics and metrics
- Highlight key differentiators
- Show relative performance or sentiment
- Include side-by-side analysis

**Response Format:**
1. Comparison overview and scope
2. Side-by-side analysis with specific data
3. Key differences and similarities
4. Comparative insights and trends
5. Recommendations based on comparison""",

            'headlines': """
## HEADLINES ANALYSIS SPECIALIZATION:
- Provide comprehensive list of relevant headlines
- Include source, date, and sentiment for each headline
- Organize headlines by relevance or date
- Highlight most significant headlines
- Provide context for headline importance
- Include full article links when available

**Response Format:**
1. Headlines summary and count
2. Organized list of headlines with metadata
3. Most significant headlines highlighted
4. Context and importance analysis
5. Links to full articles where relevant""",

            'headline_of_day': """
## HEADLINE OF THE DAY SPECIALIZATION:
- Identify the most significant headline for the specified day
- Provide the complete headline with source
- Include full article text when requested
- Explain why this headline is significant
- Provide context and background
- Include sentiment and risk analysis for the headline

**Response Format:**
1. Most significant headline with source
2. Complete article text (when requested)
3. Significance explanation and context
4. Sentiment and risk analysis
5. Full article link""",

            'full_article': """
## FULL ARTICLE SPECIALIZATION:
- Provide the complete article text when requested
- Include all article metadata (title, source, date, URL)
- Format the article content clearly
- Preserve original article structure
- Include sentiment and risk context
- Provide the exact URL for the article

**Response Format:**
1. Article title and source information
2. Complete article text
3. Article URL
4. Sentiment and risk context
5. Additional insights if relevant""",

            'specific_article': """
## SPECIFIC ARTICLE SPECIALIZATION:
- Find and provide the exact article requested
- Include complete article text and metadata
- Provide the exact URL and source
- Include sentiment and risk analysis
- Verify article relevance to the query
- Provide additional context if needed

**Response Format:**
1. Found article with complete metadata
2. Complete article text
3. Article URL and source
4. Sentiment and risk analysis
5. Relevance confirmation""",

            'data_query': """
## DATA QUERY SPECIALIZATION:
- Provide specific statistics and metrics
- Include exact counts and numbers
- Show data distribution and patterns
- Provide comprehensive data summary
- Include relevant percentages and ratios
- Highlight key data insights

**Response Format:**
1. Specific data statistics requested
2. Data distribution and patterns
3. Key metrics and percentages
4. Data insights and trends
5. Additional relevant data points""",

            'trend_analysis': """
## TREND ANALYSIS SPECIALIZATION:
- Identify patterns and trends over time
- Show evolution of sentiment, risk, or other metrics
- Highlight significant changes and shifts
- Provide trend explanations and context
- Include predictive insights where possible
- Show trend comparisons across entities

**Response Format:**
1. Trend overview and scope
2. Pattern identification and analysis
3. Significant changes and shifts
4. Trend explanations and context
5. Predictive insights and recommendations""",

            'entity_comparison': """
## ENTITY COMPARISON SPECIALIZATION:
- Compare different companies or entities
- Show relative performance and sentiment
- Identify entity-specific trends
- Provide comparative risk analysis
- Highlight entity differentiators
- Include entity-specific insights

**Response Format:**
1. Entity comparison overview
2. Side-by-side entity analysis
3. Relative performance metrics
4. Entity-specific insights
5. Comparative recommendations""",

            'general': """
## GENERAL ANALYSIS SPECIALIZATION:
- Provide comprehensive analysis based on the query
- Use all relevant data from the database
- Include specific examples and references
- Provide actionable insights
- Cover multiple perspectives and viewpoints
- Include sentiment and risk context

**Response Format:**
1. Direct answer to the query
2. Comprehensive analysis with data
3. Specific examples and references
4. Multiple perspectives covered
5. Actionable insights and recommendations"""
        }
        
        # Get the specialized prompt for this query type
        specialized_prompt = specialized_prompts.get(query_type, specialized_prompts['general'])
        
        return base_prompt + specialized_prompt

    def format_context_for_query_type(self, articles: List[Dict], query_type: str) -> str:
        """Format context specifically for the query type"""
        
        if not articles:
            return "No relevant articles found in the database."
        
        # Basic context structure
        context_parts = []
        
        # Dataset overview
        context_parts.append(f"""## DATASET OVERVIEW
Total relevant articles found: {len(articles)}
Query type: {query_type}
Analysis scope: Full article content and comprehensive metadata""")
        
        # Sentiment distribution
        sentiment_counts = {}
        for article in articles:
            sentiment = article.get('sentiment_category', 'Unknown')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        sentiment_dist = ', '.join([f"{k}: {v} articles" for k, v in sentiment_counts.items()])
        context_parts.append(f"""## SENTIMENT DISTRIBUTION
{sentiment_dist}""")
        
        # Risk score distribution for risk-related queries
        if query_type in ['risk_analysis', 'comparison']:
            risk_scores = [a.get('risk_score', 0) for a in articles if a.get('risk_score') is not None]
            if risk_scores:
                avg_risk = sum(risk_scores) / len(risk_scores)
                max_risk = max(risk_scores)
                min_risk = min(risk_scores)
                context_parts.append(f"""## RISK SCORE DISTRIBUTION
Average risk score: {avg_risk:.2f}
Highest risk score: {max_risk:.2f}
Lowest risk score: {min_risk:.2f}
Articles with risk analysis: {len(risk_scores)}""")
        
        # Entity distribution for entity-related queries
        if query_type in ['entity_comparison', 'comparison']:
            entities = {}
            for article in articles:
                entity = article.get('entity', 'Unknown')
                entities[entity] = entities.get(entity, 0) + 1
            
            entity_dist = ', '.join([f"{k}: {v} articles" for k, v in entities.items()])
            context_parts.append(f"""## ENTITY DISTRIBUTION
{entity_dist}""")
        
        # Complete article data
        context_parts.append("## COMPLETE ARTICLE DATA")
        
        # Format articles based on query type
        for i, article in enumerate(articles[:15], 1):  # Limit to 15 articles
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown source')
            entity = article.get('entity', 'Unknown entity')
            sentiment_score = article.get('sentiment_score', 'N/A')
            sentiment_category = article.get('sentiment_category', 'Unknown')
            risk_score = article.get('risk_score', 'N/A')
            text = article.get('text', 'No text available')
            url = article.get('url', 'No URL available')
            publish_date = article.get('publish_date', 'Unknown date')
            
            # Format based on query type
            if query_type == 'headlines':
                article_format = f"""### [REFERENCE {i}] - {title}
**Source:** {source}
**Date:** {publish_date}
**Sentiment:** {sentiment_category} (score: {sentiment_score})
**Risk Score:** {risk_score}
**URL:** {url}"""
            elif query_type == 'full_article':
                article_format = f"""### [REFERENCE {i}] - {title}
**Complete Article Metadata:**
- Title: {title}
- Source: {source}
- Date: {publish_date}
- Entity: {entity}
- URL: {url}
- Sentiment: {sentiment_category} (score: {sentiment_score})
- Risk Score: {risk_score}

**COMPLETE ARTICLE TEXT:**
{text}"""
            else:
                article_format = f"""### [REFERENCE {i}] - {title}
**Source:** {source}
**Date:** {publish_date}
**Entity:** {entity}
**Sentiment:** {sentiment_category} (score: {sentiment_score})
**Risk Score:** {risk_score}
**URL:** {url}
**Text Preview:** {text[:200]}..."""
            
            context_parts.append(article_format)
        
        # Analysis instructions based on query type
        if query_type == 'sentiment_trend':
            instructions = """## ANALYSIS INSTRUCTIONS
- Analyze sentiment patterns across all articles
- Provide sentiment distribution statistics
- Identify sentiment trends and shifts
- Include specific sentiment scores and categories
- Highlight significant sentiment changes"""
        elif query_type == 'risk_analysis':
            instructions = """## ANALYSIS INSTRUCTIONS
- Analyze risk scores across all articles
- Identify highest risk articles and factors
- Categorize risk types and indicators
- Provide risk assessment insights
- Include specific risk scores and categories"""
        elif query_type == 'headlines':
            instructions = """## ANALYSIS INSTRUCTIONS
- Provide comprehensive list of relevant headlines
- Include source, date, and sentiment for each headline
- Organize headlines by relevance or date
- Highlight most significant headlines
- Include full article links"""
        elif query_type == 'full_article':
            instructions = """## ANALYSIS INSTRUCTIONS
- Provide complete article text when requested
- Include all article metadata
- Format article content clearly
- Preserve original article structure
- Include sentiment and risk context"""
        else:
            instructions = """## ANALYSIS INSTRUCTIONS
- Provide comprehensive analysis based on the query
- Use all relevant data from the database
- Include specific examples and references
- Provide actionable insights
- Cover multiple perspectives and viewpoints"""
        
        context_parts.append(instructions)
        
        return "\n\n".join(context_parts)
