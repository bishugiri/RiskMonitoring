"""
Pinecone Database Integration for Risk Monitor
Stores article analysis results with OpenAI embeddings and comprehensive metadata
"""

from pinecone import Pinecone
import openai
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from risk_monitor.config.settings import Config

logger = logging.getLogger(__name__)

class PineconeDB:
    """Pinecone database integration for storing article analysis results"""
    
    def __init__(self, index_name: str = None):
        print(f"\n🔧 PINECONE DB INITIALIZATION:")
        self.config = Config()
        self.index_name = index_name or self.config.PINECONE_INDEX_NAME
        self.dimension = 3072  # OpenAI large embeddings dimension
        self.pinecone_api_key = self.config.get_pinecone_api_key()
        self.openai_api_key = self.config.get_openai_api_key()
        
        print(f"   Index name: {self.index_name}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Pinecone API key: {'✅ Set' if self.pinecone_api_key else '❌ Not set'}")
        print(f"   OpenAI API key: {'✅ Set' if self.openai_api_key else '❌ Not set'}")
        
        if not self.pinecone_api_key:
            print(f"   ❌ ERROR: Pinecone API key not found in configuration")
            raise ValueError("Pinecone API key not found in configuration")
        if not self.openai_api_key:
            print(f"   ❌ ERROR: OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key not found in configuration")
        
        # Initialize Pinecone with new API
        print(f"   🔧 Initializing Pinecone client...")
        try:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            print(f"   ✅ Pinecone client initialized")
        except Exception as e:
            print(f"   ❌ ERROR initializing Pinecone client: {e}")
            raise
        
        # Initialize OpenAI API key (not needed for new API, but keeping for compatibility)
        self.openai_api_key = self.openai_api_key
        
        # Get or create index
        print(f"   🔧 Getting or creating index...")
        try:
            self.index = self._get_or_create_index()
            print(f"   ✅ Index ready: {self.index_name}")
        except Exception as e:
            print(f"   ❌ ERROR getting/creating index: {e}")
            raise
        
        print("=" * 80)
        
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        print(f"   📋 Getting or creating index: {self.index_name}")
        try:
            # Check if index exists
            print(f"   🔍 Checking existing indexes...")
            index_list = self.pc.list_indexes().names()
            print(f"   📋 Available indexes: {index_list}")
            
            if self.index_name in index_list:
                print(f"   ✅ Using existing Pinecone index: {self.index_name}")
                logger.info(f"Using existing Pinecone index: {self.index_name}")
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                print(f"   🔧 Creating new Pinecone index: {self.index_name}")
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                try:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine"
                    )
                    print(f"   ✅ Index created successfully")
                    return self.pc.Index(self.index_name)
                except Exception as create_error:
                    print(f"   ❌ Error creating index: {create_error}")
                    if "pod quota" in str(create_error).lower() or "quota" in str(create_error).lower():
                        logger.error("Pinecone pod quota exceeded. Please upgrade your Pinecone plan.")
                        raise ValueError("Pinecone quota exceeded - please upgrade your plan")
                    else:
                        raise create_error
        except Exception as e:
            print(f"   ❌ Error initializing Pinecone index: {e}")
            logger.error(f"Error initializing Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text,
                dimensions=self.dimension
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def create_article_id(self, article: Dict) -> str:
        """Create unique ID for article based on URL and title"""
        url = article.get('url', '')
        title = article.get('title', '')
        content = f"{url}{title}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_clean_source(self, article: Dict) -> str:
        """Extract clean source name from article"""
        # Try to get source from article_analysis if available
        if 'article_analysis' in article and article['article_analysis'].get('source'):
            return article['article_analysis']['source']
        
        # Try to get source from source field
        if 'source' in article:
            source = article['source']
            if isinstance(source, dict) and 'name' in source:
                return source['name']
            elif isinstance(source, str):
                return source
        
        # Extract from URL
        url = article.get('url', '')
        if url:
            try:
                parsed = urlparse(url)
                return parsed.netloc
            except:
                pass
        
        return "Unknown"
    
    def format_metadata(self, article: Dict, analysis_result: Dict) -> Dict[str, Any]:
        """Format comprehensive metadata for Pinecone storage"""
        
        # Extract sentiment analysis
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        sentiment_score = sentiment_analysis.get('score', 0)
        sentiment_category = sentiment_analysis.get('category', 'Neutral')
        sentiment_justification = sentiment_analysis.get('justification', '')
        
        # Extract risk analysis
        risk_analysis = analysis_result.get('risk_analysis', {})
        risk_score = risk_analysis.get('risk_score', 0)
        risk_categories = risk_analysis.get('risk_categories', {})
        risk_indicators = risk_analysis.get('risk_indicators', [])
        
        # Extract article metadata
        publish_date = article.get('publish_date')
        if isinstance(publish_date, str):
            try:
                # Parse ISO format date
                parsed_date = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_date = publish_date
        elif isinstance(publish_date, datetime):
            formatted_date = publish_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            formatted_date = 'N/A'
        
        # Create comprehensive metadata
        metadata = {
            # Article identification
            'article_id': self.create_article_id(article),
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'source': self.extract_clean_source(article),
            'publish_date': formatted_date,
            'authors': article.get('authors', []),
            
            # Content
            'text': article.get('text', ''),
            'summary': article.get('summary', ''),
            'keywords': article.get('keywords', []),
            'meta_description': article.get('meta_description', ''),
            'entity': article.get('entity', ''),
            
            # Sentiment analysis
            'sentiment_score': sentiment_score,
            'sentiment_category': sentiment_category,
            'sentiment_justification': sentiment_justification,
            'positive_count': sentiment_analysis.get('positive_count', 0),
            'negative_count': sentiment_analysis.get('negative_count', 0),
            'total_relevant': sentiment_analysis.get('total_relevant', 0),
            
            # Risk analysis
            'risk_score': risk_score,
            'risk_categories': json.dumps(risk_categories),
            'risk_indicators': json.dumps(risk_indicators),
            'keywords_found': json.dumps(risk_analysis.get('keywords_found', [])),
            
            # Processing metadata
            'extraction_time': article.get('extraction_time', ''),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': analysis_result.get('analysis_method', 'lexicon'),
            
            # Full analysis result (for complete data preservation)
            'full_analysis': json.dumps(analysis_result),
            'full_article_data': json.dumps(article)
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Store article with analysis results in Pinecone"""
        try:
            # Generate embedding from article text
            text = article.get('text', '')
            if not text:
                logger.warning(f"No text content for article: {article.get('title', 'Unknown')}")
                return False
            
            # Create embedding
            embedding = self.generate_embedding(text)
            
            # Create unique ID
            article_id = self.create_article_id(article)
            
            # Format metadata
            metadata = self.format_metadata(article, analysis_result)
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    'id': article_id,
                    'values': embedding,
                    'metadata': metadata
                }]
            )
            
            logger.info(f"Successfully stored article in Pinecone: {article.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article in Pinecone: {e}")
            return False
    
    def store_articles_batch(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """Store multiple articles in batch"""
        success_count = 0
        error_count = 0
        
        for article, analysis_result in zip(articles, analysis_results):
            if self.store_article(article, analysis_result):
                success_count += 1
            else:
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }
        
        logger.info(f"Batch storage complete: {success_count} successful, {error_count} errors")
        return result
    
    def search_similar_articles(self, query: str, top_k: int = 10, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Production-level two-stage search: metadata filtering + semantic similarity"""
        print(f"\n🔍 PRODUCTION SEARCH PIPELINE - INPUT:")
        print(f"   Query: '{query}'")
        print(f"   Top_k: {top_k}")
        print(f"   Entity Filter: {entity_filter}")
        print(f"   Date Filter: {date_filter}")
        print("=" * 80)
        
        try:
            # STAGE 1: Initial Semantic Search (No Filters)
            print(f"\n📋 STAGE 1: INITIAL SEMANTIC SEARCH")
            print(f"   Performing initial search without filters to get candidates")
            
            # Generate embedding for query
            print(f"   🔍 Generating embedding for query...")
            query_embedding = self.generate_embedding(query)
            print(f"   ✅ Embedding generated: {len(query_embedding)} dimensions")
            
            # Perform initial semantic search
            try:
                initial_results = self.index.query(
                    vector=query_embedding,
                    top_k=50,  # Get more candidates for filtering
                    include_metadata=True
                )
                print(f"   ✅ Initial search results: {len(initial_results['matches'])} candidates")
                
                if not initial_results['matches']:
                    print(f"   ⚠️  No results from initial search, returning empty list")
                    return []
                    
            except Exception as search_error:
                print(f"   ❌ ERROR in initial search: {search_error}")
                print(f"      Error type: {type(search_error)}")
                return []
            
            # STAGE 1.5: Post-processing Filtering
            print(f"\n📋 STAGE 1.5: POST-PROCESSING FILTERING")
            filtered_matches = initial_results['matches']
            
            # Entity filtering
            if entity_filter and entity_filter != "All Companies":
                print(f"   🏢 Applying entity filter: '{entity_filter}'")
                entity_filtered = []
                for match in filtered_matches:
                    text = match['metadata'].get('text', '')
                    title = match['metadata'].get('title', '')
                    if entity_filter.lower() in text.lower() or entity_filter.lower() in title.lower():
                        entity_filtered.append(match)
                filtered_matches = entity_filtered
                print(f"   ✅ Entity filtering: {len(filtered_matches)} matches remaining")
            
            # Date filtering
            if date_filter and date_filter != "All Dates":
                print(f"   📅 Applying date filter: '{date_filter}'")
                from datetime import datetime, timedelta
                
                date_filtered = []
                for match in filtered_matches:
                    analysis_timestamp = match['metadata'].get('analysis_timestamp', '')
                    if analysis_timestamp:
                        try:
                            parsed_date = datetime.fromisoformat(analysis_timestamp.replace('Z', '+00:00'))
                            
                            if date_filter == "Last 7 days":
                                cutoff_date = datetime.now() - timedelta(days=7)
                                if parsed_date >= cutoff_date:
                                    date_filtered.append(match)
                            elif date_filter == "Last 30 days":
                                cutoff_date = datetime.now() - timedelta(days=30)
                                if parsed_date >= cutoff_date:
                                    date_filtered.append(match)
                            else:
                                # Specific date
                                target_date = datetime.strptime(date_filter, "%Y-%m-%d")
                                if parsed_date.date() >= target_date.date():
                                    date_filtered.append(match)
                        except Exception as e:
                            print(f"      ⚠️  Date parsing error for match: {e}")
                            continue
                
                filtered_matches = date_filtered
                print(f"   ✅ Date filtering: {len(filtered_matches)} matches remaining")
            
            # Limit to top results
            final_matches = filtered_matches[:min(top_k, 5)]
            print(f"   📊 Final filtered results: {len(final_matches)} matches")
            
            # Create results structure
            results = {'matches': final_matches}
            
            # STAGE 2: Results Processing
            print(f"\n📋 STAGE 2: RESULTS PROCESSING")
            print(f"   Processing {len(results['matches'])} final matches")
            
            # DEBUG: Show raw Pinecone response structure
            try:
                print(f"\n📋 RAW PINECONE RESPONSE STRUCTURE:")
                print(f"   Response keys: {list(results.keys())}")
                print(f"   Matches count: {len(results['matches'])}")
                print(f"   Results type: {type(results)}")
                print(f"   Matches type: {type(results['matches'])}")
                if results['matches']:
                    print(f"   First match type: {type(results['matches'][0])}")
                    print(f"   First match keys: {list(results['matches'][0].keys())}")
                    if 'metadata' in results['matches'][0]:
                        print(f"   First match metadata keys: {list(results['matches'][0]['metadata'].keys())}")
                    else:
                        print(f"   ❌ No metadata in first match")
                    print()
                else:
                    print(f"   ❌ No matches found")
                    print()
            except Exception as debug_error:
                print(f"   ❌ ERROR in debug section: {debug_error}")
                print(f"      Error type: {type(debug_error)}")
                print(f"      Results: {results}")
            
            # Format results
            print(f"📝 Formatting results...")
            try:
                print(f"   Starting to process {len(results['matches'])} matches...")
            except Exception as len_error:
                print(f"   ❌ ERROR getting matches length: {len_error}")
                print(f"      Results: {results}")
                return []
            
            formatted_results = []
            
            # Safe JSON parsing with error handling
            def safe_json_loads(value, default):
                if value is None:
                    return default
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"      ⚠️  JSON parsing error: {e} for value: {value}")
                    return default
            
            print(f"   Entering match processing loop...")
            for i, match in enumerate(results['matches'], 1):
                try:
                    metadata = match['metadata']
                    print(f"   📄 Processing match {i}: {metadata.get('title', 'Unknown')[:50]}...")
                    print(f"      Score: {match['score']:.4f}")
                    print(f"      Text length: {len(metadata.get('text', ''))} characters")
                    
                    # DEBUG: Show metadata structure for first few matches
                    if i <= 3:
                        print(f"      Metadata keys: {list(metadata.keys())}")
                        print(f"      Has text: {'text' in metadata}")
                        print(f"      Has analysis_timestamp: {'analysis_timestamp' in metadata}")
                        print(f"      Has sentiment_category: {'sentiment_category' in metadata}")
                        print(f"      Has risk_score: {'risk_score' in metadata}")
                        print(f"      Has entity: {'entity' in metadata}")
                        print()
                
                    # Create the formatted result step by step with error handling
                    formatted_result = {
                        'id': match['id'],
                        'score': match['score'],
                        'title': metadata.get('title', ''),
                        'source': metadata.get('source', ''),
                        'publish_date': metadata.get('publish_date', ''),
                        'sentiment_category': metadata.get('sentiment_category', ''),
                        'sentiment_score': metadata.get('sentiment_score', 0),
                        'risk_score': metadata.get('risk_score', 0),
                        'url': metadata.get('url', ''),
                        'summary': metadata.get('summary', ''),
                        'text': metadata.get('text', ''),  # ADDED: Full article text
                        'authors': metadata.get('authors', []),
                        'keywords': metadata.get('keywords', []),
                        'meta_description': metadata.get('meta_description', ''),
                        'entity': metadata.get('entity', ''),
                        'extraction_time': metadata.get('extraction_time', ''),
                        'analysis_timestamp': metadata.get('analysis_timestamp', ''),  # ADDED: analysis_timestamp for date filtering
                    }
                    
                    # Add JSON fields with error handling
                    try:
                        formatted_result['matched_keywords'] = safe_json_loads(metadata.get('keywords_found'), [])
                    except Exception as e:
                        print(f"      ❌ Error with matched_keywords: {e}")
                        formatted_result['matched_keywords'] = []
                    
                    try:
                        formatted_result['sentiment_analysis'] = {
                            'score': metadata.get('sentiment_score', 0),
                            'category': metadata.get('sentiment_category', 'Unknown'),
                            'justification': metadata.get('sentiment_justification', '')
                        }
                    except Exception as e:
                        print(f"      ❌ Error with sentiment_analysis: {e}")
                        formatted_result['sentiment_analysis'] = {'score': 0, 'category': 'Unknown', 'justification': ''}
                    
                    try:
                        formatted_result['risk_analysis'] = {
                            'risk_score': metadata.get('risk_score', 0),
                            'risk_categories': safe_json_loads(metadata.get('risk_categories'), {}),
                            'risk_indicators': safe_json_loads(metadata.get('risk_indicators'), [])
                        }
                    except Exception as e:
                        print(f"      ❌ Error with risk_analysis: {e}")
                        formatted_result['risk_analysis'] = {'risk_score': 0, 'risk_categories': {}, 'risk_indicators': []}
                    
                    try:
                        formatted_result['full_analysis'] = safe_json_loads(metadata.get('full_analysis'), {})
                    except Exception as e:
                        print(f"      ❌ Error with full_analysis: {e}")
                        formatted_result['full_analysis'] = {}
                    
                    try:
                        formatted_result['full_article_data'] = safe_json_loads(metadata.get('full_article_data'), {})
                    except Exception as e:
                        print(f"      ❌ Error with full_article_data: {e}")
                        formatted_result['full_article_data'] = {}
                    
                    formatted_results.append(formatted_result)
                except Exception as format_error:
                    print(f"   ❌ ERROR formatting match {i}: {format_error}")
                    print(f"      Error type: {type(format_error)}")
                    continue
            
            print(f"🔍 PINECONE SEARCH - OUTPUT:")
            print(f"   Formatted results: {len(formatted_results)} articles")
            print(f"   Average text length: {sum(len(r.get('text', '')) for r in formatted_results) // len(formatted_results) if formatted_results else 0} characters")
            
            # DEBUG: Show formatted results structure
            if formatted_results:
                print(f"\n📋 FORMATTED RESULTS STRUCTURE:")
                print(f"   First result keys: {list(formatted_results[0].keys())}")
                print(f"   Articles with text: {sum(1 for r in formatted_results if r.get('text'))}")
                print(f"   Articles with analysis_timestamp: {sum(1 for r in formatted_results if r.get('analysis_timestamp'))}")
                print(f"   Articles with sentiment_analysis: {sum(1 for r in formatted_results if 'sentiment_analysis' in r)}")
                print(f"   Articles with risk_analysis: {sum(1 for r in formatted_results if 'risk_analysis' in r)}")
                print()
            
            print("=" * 80)
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching similar articles: {e}")
            logger.error(f"Error searching similar articles: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats['total_vector_count'],
                'dimension': stats['dimension'],
                'index_fullness': stats['index_fullness'],
                'namespaces': stats['namespaces']
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
