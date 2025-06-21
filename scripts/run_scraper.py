import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
import sys
import os
import argparse
import importlib.util

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'scraping_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_scraper_module(scraper_name):
    """Dynamically load a scraper module."""
    scraper_path = Path("scrapers") / f"scrape_{scraper_name}.py"
    
    if not scraper_path.exists():
        raise FileNotFoundError(f"Scraper not found: {scraper_path}")
    
    spec = importlib.util.spec_from_file_location(f"scrape_{scraper_name}", scraper_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

async def run_async_scraper(scraper_class):
    """Run an async scraper (like team stats) and save the results."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Initialize and run scraper
        scraper = scraper_class()
        data = await scraper.scrape()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f'team_stats_{timestamp}.json'
        
        # Save data to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully scraped team stats and saved to {filename}")
        logger.info(f"Found {len(data)} tables")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during team stats scraping: {str(e)}")
        return False
    finally:
        if hasattr(scraper, 'cleanup'):
            scraper.cleanup()

def run_sync_scraper(scraper_module):
    """Run a sync scraper (like matches) and save the results."""
    try:
        logger.info("Running matches scraper...")
        result = scraper_module.get_match_results()
        
        if result is not None:
            logger.info("Successfully scraped match results")
            return True
        else:
            logger.error("Matches scraper failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during matches scraping: {str(e)}")
        return False

def list_available_scrapers():
    """List all available scrapers."""
    scrapers_dir = Path("scrapers")
    scrapers = []
    
    for file in scrapers_dir.glob("scrape_*.py"):
        if file.name != "__init__.py" and file.name != "base.py":
            scraper_name = file.stem.replace("scrape_", "")
            scrapers.append(scraper_name)
    
    return scrapers

def main():
    parser = argparse.ArgumentParser(
        description="Run StatLines scrapers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_scraper.py matches        # Run matches scraper
  python scripts/run_scraper.py team_stats     # Run team stats scraper
  python scripts/run_scraper.py --list         # List available scrapers
        """
    )
    
    parser.add_argument(
        "scraper_type",
        nargs="?",
        help="Type of scraper to run (matches, team_stats)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available scrapers"
    )
    
    args = parser.parse_args()
    
    # List available scrapers
    if args.list:
        available_scrapers = list_available_scrapers()
        print("Available scrapers:")
        for scraper in available_scrapers:
            print(f"  - {scraper}")
        return
    
    # Check if scraper type is provided
    if not args.scraper_type:
        print("Error: Please specify a scraper type or use --list to see available options")
        parser.print_help()
        sys.exit(1)
    
    # Run the specified scraper
    scraper_type = args.scraper_type.lower()
    success = False
    
    if scraper_type == "matches":
        try:
            scraper_module = load_scraper_module("matches")
            success = run_sync_scraper(scraper_module)
        except Exception as e:
            logger.error(f"Failed to run matches scraper: {e}")
            
    elif scraper_type == "team_stats":
        try:
            from scrapers.scrape_team_stats import FBrefScraper
            success = asyncio.run(run_async_scraper(FBrefScraper))
        except Exception as e:
            logger.error(f"Failed to run team stats scraper: {e}")
            
    else:
        available_scrapers = list_available_scrapers()
        logger.error(f"Unknown scraper type '{scraper_type}'")
        logger.info(f"Available scrapers: {', '.join(available_scrapers)}")
        sys.exit(1)
    
    # Exit with appropriate code
    if success:
        logger.info("✅ Scraper completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Scraper failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 