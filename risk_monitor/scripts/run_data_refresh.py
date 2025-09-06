#!/usr/bin/env python3
"""
Entry point script for running the Risk Monitor data refresh scheduler.
"""

import argparse
import os
import sys
import signal
import logging

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from risk_monitor.core.scheduler import NewsScheduler

# Set up signal handler for graceful shutdown
def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}. Shutting down scheduler gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for the scheduler"""
    parser = argparse.ArgumentParser(description="Risk Monitoring Scheduler")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to scheduler configuration file")
    parser.add_argument("--run-now", action="store_true",
                        help="Run the news collection immediately")
    parser.add_argument("--setup", action="store_true",
                        help="Set up the scheduler configuration")
    parser.add_argument("--test", action="store_true",
                        help="Test the scheduler configuration and dependencies")
    
    args = parser.parse_args()
    
    # Initialize scheduler
    scheduler = NewsScheduler(args.config)
    
    # Set up configuration if requested
    if args.setup:
        print("Setting up scheduler configuration...")
        
        # Get run time
        run_time = input(f"Enter daily run time (HH:MM, default {scheduler.config.DEFAULT_RUN_TIME}): ")
        if run_time:
            scheduler.config.run_time = run_time
        
        # Get timezone
        timezone = input(f"Enter timezone (default {scheduler.config.DEFAULT_TIMEZONE}): ")
        if timezone:
            scheduler.config.timezone = timezone
        
        # Get articles per entity
        articles_input = input(f"Enter articles per entity (default {scheduler.config.DEFAULT_ARTICLES_PER_ENTITY}): ")
        if articles_input:
            try:
                scheduler.config.articles_per_entity = int(articles_input)
            except ValueError:
                print(f"Invalid input. Using default: {scheduler.config.DEFAULT_ARTICLES_PER_ENTITY}")
        
        # Get entities
        entities_input = input("Enter entities to monitor (comma-separated): ")
        if entities_input:
            scheduler.config.entities = [e.strip() for e in entities_input.split(",")]
        
        # Get keywords
        keywords_input = input("Enter keywords to filter (comma-separated, leave blank for no filtering): ")
        if keywords_input:
            scheduler.config.keywords = [k.strip() for k in keywords_input.split(",")]
        
        # Get sentiment analysis method
        use_openai = input("Use OpenAI for sentiment analysis? (y/n, default y): ")
        scheduler.config.use_openai = use_openai.lower() != "n"
        
        # Save configuration
        scheduler.config.save_config()
        print(f"Configuration saved to {scheduler.config.config_file}")
    
    # Test mode if requested
    if args.test:
        print("Testing scheduler configuration and dependencies...")
        try:
            # Test configuration loading
            print("✓ Configuration loaded successfully")
            
            # Test dependencies
            import streamlit
            print("✓ Streamlit available")
            
            import openai
            print("✓ OpenAI available")
            
            import pinecone
            print("✓ Pinecone available")
            
            # Test scheduler initialization
            scheduler = NewsScheduler(args.config)
            print("✓ Scheduler initialized successfully")
            
            print("✓ All tests passed! Scheduler is ready to run.")
            return
        except Exception as e:
            print(f"✗ Test failed: {e}")
            sys.exit(1)
    
    # Run now if requested
    if args.run_now:
        scheduler.run_now()
    else:
        # Start the scheduler
        print(f"Starting scheduler. Will run daily at {scheduler.config.run_time} {scheduler.config.timezone}")
        print("Press Ctrl+C to exit")
        try:
            scheduler.schedule_daily_run()
        except KeyboardInterrupt:
            print("Scheduler stopped by user")
        except Exception as e:
            print(f"Scheduler error: {e}")
            logging.error(f"Scheduler error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
