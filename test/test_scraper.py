import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define headers and URL
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

async def get_page_async(url: str) -> str:
    """Fetch a page asynchronously with rate limiting."""
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

async def main():
    try:
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Fetch the page
        html = await get_page_async(base_url)
        print(f"Successfully fetched {len(html)} characters")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = data_dir / f'fbref_raw_{timestamp}.html'
        
        # Save raw HTML
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Raw HTML saved to: {html_filename}")
        
        # Parse the HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Save parsed tables to a separate file
        tables_data = {}
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables")
        
        # Extract and save table data
        for i, table in enumerate(tables):
            table_name = table.get('id')
            
            # Extract table data
            rows = []
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.get_text(strip=True) for cell in cells]
                    rows.append(row)
            
            if rows:
                tables_data[table_name] = rows
        
        # Save parsed tables data
        tables_filename = data_dir / f'fbref_tables_{timestamp}.json'
        import json
        with open(tables_filename, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)
        print(f"Parsed tables saved to: {tables_filename}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 