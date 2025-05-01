import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
import sys
import os

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

async def run_scraper(scraper_class):
    """Run the scraper and save the results."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Initialize and run scraper
        scraper = scraper_class()
        data = await scraper.scrape()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f'premier_league_stats_{timestamp}.json'
        
        # Save data to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully scraped data and saved to {filename}")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    from scrapers.fbref_scraper import FBrefScraper
    asyncio.run(run_scraper(FBrefScraper)) 