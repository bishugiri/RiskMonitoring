#!/usr/bin/env python3
"""
Performance test script to demonstrate the optimizations.
Compares processing times before and after optimizations.
"""

import asyncio
import time
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.news_collector import NewsCollector
from risk_monitor.core.risk_analyzer import RiskAnalyzer
from risk_monitor.scripts.performance_monitor import performance_monitor

async def test_news_collection_performance():
    """Test the performance of news collection"""
    print("🚀 Testing News Collection Performance")
    print("=" * 50)
    
    collector = NewsCollector()
    
    # Test with different numbers of articles
    test_cases = [3, 5, 10]
    
    for num_articles in test_cases:
        print(f"\n📰 Testing with {num_articles} articles:")
        
        with performance_monitor.track_operation(f"collect_{num_articles}_articles", {"num_articles": num_articles}):
            articles = await collector.collect_articles_async(
                query="Apple",
                num_articles=num_articles
            )
        
        print(f"   ✅ Collected {len(articles)} articles")
        
        if articles:
            # Test analysis performance
            analyzer = RiskAnalyzer()
            
            with performance_monitor.track_operation(f"analyze_{num_articles}_articles", {"num_articles": num_articles}):
                analysis_results = await analyzer.analyze_articles_async(
                    articles, 
                    sentiment_method='llm'
                )
            
            print(f"   ✅ Analyzed {len(articles)} articles")

async def test_concurrent_processing():
    """Test concurrent processing capabilities"""
    print("\n🔄 Testing Concurrent Processing")
    print("=" * 50)
    
    collector = NewsCollector()
    analyzer = RiskAnalyzer()
    
    # Test multiple entities concurrently
    entities = ["Apple", "Microsoft", "Google"]
    
    print(f"Testing concurrent collection for {len(entities)} entities:")
    
    with performance_monitor.track_operation("concurrent_entity_collection", {"entities": entities}):
        # Collect articles for all entities concurrently
        collection_tasks = []
        for entity in entities:
            task = collector.collect_articles_async(query=entity, num_articles=3)
            collection_tasks.append(task)
        
        all_articles = await asyncio.gather(*collection_tasks)
        
        # Flatten results
        total_articles = []
        for articles in all_articles:
            total_articles.extend(articles)
    
    print(f"   ✅ Collected {len(total_articles)} total articles")
    
    if total_articles:
        # Test concurrent analysis
        with performance_monitor.track_operation("concurrent_analysis", {"total_articles": len(total_articles)}):
            analysis_results = await analyzer.analyze_articles_async(
                total_articles, 
                sentiment_method='llm'
            )
        
        print(f"   ✅ Analyzed {len(total_articles)} articles concurrently")

async def test_batch_processing():
    """Test batch processing capabilities"""
    print("\n📦 Testing Batch Processing")
    print("=" * 50)
    
    collector = NewsCollector()
    analyzer = RiskAnalyzer()
    
    # Collect a larger batch
    print("Testing batch processing with 15 articles:")
    
    with performance_monitor.track_operation("batch_collection", {"batch_size": 15}):
        articles = await collector.collect_articles_async(
            query="Apple",
            num_articles=15
        )
    
    print(f"   ✅ Collected {len(articles)} articles")
    
    if articles:
        # Test batch analysis
        with performance_monitor.track_operation("batch_analysis", {"batch_size": len(articles)}):
            analysis_results = await analyzer.analyze_articles_async(
                articles, 
                sentiment_method='llm'
            )
        
        print(f"   ✅ Analyzed {len(articles)} articles in batch")

async def main():
    """Main test function"""
    print("🎯 Risk Monitor Performance Test")
    print("=" * 60)
    print("This test will demonstrate the performance improvements")
    print("implemented in the news collection and analysis pipeline.")
    print()
    
    try:
        # Run performance tests
        await test_news_collection_performance()
        await test_concurrent_processing()
        await test_batch_processing()
        
        # Generate performance report
        print("\n📊 Performance Summary")
        print("=" * 50)
        
        summary = performance_monitor.get_summary()
        
        print(f"Total Operations: {summary['summary']['total_operations']}")
        print(f"Success Rate: {summary['summary']['success_rate']}")
        print(f"Total Duration: {summary['summary']['total_duration']}")
        print(f"Average Duration: {summary['summary']['average_duration']}")
        
        print("\n📈 Operation Statistics:")
        for op_name, stats in summary['operation_stats'].items():
            print(f"   {op_name}:")
            print(f"     Count: {stats['count']}")
            print(f"     Avg Duration: {stats['avg_duration']:.2f}s")
            print(f"     Success Rate: {stats['success_count']}/{stats['count']}")
        
        if summary['bottlenecks']:
            print("\n⚠️  Identified Bottlenecks:")
            for bottleneck in summary['bottlenecks']:
                print(f"   {bottleneck['description']}")
        
        if summary['recommendations']:
            print("\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"   • {rec}")
        
        # Save detailed report
        report_file = performance_monitor.save_report()
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
