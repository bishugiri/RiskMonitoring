#!/usr/bin/env python3
"""
Entry point script for running the Risk Monitor data refresh scheduler.
"""

import argparse
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from risk_monitor.core.scheduler import NewsScheduler

def main():
    """Main entry point for the scheduler"""
    parser = argparse.ArgumentParser(description="Risk Monitoring Scheduler")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to scheduler configuration file")
    parser.add_argument("--run-now", action="store_true",
                        help="Run the news collection immediately")
    parser.add_argument("--setup", action="store_true",
                        help="Set up the scheduler configuration")
    
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
            print("Scheduler stopped")

if __name__ == "__main__":
    main()
